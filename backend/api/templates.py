"""Template-Endpunkte: gelernte Absender-Templates auflisten und loeschen."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from core import template_matcher
from backend.deps import AppState, get_state

router = APIRouter(tags=["templates"])


def _templates_dir(state: AppState) -> Path:
    return Path(state.cfg.get("templates", {}).get("path", "./templates"))


@router.get("/templates")
async def list_templates(state: AppState = Depends(get_state)) -> list[dict]:
    tpls = template_matcher.load_templates(str(_templates_dir(state)))
    return [t.model_dump(mode="json") for t in tpls]


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, state: AppState = Depends(get_state)) -> dict:
    base = _templates_dir(state).resolve()
    target = (base / f"{template_id}.yaml").resolve()
    # Containment-Check — kein Loeschen ausserhalb des Template-Ordners.
    if base != target.parent:
        raise HTTPException(400, "Ungueltige Template-ID")
    if not target.exists():
        raise HTTPException(404, "Template nicht gefunden")
    target.unlink()
    state.processor.reload_templates()
    return {"ok": True, "deleted": template_id}
