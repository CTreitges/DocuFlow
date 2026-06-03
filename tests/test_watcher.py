"""F5: Watchdog-Integration ueber die API + deterministischer Verarbeitungspfad.

Der Lifecycle (start/stop) laeuft ueber die Endpoints. Die eigentliche
Verarbeitung wird deterministisch getestet, indem der Worker-Schritt direkt
aufgerufen wird — nicht ueber reale Observer-Events (deren Timing waere flaky).
"""

from __future__ import annotations


def test_watch_start_stop_lifecycle(iso_client):
    c = iso_client
    started = c.post("/api/watch/start").json()
    assert started["running"] is True
    assert any("inbox" in f for f in started["folders"])

    status = c.get("/api/watch/status").json()
    assert status["running"] is True

    stopped = c.post("/api/watch/stop").json()
    assert stopped["running"] is False
    assert c.get("/api/watch/status").json()["running"] is False


def test_watch_status_shape(iso_client):
    st = iso_client.get("/api/watch/status").json()
    for key in ("running", "folders", "queue", "current", "recent", "processed_count", "error_count"):
        assert key in st
    assert st["running"] is False  # kein Autostart


def test_watcher_processes_dropped_file(iso_client, make_pdf):
    c = iso_client
    make_pdf(c.env.inbox / "drop.pdf", "RECHNUNG\nTest GmbH\nBetrag: 5,00 EUR")

    watcher = c.app.state.docuflow.watcher
    # Direkter, deterministischer Aufruf des Worker-Schritts (ohne Observer).
    watcher._scan_and_process()

    docs = c.get("/api/documents").json()
    assert len(docs) == 1
    assert docs[0]["status"] == "review"
    assert docs[0]["extraction"]["raw_text"]

    st = watcher.status()
    assert st["processed_count"] >= 1
    assert st["error_count"] == 0
    assert st["recent"] and st["recent"][0]["file"] == "drop.pdf"


def test_watch_scan_now_registers_without_running(iso_client, make_pdf):
    c = iso_client
    make_pdf(c.env.inbox / "neu.pdf", "RECHNUNG\nXY GmbH")
    r = c.post("/api/watch/scan-now").json()
    assert r["new"] == 1
    assert r["watching"] is False
    # Datei ist als 'neu' registriert (Verarbeitung erfolgt beim laufenden Watcher).
    docs = c.get("/api/documents").json()
    assert docs and docs[0]["file_name"] == "neu.pdf"
