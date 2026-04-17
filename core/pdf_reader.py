"""DocuFlow PDF-Reader — Text-Extraktion mit PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def extract_text(file_path: str | Path) -> str:
    """Extrahiert den gesamten Text aus einem PDF."""
    with fitz.open(str(file_path)) as doc:
        return "\n".join(page.get_text() for page in doc)


def extract_text_per_page(file_path: str | Path) -> list[str]:
    """Extrahiert Text seitenweise."""
    with fitz.open(str(file_path)) as doc:
        return [page.get_text() for page in doc]


def has_text(file_path: str | Path) -> bool:
    """Prueft ob das PDF eingebetteten Text hat (nicht nur gescannt)."""
    with fitz.open(str(file_path)) as doc:
        for page in doc:
            if page.get_text().strip():
                return True
    return False


def get_page_count(file_path: str | Path) -> int:
    with fitz.open(str(file_path)) as doc:
        return len(doc)


def render_page_as_image(file_path: str | Path, page_num: int = 0, dpi: int = 200) -> bytes:
    """Rendert eine PDF-Seite als PNG-Bytes (fuer OCR oder Vorschau)."""
    with fitz.open(str(file_path)) as doc:
        page = doc[page_num]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")


def get_metadata(file_path: str | Path) -> dict:
    with fitz.open(str(file_path)) as doc:
        meta = dict(doc.metadata) if doc.metadata else {}
        meta["page_count"] = len(doc)
        return meta
