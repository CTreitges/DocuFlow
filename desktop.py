"""DocuFlow Desktop-Shell.

Startet das FastAPI-Backend (uvicorn) in einem Hintergrund-Thread und oeffnet
ein natives pywebview-Fenster auf das gebaute Svelte-Frontend.

Voraussetzung: das Frontend ist gebaut (frontend/dist vorhanden):
    cd frontend && npm install && npm run build

Start der App:
    python desktop.py

Optionale Env-Variablen: DOCUFLOW_HOST, DOCUFLOW_PORT.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time

import uvicorn

from backend.main import FRONTEND_DIST, app

HOST = os.environ.get("DOCUFLOW_HOST", "127.0.0.1")
PORT = int(os.environ.get("DOCUFLOW_PORT", "8000"))


def _serve(host: str, port: int) -> None:
    # uvicorn.run() ueberspringt die Signal-Handler-Installation automatisch, wenn
    # es nicht im Haupt-Thread laeuft — daher ist der Start im Daemon-Thread ok.
    uvicorn.run(app, host=host, port=port, log_level="warning")


def _free_port(preferred: int, host: str = "127.0.0.1") -> int:
    """Gibt den gewuenschten Port zurueck, oder einen freien, falls belegt."""
    with socket.socket() as s:
        try:
            s.bind((host, preferred))
            return preferred
        except OSError:
            pass
    with socket.socket() as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.2)
    return False


def start_backend(host: str = HOST, port: int = PORT, timeout: float = 20.0) -> str:
    """Startet uvicorn in einem Daemon-Thread und wartet, bis der Port bereit ist.

    Gibt die Basis-URL zurueck. Wirft SystemExit, falls der Port nicht erreichbar
    wird. Getrennt von der Fenster-Logik, damit der Serve-Pfad testbar ist.
    """
    threading.Thread(target=_serve, args=(host, port), daemon=True).start()
    if not _wait_for_port(host, port, timeout):
        raise SystemExit(f"Backend nicht erreichbar auf {host}:{port}.")
    return f"http://{host}:{port}"


def main() -> None:
    if not FRONTEND_DIST.exists():
        print(
            "Warnung: frontend/dist fehlt — baue mit 'cd frontend && npm run build'. "
            "Das Fenster zeigt sonst nur die API-Fallback-Seite.",
            file=sys.stderr,
        )

    port = _free_port(PORT, HOST)
    url = start_backend(HOST, port)

    import webview  # lazy — nur für die Desktop-Shell nötig

    webview.create_window(
        "DocuFlow",
        url,
        width=1280,
        height=850,
        min_size=(960, 640),
    )
    webview.start()


if __name__ == "__main__":
    main()
