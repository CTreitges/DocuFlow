"""DocuFlow FastAPI-App — serviert die JSON-API und (in Produktion) das Frontend.

Dev:   uvicorn backend.main:app --reload   (Frontend laeuft separat via Vite)
Prod:  Frontend nach frontend/dist bauen, dann wird es hier statisch geliefert.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.deps import AppState
from backend.api import documents, rules, settings, system, templates

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = AppState()
    state.maybe_start_ollama()
    app.state.docuflow = state
    try:
        yield
    finally:
        state.close()


app = FastAPI(title="DocuFlow API", version="0.2", lifespan=lifespan)

# CORS fuer den Vite-Dev-Server (Prod laeuft same-origin und braucht es nicht).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (system, documents, rules, templates, settings):
    app.include_router(module.router, prefix="/api")


if FRONTEND_DIST.exists():
    # Gebautes Frontend statisch ausliefern (html=True → SPA-Fallback auf index.html).
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    async def root_fallback() -> dict:
        return {
            "app": "DocuFlow API",
            "docs": "/docs",
            "hint": "Frontend nicht gebaut — 'cd frontend && npm install && npm run build'.",
        }
