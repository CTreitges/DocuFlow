"""DocuFlow Zahlen-Parser — Toleranter Parser fuer deutsches/internationales Format."""

from __future__ import annotations


def parse_amount(val: str | float | int | None) -> float | None:
    """Wandelt einen Text mit Zahl in float.

    Akzeptiert deutsches ('1.234,56'), englisches ('1,234.56') und einfaches
    Format ('1234.56', '1234,56'). Ignoriert Waehrungszeichen und Leerzeichen.
    Gibt None zurueck wenn der Wert nicht konvertierbar ist.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    raw = str(val).strip()
    if not raw:
        return None

    # Waehrungszeichen und Leerzeichen entfernen
    for ch in ("€", "$", "£", "EUR", "USD", "GBP", "\xa0", " "):
        raw = raw.replace(ch, "")
    raw = raw.replace("%", "")

    if not raw:
        return None

    has_dot = "." in raw
    has_comma = "," in raw

    if has_dot and has_comma:
        # Wenn Komma hinter Punkt → deutsches Format (Punkt=Tausender, Komma=Dezimal)
        # Wenn Punkt hinter Komma → englisches Format (Komma=Tausender, Punkt=Dezimal)
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif has_comma:
        # Nur Komma → als Dezimaltrenner interpretieren
        raw = raw.replace(",", ".")

    try:
        return float(raw)
    except ValueError:
        return None
