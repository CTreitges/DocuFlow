"""Smoke-Test des FastAPI-Backends via TestClient (Lifespan + Kern-Endpunkte)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Isolierte Test-DB, kein Ollama-Spawn.
    monkeypatch.setenv("DOCUFLOW_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("DOCUFLOW_NO_OLLAMA", "1")
    from backend.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "auto_mode" in body
    assert "ocr_available" in body


def test_stats_empty(client):
    r = client.get("/api/stats")
    assert r.status_code == 200
    assert r.json()["gesamt"] == 0


def test_documents_empty(client):
    r = client.get("/api/documents")
    assert r.status_code == 200
    assert r.json() == []


def test_unknown_status_400(client):
    r = client.get("/api/documents", params={"status": "quatsch"})
    assert r.status_code == 400


def test_rules_default(client):
    r = client.get("/api/rules")
    assert r.status_code == 200
    rules = r.json()
    assert isinstance(rules, list) and len(rules) >= 1
    assert "target_base" in rules[0]


def test_rules_preview_blocks_traversal(client):
    # Auch ueber die API darf eine boese Extraktion nicht aus dem Basisordner ausbrechen.
    rule = {
        "id": "r", "name": "r", "conditions": [],
        "target_base": "/tmp/docuflow_out",
        "target_subfolders": ["{absender}"],
        "filename_parts": ["{datum}"], "enabled": True, "priority": 0,
    }
    extraction = {"sender": "../../etc", "date": "2026-03-15"}
    r = client.post("/api/rules/preview", json={"rule": rule, "extraction": extraction})
    assert r.status_code == 200
    preview = r.json()["preview"]
    assert ".." not in preview.replace("\\", "/").split("/tmp/docuflow_out")[-1]


def test_settings_roundtrip(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert "auto_mode" in r.json()


def test_extraction_patch_roundtrip(client):
    """Live-Pfad: editField → PATCH /extraction re-serialisiert ExtractionResult."""
    from core.models import Document, DocumentStatus, ExtractionResult

    db = client.app.state.docuflow.db
    doc = Document(
        file_path="/tmp/x.pdf", file_name="x.pdf", status=DocumentStatus.REVIEW,
        extraction=ExtractionResult(sender="Alt GmbH", confidence={"overall": 0.9, "sender": 0.9}),
    )
    doc.id = db.add_document(doc)

    new_ext = doc.extraction.model_dump(mode="json")
    new_ext["sender"] = "Neu GmbH"
    r = client.patch(f"/api/documents/{doc.id}/extraction", json={"extraction": new_ext})
    assert r.status_code == 200
    assert r.json()["extraction"]["sender"] == "Neu GmbH"

    # Persistenz pruefen
    r2 = client.get(f"/api/documents/{doc.id}")
    assert r2.status_code == 200
    assert r2.json()["extraction"]["sender"] == "Neu GmbH"
