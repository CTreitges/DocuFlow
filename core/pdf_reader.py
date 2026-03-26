"""DocuFlow PDF-Reader — Text-Extraktion mit PyMuPDF."""

from __future__ import annotations

import io
from pathlib import Path

import fitz  # PyMuPDF


def extract_text(file_path: str | Path) -> str:
    """Extrahiert den gesamten Text aus einem PDF."""
    doc = fitz.open(str(file_path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_per_page(file_path: str | Path) -> list[str]:
    """Extrahiert Text seitenweise."""
    doc = fitz.open(str(file_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return pages


def has_text(file_path: str | Path) -> bool:
    """Prueft ob das PDF eingebetteten Text hat (nicht nur gescannt)."""
    doc = fitz.open(str(file_path))
    for page in doc:
        if page.get_text().strip():
            doc.close()
            return True
    doc.close()
    return False


def get_page_count(file_path: str | Path) -> int:
    doc = fitz.open(str(file_path))
    count = len(doc)
    doc.close()
    return count


def render_page_as_image(file_path: str | Path, page_num: int = 0, dpi: int = 200) -> bytes:
    """Rendert eine PDF-Seite als PNG-Bytes (fuer OCR oder Vorschau)."""
    doc = fitz.open(str(file_path))
    page = doc[page_num]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


def get_metadata(file_path: str | Path) -> dict:
    doc = fitz.open(str(file_path))
    meta = dict(doc.metadata) if doc.metadata else {}
    meta["page_count"] = len(doc)
    doc.close()
    return meta
