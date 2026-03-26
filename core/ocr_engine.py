"""DocuFlow OCR-Engine — GLM-OCR via Ollama fuer KI-basierte Dokumenten-Extraktion."""

from __future__ import annotations

import base64
import json
import re
from datetime import date
from pathlib import Path

import ollama

from core import pdf_reader
from core.models import DocumentType, ExtractionResult, LineItem


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


def is_available(ollama_url: str = "http://localhost:11434", model: str = "glm-ocr") -> bool:
    """Prueft ob Ollama erreichbar ist und das Modell vorhanden."""
    try:
        client = ollama.Client(host=ollama_url)
        models = client.list()
        model_names = [m.model for m in models.models]
        return any(model in name for name in model_names)
    except Exception:
        return False


async def extract_from_pdf(
    file_path: str | Path,
    ollama_url: str = "http://localhost:11434",
    model: str = "glm-ocr",
    timeout: int = 120,
) -> ExtractionResult:
    """Extrahiert Daten aus einem PDF via GLM-OCR (async, blockiert Event-Loop nicht)."""
    import asyncio
    file_path = Path(file_path)

    # Sync-Operationen in Thread auslagern damit Event-Loop frei bleibt
    loop = asyncio.get_event_loop()
    img_bytes = await loop.run_in_executor(
        None, pdf_reader.render_page_as_image, file_path, 0, 200
    )
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # AsyncClient statt Client — blockiert Event-Loop nicht während Ollama antwortet
    client = ollama.AsyncClient(host=ollama_url)

    response = await client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT,
                "images": [img_b64],
            },
        ],
        options={"num_gpu": 99},  # GPU-Modus: minicpm-v läuft auf Pascal (GTX 1080 Ti)
    )

    raw_response = response.message.content
    return _parse_response(raw_response)


def _parse_response(raw: str) -> ExtractionResult:
    """Parst die JSON-Antwort des OCR-Modells."""
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

    parsed_date = _safe_date(data.get("date"))
    due_date = _safe_date(data.get("due_date"))

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

    return ExtractionResult(
        sender=str(data.get("sender", "") or ""),
        date=parsed_date,
        invoice_number=str(data.get("invoice_number", "") or ""),
        total_amount=_safe_float(data.get("total_amount")),
        currency=str(data.get("currency", "EUR") or "EUR"),
        line_items=line_items,
        vat_rate=_safe_float(data.get("vat_rate")),
        vat_amount=_safe_float(data.get("vat_amount")),
        due_date=due_date,
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
