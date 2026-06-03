"""System-Endpunkte: Health, Statistiken, History."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core import ocr_engine
from backend.deps import AppState, get_state

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(state: AppState = Depends(get_state)) -> dict:
    ollama_cfg = state.cfg.get("ollama", {})
    return {
        "status": "ok",
        "app": state.cfg.get("app", {}).get("name", "DocuFlow"),
        "version": state.cfg.get("app", {}).get("version", "0.2"),
        "auto_mode": state.cfg.get("auto_mode", False),
        "auto_confidence_threshold": state.cfg.get("auto_confidence_threshold", 0.9),
        "german_ocr_available": ocr_engine.is_german_ocr_available(),
        "ocr_available": ocr_engine.is_available(
            ollama_cfg.get("url", "http://localhost:11434"),
            ollama_cfg.get("model", "minicpm-v"),
        ),
    }


@router.get("/stats")
async def stats(state: AppState = Depends(get_state)) -> dict:
    return state.db.get_stats()


@router.get("/history")
async def history(limit: int = 50, state: AppState = Depends(get_state)) -> list[dict]:
    return state.db.get_history(limit)


@router.post("/reset")
async def reset_database(state: AppState = Depends(get_state)) -> dict:
    """Loescht den Dokument-Index, Templates-Zuordnung und das Log (DB-Reset).

    Bereits sortierte Dateien auf der Festplatte bleiben unveraendert — es wird
    nur der SQLite-Index geleert. Vom Einstellungen-Dialog (mit Bestaetigung).
    """
    state.db.clear_all()
    return {"ok": True}
