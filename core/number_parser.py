"""Zentrales Parsen deutscher Geldbetraege/Zahlen (Tausenderpunkt, Dezimalkomma).

Frueher dupliziert: ocr_engine._safe_float_de (behandelte den reinen
Tausenderpunkt-Fall '1.234' falsch -> 1.234 statt 1234) und mehrere inline
`float(value.replace(",", "."))`-Stellen im template_matcher (gleicher Bug bei
'1.234,56'). Diese Funktion ist die eine Quelle der Wahrheit.

Deutsche Konvention: '.' = Tausendertrenner, ',' = Dezimaltrenner.
"""

from __future__ import annotations


def parse_amount(value: object) -> float | None:
    """Parst einen deutschen Zahlen-/Betragsstring in float. None bei Unparsbarem.

    Beispiele:
        '1.234'      -> 1234.0     (Tausenderpunkt, 3 Stellen)
        '1.500'      -> 1500.0
        '1.234,56'   -> 1234.56    (Tausenderpunkt + Dezimalkomma)
        '1.500,50'   -> 1500.5
        '1234,56'    -> 1234.56    (nur Dezimalkomma)
        '1234.56'    -> 1234.56    (einzelner Punkt, !=3 Nachkommastellen -> Dezimal)
        '1.234.567'  -> 1234567.0  (mehrere Tausenderpunkte)
        '19,5%'      -> 19.5
        '-1.500'     -> -1500.0
        'abc' / ''   -> None
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    # Waehrungs-/Prozent-/Leerzeichen-Rauschen entfernen (auch geschuetztes Leerz.).
    for token in ("€", "EUR", "eur", "%", " ", " "):
        raw = raw.replace(token, "")
    raw = raw.strip()
    if not raw:
        return None

    sign = ""
    if raw[0] in "+-":
        sign, raw = raw[0], raw[1:]
    if not raw:
        return None

    has_dot = "." in raw
    has_comma = "," in raw

    if has_dot and has_comma:
        # Beide vorhanden -> Punkt(e) sind Tausender, Komma ist Dezimal.
        raw = raw.replace(".", "").replace(",", ".")
    elif has_comma:
        # Nur Komma -> Dezimaltrenner.
        raw = raw.replace(",", ".")
    elif has_dot:
        parts = raw.split(".")
        if len(parts) > 2:
            # Mehrere Punkte koennen nur Tausendertrenner sein.
            raw = "".join(parts)
        elif len(parts[1]) == 3 and parts[0].isdigit() and parts[0] != "":
            # Einzelner Punkt mit genau 3 Folgestellen ('1.234') -> Tausenderpunkt.
            raw = parts[0] + parts[1]
        # sonst: einzelner Punkt als Dezimalpunkt belassen ('1234.56', '1.5').

    try:
        return float(sign + raw)
    except ValueError:
        return None
