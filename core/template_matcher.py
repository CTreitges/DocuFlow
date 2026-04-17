"""DocuFlow Template-Matcher — Erkennung bekannter Absender via Regex-Muster."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from ruamel.yaml import YAML

from core.models import DocumentType, ExtractionResult, LineItem, Template
from core.number_parser import parse_amount

_yaml = YAML()


def load_templates(templates_dir: str = "./templates") -> list[Template]:
    """Laedt alle Templates aus dem Templates-Ordner."""
    tpl_dir = Path(templates_dir)
    if not tpl_dir.exists():
        return []

    templates = []
    for f in sorted(tpl_dir.glob("*.yaml")):
        try:
            with open(f) as fh:
                data = _yaml.load(fh)
            if data:
                templates.append(Template(**data))
        except Exception:
            continue
    return templates


def match_template(text: str, templates: list[Template]) -> tuple[Template | None, float]:
    """Versucht den Text einem Template zuzuordnen. Gibt (Template, Confidence) zurueck."""
    best_match: Template | None = None
    best_score = 0.0

    for tpl in templates:
        score = _calculate_match_score(text, tpl)
        if score > best_score:
            best_score = score
            best_match = tpl

    if best_match and best_score >= best_match.confidence_threshold:
        return best_match, best_score
    return None, 0.0


def extract_with_template(text: str, template: Template) -> ExtractionResult:
    """Extrahiert Daten aus Text anhand eines Templates (Regex-Muster)."""
    result = ExtractionResult(
        sender=template.sender_name,
        raw_text=text,
    )
    confidence = {"sender": 1.0}

    for field_name, pattern in template.field_patterns.items():
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                _set_field(result, field_name, value)
                confidence[field_name] = 0.95
            else:
                confidence[field_name] = 0.0
        except re.error:
            confidence[field_name] = 0.0

    result.confidence = confidence
    return result


def _calculate_match_score(text: str, template: Template) -> float:
    """Berechnet wie gut der Text zum Template passt (0-1)."""
    if not template.sender_patterns:
        return 0.0

    matches = 0
    for pattern in template.sender_patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        except re.error:
            continue

    return matches / len(template.sender_patterns) if template.sender_patterns else 0.0


def _set_field(result: ExtractionResult, field_name: str, value: str) -> None:
    """Setzt ein Feld im ExtractionResult basierend auf dem Feldnamen."""
    value = value.strip()
    if field_name == "date":
        try:
            result.date = date.fromisoformat(value[:10])
        except ValueError:
            pass
    elif field_name == "invoice_number":
        result.invoice_number = value
    elif field_name == "total_amount":
        parsed = parse_amount(value)
        if parsed is not None:
            result.total_amount = parsed
    elif field_name == "vat_rate":
        parsed = parse_amount(value)
        if parsed is not None:
            result.vat_rate = parsed
    elif field_name == "vat_amount":
        parsed = parse_amount(value)
        if parsed is not None:
            result.vat_amount = parsed
    elif field_name == "iban":
        result.iban = value
    elif field_name == "customer_number":
        result.customer_number = value
    elif field_name == "due_date":
        try:
            result.due_date = date.fromisoformat(value[:10])
        except ValueError:
            pass
    elif field_name == "currency":
        result.currency = value
