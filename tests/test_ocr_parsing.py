"""Tests fuer den Markdown-Parser der german-ocr Ausgabe."""

from __future__ import annotations

from datetime import date

import pytest

# ocr_engine zieht via pdf_reader PyMuPDF nach; in CI ohne diese Bibliothek
# werden die reinen Parser-Tests uebersprungen.
pytest.importorskip("fitz")
pytest.importorskip("ollama")

from core.models import DocumentType  # noqa: E402
from core.ocr_engine import _parse_german_markdown, _parse_response  # noqa: E402


GERMAN_OCR_MARKDOWN = """
# Amazon Rechnung

## Absender
**Amazon EU S.a.r.l.**

**Rechnungsnummer:** INV-98765
**Rechnungsdatum:** 15.03.2026
**Fälligkeitsdatum:** 30.03.2026

| Pos. | Beschreibung       | Menge | Einzelpreis | Gesamt  |
|------|--------------------|-------|-------------|---------|
| 1    | Buch               | 2     | 19,95       | 39,90   |
| 2    | Versand            | 1     | 4,99        | 4,99    |

**Gesamtbetrag:** 44,89 €
**MwSt (19%):** 7,17 €

IBAN: DE11 2345 6789 0000 1234 56
**Kundennummer:** 123-4567890-1234567
"""


class TestGermanMarkdownParser:
    def setup_method(self):
        self.result = _parse_german_markdown(GERMAN_OCR_MARKDOWN)

    def test_invoice_number(self):
        assert self.result.invoice_number == "INV-98765"

    def test_date(self):
        assert self.result.date == date(2026, 3, 15)

    def test_due_date(self):
        assert self.result.due_date == date(2026, 3, 30)

    def test_total_amount(self):
        assert self.result.total_amount == 44.89

    def test_vat_rate(self):
        assert self.result.vat_rate == 19.0

    def test_vat_amount(self):
        assert self.result.vat_amount == 7.17

    def test_iban_whitespace_removed(self):
        assert self.result.iban == "DE11234567890000123456"

    def test_customer_number(self):
        assert self.result.customer_number == "123-4567890-1234567"

    def test_document_type_from_heading(self):
        assert self.result.document_type == DocumentType.INVOICE

    def test_line_items_parsed(self):
        assert len(self.result.line_items) == 2
        first = self.result.line_items[0]
        assert first.description == "Buch"
        assert first.quantity == 2
        assert first.unit_price == 19.95
        assert first.total == 39.90


class TestOllamaJsonParser:
    def test_parses_valid_json(self):
        raw = (
            'Hier das Ergebnis: ```json\n'
            '{"sender":"Telekom",'
            '"date":"2026-01-15",'
            '"invoice_number":"R-42",'
            '"total_amount":59.99,'
            '"currency":"EUR",'
            '"document_type":"rechnung",'
            '"line_items":[{"description":"Mobilfunk","quantity":1,"unit_price":59.99,"total":59.99}]'
            '}```'
        )
        result = _parse_response(raw)
        assert result.sender == "Telekom"
        assert result.invoice_number == "R-42"
        assert result.total_amount == 59.99
        assert result.date == date(2026, 1, 15)
        assert result.document_type == DocumentType.INVOICE
        assert len(result.line_items) == 1

    def test_missing_json_returns_empty_with_low_confidence(self):
        result = _parse_response("Keine strukturierte Antwort erhalten.")
        assert result.sender == ""
        assert result.confidence["overall"] == 0.1

    def test_invalid_json_returns_empty(self):
        result = _parse_response("{ not valid json")
        assert result.sender == ""
        assert result.confidence["overall"] == 0.1

    def test_unknown_document_type_falls_back_to_other(self):
        raw = '{"sender":"X","document_type":"unknown","total_amount":1.0}'
        result = _parse_response(raw)
        assert result.document_type == DocumentType.OTHER
