"""K2-Regression: Path-Traversal-Schutz im Datei-Organizer.

Bug (vorher): _sanitize_filename saeuberte nur den Dateinamen, nicht die
Ordner-Segmente. Ein OCR-Platzhalter wie {absender} = '../../x' lenkte
shutil.move aus dem Basisordner heraus.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from core.file_organizer import (
    build_target_path,
    preview_target_path,
    _sanitize_segment,
)
from core.models import Document, ExtractionResult, SortRule


def _doc(sender: str) -> Document:
    return Document(
        file_path="/tmp/x.pdf",
        file_name="x.pdf",
        extraction=ExtractionResult(sender=sender, date=date(2026, 3, 15)),
    )


def _rule(base: Path) -> SortRule:
    return SortRule(
        id="r",
        name="r",
        conditions=[],
        target_base=str(base),
        target_subfolders=["{jahr}", "{absender}"],
        filename_parts=["{datum}", "{absender}"],
        enabled=True,
        priority=0,
    )


def test_sanitize_segment_strips_traversal():
    assert _sanitize_segment("../../etc") == "etc"
    assert _sanitize_segment("..\\..\\Windows") == "Windows"
    assert _sanitize_segment("a/b") == "a_b"
    assert _sanitize_segment("..") == ""
    assert _sanitize_segment(".") == ""
    assert _sanitize_segment("Amazon") == "Amazon"


def test_build_target_path_blocks_unix_traversal(tmp_path):
    base = tmp_path / "out"
    target = build_target_path(_doc("../../../../etc/passwd"), _rule(base))
    assert target.resolve().is_relative_to(base.resolve()), f"escaped base: {target}"


def test_build_target_path_blocks_windows_traversal(tmp_path):
    base = tmp_path / "out"
    target = build_target_path(_doc("..\\..\\..\\Windows\\System32"), _rule(base))
    assert target.resolve().is_relative_to(base.resolve()), f"escaped base: {target}"


def test_preview_target_path_blocks_traversal(tmp_path):
    base = tmp_path / "out"
    ext = ExtractionResult(sender="../../secret", date=date(2026, 3, 15))
    preview = preview_target_path(ext, _rule(base))
    assert Path(preview).resolve().is_relative_to(base.resolve())


def test_normal_sender_still_works(tmp_path):
    base = tmp_path / "out"
    target = build_target_path(_doc("Amazon"), _rule(base))
    assert target.resolve().is_relative_to(base.resolve())
    assert "Amazon" in str(target)
    assert target.name.endswith(".pdf")
    assert "2026" in str(target)
