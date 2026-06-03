"""DocuFlow Konfiguration — Laden und Speichern via ruamel.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

_yaml = YAML()
_yaml.preserve_quotes = True

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

_config: dict[str, Any] | None = None


def _config_path() -> Path:
    """Aktiver Config-Pfad. DOCUFLOW_CONFIG erlaubt isolierte Configs (Tests,
    Live-Demos), ohne die echte config.yaml anzufassen — analog zu DOCUFLOW_DB."""
    env = os.environ.get("DOCUFLOW_CONFIG")
    return Path(env) if env else CONFIG_PATH


def load(path: Path | None = None) -> dict[str, Any]:
    global _config
    p = path or _config_path()
    if not p.exists():
        _config = _defaults()
        save(_config, p)
    else:
        with open(p, encoding="utf-8") as f:
            _config = dict(_yaml.load(f))
    return _config


def save(cfg: dict[str, Any] | None = None, path: Path | None = None) -> None:
    global _config
    c = cfg or _config or _defaults()
    p = path or _config_path()
    with open(p, "w", encoding="utf-8") as f:
        _yaml.dump(c, f)
    _config = c


def get() -> dict[str, Any]:
    if _config is None:
        return load()
    return _config


def _defaults() -> dict[str, Any]:
    return {
        "app": {"name": "DocuFlow", "version": "0.1", "host": "127.0.0.1", "port": 8080},
        "input_folders": [{"path": "./inbox", "enabled": True, "watch": True}],
        "output": {"base_path": "./sorted"},
        "auto_mode": False,
        "auto_confidence_threshold": 0.9,
        "ollama": {"url": "http://localhost:11434", "model": "glm-ocr", "timeout": 120},
        "database": {"path": "./data/docuflow.db"},
        "templates": {"path": "./templates"},
    }
