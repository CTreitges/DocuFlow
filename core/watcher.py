"""DocuFlow Ordner-Ueberwachung — erkennt neue PDFs und verarbeitet sie automatisch.

Der FolderWatcher startet einen watchdog.Observer auf allen Input-Ordnern mit
``watch: true``. Neu erkannte PDFs werden in die DB aufgenommen und seriell durch
die Verarbeitungs-Pipeline geschickt (Text -> Template -> OCR), inklusive
optionaler Auto-Sortierung (wenn auto_mode an + Konfidenz ueber Schwellwert).

Design-Entscheidungen:
- **Entprellt (debounced):** watchdog-Events setzen nur ein Dirty-Flag. Der
  Worker scannt erst nach einer kurzen Ruhephase, damit halb-geschriebene
  Dateien nicht zu frueh gelesen werden. Zusaetzlich wird vor dem Verarbeiten
  die Dateigroesse auf Stabilitaet geprueft.
- **Seriell:** Ein einzelner Worker-Thread verarbeitet ein Dokument nach dem
  anderen. Das vermeidet Konkurrenz auf dem geteilten Processor-Zustand; die DB
  ist zusaetzlich per RLock serialisiert.
- **Thread-sicherer Status-Snapshot:** ``status()`` wird vom Endpoint
  ``/api/watch/status`` und der Live-Anzeige im Frontend gepollt.

watchdog wird erst in ``start()`` importiert, damit das Backend auch ohne das
Paket startet (dann schlaegt nur das Starten der Ueberwachung kontrolliert fehl).
"""

from __future__ import annotations

import asyncio
import threading
import time
from datetime import datetime
from pathlib import Path

from core.models import DocumentStatus

_RECENT_MAX = 12


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


class FolderWatcher:
    def __init__(self, processor, debounce_seconds: float = 1.0):
        self._processor = processor
        self._debounce = debounce_seconds
        self._observer = None
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._wakeup = threading.Event()
        self._lock = threading.RLock()
        # Serialisiert start/stop, damit zwei gleichzeitige Aufrufe nicht zwei
        # Observer erzeugen oder kollidieren (getrennt vom Status-Lock _lock).
        self._lifecycle_lock = threading.Lock()
        self._running = False
        self._dirty = False
        self._dirty_at = 0.0
        self._folders: list[str] = []
        # Live-Status
        self._current: dict | None = None     # {"file","stage","started"}
        self._recent: list[dict] = []          # zuletzt verarbeitete Dateien
        self._processed_count = 0
        self._error_count = 0
        self._last_scan: str | None = None

    # --- Lifecycle ---------------------------------------------------------

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self) -> dict:
        """Startet die Ueberwachung (thread-sicher gegen doppelten Start)."""
        with self._lifecycle_lock:
            return self._start_locked()

    def _start_locked(self) -> dict:
        if self.is_running():
            return self.status()

        try:
            from watchdog.events import PatternMatchingEventHandler
            from watchdog.observers import Observer
        except Exception as exc:  # noqa: BLE001 — watchdog nicht installiert
            raise RuntimeError(f"watchdog nicht verfuegbar: {exc}")

        valid = []
        for folder in self._enabled_watch_folders():
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
                valid.append(folder)
            except OSError:
                continue

        watcher = self

        class _Handler(PatternMatchingEventHandler):
            def __init__(self) -> None:
                super().__init__(patterns=["*.pdf", "*.PDF"], ignore_directories=True)

            def on_created(self, event) -> None:  # noqa: ANN001
                watcher._notify()

            def on_moved(self, event) -> None:  # noqa: ANN001
                watcher._notify()

            def on_modified(self, event) -> None:  # noqa: ANN001
                watcher._notify()

        observer = Observer()
        handler = _Handler()
        for folder in valid:
            observer.schedule(handler, folder, recursive=False)
        observer.daemon = True
        observer.start()

        self._stop.clear()
        self._wakeup.clear()
        worker = threading.Thread(target=self._worker_loop, name="docuflow-watch", daemon=True)
        worker.start()

        with self._lock:
            self._observer = observer
            self._worker = worker
            self._running = True
            self._folders = valid
        # Initialer Lauf: bereits vorhandene Dateien aufnehmen + verarbeiten.
        self._notify()
        return self.status()

    def stop(self) -> dict:
        """Stoppt die Ueberwachung (thread-sicher); laufende Verarbeitung sauber beendet."""
        with self._lifecycle_lock:
            return self._stop_locked()

    def _stop_locked(self) -> dict:
        with self._lock:
            if not self._running:
                return self.status()
            observer = self._observer
        self._stop.set()
        self._wakeup.set()
        if observer is not None:
            try:
                observer.stop()
                observer.join(timeout=5)
            except Exception:  # noqa: BLE001
                pass
        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=10)
        with self._lock:
            self._running = False
            self._observer = None
            self._worker = None
            self._current = None
        return self.status()

    def restart(self) -> dict:
        """Stoppt und startet neu — noetig wenn sich die ueberwachten Ordner aendern."""
        if self.is_running():
            self.stop()
        return self.start()

    def poke(self) -> None:
        """Externer Anstoss fuer einen Scan-/Verarbeitungslauf (z.B. 'Jetzt scannen')."""
        self._notify()

    # --- Worker ------------------------------------------------------------

    def _notify(self) -> None:
        with self._lock:
            self._dirty = True
            self._dirty_at = time.monotonic()
        self._wakeup.set()

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            self._wakeup.wait(timeout=2.0)
            self._wakeup.clear()
            if self._stop.is_set():
                break
            with self._lock:
                dirty = self._dirty
                quiet_for = time.monotonic() - self._dirty_at
            if not dirty:
                continue
            if quiet_for < self._debounce:
                time.sleep(self._debounce - quiet_for)
                if self._stop.is_set():
                    break
            with self._lock:
                self._dirty = False
            try:
                self._scan_and_process()
            except Exception as exc:  # noqa: BLE001 — Worker darf nie sterben
                with self._lock:
                    self._error_count += 1
                    self._recent.insert(0, {"file": "—", "result": f"Fehler: {exc}", "time": _now()})
                    self._recent = self._recent[:_RECENT_MAX]

    def _scan_and_process(self) -> None:
        proc = self._processor
        proc.scan_input_folders()  # neue Dateien registrieren (dedupliziert via DB)
        with self._lock:
            self._last_scan = _now()
        # Alle NEU-Dokumente seriell abarbeiten. Jede Verarbeitung verlaesst den
        # NEU-Status (-> REVIEW/PROCESSED/ERROR), daher terminiert die Schleife.
        guard = 0
        while not self._stop.is_set() and guard < 1000:
            news = proc.db.get_documents(DocumentStatus.NEW)
            if not news:
                break
            self._process_one(news[-1])  # aelteste zuerst (Liste ist DESC sortiert)
            guard += 1

    def _process_one(self, doc) -> None:  # noqa: ANN001
        proc = self._processor
        self._wait_stable(Path(doc.file_path))
        with self._lock:
            self._current = {"file": doc.file_name, "stage": "start", "started": _now()}

        def on_stage(stage: str) -> None:
            with self._lock:
                if self._current:
                    self._current["stage"] = stage

        result = "?"
        try:
            processed, auto_sorted = asyncio.run(
                proc.process_and_maybe_auto_sort(doc, on_stage=on_stage)
            )
            result = "auto-sortiert" if auto_sorted else processed.status.value
            with self._lock:
                self._processed_count += 1
        except Exception as exc:  # noqa: BLE001
            result = f"Fehler: {exc}"
            with self._lock:
                self._error_count += 1
        finally:
            with self._lock:
                self._recent.insert(0, {"file": doc.file_name, "result": result, "time": _now()})
                self._recent = self._recent[:_RECENT_MAX]
                self._current = None

    @staticmethod
    def _wait_stable(path: Path, checks: int = 3, interval: float = 0.4) -> None:
        """Wartet bis die Dateigroesse stabil ist (Datei fertig geschrieben)."""
        if not path.exists():
            return
        last = -1
        stable = 0
        for _ in range(checks * 4):
            try:
                size = path.stat().st_size
            except OSError:
                return
            if size == last and size > 0:
                stable += 1
                if stable >= checks:
                    return
            else:
                stable = 0
                last = size
            time.sleep(interval)

    # --- Status ------------------------------------------------------------

    def _enabled_watch_folders(self) -> list[str]:
        folders = []
        for fc in self._processor.cfg.get("input_folders", []):
            if fc.get("enabled", True) and fc.get("watch", True):
                folders.append(fc["path"])
        return folders

    def status(self) -> dict:
        """Thread-sicherer Snapshot fuer /api/watch/status + Live-Anzeige."""
        try:
            pending = len(self._processor.db.get_documents(DocumentStatus.NEW))
        except Exception:  # noqa: BLE001
            pending = 0
        running = self.is_running()
        folders = list(self._folders) if running else self._enabled_watch_folders()
        with self._lock:
            return {
                "running": running,
                "folders": folders,
                "queue": pending,
                "current": dict(self._current) if self._current else None,
                "recent": [dict(r) for r in self._recent],
                "processed_count": self._processed_count,
                "error_count": self._error_count,
                "last_scan": self._last_scan,
            }
