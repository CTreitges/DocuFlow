"""Ueberwachungs-Endpunkte: Watchdog starten/stoppen, Live-Status, manueller Scan."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import AppState, get_state

router = APIRouter(tags=["watch"])


@router.get("/watch/status")
async def watch_status(state: AppState = Depends(get_state)) -> dict:
    """Live-Status der Ordner-Ueberwachung (vom Frontend gepollt)."""
    return state.watcher.status()


@router.post("/watch/start")
async def watch_start(state: AppState = Depends(get_state)) -> dict:
    """Startet die Ueberwachung der konfigurierten Input-Ordner (watch=true)."""
    try:
        return state.watcher.start()
    except RuntimeError as exc:
        # watchdog nicht installiert o.ae.
        raise HTTPException(503, str(exc))


@router.post("/watch/stop")
async def watch_stop(state: AppState = Depends(get_state)) -> dict:
    """Stoppt die Ueberwachung."""
    return state.watcher.stop()


@router.post("/watch/scan-now")
async def watch_scan_now(state: AppState = Depends(get_state)) -> dict:
    """Einmaliger manueller Scan: registriert neue Dateien und stoesst (falls die
    Ueberwachung laeuft) deren Verarbeitung an."""
    new_docs = state.processor.scan_input_folders()
    if state.watcher.is_running():
        state.watcher.poke()
    return {"new": len(new_docs), "watching": state.watcher.is_running()}
