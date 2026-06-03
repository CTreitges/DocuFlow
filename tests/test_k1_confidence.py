"""K1-Regression: confidence['overall'] muss gesetzt werden.

Bug (vorher): extract_with_template setzte 'overall' nie, und process_document
schrieb den Template-Match-Score nur in die History. Die Auto-Sortierung las
confidence.get('overall', 0) → immer 0 → toter Code.
"""

from __future__ import annotations

from core import template_matcher
from core.models import Template


def _amazon_template() -> Template:
    return Template(
        id="amazon_1",
        sender_name="Amazon",
        sender_patterns=["Amazon", "amazon\\.de"],
        field_patterns={
            "invoice_number": r"Rechnungsnummer[:\s]+(\S+)",
            "total_amount": r"Gesamt[:\s]+([\d.,]+)",
        },
        confidence_threshold=0.5,
    )


def test_extract_with_template_sets_overall():
    tpl = _amazon_template()
    text = "Amazon\nRechnungsnummer: INV-123\nGesamt: 49,99\n"
    result = template_matcher.extract_with_template(text, tpl)

    # Der Kern des K1-Bugs: 'overall' fehlte komplett.
    assert "overall" in result.confidence
    assert 0.0 < result.confidence["overall"] <= 1.0
    assert result.invoice_number == "INV-123"


def test_extract_with_template_overall_present_even_without_fields():
    tpl = Template(id="x", sender_name="Leer", sender_patterns=["Leer"], field_patterns={})
    result = template_matcher.extract_with_template("Leer GmbH", tpl)
    assert "overall" in result.confidence  # darf nie KeyError werfen


def test_match_template_returns_real_score():
    tpl = _amazon_template()
    matched, score = template_matcher.match_template("Bestellung bei Amazon (amazon.de)", [tpl])
    assert matched is not None
    assert 0.0 < score <= 1.0


def test_match_template_below_threshold_rejected():
    tpl = Template(id="x", sender_name="Foo", sender_patterns=["Foo", "Bar", "Baz"], confidence_threshold=0.9)
    # Nur 1 von 3 Mustern matcht → Score 0.33 < 0.9 → kein Match.
    matched, score = template_matcher.match_template("nur Foo hier", [tpl])
    assert matched is None
    assert score == 0.0
