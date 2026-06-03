"""Einstellungs-Endpunkte: App-Konfiguration lesen und schreiben (config.yaml)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends

from core import config
from backend.deps import AppState, get_state

router = APIRouter(tags=["settings"])

# Nur diese Schluessel duerfen ueber die API geaendert werden.
_ALLOWED_KEYS = {
    "input_folders",
    "output",
    "auto_mode",
    "auto_confidence_threshold",
    "ollama",
    "german_ocr",
    "templates",
}


@router.get("/settings")
async def get_settings(state: AppState = Depends(get_state)) -> dict:
    return dict(state.cfg)


@router.put("/settings")
async def put_settings(
    payload: dict[str, Any] = Body(...), state: AppState = Depends(get_state)
) -> dict:
    cfg = config.get()
    changed = []
    for key, value in payload.items():
        if key in _ALLOWED_KEYS:
            cfg[key] = value
            changed.append(key)
    config.save(cfg)
    state.reload_config()
    return {"ok": True, "changed": changed, "settings": dict(state.cfg)}
