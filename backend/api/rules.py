"""Regel-Endpunkte: Sortier-Regeln lesen, anlegen, aendern, loeschen, sortieren.

Granulares CRUD (POST/PUT/DELETE pro Regel + reorder) fuer den visuellen
Regel-Editor mit Auto-Save. Die Bulk-Variante (PUT /rules) bleibt erhalten.
Alle schreibenden Operationen persistieren nach data/rules.yaml und laden den
Processor-Regelsatz neu.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from core.file_organizer import preview_target_path
from core.models import ExtractionResult, SortRule
from core.rules_store import create_rule, save_rules
from backend.deps import AppState, get_state
from backend.schemas import ReorderPayload, RulePreviewRequest, RulesPayload

router = APIRouter(tags=["rules"])


def _persist(state: AppState, rules: list[SortRule]) -> None:
    save_rules(rules)
    state.reload_rules()


@router.get("/rules")
async def get_rules(state: AppState = Depends(get_state)) -> list[dict]:
    return [r.model_dump(mode="json") for r in state.rules]


@router.get("/rules/blank")
async def blank_rule() -> dict:
    """Liefert eine leere Vorlage-Regel (Client kann sie befuellen)."""
    return create_rule("Neue Regel").model_dump(mode="json")


@router.put("/rules")
async def put_rules(payload: RulesPayload, state: AppState = Depends(get_state)) -> dict:
    """Ersetzt die gesamte Regelliste (Bulk-Save)."""
    _persist(state, payload.rules)
    return {"ok": True, "count": len(state.rules)}


@router.post("/rules")
async def create_rule_endpoint(rule: SortRule, state: AppState = Depends(get_state)) -> dict:
    """Legt eine neue Regel an (ans Ende, niedrigste Prioritaet zuletzt geprueft)."""
    rules = list(state.rules)
    existing_ids = {r.id for r in rules}
    if not rule.id or rule.id in existing_ids:
        rule.id = uuid.uuid4().hex[:8]
    rule.priority = len(rules)
    rules.append(rule)
    _persist(state, rules)
    return rule.model_dump(mode="json")


@router.post("/rules/reorder")
async def reorder_rules(payload: ReorderPayload, state: AppState = Depends(get_state)) -> dict:
    """Setzt die Reihenfolge (Prioritaet) anhand einer ID-Liste neu."""
    by_id = {r.id: r for r in state.rules}
    ordered: list[SortRule] = []
    for rid in payload.order:
        r = by_id.get(rid)
        if r is not None:
            r.priority = len(ordered)
            ordered.append(r)
    # In der Order nicht genannte Regeln stabil hinten anhaengen.
    for r in state.rules:
        if r.id not in payload.order:
            r.priority = len(ordered)
            ordered.append(r)
    _persist(state, ordered)
    return {"ok": True, "count": len(ordered)}


@router.put("/rules/{rule_id}")
async def update_rule_endpoint(
    rule_id: str, rule: SortRule, state: AppState = Depends(get_state)
) -> dict:
    """Ersetzt eine einzelne Regel (per ID)."""
    rules = list(state.rules)
    idx = next((i for i, r in enumerate(rules) if r.id == rule_id), None)
    if idx is None:
        raise HTTPException(404, "Regel nicht gefunden")
    rule.id = rule_id
    rule.priority = rules[idx].priority  # Position bleibt erhalten
    rules[idx] = rule
    _persist(state, rules)
    return rule.model_dump(mode="json")


@router.delete("/rules/{rule_id}")
async def delete_rule_endpoint(rule_id: str, state: AppState = Depends(get_state)) -> dict:
    """Loescht eine Regel (per ID)."""
    rules = [r for r in state.rules if r.id != rule_id]
    if len(rules) == len(state.rules):
        raise HTTPException(404, "Regel nicht gefunden")
    _persist(state, rules)
    return {"ok": True, "deleted": rule_id}


@router.post("/rules/preview")
async def rules_preview(req: RulePreviewRequest) -> dict:
    """Berechnet den Zielpfad fuer eine Regel anhand einer Beispiel-Extraktion."""
    extraction = req.extraction or ExtractionResult(
        sender="Beispiel GmbH",
        invoice_number="RE-2026-001",
        total_amount=123.45,
    )
    return {"preview": preview_target_path(extraction, req.rule)}
