"""Regel-Endpunkte: Sortier-Regeln lesen, speichern, Zielpfad-Vorschau."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.file_organizer import preview_target_path
from core.models import ExtractionResult
from core.rules_store import create_rule, save_rules
from backend.deps import AppState, get_state
from backend.schemas import RulePreviewRequest, RulesPayload

router = APIRouter(tags=["rules"])


@router.get("/rules")
async def get_rules(state: AppState = Depends(get_state)) -> list[dict]:
    return [r.model_dump(mode="json") for r in state.rules]


@router.get("/rules/blank")
async def blank_rule() -> dict:
    """Liefert eine leere Vorlage-Regel (Client kann sie befuellen)."""
    return create_rule("Neue Regel").model_dump(mode="json")


@router.put("/rules")
async def put_rules(payload: RulesPayload, state: AppState = Depends(get_state)) -> dict:
    """Ersetzt die gespeicherten Regeln (vom Regel-Editor ausgeloest)."""
    save_rules(payload.rules)
    state.reload_rules()
    return {"ok": True, "count": len(state.rules)}


@router.post("/rules/preview")
async def rules_preview(req: RulePreviewRequest) -> dict:
    """Berechnet den Zielpfad fuer eine Regel anhand einer Beispiel-Extraktion."""
    extraction = req.extraction or ExtractionResult(
        sender="Beispiel GmbH",
        invoice_number="RE-2026-001",
        total_amount=123.45,
    )
    return {"preview": preview_target_path(extraction, req.rule)}
