"""F5: End-to-End-Integration ueber die echte API (TestClient).

Deckt den vollen Lebenszyklus ab: Scan -> Verarbeitung -> Korrektur -> Bestaetigen
-> Datei physisch sortiert. Plus Auto-Sortierung (K1) ueber die API: positiv via
Lernschleife (PLAN.md: einmal bestaetigen, dann automatisch) und negativ via
Konfidenz-Schwellwert.
"""

from __future__ import annotations

from pathlib import Path

AMAZON = "RECHNUNG\nAmazon EU S.a.r.l.\nRechnungsnummer: {nr}\nDatum: 2026-03-15\nGesamtbetrag: 249,90 EUR"


def test_scan_process_confirm_sorts_file(iso_client, make_pdf):
    c = iso_client
    make_pdf(c.env.inbox / "amazon1.pdf", AMAZON.format(nr="INV-2026-0042"))

    assert c.post("/api/scan").json()["new"] == 1
    doc_id = c.get("/api/documents").json()[0]["id"]

    pr = c.post(f"/api/documents/{doc_id}/process").json()
    assert pr["document"]["status"] == "review"
    assert pr["document"]["extraction"]["raw_text"]  # Textebene wurde gelesen

    # Nutzer-Korrektur der Felder
    ext = dict(pr["document"]["extraction"])
    ext.update(sender="Amazon EU", date="2026-03-15", invoice_number="INV-2026-0042")
    rp = c.patch(f"/api/documents/{doc_id}/extraction", json={"extraction": ext})
    assert rp.status_code == 200
    assert rp.json()["extraction"]["sender"] == "Amazon EU"

    # Bestaetigen -> Datei wird sortiert
    cr = c.post(f"/api/documents/{doc_id}/confirm").json()
    sorted_path = cr["sorted_path"]
    assert sorted_path is not None
    p = Path(sorted_path)
    assert p.exists()
    assert c.env.out.resolve() in p.resolve().parents      # innerhalb des Ausgabeordners
    assert not (c.env.inbox / "amazon1.pdf").exists()        # Quelle verschoben
    assert cr["document"]["status"] == "verarbeitet"

    assert any(h["action"] == "sorted" for h in c.get("/api/history").json())


def test_learning_loop_auto_sorts_second_document(iso_client, make_pdf):
    """K1 lebt: nach Bestaetigung von Dok 1 wird ein Template erzeugt; ein zweites
    Dokument desselben Absenders wird automatisch sortiert."""
    c = iso_client

    # Dok 1: verarbeiten, korrigieren, bestaetigen -> Template entsteht
    make_pdf(c.env.inbox / "amazon_a.pdf", AMAZON.format(nr="INV-A1"))
    c.post("/api/scan")
    d1 = c.get("/api/documents").json()[0]["id"]
    p1 = c.post(f"/api/documents/{d1}/process").json()["document"]
    ext = dict(p1["extraction"])
    ext.update(sender="Amazon EU", date="2026-03-15", invoice_number="INV-A1")
    c.patch(f"/api/documents/{d1}/extraction", json={"extraction": ext})
    c.post(f"/api/documents/{d1}/confirm")
    assert c.get("/api/templates").json(), "Template sollte nach Bestaetigung existieren"

    # Auto-Modus an
    r = c.put("/api/settings", json={"auto_mode": True, "auto_confidence_threshold": 0.9})
    assert r.status_code == 200

    # Dok 2: gleicher Absender -> automatisch sortiert (kein manueller Schritt)
    make_pdf(c.env.inbox / "amazon_b.pdf", AMAZON.format(nr="INV-B2"))
    c.post("/api/scan")
    d2 = next(d["id"] for d in c.get("/api/documents").json() if d["file_name"] == "amazon_b.pdf")
    res = c.post(f"/api/documents/{d2}/process").json()

    assert res["auto_sorted"] is True, res
    assert res["document"]["status"] == "verarbeitet"
    assert res["document"]["template_id"]
    assert not (c.env.inbox / "amazon_b.pdf").exists()       # automatisch verschoben
    assert any(h["action"] == "auto_sorted" for h in c.get("/api/history").json())


def test_auto_sort_below_threshold_stays_in_inbox(iso_client, make_pdf, write_template):
    """Negativ: Template matcht (Score 0.5), aber unter dem Auto-Schwellwert (0.9)
    -> Dokument bleibt zur Pruefung in der Inbox (auto_skipped)."""
    c = iso_client
    # 2 Muster, das Dokument trifft nur eins -> Score 0.5; Template-Schwelle 0.4.
    write_template(
        c.env.tpl / "foo.yaml",
        sender_patterns=["Foo GmbH", "WIRD_NIE_VORKOMMEN_XZ"],
        threshold=0.4,
    )
    c.app.state.docuflow.processor.reload_templates()
    c.put("/api/settings", json={"auto_mode": True, "auto_confidence_threshold": 0.9})

    make_pdf(c.env.inbox / "foo.pdf", "RECHNUNG\nFoo GmbH\nBetrag: 10,00 EUR")
    c.post("/api/scan")
    d = c.get("/api/documents").json()[0]["id"]
    res = c.post(f"/api/documents/{d}/process").json()

    assert res["auto_sorted"] is False
    assert res["document"]["status"] == "review"             # in Inbox geblieben
    assert res["document"]["template_id"]                     # Template hat gematcht
    assert abs(res["document"]["extraction"]["confidence"]["overall"] - 0.5) < 1e-6
    assert (c.env.inbox / "foo.pdf").exists()                 # NICHT verschoben
    assert any(h["action"] == "auto_skipped" for h in c.get("/api/history").json())


def test_auto_mode_off_keeps_documents_in_review(iso_client, make_pdf, write_template):
    """Negativ: bei ausgeschaltetem Auto-Modus wird trotz Template nicht sortiert."""
    c = iso_client
    write_template(c.env.tpl / "foo.yaml", sender_patterns=["Foo GmbH"], threshold=0.5)
    c.app.state.docuflow.processor.reload_templates()
    # auto_mode bleibt aus (Default)

    make_pdf(c.env.inbox / "foo.pdf", "RECHNUNG\nFoo GmbH\nBetrag: 10,00 EUR")
    c.post("/api/scan")
    d = c.get("/api/documents").json()[0]["id"]
    res = c.post(f"/api/documents/{d}/process").json()

    assert res["auto_sorted"] is False
    assert res["document"]["status"] == "review"
    assert (c.env.inbox / "foo.pdf").exists()
