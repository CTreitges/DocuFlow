"""DocuFlow Datei-Organizer — Sortiert und benennt Dateien nach Regeln."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from core.models import (
    ConditionField,
    ConditionOperator,
    Document,
    ExtractionResult,
    RuleCondition,
    SortRule,
)


def evaluate_rules(doc: Document, rules: list[SortRule]) -> SortRule | None:
    """Prueft Regeln von oben nach unten, gibt die erste passende zurueck."""
    if not doc.extraction:
        return None
    for rule in sorted(rules, key=lambda r: r.priority):
        if rule.enabled and _matches_conditions(doc.extraction, rule.conditions):
            return rule
    return None


def build_target_path(doc: Document, rule: SortRule) -> Path:
    """Baut den Zielpfad aus Regel-Platzhaltern.

    K2-Sicherheit: Ordner-Segmente stammen aus OCR-Platzhaltern ({absender} etc.)
    und sind damit nicht vertrauenswuerdig. Jedes Segment wird sanitisiert
    (entfernt '..' und Pfad-Separatoren), und der finale Pfad wird gegen den
    Basisordner verankert, damit shutil.move nicht aus dem Zielordner ausbricht.
    """
    extraction = doc.extraction or ExtractionResult()
    placeholders = _build_placeholders(extraction)

    base_root = Path(rule.target_base)
    base = base_root
    for subfolder in rule.target_subfolders:
        segment = _sanitize_segment(_resolve_template(subfolder, placeholders))
        if segment:
            base = base / segment

    filename_parts = []
    for part in rule.filename_parts:
        resolved = _resolve_template(part, placeholders)
        if resolved:
            filename_parts.append(resolved)

    if filename_parts:
        filename = "_".join(filename_parts) + ".pdf"
    else:
        filename = doc.file_name

    filename = _sanitize_filename(filename)
    return _enforce_within_base(base / filename, base_root, filename)


def move_file(source: str | Path, target: Path) -> Path:
    """Verschiebt eine Datei zum Zielpfad. Erstellt Ordner bei Bedarf."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while target.exists():
            target = target.parent / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.move(str(source), str(target))
    return target


def preview_target_path(extraction: ExtractionResult, rule: SortRule) -> str:
    """Erstellt eine Vorschau des Zielpfads (ohne tatsaechlich zu verschieben)."""
    placeholders = _build_placeholders(extraction)
    base_root = Path(rule.target_base)
    base = base_root
    for subfolder in rule.target_subfolders:
        segment = _sanitize_segment(_resolve_template(subfolder, placeholders))
        if segment:
            base = base / segment

    filename_parts = [
        r for r in (_resolve_template(p, placeholders) for p in rule.filename_parts) if r
    ]
    filename = "_".join(filename_parts) + ".pdf" if filename_parts else "dokument.pdf"
    filename = _sanitize_filename(filename)
    return str(_enforce_within_base(base / filename, base_root, filename))


def _matches_conditions(extraction: ExtractionResult, conditions: list[RuleCondition]) -> bool:
    """Prueft ob alle Bedingungen einer Regel erfuellt sind."""
    if not conditions:
        return True

    results = []
    for cond in conditions:
        results.append((cond.logic, _check_condition(extraction, cond)))

    result = results[0][1]
    for i in range(1, len(results)):
        logic, val = results[i]
        if logic == "OR":
            result = result or val
        else:
            result = result and val
    return result


def _check_condition(extraction: ExtractionResult, cond: RuleCondition) -> bool:
    """Prueft eine einzelne Bedingung."""
    field_value = _get_field_value(extraction, cond.field)

    if cond.operator == ConditionOperator.CONTAINS:
        return cond.value.lower() in str(field_value).lower()
    elif cond.operator == ConditionOperator.EQUALS:
        return str(field_value).lower() == cond.value.lower()
    elif cond.operator == ConditionOperator.STARTS_WITH:
        return str(field_value).lower().startswith(cond.value.lower())
    elif cond.operator == ConditionOperator.GREATER_THAN:
        try:
            return float(field_value) > float(cond.value)
        except (ValueError, TypeError):
            return False
    elif cond.operator == ConditionOperator.LESS_THAN:
        try:
            return float(field_value) < float(cond.value)
        except (ValueError, TypeError):
            return False
    return False


def _get_field_value(extraction: ExtractionResult, field: ConditionField):
    mapping = {
        ConditionField.SENDER: extraction.sender,
        ConditionField.AMOUNT: extraction.total_amount,
        ConditionField.CONTENT: extraction.raw_text,
        ConditionField.DOC_TYPE: extraction.document_type.value,
        ConditionField.INVOICE_NUMBER: extraction.invoice_number,
    }
    return mapping.get(field, "")


def _build_placeholders(extraction: ExtractionResult) -> dict[str, str]:
    d = extraction.date or datetime.now().date()
    return {
        "absender": extraction.sender or "Unbekannt",
        "datum": d.isoformat(),
        "jahr": str(d.year),
        "monat": f"{d.month:02d}",
        "tag": f"{d.day:02d}",
        "rechnungsnr": extraction.invoice_number or "ohne-nr",
        "betrag": f"{extraction.total_amount:.2f}" if extraction.total_amount else "0.00",
        "typ": extraction.document_type.value,
        "waehrung": extraction.currency,
    }


def _resolve_template(template: str, placeholders: dict[str, str]) -> str:
    """Ersetzt {platzhalter} in einem Template-String."""
    result = template
    for key, value in placeholders.items():
        result = result.replace(f"{{{key}}}", value)
    return result


def _sanitize_segment(segment: str) -> str:
    """Sanitisiert ein einzelnes Ordner-Segment (K2-Schutz).

    Neutralisiert Pfad-Separatoren und '..'-Traversal: ein Segment darf nur
    EINE Ordnerebene tief sein. '../../etc' wird so zu 'etc', 'a/b' zu 'a_b'.
    Ungueltige Dateisystem-Zeichen werden durch '_' ersetzt.
    """
    parts = re.split(r"[\\/]+", segment)
    safe_parts = []
    for part in parts:
        part = re.sub(r'[<>:"|?*\x00-\x1f]', "_", part)
        part = part.strip(". ")
        if part in ("", ".", ".."):
            continue
        safe_parts.append(part)
    return "_".join(safe_parts)


def _sanitize_filename(filename: str) -> str:
    """Entfernt ungueltige Zeichen aus Dateinamen."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_. ')


def _enforce_within_base(target: Path, base_root: Path, filename: str) -> Path:
    """Stellt sicher, dass der Zielpfad innerhalb von base_root bleibt (K2-Schutz).

    Letzte Verteidigungslinie nach der Segment-Sanitisierung: Sollte ein Pfad
    dennoch aus dem Basisordner ausbrechen, wird die Datei hart direkt unter
    base_root abgelegt statt an einen beliebigen Ort verschoben.
    """
    try:
        resolved_target = target.resolve()
        resolved_base = base_root.resolve()
    except (OSError, RuntimeError, ValueError):
        return base_root / (_sanitize_filename(filename) or "dokument.pdf")

    if resolved_target == resolved_base or resolved_target.is_relative_to(resolved_base):
        return target
    return base_root / (_sanitize_filename(filename) or "dokument.pdf")
