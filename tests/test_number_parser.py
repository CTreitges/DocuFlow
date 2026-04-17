"""Tests fuer den toleranten Zahlen-Parser."""

from __future__ import annotations

import pytest

from core.number_parser import parse_amount


class TestGermanFormat:
    def test_thousands_dot_decimal_comma(self):
        assert parse_amount("1.234,56") == 1234.56

    def test_thousands_dot_decimal_comma_with_currency(self):
        assert parse_amount("1.234,56 €") == 1234.56

    def test_simple_decimal_comma(self):
        assert parse_amount("12,50") == 12.5

    def test_no_decimals(self):
        assert parse_amount("1234") == 1234.0


class TestEnglishFormat:
    def test_thousands_comma_decimal_dot(self):
        assert parse_amount("1,234.56") == 1234.56

    def test_simple_decimal_dot(self):
        assert parse_amount("12.50") == 12.5


class TestCurrency:
    def test_euro_symbol(self):
        assert parse_amount("€ 99,99") == 99.99

    def test_eur_string(self):
        assert parse_amount("99.99 EUR") == 99.99

    def test_dollar_symbol(self):
        assert parse_amount("$1,500.00") == 1500.0

    def test_percent_sign(self):
        assert parse_amount("19%") == 19.0

    def test_decimal_percent(self):
        assert parse_amount("7,5%") == 7.5


class TestEdgeCases:
    def test_none(self):
        assert parse_amount(None) is None

    def test_empty(self):
        assert parse_amount("") is None

    def test_whitespace(self):
        assert parse_amount("   ") is None

    def test_not_a_number(self):
        assert parse_amount("abc") is None

    def test_int_passthrough(self):
        assert parse_amount(42) == 42.0

    def test_float_passthrough(self):
        assert parse_amount(3.14) == 3.14

    @pytest.mark.parametrize("val,expected", [
        ("10,00", 10.0),
        ("0,01", 0.01),
        ("1 234,56", 1234.56),       # Leerzeichen als Tausender-Trennung
        ("1234.5", 1234.5),
    ])
    def test_varied_formats(self, val, expected):
        assert parse_amount(val) == expected

    def test_ambiguous_single_dot_treated_as_decimal(self):
        """'1.000' ist mehrdeutig — Parser interpretiert isoliertes Komma-freies
        Format als englischen Dezimaltrenner (sicherer Default)."""
        assert parse_amount("1.000") == 1.0
