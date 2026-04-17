"""DocuFlow Verarbeitungs-Pipeline — Dreistufig: Text → Template → OCR."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core import config, ocr_engine, pdf_reader, template_matcher, template_generator
from core.database import Database
from core.file_organizer import build_target_path, evaluate_rules, move_file
from core.models import Document, DocumentStatus, ExtractionResult, SortRule


class Processor:
    def __init__(self, db: Database):
        self.db = db
        self.cfg = config.get()
        self._templates = template_matcher.load_templates(
            self.cfg.get("templates", {}).get("path", "./templates")
        )
        self._rules: list[SortRule] = []

    def set_rules(self, rules: list[SortRule]) -> None:
        self._rules = rules

    def reload_templates(self) -> None:
        self._templates = template_matcher.load_templates(
            self.cfg.get("templates", {}).get("path", "./templates")
        )

    def scan_input_folders(self) -> list[Document]:
        """Scannt alle Input-Ordner nach neuen PDFs."""
        new_docs = []
        for folder_cfg in self.cfg.get("input_folders", []):
            if not folder_cfg.get("enabled", True):
                continue
            folder = Path(folder_cfg["path"])
            folder.mkdir(parents=True, exist_ok=True)
            for pdf_file in folder.glob("*.pdf"):
                file_path = str(pdf_file.resolve())
                if not self.db.document_exists(file_path):
                    doc = Document(
                        file_path=file_path,
                        file_name=pdf_file.name,
                        status=DocumentStatus.NEW,
                    )
                    doc.id = self.db.add_document(doc)
                    self.db.add_history(doc.id, "scan", f"Neue Datei erkannt: {pdf_file.name}")
                    new_docs.append(doc)
        return new_docs

    async def process_document(self, doc: Document) -> Document:
        """Dreistufige Verarbeitung: Text → Template → OCR."""
        import asyncio
        doc.status = DocumentStatus.PROCESSING
        self.db.update_document(doc)

        file_path = Path(doc.file_path)
        if not file_path.exists():
            doc.status = DocumentStatus.ERROR
            self.db.update_document(doc)
            return doc

        # Stufe 1: Text-Extraktion (in Thread damit Event-Loop frei bleibt)
        text = ""
        has_text = await asyncio.to_thread(pdf_reader.has_text, file_path)
        if has_text:
            text = await asyncio.to_thread(pdf_reader.extract_text, file_path)

        # Stufe 2: Template-Matching
        if text:
            matched_tpl, confidence = template_matcher.match_template(text, self._templates)
            if matched_tpl:
                extraction = template_matcher.extract_with_template(text, matched_tpl)
                doc.extraction = extraction
                doc.template_id = matched_tpl.id
                doc.status = DocumentStatus.REVIEW
                doc.processed_at = datetime.now()
                self.db.update_document(doc)
                self.db.add_history(doc.id, "template_match",
                                    f"Template '{matched_tpl.sender_name}' erkannt (Score: {confidence:.0%})")
                return doc

        # Stufe 3: OCR (german-ocr primär, Ollama als Fallback)
        ollama_cfg = self.cfg.get("ollama", {})
        german_ocr_cfg = self.cfg.get("german_ocr", {})
        use_german_ocr = german_ocr_cfg.get("enabled", True)
        german_ocr_backend = german_ocr_cfg.get("backend", "llamacpp")
        german_ocr_gpu_layers = german_ocr_cfg.get("n_gpu_layers", -1)

        if ocr_engine.is_available(ollama_cfg.get("url", "http://localhost:11434"),
                                   ollama_cfg.get("model", "minicpm-v")):
            try:
                extraction = await ocr_engine.extract_from_pdf(
                    file_path,
                    ollama_url=ollama_cfg.get("url", "http://localhost:11434"),
                    model=ollama_cfg.get("model", "minicpm-v"),
                    timeout=ollama_cfg.get("timeout", 120),
                    german_ocr_backend=german_ocr_backend,
                    german_ocr_gpu_layers=german_ocr_gpu_layers,
                    use_german_ocr=use_german_ocr,
                )
                if text and not extraction.raw_text:
                    extraction.raw_text = text
                doc.extraction = extraction
                doc.status = DocumentStatus.REVIEW
                doc.processed_at = datetime.now()
                self.db.update_document(doc)
                ocr_label = "German-OCR" if use_german_ocr and ocr_engine.is_german_ocr_available() else "Ollama-OCR"
                self.db.add_history(doc.id, "ocr", f"{ocr_label} Extraktion abgeschlossen")
                return doc
            except Exception as e:
                doc.status = DocumentStatus.ERROR
                self.db.update_document(doc)
                self.db.add_history(doc.id, "error", f"OCR-Fehler: {e}")
                return doc

        # Fallback: Nur Text, keine strukturierte Extraktion
        if text:
            doc.extraction = ExtractionResult(raw_text=text)
            doc.status = DocumentStatus.REVIEW
        else:
            doc.status = DocumentStatus.ERROR
            self.db.add_history(doc.id, "error", "Kein Text extrahierbar und OCR nicht verfuegbar")

        doc.processed_at = datetime.now()
        self.db.update_document(doc)
        return doc

    def confirm_and_sort(self, doc: Document) -> str | None:
        """Bestaetigt Extraktion, erstellt Template und sortiert die Datei."""
        if not doc.extraction:
            return None

        # Template erzeugen wenn noch keins zugeordnet
        if not doc.template_id and doc.extraction.sender:
            tpl = template_generator.generate_template(doc.extraction, doc.extraction.raw_text)
            tpl_path = template_generator.save_template(
                tpl, self.cfg.get("templates", {}).get("path", "./templates")
            )
            doc.template_id = tpl.id
            self.reload_templates()
            self.db.add_history(doc.id, "template_created",
                                f"Template '{tpl.sender_name}' erstellt: {tpl_path}")

        # Sortier-Regel anwenden
        rule = evaluate_rules(doc, self._rules)
        if rule:
            target = build_target_path(doc, rule)
            actual_path = move_file(doc.file_path, target)
            doc.sorted_path = str(actual_path)
            doc.status = DocumentStatus.PROCESSED
            self.db.update_document(doc)
            self.db.add_history(doc.id, "sorted",
                                f"Sortiert nach: {actual_path}")
            return str(actual_path)

        # Keine passende Regel — nur als verarbeitet markieren
        doc.status = DocumentStatus.PROCESSED
        self.db.update_document(doc)
        self.db.add_history(doc.id, "confirmed", "Bestaetigt ohne Sortier-Regel")
        return None
