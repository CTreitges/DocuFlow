"""K1-Regression: process_and_maybe_auto_sort sortiert nur bei echter Konfidenz.

Prueft die Gating-Logik direkt: Auto-Modus AUS, unter Schwellwert, ueber Schwellwert.
process_document wird gestubbt, damit kein PDF/OCR noetig ist.
"""

from __future__ import annotations

import asyncio
from datetime import date

import pytest

from core.models import (
    Document,
    DocumentStatus,
    ExtractionResult,
    SortRule,
)
from core.processor import Processor


class _StubDB:
    def __init__(self):
        self.history: list[tuple[str, str]] = []

    def update_document(self, doc):  # noqa: D401
        pass

    def add_history(self, document_id, action, details=""):
        self.history.append((action, details))


def _make_processor(tmp_path, *, auto_mode: bool, threshold: float = 0.9) -> Processor:
    proc = Processor.__new__(Processor)  # __init__ umgehen (laedt OCR/Templates)
    proc.db = _StubDB()
    proc.cfg = {
        "auto_mode": auto_mode,
        "auto_confidence_threshold": threshold,
        "templates": {"path": str(tmp_path / "templates")},
    }
    proc._templates = []
    proc._rules = [
        SortRule(
            id="fallback",
            name="alle",
            conditions=[],
            target_base=str(tmp_path / "out"),
            target_subfolders=["{jahr}"],
            filename_parts=["{datum}", "{absender}"],
            enabled=True,
            priority=0,
        )
    ]
    return proc


def _reviewed_doc(tmp_path, overall: float) -> Document:
    src = tmp_path / "rechnung.pdf"
    src.write_bytes(b"%PDF-1.4 dummy")
    return Document(
        id=1,
        file_path=str(src),
        file_name="rechnung.pdf",
        status=DocumentStatus.REVIEW,
        template_id="amazon_1",
        extraction=ExtractionResult(
            sender="Amazon",
            date=date(2026, 3, 15),
            invoice_number="INV-1",
            confidence={"overall": overall, "sender": 1.0},
        ),
    )


def _patch_process(proc: Processor, doc: Document) -> None:
    async def _fake(_doc, on_stage=None):
        # Signatur spiegelt das echte process_document (optionaler Stage-Callback).
        if on_stage:
            on_stage("done")
        return doc
    proc.process_document = _fake  # type: ignore[assignment]


def test_auto_mode_off_never_sorts(tmp_path):
    proc = _make_processor(tmp_path, auto_mode=False)
    doc = _reviewed_doc(tmp_path, overall=0.99)
    _patch_process(proc, doc)

    _, sorted_ = asyncio.run(proc.process_and_maybe_auto_sort(doc))
    assert sorted_ is False
    assert (tmp_path / "rechnung.pdf").exists()  # nicht verschoben


def test_below_threshold_skips(tmp_path):
    proc = _make_processor(tmp_path, auto_mode=True, threshold=0.9)
    doc = _reviewed_doc(tmp_path, overall=0.5)
    _patch_process(proc, doc)

    _, sorted_ = asyncio.run(proc.process_and_maybe_auto_sort(doc))
    assert sorted_ is False
    assert any(a == "auto_skipped" for a, _ in proc.db.history)
    assert (tmp_path / "rechnung.pdf").exists()


def test_above_threshold_auto_sorts(tmp_path):
    proc = _make_processor(tmp_path, auto_mode=True, threshold=0.9)
    doc = _reviewed_doc(tmp_path, overall=0.95)
    _patch_process(proc, doc)

    result_doc, sorted_ = asyncio.run(proc.process_and_maybe_auto_sort(doc))
    assert sorted_ is True
    assert result_doc.status == DocumentStatus.PROCESSED
    assert result_doc.sorted_path is not None
    moved = (tmp_path / "out").resolve()
    assert moved in __import__("pathlib").Path(result_doc.sorted_path).resolve().parents
    assert not (tmp_path / "rechnung.pdf").exists()  # Quelle wurde verschoben
    assert any(a == "auto_sorted" for a, _ in proc.db.history)
