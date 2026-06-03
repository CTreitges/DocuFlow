"""DocuFlow Regeln-Store — Laden und Speichern von Sortier-Regeln."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from ruamel.yaml import YAML

from core.models import ConditionField, ConditionOperator, RuleCondition, SortRule

_yaml = YAML()
_yaml.default_flow_style = False

# Default-Regeldatei. In Tests via monkeypatch ueberschreibbar.
RULES_FILE = Path(__file__).parent.parent / "data" / "rules.yaml"


def _rules_file() -> Path:
    """Aktive Regeldatei. DOCUFLOW_RULES (zur Aufrufzeit gelesen!) erlaubt eine
    isolierte Datei fuer Tests/Live-Demos, ohne die echte data/rules.yaml
    anzufassen — analog zu DOCUFLOW_DB / DOCUFLOW_CONFIG. Faellt sonst auf das
    (in Tests monkeypatchbare) Modul-Attribut RULES_FILE zurueck."""
    env = os.environ.get("DOCUFLOW_RULES")
    return Path(env) if env else RULES_FILE


def load_rules(path: Path | None = None) -> list[SortRule]:
    p = path or _rules_file()
    if not p.exists():
        return _default_rules()
    try:
        with open(p) as f:
            data = _yaml.load(f)
        if not data or not isinstance(data, list):
            return _default_rules()
        return [SortRule(**r) for r in data]
    except Exception:
        return _default_rules()


def save_rules(rules: list[SortRule], path: Path | None = None) -> None:
    p = path or _rules_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump(mode="json") for r in rules]
    with open(p, "w", encoding="utf-8") as f:
        _yaml.dump(data, f)


def create_rule(name: str) -> SortRule:
    return SortRule(
        id=uuid.uuid4().hex[:8],
        name=name,
        conditions=[],
        target_base="./sorted",
        target_subfolders=["{jahr}"],
        filename_parts=["{datum}", "{absender}"],
        enabled=True,
        priority=0,
    )


def _default_rules() -> list[SortRule]:
    return [
        SortRule(
            id="fallback",
            name="Fallback (alle Dokumente)",
            conditions=[],
            target_base="./sorted",
            target_subfolders=["{jahr}", "Sonstige"],
            filename_parts=["{datum}", "{absender}"],
            enabled=True,
            priority=999,
        )
    ]
