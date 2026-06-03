"""Geteilte Fixtures fuer die Integrationstests.

iso_env/iso_client isolieren Config, DB, Regeln und Templates vollstaendig in
tmp_path (via DOCUFLOW_CONFIG/DOCUFLOW_RULES/DOCUFLOW_DB), damit echte Projekt-
dateien unangetastet bleiben und Tests parallelisierbar sind. Kein Ollama.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from ruamel.yaml import YAML

_yaml = YAML()
_yaml.default_flow_style = False


def _write_yaml(path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        _yaml.dump(data, f)


@pytest.fixture()
def iso_env(tmp_path, monkeypatch):
    inbox = tmp_path / "inbox"; inbox.mkdir()
    out = tmp_path / "out"; out.mkdir()
    tpl = tmp_path / "templates"; tpl.mkdir()
    cfg_path = tmp_path / "config.yaml"
    rules_path = tmp_path / "rules.yaml"

    _write_yaml(cfg_path, {
        "app": {"name": "DocuFlow", "version": "test"},
        "input_folders": [{"path": str(inbox), "enabled": True, "watch": True}],
        "output": {"base_path": str(out)},
        "auto_mode": False,
        "auto_confidence_threshold": 0.9,
        "german_ocr": {"enabled": False, "backend": "ollama"},
        # Unerreichbare Ollama-URL -> is_available() faellt schnell auf False zurueck.
        "ollama": {"url": "http://127.0.0.1:1", "model": "none", "timeout": 1},
        "database": {"path": str(tmp_path / "df.db")},
        "templates": {"path": str(tpl)},
    })
    # Fallback-Regel, die in den Test-Ausgabeordner sortiert (sonst nach ./sorted).
    _write_yaml(rules_path, [{
        "id": "fallback", "name": "Fallback", "conditions": [],
        "target_base": str(out), "target_subfolders": ["{jahr}"],
        "filename_parts": ["{datum}", "{absender}"], "enabled": True, "priority": 999,
    }])

    monkeypatch.setenv("DOCUFLOW_CONFIG", str(cfg_path))
    monkeypatch.setenv("DOCUFLOW_RULES", str(rules_path))
    monkeypatch.setenv("DOCUFLOW_NO_OLLAMA", "1")
    return SimpleNamespace(
        inbox=inbox, out=out, tpl=tpl, cfg_path=cfg_path, rules_path=rules_path, tmp=tmp_path
    )


@pytest.fixture()
def iso_client(iso_env):
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as c:
        c.env = iso_env
        yield c


@pytest.fixture()
def make_pdf():
    """Erzeugt ein einseitiges PDF mit eingebetteter Textebene."""
    fitz = pytest.importorskip("fitz")

    def _make(path, text):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        doc.save(str(path))
        doc.close()
        return path

    return _make


@pytest.fixture()
def write_template():
    """Schreibt ein Template-YAML (Hand-Template fuer Auto-Sort-Tests)."""
    def _write(path, *, sender_name="Foo GmbH", sender_patterns, threshold=0.9, field_patterns=None):
        _write_yaml(path, {
            "id": path.stem,
            "sender_name": sender_name,
            "sender_patterns": list(sender_patterns),
            "field_patterns": field_patterns or {},
            "confidence_threshold": threshold,
            "times_used": 0,
            "last_used": None,
        })
        return path

    return _write
