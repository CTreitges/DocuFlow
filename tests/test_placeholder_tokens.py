"""Cross-Language-Anker: Die Platzhalter-Tokens im Frontend-Regelbuilder müssen
exakt den Backend-Tokens entsprechen.

Hintergrund: Der Regelbuilder (frontend/src/lib/mock.js → TOKEN_CATALOG) bietet die
Tokens als auswählbare Bausteine an; aufgelöst werden sie in
core/file_organizer.py:_build_placeholders. Driften beide auseinander, bietet die
UI Tokens an, die das Backend nicht kennt (oder umgekehrt). Dieser Test hält sie
synchron, ohne eine eigene JS-Test-Infrastruktur zu brauchen.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.file_organizer import _build_placeholders
from core.models import ExtractionResult

MOCK_JS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "lib" / "mock.js"


def _backend_tokens() -> set[str]:
    return set(_build_placeholders(ExtractionResult()).keys())


def _frontend_tokens() -> set[str]:
    text = MOCK_JS.read_text(encoding="utf-8")
    # TOKEN_CATALOG-Block isolieren, dann alle token: '{...}' einsammeln.
    start = text.index("TOKEN_CATALOG")
    end = text.index("];", start)
    block = text[start:end]
    return {m.strip("{}") for m in re.findall(r"token:\s*'\{([a-z]+)\}'", block)}


def test_frontend_token_catalog_matches_backend():
    backend = _backend_tokens()
    frontend = _frontend_tokens()
    assert frontend == backend, (
        f"Token-Drift Frontend↔Backend: nur Frontend={frontend - backend}, "
        f"nur Backend={backend - frontend}"
    )


def test_backend_has_exactly_nine_tokens():
    assert len(_backend_tokens()) == 9
