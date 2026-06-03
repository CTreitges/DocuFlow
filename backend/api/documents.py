"""Dokument-Endpunkte: Scan, Verarbeitung, Bestaetigung, Ignorieren, Vorschau."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response

from core import pdf_reader
from core.models import DocumentStatus
from backend.deps import AppState, get_state
from backend.schemas import ExtractionUpdate

router = APIRouter(tags=["documents"])


def _dump(doc) -> dict:
    return doc.model_dump(mode="json")


@router.post("/scan")
async def scan(state: AppState = Depends(get_state)) -> dict:
    """Scannt alle aktivierten Input-Ordner nach neuen PDFs."""
    new_docs = state.processor.scan_input_folders()
    return {"new": len(new_docs), "documents": [_dump(d) for d in new_docs]}


@router.get("/documents")
async def list_documents(
    status: str | None = None, state: AppState = Depends(get_state)
) -> list[dict]:
    st: DocumentStatus | None = None
    if status:
        try:
            st = DocumentStatus(status)
        except ValueError:
            raise HTTPException(400, f"Unbekannter Status: {status}")
    return [_dump(d) for d in state.db.get_documents(st)]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: int, state: AppState = Depends(get_state)) -> dict:
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    return _dump(doc)


@router.post("/documents/{doc_id}/process")
async def process_document(doc_id: int, state: AppState = Depends(get_state)) -> dict:
    """Verarbeitet ein Dokument (Text → Template → OCR) und sortiert ggf. automatisch."""
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    doc, auto_sorted = await state.processor.process_and_maybe_auto_sort(doc)
    return {"document": _dump(doc), "auto_sorted": auto_sorted}


@router.post("/process-all")
async def process_all(state: AppState = Depends(get_state)) -> dict:
    """Verarbeitet alle neuen Dokumente sequentiell."""
    docs = state.db.get_documents(DocumentStatus.NEW)
    results = []
    for doc in docs:
        doc, auto_sorted = await state.processor.process_and_maybe_auto_sort(doc)
        results.append(
            {"id": doc.id, "status": doc.status.value, "auto_sorted": auto_sorted}
        )
    return {"processed": len(results), "results": results}


@router.patch("/documents/{doc_id}/extraction")
async def update_extraction(
    doc_id: int, payload: ExtractionUpdate, state: AppState = Depends(get_state)
) -> dict:
    """Speichert manuelle Korrekturen der extrahierten Felder."""
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    doc.extraction = payload.extraction
    state.db.update_document(doc)
    state.db.add_history(doc.id, "korrigiert", "Extraktion manuell korrigiert")
    return _dump(doc)


@router.post("/documents/{doc_id}/confirm")
async def confirm(doc_id: int, state: AppState = Depends(get_state)) -> dict:
    """Bestaetigt die Extraktion, erzeugt ggf. ein Template und sortiert die Datei."""
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    sorted_path = state.processor.confirm_and_sort(doc)
    updated = state.db.get_document(doc_id)
    return {"sorted_path": sorted_path, "document": _dump(updated) if updated else None}


@router.post("/documents/{doc_id}/ignore")
async def ignore(doc_id: int, state: AppState = Depends(get_state)) -> dict:
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    doc.status = DocumentStatus.IGNORED
    state.db.update_document(doc)
    state.db.add_history(doc.id, "ignoriert", f"Dokument ignoriert: {doc.file_name}")
    return {"ok": True}


@router.post("/documents/{doc_id}/reactivate")
async def reactivate(doc_id: int, state: AppState = Depends(get_state)) -> dict:
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    doc.status = DocumentStatus.NEW
    state.db.update_document(doc)
    state.db.add_history(doc.id, "reaktiviert", f"Dokument reaktiviert: {doc.file_name}")
    return {"ok": True}


@router.get("/documents/{doc_id}/preview")
def preview(doc_id: int, state: AppState = Depends(get_state)) -> Response:
    """Rendert die erste Seite des PDFs als PNG (Vorschau)."""
    doc = state.db.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    path = Path(doc.sorted_path or doc.file_path)
    if not path.exists():
        raise HTTPException(404, "Datei nicht gefunden")
    try:
        png = pdf_reader.render_page_as_image(path, 0, 150)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Vorschau fehlgeschlagen: {exc}")
    return Response(content=png, media_type="image/png")
