"""Tests fuer den Template-Matcher (Muster-basierte Extraktion)."""

from __future__ import annotations

from datetime import date

from core.models import Template
from core.template_matcher import _calculate_match_score, extract_with_template, match_template


AMAZON_TPL = Template(
    id="amazon",
    sender_name="Amazon",
    sender_patterns=[r"Amazon EU", r"amazon\.de"],
    field_patterns={
        "invoice_number": r"Rechnungs-?Nr\.?\s*:\s*([A-Z0-9\-]+)",
        "total_amount": r"Gesamt:\s*([\d\.,]+)\s*EUR",
        "date": r"Datum:\s*(\d{4}-\d{2}-\d{2})",
        "iban": r"IBAN:\s*([A-Z0-9]+)",
    },
    confidence_threshold=0.5,
)


SAMPLE_TEXT = """
Amazon EU S.a.r.l.
amazon.de
Rechnung

Rechnungs-Nr: INV-98765
Datum: 2026-03-15
Gesamt: 1.234,56 EUR
IBAN: DE11234567890000
"""


def test_match_score_both_patterns():
    assert _calculate_match_score(SAMPLE_TEXT, AMAZON_TPL) == 1.0


def test_match_score_no_patterns():
    empty = Template(id="x", sender_name="X", sender_patterns=[])
    assert _calculate_match_score(SAMPLE_TEXT, empty) == 0.0


def test_match_template_returns_matching():
    tpl, score = match_template(SAMPLE_TEXT, [AMAZON_TPL])
    assert tpl is not None
    assert tpl.id == "amazon"
    assert score == 1.0


def test_match_template_below_threshold():
    strict = AMAZON_TPL.model_copy(update={"confidence_threshold": 1.5})
    tpl, score = match_template(SAMPLE_TEXT, [strict])
    assert tpl is None
    assert score == 0.0


def test_extract_with_template_fills_fields():
    result = extract_with_template(SAMPLE_TEXT, AMAZON_TPL)
    assert result.sender == "Amazon"
    assert result.invoice_number == "INV-98765"
    assert result.total_amount == 1234.56            # deutsches Format muss korrekt geparst werden
    assert result.date == date(2026, 3, 15)
    assert result.iban == "DE11234567890000"
    assert result.confidence["sender"] == 1.0
    # Felder mit erfolgreichem Match bekommen 0.95
    assert result.confidence["invoice_number"] == 0.95
    assert result.confidence["total_amount"] == 0.95


def test_extract_with_template_missing_field():
    text_missing = "Amazon EU S.a.r.l.\namazon.de\nRechnung"
    result = extract_with_template(text_missing, AMAZON_TPL)
    assert result.sender == "Amazon"
    assert result.invoice_number == ""
    assert result.total_amount is None
    assert result.confidence["invoice_number"] == 0.0


def test_extract_handles_invalid_regex_gracefully():
    bad_tpl = AMAZON_TPL.model_copy(update={
        "field_patterns": {"invoice_number": r"(unclosed"}
    })
    result = extract_with_template(SAMPLE_TEXT, bad_tpl)
    # Sollte nicht werfen und confidence auf 0 setzen
    assert result.confidence["invoice_number"] == 0.0
