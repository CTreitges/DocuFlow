"""Regressionstest TD-03 — zentrales Parsen deutscher Betraege.

Deckt explizit die in ANALYSE_2026-06-02.md §2 genannten Bugs ab:
'1.234' wurde zu 1.234 (statt 1234), '1.500' zu 1.5 (statt 1500). Diese kamen
vom reinen str.replace-/_safe_float_de-Pfad, der den Tausenderpunkt ohne Komma
nicht behandelte.
"""

from __future__ import annotations

import pytest

from core.number_parser import parse_amount

CASES = [
    # (input, erwartet)
    ("1.234", 1234.0),        # <- ANALYSE-Bug: war 1.234
    ("1.500", 1500.0),        # <- ANALYSE-Bug: war 1.5
    ("1.234,56", 1234.56),
    ("1.500,50", 1500.5),
    ("1234,56", 1234.56),
    ("1234.56", 1234.56),     # einzelner Punkt, !=3 Nachkommastellen -> Dezimal
    ("1.234.567", 1234567.0),  # mehrere Tausenderpunkte
    ("1.234.567,89", 1234567.89),
    ("19,5%", 19.5),
    ("1.234,56 €", 1234.56),
    ("-1.500", -1500.0),
    ("-1.234,56", -1234.56),
    ("0", 0.0),
    ("1,5", 1.5),
    ("1.5", 1.5),             # einzelner Punkt, 1 Stelle -> Dezimal
    ("123", 123.0),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_parse_amount_values(text, expected):
    assert parse_amount(text) == pytest.approx(expected)


@pytest.mark.parametrize("bad", [None, "", "   ", "abc", "€", "-", "1.2.3.4abc"])
def test_parse_amount_unparsable_returns_none(bad):
    assert parse_amount(bad) is None


def test_thousands_dot_bug_is_fixed_via_ocr_helper():
    """Die OCR-Helfer-Weiterleitung _safe_float_de muss denselben Fix erben."""
    from core.ocr_engine import _safe_float_de

    assert _safe_float_de("1.234") == 1234.0
    assert _safe_float_de("1.500") == 1500.0
    assert _safe_float_de("1.234,56") == pytest.approx(1234.56)
