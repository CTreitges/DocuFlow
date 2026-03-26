"""DocuFlow OCR-Engine — german-ocr (primär, HuggingFace) + Ollama (Fallback)."""

from __future__ import annotations

import base64
import json
import re
import tempfile
from datetime import date
from pathlib import Path

import ollama

from core import pdf_reader
from core.models import DocumentType, ExtractionResult, LineItem


# ---------------------------------------------------------------------------
# Prompt fuer Ollama-Fallback (JSON-Extraktion)
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """You are a document data extraction assistant. Analyze this document image and extract the following information as JSON. IMPORTANT: Respond in English only. Return ONLY the JSON, no explanation.

{
  "sender": "company name of sender (in original language)",
  "date": "YYYY-MM-DD",
  "invoice_number": "invoice number or empty string",
  "total_amount": 0.00,
  "currency": "EUR",
  "vat_rate": 19.0,
  "vat_amount": 0.00,
  "due_date": "YYYY-MM-DD or null",
  "iban": "IBAN or empty string",
  "customer_number": "customer number or empty string",
  "document_type": "rechnung|vertrag|lieferschein|brief|sonstig",
  "line_items": [
    {"description": "item description", "quantity": 1, "unit_price": 0.00, "total": 0.00}
  ]
}

Rules:
- Return ONLY valid JSON, no markdown, no Chinese, no explanation
- Missing fields: use null for numbers/dates, empty string for text
- document_type must be one of: rechnung, vertrag, lieferschein, brief, sonstig"""


# ---------------------------------------------------------------------------
# Singleton — german-ocr Modell wird nur einmal geladen
# ---------------------------------------------------------------------------
_german_ocr_instance = None
_german_ocr_backend_loaded: str | None = None


def _get_german_ocr(backend: str = "ollama", n_gpu_layers: int = -1):
    global _german_ocr_instance, _german_ocr_backend_loaded
    if _german_ocr_instance is None or _german_ocr_backend_loaded != backend:
        from german_ocr import GermanOCR  # type: ignore
        if backend == "llamacpp":
            _german_ocr_instance = GermanOCR(backend=backend, n_gpu_layers=n_gpu_layers)
        else:
            _german_ocr_instance = GermanOCR(backend=backend)
        _german_ocr_backend_loaded = backend
    return _german_ocr_instance


# ---------------------------------------------------------------------------
# Verfügbarkeits-Checks
# ---------------------------------------------------------------------------

def is_german_ocr_available() -> bool:
    """Prueft ob das german-ocr Paket installiert ist."""
    try:
        import german_ocr  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def is_model_loaded() -> bool:
    """Prueft ob das Modell bereits im Speicher geladen ist (Singleton aktiv)."""
    return _german_ocr_instance is not None


async def preload_model(backend: str = "ollama", n_gpu_layers: int = -1) -> None:
    """Laedt das Modell im Hintergrund vor (blockiert Event-Loop nicht)."""
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _get_german_ocr, backend, n_gpu_layers)


def is_available(ollama_url: str = "http://localhost:11434", model: str = "minicpm-v") -> bool:
    """Prueft ob irgendein OCR-Backend verfuegbar ist (german-ocr oder Ollama)."""
    if is_german_ocr_available():
        return True
    try:
        client = ollama.Client(host=ollama_url)
        models = client.list()
        model_names = [m.model for m in models.models]
        return any(model in name for name in model_names)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Haupt-Einstiegspunkt
# ---------------------------------------------------------------------------

async def extract_from_pdf(
    file_path: str | Path,
    ollama_url: str = "http://localhost:11434",
    model: str = "minicpm-v",
    timeout: int = 120,
    german_ocr_backend: str = "ollama",
    german_ocr_gpu_layers: int = -1,
    use_german_ocr: bool = True,
) -> ExtractionResult:
    """Extrahiert Daten aus einem PDF.

    Reihenfolge:
    1. german-ocr (transformers, HuggingFace) — falls installiert und use_german_ocr=True
    2. Ollama (minicpm-v oder konfiguriertes Modell) — Fallback
    """
    import asyncio
    file_path = Path(file_path)
    loop = asyncio.get_event_loop()

    # Seite als Bild rendern (wird von beiden Backends genutzt)
    img_bytes = await loop.run_in_executor(
        None, pdf_reader.render_page_as_image, file_path, 0, 200
    )

    # --- Primär: german-ocr ---
    if use_german_ocr and is_german_ocr_available():
        try:
            result = await _extract_with_german_ocr(img_bytes, german_ocr_backend, german_ocr_gpu_layers, loop)
            if result.confidence.get("overall", 0) > 0.2:
                return result
        except Exception:
            pass  # Weiterleitung zum Fallback

        # Ollama-Fallback nur wenn Server erreichbar (kein Verbindungsfehler riskieren)
        if not _is_ollama_reachable(ollama_url):
            return ExtractionResult(
                raw_text="[German-OCR fehlgeschlagen, Ollama nicht erreichbar]",
                confidence={"overall": 0.0},
            )

    # --- Fallback: Ollama ---
    return await _extract_with_ollama(img_bytes, ollama_url, model)


def _is_ollama_reachable(ollama_url: str) -> bool:
    """Schneller Check ob Ollama-Server antwortet (kein Modell-Check)."""
    try:
        client = ollama.Client(host=ollama_url)
        client.list()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Interne Extraktions-Backends
# ---------------------------------------------------------------------------

async def _extract_with_german_ocr(
    img_bytes: bytes, backend: str, n_gpu_layers: int, loop
) -> ExtractionResult:
    """Extraktion via german-ocr (schreibt temp-Datei, laeuft in Thread)."""

    def _run_sync() -> str:
        ocr = _get_german_ocr(backend, n_gpu_layers)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name
        try:
            return ocr.extract(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    markdown_text = await loop.run_in_executor(None, _run_sync)
    return _parse_german_markdown(markdown_text)


async def _extract_with_ollama(
    img_bytes: bytes, ollama_url: str, model: str
) -> ExtractionResult:
    """Extraktion via Ollama-Modell (AsyncClient, blockiert Event-Loop nicht)."""
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    client = ollama.AsyncClient(host=ollama_url)
    response = await client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT,
                "images": [img_b64],
            }
        ],
        options={"num_gpu": 99},
    )
    return _parse_response(response.message.content)


# ---------------------------------------------------------------------------
# Markdown-Parser fuer german-ocr Output (robust, viele Varianten)
# ---------------------------------------------------------------------------

def _parse_german_markdown(text: str) -> ExtractionResult:
    """Parst den Markdown-Output von german-ocr in ein ExtractionResult.

    Sehr tolerant gegenueber Variationen im Modell-Output:
    - Mit/ohne **Fettdruck**
    - Verschiedene Feldnamen (Rechnung Nr., Rechnungsnr., ...)
    - Windows-/Unix-Zeilenenden
    - Deutsches und ISO-Datumsformat
    """
    # Zeilenenden normalisieren
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    def _find_any(patterns: list[str], default: str = "") -> str:
        """Probiert mehrere Patterns, gibt ersten Treffer zurueck."""
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                val = m.group(1).strip().rstrip('*').strip()
                if val:
                    return val
        return default

    def _find_amount_any(patterns: list[str]) -> float | None:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                result = _safe_float_de(m.group(1))
                if result is not None:
                    return result
        return None

    def _parse_german_date(raw: str) -> date | None:
        if not raw:
            return None
        raw = raw.strip().split()[0]  # Nur erstes Token (kein Wochentag etc.)
        # DD.MM.YYYY
        m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", raw)
        if m:
            year = int(m.group(3))
            if year < 100:
                year += 2000
            try:
                return date(year, int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass
        # ISO YYYY-MM-DD
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None

    # --- Dokumenttyp ---
    doc_type_raw = _find_any([
        r"#\s*Dokumenttyp\s*[:\-]\s*\*{0,2}(\w+)",
        r"Dokumenttyp\s*[:\-]\s*\*{0,2}(\w+)",
        r"Typ\s*[:\-]\s*\*{0,2}(\w+)",
    ]).lower()
    _DOC_TYPE_MAP = {
        "rechnung": DocumentType.INVOICE,
        "invoice": DocumentType.INVOICE,
        "vertrag": DocumentType.CONTRACT,
        "lieferschein": DocumentType.DELIVERY_NOTE,
        "brief": DocumentType.LETTER,
        "angebot": DocumentType.OTHER,
        "gutschrift": DocumentType.INVOICE,
    }
    doc_type = _DOC_TYPE_MAP.get(doc_type_raw, DocumentType.OTHER)

    # Falls kein expliziter Typ: aus Überschrift ableiten
    if doc_type == DocumentType.OTHER:
        heading = _find_any([r"^#\s+(.+)$"])
        if re.search(r"rechnung|invoice", heading, re.IGNORECASE):
            doc_type = DocumentType.INVOICE
        elif re.search(r"lieferschein", heading, re.IGNORECASE):
            doc_type = DocumentType.DELIVERY_NOTE

    # --- Rechnungsnummer ---
    invoice_number = _find_any([
        r"\*{0,2}Rechnungsnummer\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Rechnung(?:s)?[\s\-]?(?:Nr|No|Num)\.?\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Re(?:chn)?\.?[\s\-]?Nr\.?\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Invoice[\s\-]?(?:Nr|No|Number)\.?\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Belegnummer\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
    ])

    # --- Datum ---
    date_raw = _find_any([
        r"\*{0,2}(?:Rechnungs)?datum\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}Datum\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}Date\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}Ausstellungsdatum\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        # ISO-Format
        r"\*{0,2}(?:Rechnungs)?datum\*{0,2}\s*[:\-]\s*\*{0,2}\s*(\d{4}-\d{2}-\d{2})",
        r"\*{0,2}Datum\*{0,2}\s*[:\-]\s*\*{0,2}\s*(\d{4}-\d{2}-\d{2})",
    ])

    # --- Fälligkeitsdatum ---
    due_date_raw = _find_any([
        r"\*{0,2}F[äa]lligkeitsdatum\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}Zahlungsziel\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}F[äa]llig(?:\s+am)?\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        r"\*{0,2}Due\s+Date\*{0,2}\s*[:\-]\s*\*{0,2}\s*([\d]{1,2}[\./\-][\d]{1,2}[\./\-][\d]{2,4})",
        # ISO-Format (Zahlungsziel)
        r"\*{0,2}(?:F[äa]lligkeitsdatum|Zahlungsziel)\*{0,2}\s*[:\-]\s*\*{0,2}\s*(\d{4}-\d{2}-\d{2})",
    ])

    # --- IBAN ---
    iban_raw = _find_any([
        r"\*{0,2}IBAN\*{0,2}\s*[:\-]\s*\*{0,2}\s*([A-Z]{2}\d{2}[\dA-Z\s]{10,30})",
    ])
    iban = re.sub(r'\s+', '', iban_raw) if iban_raw else ""  # Leerzeichen entfernen

    # --- Kundennummer ---
    customer_number = _find_any([
        r"\*{0,2}Kundennummer\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Kunden[\s\-]?Nr\.?\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
        r"\*{0,2}Kd\.?[\s\-]?Nr\.?\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*]+)",
    ])

    # --- Absender ---
    sender = _find_any([
        # "## Absender\n**Firma XYZ**"
        r"##\s*(?:Absender|Rechnungssteller|Von|Lieferant|Vendor)\s*\n\*{1,2}([^\n\*]+)\*{0,2}",
        # "**Absender**: Firma XYZ" oder "**Von:** Firma"
        r"\*{0,2}(?:Absender|Rechnungssteller|Von|Verkäufer|Lieferant)\*{0,2}\s*[:\-]\s*\*{0,2}\s*([^\n\*]+)",
        # Erste fett-formatierte Zeile im Dokument (oft Firmenname)
        r"^\*\*([A-ZÄÖÜ][^\n\*]{3,50}(?:GmbH|AG|KG|OHG|UG|e\.V\.|eG|GbR|Ltd|Inc|SE))\*\*",
        # Firmenname in Überschrift: "# Amazon Rechnung" → "Amazon"
        r"^#+\s+([A-ZÄÖÜ][^\n]+?)(?:\s+Rechnung|\s+Invoice|\s+GmbH|\s+AG|\s+KG)\b",
    ])

    # --- Gesamtbetrag ---
    total_amount = _find_amount_any([
        r"\*{0,2}Gesamtbetrag\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}Gesamt(?:summe|betrag)?\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}Total(?:\s+Amount)?\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}Brutto(?:betrag)?\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}Rechnungsbetrag\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}Endbetrag\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        # Tabellenzelle mit "Gesamt" am Ende
        r"(?:Gesamt|Total)\s*\|\s*€?\s*([\d.,]+)",
    ])

    # --- MwSt ---
    vat_rate_m = re.search(
        r"(?:MwSt|USt|VAT|Mehrwertsteuer)[.\s]*\(?(\d+(?:[.,]\d+)?)%\)?",
        text, re.IGNORECASE
    )
    vat_rate = _safe_float_de(vat_rate_m.group(1)) if vat_rate_m else None

    vat_amount = _find_amount_any([
        r"\*{0,2}MwSt\.?\s*\(?\d+%?\)?\*{0,2}\s*[:\-]\s*\*{0,2}€?\s*([\d.,]+)",
        r"\*{0,2}(?:USt|VAT|Mehrwertsteuer)\b[^\n]*?€?\s*([\d.,]+)",
        r"(?:MwSt|USt|VAT)\s*\|\s*€?\s*([\d.,]+)",
    ])

    # --- Positionen aus Markdown-Tabelle ---
    line_items: list[LineItem] = []
    # Robuster Tabellen-Parser: mit oder ohne führendes |, 4 oder 5 Spalten
    _header_re = re.compile(
        r'(?i)^(?:pos\.?|beschr|desc|artikel|leistung|menge|qty|einzel|preis|price|gesamt|total|betrag)',
    )
    _sep_re = re.compile(r'^[\|\-\s:]+$')  # Trennzeilen überspringen

    for line in text.split('\n'):
        # Nur Zeilen mit mindestens 3 Pipe-Zeichen
        if line.count('|') < 3:
            continue
        # Trennzeile (--- | --- | ---)
        stripped = line.strip().strip('|')
        if _sep_re.match(stripped):
            continue
        cols = [c.strip().replace('*', '').replace('€', '').replace('EUR', '').strip()
                for c in line.split('|') if c.strip()]
        if len(cols) < 3:
            continue
        # Header-Zeilen überspringen
        if any(_header_re.match(c) for c in cols):
            continue
        # 5-Spalten-Tabelle: Pos | Beschreibung | Menge | Einzelpreis | Gesamt
        if len(cols) >= 5:
            desc, qty_s, price_s, total_s = cols[1], cols[2], cols[3], cols[4]
        # 4-Spalten-Tabelle: Beschreibung | Menge | Preis | Gesamt
        else:
            desc, qty_s, price_s, total_s = cols[0], cols[1], cols[2], cols[3]
        qty = _safe_float_de(qty_s)
        price = _safe_float_de(price_s)
        total = _safe_float_de(total_s)
        if desc and qty is not None:
            line_items.append(LineItem(
                description=desc,
                quantity=qty,
                unit_price=price,
                total=total,
            ))

    # --- Konfidenz ---
    found_fields = [sender, invoice_number, date_raw, total_amount]
    filled = sum(1 for f in found_fields if f)
    overall = 0.25 + 0.65 * (filled / len(found_fields))

    confidence: dict[str, float] = {
        "overall": overall,
        "sender": 0.85 if sender else 0.2,
        "date": 0.85 if date_raw else 0.2,
        "invoice_number": 0.85 if invoice_number else 0.2,
        "total_amount": 0.85 if total_amount else 0.2,
    }

    return ExtractionResult(
        sender=sender,
        date=_parse_german_date(date_raw),
        invoice_number=invoice_number,
        total_amount=total_amount,
        currency="EUR",
        line_items=line_items,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        due_date=_parse_german_date(due_date_raw),
        iban=iban,
        customer_number=customer_number,
        document_type=doc_type,
        confidence=confidence,
        raw_text=text,
    )


def _safe_float_de(val: str) -> float | None:
    """Konvertiert deutsches Zahlenformat ('1.234,56') in float."""
    if not val:
        return None
    raw = val.strip().replace("€", "").replace(" ", "")
    if "." in raw and "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Ollama JSON-Parser (unveraendert)
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> ExtractionResult:
    """Parst die JSON-Antwort des Ollama-Modells."""
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        return ExtractionResult(raw_text=raw, confidence={"overall": 0.1})

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError:
        return ExtractionResult(raw_text=raw, confidence={"overall": 0.1})

    line_items = []
    for item in data.get("line_items", []) or []:
        if isinstance(item, dict):
            line_items.append(LineItem(
                description=str(item.get("description", "")),
                quantity=_safe_float(item.get("quantity")),
                unit_price=_safe_float(item.get("unit_price")),
                total=_safe_float(item.get("total")),
            ))

    doc_type_str = str(data.get("document_type", "sonstig")).lower()
    try:
        doc_type = DocumentType(doc_type_str)
    except ValueError:
        doc_type = DocumentType.OTHER

    confidence = {}
    for field in ["sender", "date", "invoice_number", "total_amount"]:
        val = data.get(field)
        if val and str(val).strip() and str(val) != "null":
            confidence[field] = 0.8
        else:
            confidence[field] = 0.2
    confidence["overall"] = sum(confidence.values()) / len(confidence)

    return ExtractionResult(
        sender=str(data.get("sender", "") or ""),
        date=_safe_date(data.get("date")),
        invoice_number=str(data.get("invoice_number", "") or ""),
        total_amount=_safe_float(data.get("total_amount")),
        currency=str(data.get("currency", "EUR") or "EUR"),
        line_items=line_items,
        vat_rate=_safe_float(data.get("vat_rate")),
        vat_amount=_safe_float(data.get("vat_amount")),
        due_date=_safe_date(data.get("due_date")),
        iban=str(data.get("iban", "") or ""),
        customer_number=str(data.get("customer_number", "") or ""),
        document_type=doc_type,
        confidence=confidence,
        raw_text=raw,
    )


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_date(val) -> date | None:
    if not val or str(val).lower() == "null":
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except ValueError:
        return None
