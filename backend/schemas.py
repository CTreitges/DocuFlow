"""DocuFlow Backend — Request-/Response-Schemas (nutzt core.models wieder)."""

from __future__ import annotations

from pydantic import BaseModel

from core.models import ExtractionResult, SortRule


class RulesPayload(BaseModel):
    """Vollstaendige Regel-Liste (ersetzt die gespeicherten Regeln)."""

    rules: list[SortRule]


class RulePreviewRequest(BaseModel):
    """Vorschau eines Zielpfads fuer eine Regel + Beispiel-Extraktion."""

    rule: SortRule
    extraction: ExtractionResult | None = None


class ExtractionUpdate(BaseModel):
    """Manuelle Korrektur der extrahierten Felder eines Dokuments."""

    extraction: ExtractionResult


class ReorderPayload(BaseModel):
    """Neue Reihenfolge der Regeln (Liste von Regel-IDs, oben = zuerst geprueft)."""

    order: list[str]
