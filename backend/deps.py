"""DocuFlow Backend — geteilter App-Zustand (DB, Processor, Regeln, Config).

Der Zustand wird in der FastAPI-Lifespan einmalig erzeugt und auf app.state
abgelegt. Endpunkte erhalten ihn ueber die get_state-Dependency.
"""

from __future__ import annotations

import os
import subprocess
import sys

from fastapi import Request

from core import config
from core.database import Database
from core.processor import Processor
from core.rules_store import load_rules


class AppState:
    def __init__(self) -> None:
        self.cfg = config.load()
        db_path = os.environ.get("DOCUFLOW_DB") or self.cfg.get("database", {}).get(
            "path", "./data/docuflow.db"
        )
        self.db = Database(db_path)
        self.db.connect()
        self.processor = Processor(self.db)
        self.rules = load_rules()
        self.processor.set_rules(self.rules)

    def reload_config(self) -> None:
        self.cfg = config.load()
        # Processor haelt eine eigene Referenz auf das Config-Dict.
        self.processor.cfg = config.get()

    def reload_rules(self) -> None:
        self.rules = load_rules()
        self.processor.set_rules(self.rules)

    def maybe_start_ollama(self) -> None:
        """Startet den Ollama-Daemon best-effort (nur wenn installiert)."""
        if os.environ.get("DOCUFLOW_NO_OLLAMA"):
            return
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        except (FileNotFoundError, OSError):
            pass  # Ollama nicht installiert — kein Fehler

    def close(self) -> None:
        self.db.close()


def get_state(request: Request) -> AppState:
    """FastAPI-Dependency: liefert den geteilten App-Zustand."""
    return request.app.state.docuflow
