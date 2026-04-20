"""DocuFlow Watchdog — Hintergrund-Ordnerüberwachung für neue PDFs."""

from __future__ import annotations

import logging
import queue
from pathlib import Path
from typing import Optional

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

_new_files: queue.Queue[str] = queue.Queue()


class _PDFHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".pdf":
            _new_files.put(str(path.resolve()))
            logger.info("Watchdog: Neue PDF erkannt: %s", path.name)


class WatchdogService:
    """Überwacht Input-Ordner im Hintergrund-Thread auf neue PDFs."""

    def __init__(self) -> None:
        self._observer: Optional[Observer] = None
        self._watched: set[str] = set()
        self.is_running: bool = False

    def start(self, input_folders: list[dict]) -> None:
        """Startet den Watchdog für alle aktivierten Ordner."""
        if self._observer and self._observer.is_alive():
            self.stop()

        self._observer = Observer()
        self._watched = set()
        handler = _PDFHandler()

        for folder_cfg in input_folders:
            if not folder_cfg.get("enabled", True):
                continue
            path = Path(folder_cfg["path"])
            try:
                path.mkdir(parents=True, exist_ok=True)
                self._observer.schedule(handler, str(path), recursive=False)
                self._watched.add(str(path))
                logger.info("Watchdog: Überwache %s", path)
            except Exception as exc:
                logger.warning("Watchdog: Ordner nicht überwachbar: %s — %s", path, exc)

        if self._watched:
            self._observer.start()
            self.is_running = True
            logger.info("Watchdog gestartet (%d Ordner)", len(self._watched))
        else:
            logger.info("Watchdog: Keine überwachbaren Ordner")

    def stop(self) -> None:
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=3)
            except Exception:
                pass
            self._observer = None
        self.is_running = False
        self._watched = set()

    def restart(self, input_folders: list[dict]) -> None:
        self.stop()
        self.start(input_folders)

    def get_watched_folders(self) -> set[str]:
        return self._watched.copy()

    def drain_new_files(self) -> list[str]:
        """Gibt alle neu erkannten PDF-Pfade zurück und leert die Queue."""
        files: list[str] = []
        while True:
            try:
                files.append(_new_files.get_nowait())
            except queue.Empty:
                break
        return files


watchdog_service = WatchdogService()
