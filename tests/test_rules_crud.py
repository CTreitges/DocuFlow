"""F3-Tests: granulares Regel-CRUD über die API (create/update/reorder/delete).

Isoliert RULES_FILE in tmp_path, damit die echte data/rules.yaml unangetastet
bleibt. Prüft Persistenz auf Platte und 404-Verhalten.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUFLOW_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("DOCUFLOW_NO_OLLAMA", "1")
    import core.rules_store as rs

    monkeypatch.setattr(rs, "RULES_FILE", tmp_path / "rules.yaml")
    from backend.main import app

    with TestClient(app) as c:
        c._rules_file = tmp_path / "rules.yaml"  # für Persistenz-Checks
        yield c


def _new_rule(name="Amazon", value="Amazon"):
    return {
        "id": "", "name": name,
        "conditions": [{"field": "absender", "operator": "enthaelt", "value": value, "logic": "AND"}],
        "target_base": "/tmp/out", "target_subfolders": ["{jahr}", "{absender}"],
        "filename_parts": ["{datum}", "{rechnungsnr}"], "enabled": True, "priority": 0,
    }


def test_create_assigns_id_and_persists(client):
    before = client.get("/api/rules").json()
    r = client.post("/api/rules", json=_new_rule())
    assert r.status_code == 200
    created = r.json()
    assert created["id"]  # ID wurde vergeben
    assert created["name"] == "Amazon"

    after = client.get("/api/rules").json()
    assert len(after) == len(before) + 1
    assert any(x["id"] == created["id"] for x in after)

    # Auf Platte persistiert?
    from core.rules_store import load_rules
    on_disk = load_rules(client._rules_file)
    assert any(x.id == created["id"] for x in on_disk)


def test_update_changes_fields(client):
    created = client.post("/api/rules", json=_new_rule()).json()
    upd = _new_rule(name="Amazon EU", value="Amazon EU")
    upd["enabled"] = False
    r = client.put(f"/api/rules/{created['id']}", json=upd)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Amazon EU"
    assert body["enabled"] is False
    assert body["id"] == created["id"]  # ID bleibt stabil

    fetched = next(x for x in client.get("/api/rules").json() if x["id"] == created["id"])
    assert fetched["name"] == "Amazon EU"
    assert fetched["enabled"] is False


def test_update_unknown_404(client):
    r = client.put("/api/rules/gibtsnicht", json=_new_rule())
    assert r.status_code == 404


def test_delete_removes_and_persists(client):
    created = client.post("/api/rules", json=_new_rule()).json()
    r = client.delete(f"/api/rules/{created['id']}")
    assert r.status_code == 200
    assert r.json()["deleted"] == created["id"]
    assert not any(x["id"] == created["id"] for x in client.get("/api/rules").json())

    from core.rules_store import load_rules
    assert not any(x.id == created["id"] for x in load_rules(client._rules_file))


def test_delete_unknown_404(client):
    r = client.delete("/api/rules/gibtsnicht")
    assert r.status_code == 404


def test_reorder_sets_priority(client):
    a = client.post("/api/rules", json=_new_rule(name="A")).json()
    b = client.post("/api/rules", json=_new_rule(name="B")).json()
    c = client.post("/api/rules", json=_new_rule(name="C")).json()
    # Umkehren: c, b, a
    order = [c["id"], b["id"], a["id"]]
    r = client.post("/api/rules/reorder", json={"order": order})
    assert r.status_code == 200

    rules = client.get("/api/rules").json()
    prio = {x["id"]: x["priority"] for x in rules}
    assert prio[c["id"]] < prio[b["id"]] < prio[a["id"]]
