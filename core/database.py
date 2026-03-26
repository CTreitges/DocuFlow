"""DocuFlow Datenbank — SQLite via aiosqlite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from core.models import SCHEMA_SQL, Document, DocumentStatus, ExtractionResult


class Database:
    def __init__(self, db_path: str = "./data/docuflow.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_document(self, doc: Document) -> int:
        extraction_json = doc.extraction.model_dump_json() if doc.extraction else None
        cur = self.conn.execute(
            """INSERT INTO documents (file_path, file_name, status, extraction_json,
               template_id, sorted_path, created_at, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc.file_path, doc.file_name, doc.status.value, extraction_json,
             doc.template_id, doc.sorted_path,
             doc.created_at.isoformat(), doc.processed_at.isoformat() if doc.processed_at else None),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_document(self, doc: Document) -> None:
        extraction_json = doc.extraction.model_dump_json() if doc.extraction else None
        self.conn.execute(
            """UPDATE documents SET status=?, extraction_json=?, template_id=?,
               sorted_path=?, processed_at=? WHERE id=?""",
            (doc.status.value, extraction_json, doc.template_id,
             doc.sorted_path, doc.processed_at.isoformat() if doc.processed_at else None,
             doc.id),
        )
        self.conn.commit()

    def get_document(self, doc_id: int) -> Document | None:
        row = self.conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        return self._row_to_doc(row) if row else None

    def get_documents(self, status: DocumentStatus | None = None) -> list[Document]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM documents WHERE status=? ORDER BY created_at DESC",
                (status.value,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_doc(r) for r in rows]

    def document_exists(self, file_path: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM documents WHERE file_path=?", (file_path,)
        ).fetchone()
        return row is not None

    def add_history(self, document_id: int, action: str, details: str = "") -> None:
        self.conn.execute(
            "INSERT INTO history (document_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (document_id, action, details, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_history(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            """SELECT h.*, d.file_name FROM history h
               JOIN documents d ON h.document_id = d.id
               ORDER BY h.timestamp DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        stats = {}
        for status in DocumentStatus:
            row = self.conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE status=?", (status.value,)
            ).fetchone()
            stats[status.value] = row["cnt"]
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
        stats["gesamt"] = row["cnt"]
        return stats

    @staticmethod
    def _row_to_doc(row: sqlite3.Row) -> Document:
        extraction = None
        if row["extraction_json"]:
            extraction = ExtractionResult.model_validate_json(row["extraction_json"])
        return Document(
            id=row["id"],
            file_path=row["file_path"],
            file_name=row["file_name"],
            status=DocumentStatus(row["status"]),
            extraction=extraction,
            template_id=row["template_id"],
            sorted_path=row["sorted_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
        )
