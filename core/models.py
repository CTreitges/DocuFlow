"""DocuFlow Datenmodelle — Pydantic-Modelle fuer Dokumente, Regeln, Templates."""

import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class DocumentStatus(str, Enum):
    NEW = "neu"
    PROCESSING = "verarbeitung"
    REVIEW = "review"
    PROCESSED = "verarbeitet"
    ERROR = "fehler"
    IGNORED = "ignoriert"


class DocumentType(str, Enum):
    INVOICE = "rechnung"
    CONTRACT = "vertrag"
    DELIVERY_NOTE = "lieferschein"
    LETTER = "brief"
    OTHER = "sonstig"


class ConditionOperator(str, Enum):
    CONTAINS = "enthaelt"
    EQUALS = "ist"
    STARTS_WITH = "beginnt_mit"
    GREATER_THAN = "groesser_als"
    LESS_THAN = "kleiner_als"


class ConditionField(str, Enum):
    SENDER = "absender"
    AMOUNT = "betrag"
    CONTENT = "inhalt"
    DOC_TYPE = "dokumenttyp"
    INVOICE_NUMBER = "rechnungsnr"


# --- Datenmodelle ---

class LineItem(BaseModel):
    description: str = ""
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractionResult(BaseModel):
    sender: str = ""
    date: Optional[dt.date] = None
    invoice_number: str = ""
    total_amount: Optional[float] = None
    currency: str = "EUR"
    line_items: list[LineItem] = Field(default_factory=list)
    vat_rate: Optional[float] = None
    vat_amount: Optional[float] = None
    due_date: Optional[dt.date] = None
    iban: str = ""
    customer_number: str = ""
    document_type: DocumentType = DocumentType.OTHER
    confidence: dict[str, float] = Field(default_factory=dict)
    raw_text: str = ""


class Document(BaseModel):
    id: Optional[int] = None
    file_path: str
    file_name: str
    status: DocumentStatus = DocumentStatus.NEW
    extraction: Optional[ExtractionResult] = None
    template_id: Optional[str] = None
    sorted_path: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)
    processed_at: Optional[dt.datetime] = None


# --- Sortier-Regeln ---

class RuleCondition(BaseModel):
    field: ConditionField
    operator: ConditionOperator
    value: str
    logic: str = "AND"


class SortRule(BaseModel):
    id: str = ""
    name: str = ""
    conditions: list[RuleCondition] = Field(default_factory=list)
    target_base: str = ""
    target_subfolders: list[str] = Field(default_factory=list)
    filename_parts: list[str] = Field(default_factory=list)
    enabled: bool = True
    priority: int = 0


# --- Templates ---

class Template(BaseModel):
    id: str = ""
    sender_name: str = ""
    sender_patterns: list[str] = Field(default_factory=list)
    field_patterns: dict[str, str] = Field(default_factory=dict)
    confidence_threshold: float = 0.9
    times_used: int = 0
    last_used: Optional[dt.datetime] = None


# --- SQLite Schema ---

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'neu',
    extraction_json TEXT,
    template_id TEXT,
    sorted_path TEXT,
    created_at TEXT NOT NULL,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
"""
