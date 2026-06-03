"""Regressionstest TD-01 — config.py muss config.yaml als UTF-8 lesen/schreiben.

Hintergrund: core.config.load()/save() nutzten open() ohne encoding-Argument.
Auf Plattformen, deren Default-Encoding nicht UTF-8 ist (Windows cp1252; unter
POSIX das C-Locale = ASCII), zerlegt das Umlaut-Pfade in der Konfiguration
(z.B. Ausgabe-Ordner "…/Müll/Würzburg"). Der Fix setzt encoding="utf-8" an
beiden open()-Stellen.

Der erste Test ist der echte Rot→Grün-Beweis: ein Subprozess mit LC_ALL=C
(ASCII-Default) liest/schreibt die Config. Mit dem alten Code wirft das einen
UnicodeDecode-/EncodeError (Exit≠0); mit dem Fix laeuft es durch.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _reset_config_global():
    """config.load/save setzen das Modul-Global core.config._config. Nach jedem
    Test zuruecksetzen, damit keine reihenfolge-abhaengige Flakiness entsteht."""
    import core.config as cfg
    before = cfg._config
    yield
    cfg._config = before
UMLAUT_PATH = "/data/Müll/Würzburg/Anhänge & Belege"
UMLAUT_NAME = "DocuFlöw – Büro"

_yaml = YAML()


def _write_config_utf8(cfg_path: Path) -> None:
    """Schreibt eine Config mit Umlauten garantiert als UTF-8 (Setup, unabhaengig
    vom Code under Test)."""
    cfg = {
        "app": {"name": UMLAUT_NAME, "version": "test"},
        "output": {"base_path": UMLAUT_PATH},
        "auto_mode": False,
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        _yaml.dump(cfg, f)


def test_config_survives_c_locale(tmp_path):
    """Echter Rot→Grün-Test: unter LC_ALL=C (ASCII-Default) muss config.load()
    die UTF-8-Umlaut-Config lesen und config.save() sie wieder schreiben koennen.
    Der -c-Quelltext enthaelt bewusst KEINE Umlaute (sonst scheitert schon das
    Parsen des Arguments unter C-Locale) — die Umlaute stecken nur in der Datei.
    """
    cfg_path = tmp_path / "config.yaml"
    _write_config_utf8(cfg_path)

    env = {
        **os.environ,
        "LC_ALL": "C",
        "LANG": "C",
        "LC_CTYPE": "C",
        "PYTHONUTF8": "0",          # UTF-8-Mode aus -> C-Locale = ASCII greift
        "PYTHONCOERCECLOCALE": "0",  # keine C.UTF-8-Coercion (PEP 538)
        "PYTHONWARNINGS": "ignore",
        "DOCUFLOW_CONFIG": str(cfg_path),
    }
    script = "from core import config; c = config.load(); config.save(c); print('OK')"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"config unter C-Locale gescheitert (alter Bug?):\nSTDOUT={proc.stdout}\nSTDERR={proc.stderr}"
    )
    assert "OK" in proc.stdout

    # Datei muss weiterhin gueltiges UTF-8 mit intakten Umlauten sein.
    raw = cfg_path.read_bytes()
    text = raw.decode("utf-8")  # wirft bei kaputtem Encoding
    assert UMLAUT_PATH in text
    assert UMLAUT_NAME in text


def test_config_roundtrip_utf8(tmp_path):
    """In-Process-Roundtrip: save -> load liefert die Umlaut-Werte unveraendert,
    und die Datei ist als UTF-8 abgelegt (Multibyte-Sequenz fuer 'ü' vorhanden)."""
    from core import config

    cfg_path = tmp_path / "config.yaml"
    cfg = {
        "app": {"name": UMLAUT_NAME},
        "output": {"base_path": UMLAUT_PATH},
        "auto_mode": False,
    }
    config.save(cfg, cfg_path)
    loaded = config.load(cfg_path)

    assert loaded["output"]["base_path"] == UMLAUT_PATH
    assert loaded["app"]["name"] == UMLAUT_NAME

    raw = cfg_path.read_bytes()
    assert raw.decode("utf-8")          # gueltiges UTF-8
    assert "ü".encode("utf-8") in raw   # b"\xc3\xbc" -> tatsaechlich UTF-8, nicht cp1252
