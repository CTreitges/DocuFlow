"""Tests fuer den Datei-Organizer (Regel-Auswertung, Pfad-Aufbau, Dateinamen)."""

from __future__ import annotations

from datetime import date

import pytest

from core.file_organizer import (
    _matches_conditions,
    _sanitize_filename,
    build_target_path,
    evaluate_rules,
    preview_target_path,
)
from core.models import (
    ConditionField,
    ConditionOperator,
    Document,
    DocumentType,
    ExtractionResult,
    RuleCondition,
    SortRule,
)


def _mk_cond(field, op, value, logic="AND"):
    return RuleCondition(field=field, operator=op, value=value, logic=logic)


def _amazon_extraction():
    return ExtractionResult(
        sender="Amazon EU S.a.r.l.",
        date=date(2026, 3, 15),
        invoice_number="INV-12345",
        total_amount=99.99,
        currency="EUR",
        document_type=DocumentType.INVOICE,
    )


class TestSanitizeFilename:
    def test_removes_illegal_chars(self):
        assert _sanitize_filename("bad<name>:|*?.pdf") == "bad_name_.pdf"

    def test_collapses_underscores(self):
        assert _sanitize_filename("a___b") == "a_b"

    def test_strips_trailing(self):
        assert _sanitize_filename("_name_.") == "name"


class TestMatchesConditions:
    def test_no_conditions_always_matches(self):
        assert _matches_conditions(_amazon_extraction(), []) is True

    def test_single_condition_contains(self):
        cond = _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon")
        assert _matches_conditions(_amazon_extraction(), [cond]) is True

    def test_single_condition_no_match(self):
        cond = _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "telekom")
        assert _matches_conditions(_amazon_extraction(), [cond]) is False

    def test_and_all_true(self):
        conds = [
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon"),
            _mk_cond(ConditionField.DOC_TYPE, ConditionOperator.EQUALS, "rechnung", logic="AND"),
        ]
        assert _matches_conditions(_amazon_extraction(), conds) is True

    def test_and_one_false(self):
        conds = [
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon"),
            _mk_cond(ConditionField.DOC_TYPE, ConditionOperator.EQUALS, "vertrag", logic="AND"),
        ]
        assert _matches_conditions(_amazon_extraction(), conds) is False

    def test_or_one_true(self):
        conds = [
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "telekom"),
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon", logic="OR"),
        ]
        assert _matches_conditions(_amazon_extraction(), conds) is True

    def test_and_binds_stronger_than_or(self):
        """A OR (B AND C) — nur B kann false sein und Gesamtergebnis bleibt true, weil A gilt."""
        ext = _amazon_extraction()
        conds = [
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon"),          # A: true
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "telekom", "OR"),   # B: false
            _mk_cond(ConditionField.AMOUNT, ConditionOperator.GREATER_THAN, "5000", "AND"), # C: false
        ]
        # (B AND C) = false, A = true → A OR false = true
        assert _matches_conditions(ext, conds) is True

    def test_and_binds_stronger_than_or_negative(self):
        """Wenn A false und (B AND C) false, muss Ergebnis false sein."""
        ext = _amazon_extraction()
        conds = [
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "telekom"),         # A: false
            _mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon", "OR"),    # B: true
            _mk_cond(ConditionField.AMOUNT, ConditionOperator.GREATER_THAN, "5000", "AND"), # C: false
        ]
        # B AND C = false, A = false → false
        assert _matches_conditions(ext, conds) is False

    def test_amount_greater_than(self):
        ext = _amazon_extraction()
        cond = _mk_cond(ConditionField.AMOUNT, ConditionOperator.GREATER_THAN, "50")
        assert _matches_conditions(ext, [cond]) is True

    def test_amount_less_than(self):
        ext = _amazon_extraction()
        cond = _mk_cond(ConditionField.AMOUNT, ConditionOperator.LESS_THAN, "50")
        assert _matches_conditions(ext, [cond]) is False

    def test_starts_with_case_insensitive(self):
        ext = _amazon_extraction()
        cond = _mk_cond(ConditionField.SENDER, ConditionOperator.STARTS_WITH, "AMAZON")
        assert _matches_conditions(ext, [cond]) is True


class TestEvaluateRules:
    def _rule(self, name, priority, conditions):
        return SortRule(
            id=name, name=name, priority=priority, conditions=conditions,
            target_base="/tmp/out", enabled=True,
        )

    def test_returns_first_matching_rule_by_priority(self):
        doc = Document(file_path="/x.pdf", file_name="x.pdf", extraction=_amazon_extraction())
        rules = [
            self._rule("fallback", 999, []),
            self._rule("amazon", 1, [_mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon")]),
        ]
        picked = evaluate_rules(doc, rules)
        assert picked is not None and picked.name == "amazon"

    def test_returns_none_when_extraction_missing(self):
        doc = Document(file_path="/x.pdf", file_name="x.pdf")
        rules = [self._rule("fallback", 999, [])]
        assert evaluate_rules(doc, rules) is None

    def test_skips_disabled_rule(self):
        doc = Document(file_path="/x.pdf", file_name="x.pdf", extraction=_amazon_extraction())
        rule = self._rule("amazon", 1, [_mk_cond(ConditionField.SENDER, ConditionOperator.CONTAINS, "amazon")])
        rule.enabled = False
        assert evaluate_rules(doc, [rule]) is None


class TestBuildTargetPath:
    def test_full_placeholder_resolution(self):
        doc = Document(file_path="/in/x.pdf", file_name="x.pdf", extraction=_amazon_extraction())
        rule = SortRule(
            id="r1", name="Amazon", target_base="/out",
            target_subfolders=["{jahr}", "{absender}"],
            filename_parts=["{datum}", "{rechnungsnr}"],
        )
        target = build_target_path(doc, rule)
        assert target.parts[-3:] == ("2026", "Amazon EU S.a.r.l.", "2026-03-15_INV-12345.pdf")

    def test_empty_filename_parts_uses_original_name(self):
        doc = Document(file_path="/in/orig.pdf", file_name="orig.pdf", extraction=_amazon_extraction())
        rule = SortRule(id="r1", name="X", target_base="/out", filename_parts=[])
        target = build_target_path(doc, rule)
        assert target.name == "orig.pdf"


class TestPreviewTargetPath:
    def test_preview_uses_extraction(self):
        ext = _amazon_extraction()
        rule = SortRule(
            id="r1", name="X", target_base="/out",
            target_subfolders=["{jahr}"],
            filename_parts=["{datum}", "{absender}"],
        )
        preview = preview_target_path(ext, rule)
        assert "2026" in preview
        assert "2026-03-15" in preview
