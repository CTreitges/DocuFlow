"""Regressionstest TD-02 — der german-ocr-Singleton darf nur EINMAL laden.

Hintergrund: _get_german_ocr() pruefte `is None` und instanziierte ohne Lock.
Greifen Watchdog-Worker-Thread und FastAPI-Request-Threadpool gleichzeitig zu,
sehen beide None und laden das Modell doppelt -> doppelter VRAM auf der GPU.
Der Fix kapselt die Lazy-Init in einen threading.Lock (Double-Checked-Locking).

Das echte german-ocr-Paket ist hier nicht installiert; wir injizieren ein
Fake-Modul, dessen Loader die Instanziierungen zaehlt und kurz schlaeft, um das
Race-Fenster aufzuweiten. Ohne Lock zaehlt das >1, mit Lock genau 1.
"""

from __future__ import annotations

import sys
import threading
import time
import types

import core.ocr_engine as oe

N_THREADS = 8


def test_singleton_loads_once_under_concurrency(monkeypatch):
    calls: list[str] = []

    class FakeGermanOCR:
        def __init__(self, backend=None, n_gpu_layers=-1, **kwargs):
            calls.append(backend)
            time.sleep(0.05)  # Race-Fenster aufweiten

    fake_mod = types.ModuleType("german_ocr")
    fake_mod.GermanOCR = FakeGermanOCR
    monkeypatch.setitem(sys.modules, "german_ocr", fake_mod)

    # Singleton-State fuer den Test zuruecksetzen (monkeypatch stellt ihn wieder her).
    monkeypatch.setattr(oe, "_german_ocr_instance", None, raising=False)
    monkeypatch.setattr(oe, "_german_ocr_backend_loaded", None, raising=False)

    barrier = threading.Barrier(N_THREADS)
    results: list[object] = []
    lock = threading.Lock()

    def worker():
        barrier.wait()  # alle Threads moeglichst gleichzeitig in _get_german_ocr
        inst = oe._get_german_ocr(backend="ollama")
        with lock:
            results.append(inst)

    threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(calls) == 1, f"Modell {len(calls)}x geladen statt 1x (Lock fehlt?)"
    assert len(results) == N_THREADS
    # Alle Threads bekommen dieselbe Instanz.
    assert len({id(r) for r in results}) == 1


def test_backend_switch_reloads(monkeypatch):
    """Anderes Backend -> neu laden (Korrektheit des Cache-Keys bleibt erhalten)."""
    calls: list[str] = []

    class FakeGermanOCR:
        def __init__(self, backend=None, n_gpu_layers=-1, **kwargs):
            calls.append(backend)

    fake_mod = types.ModuleType("german_ocr")
    fake_mod.GermanOCR = FakeGermanOCR
    monkeypatch.setitem(sys.modules, "german_ocr", fake_mod)
    monkeypatch.setattr(oe, "_german_ocr_instance", None, raising=False)
    monkeypatch.setattr(oe, "_german_ocr_backend_loaded", None, raising=False)

    oe._get_german_ocr(backend="ollama")
    oe._get_german_ocr(backend="ollama")     # Cache-Hit
    oe._get_german_ocr(backend="llamacpp")   # Backend-Wechsel -> reload
    assert calls == ["ollama", "llamacpp"]
