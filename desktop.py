"""DocuFlow Desktop-Shell.

Startet das FastAPI-Backend (uvicorn) in einem Hintergrund-Thread und oeffnet
ein natives pywebview-Fenster auf das gebaute Svelte-Frontend.

Voraussetzung: das Frontend ist gebaut (frontend/dist vorhanden):
    cd frontend && npm install && npm run build

Start der App:
    python desktop.py
"""

from __future__ import annotations

import socket
import threading
import time

import uvicorn

from backend.main import app

HOST = "127.0.0.1"
PORT = 8000


def _serve() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


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


def main() -> None:
    threading.Thread(target=_serve, daemon=True).start()
    if not _wait_for_port(HOST, PORT):
        raise SystemExit("Backend ist nicht gestartet (Port nicht erreichbar).")

    import webview  # lazy — nur für die Desktop-Shell nötig

    webview.create_window(
        "DocuFlow",
        f"http://{HOST}:{PORT}",
        width=1280,
        height=850,
        min_size=(960, 640),
    )
    webview.start()


if __name__ == "__main__":
    main()
