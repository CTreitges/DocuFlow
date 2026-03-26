"""DocuFlow Template-Generator — Erzeugt Templates aus bestaetigten Extraktionen."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path

from ruamel.yaml import YAML

from core.models import ExtractionResult, Template

_yaml = YAML()
_yaml.default_flow_style = False


def generate_template(extraction: ExtractionResult, raw_text: str) -> Template:
    """Generiert ein Template aus einer bestaetigten Extraktion."""
    sender = extraction.sender
    sender_id = re.sub(r'[^a-z0-9]', '_', sender.lower()).strip('_')
    template_id = f"{sender_id}_{uuid.uuid4().hex[:6]}"

    sender_patterns = _generate_sender_patterns(sender, raw_text)
    field_patterns = _generate_field_patterns(extraction, raw_text)

    return Template(
        id=template_id,
        sender_name=sender,
        sender_patterns=sender_patterns,
        field_patterns=field_patterns,
        confidence_threshold=0.9,
        times_used=0,
        last_used=None,
    )


def save_template(template: Template, templates_dir: str = "./templates") -> Path:
    """Speichert ein Template als YAML-Datei."""
    tpl_dir = Path(templates_dir)
    tpl_dir.mkdir(parents=True, exist_ok=True)

    file_path = tpl_dir / f"{template.id}.yaml"
    data = template.model_dump(mode="json")
    with open(file_path, "w", encoding="utf-8") as f:
        _yaml.dump(data, f)
    return file_path


def _generate_sender_patterns(sender: str, text: str) -> list[str]:
    """Generiert Regex-Muster um den Absender im Text zu erkennen."""
    patterns = []
    if sender:
        escaped = re.escape(sender)
        patterns.append(escaped)
        words = sender.split()
        if len(words) > 1:
            patterns.append(r'\b' + re.escape(words[0]) + r'\b')
    return patterns


def _generate_field_patterns(extraction: ExtractionResult, text: str) -> dict[str, str]:
    """Generiert Regex-Muster fuer erkannte Felder basierend auf deren Position im Text."""
    patterns = {}

    if extraction.invoice_number:
        escaped = re.escape(extraction.invoice_number)
        context = _find_context_pattern(text, extraction.invoice_number)
        patterns["invoice_number"] = context or f"({escaped})"

    if extraction.total_amount is not None:
        amount_str = f"{extraction.total_amount:.2f}"
        amount_comma = amount_str.replace(".", ",")
        patterns["total_amount"] = (
            r'(?:Gesamt|Total|Summe|Endbetrag|Rechnungsbetrag)[:\s]*'
            rf'(\d+[.,]\d{{2}})'
        )

    if extraction.date:
        patterns["date"] = (
            r'(?:Datum|Rechnungsdatum|Date)[:\s]*'
            r'(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})'
        )

    if extraction.iban:
        patterns["iban"] = r'(DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})'

    if extraction.vat_rate:
        patterns["vat_rate"] = r'(?:MwSt|USt|Mehrwertsteuer)[.\s]*(\d+(?:[.,]\d+)?)\s*%'

    if extraction.customer_number:
        patterns["customer_number"] = r'(?:Kundennr|Kundennummer|Kd-?Nr)[.:\s]*(\S+)'

    return patterns


def _find_context_pattern(text: str, value: str) -> str | None:
    """Sucht den Kontext eines Werts im Text und erstellt ein Regex-Pattern."""
    escaped = re.escape(value)
    match = re.search(rf'(\S+[\s:]+){escaped}', text)
    if match:
        prefix = match.group(1).strip()
        prefix_escaped = re.escape(prefix)
        return rf'{prefix_escaped}\s*(\S+)'
    return None
