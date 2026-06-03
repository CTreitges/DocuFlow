// Mock-Daten aus dem Claude-Design (data.jsx) — dienen als Fallback-Anzeige,
// wenn das Backend nicht erreichbar ist, und liefern die Editor-Optionslisten.

export const DOCUMENTS = [
  {
    id: 'd1', filename: 'rechnung_amazon_4412.pdf', path: 'D:/Scans/Eingang/rechnung_amazon_4412.pdf',
    status: 'review', absender: 'Amazon EU S.à r.l.', datum: '2026-03-15', betrag: '1.234,56 EUR', reNr: 'INV-2026-0412', konfidenz: 96,
    extraction: {
      absender: { value: 'Amazon EU S.à r.l.', conf: 96 }, datum: { value: '2026-03-15', conf: 94 },
      rechnungsnr: { value: 'INV-2026-0412', conf: 91 }, betrag: { value: '1.234,56 EUR', conf: 88 },
      iban: { value: 'DE89 3704 0044 0532 0130 00' }, kundennr: { value: 'KD-770421' },
      mwst: { value: '19 %' }, zahlungsziel: { value: '14 Tage netto' }, dokumenttyp: { value: 'Rechnung' },
    },
    positionen: [
      { nr: 1, beschreibung: 'Logitech MX Master 3S', menge: '2', gesamt: '199,80 EUR' },
      { nr: 2, beschreibung: 'USB-C Hub 8-in-1', menge: '1', gesamt: '49,90 EUR' },
      { nr: 3, beschreibung: 'Versand & Verpackung', menge: '1', gesamt: '4,99 EUR' },
    ],
  },
  { id: 'd2', filename: 'telekom_maerz.pdf', path: 'D:/Scans/Eingang/telekom_maerz.pdf', status: 'neu', absender: 'Telekom Deutschland GmbH', datum: '2026-03-12', betrag: '89,90 EUR', reNr: 'RG-88231', konfidenz: 73 },
  { id: 'd3', filename: 'scan_2026-03-18_093442.pdf', path: 'D:/Scans/Eingang/scan_2026-03-18_093442.pdf', status: 'neu', absender: '—', datum: '—', betrag: '—', reNr: '—', konfidenz: 0 },
  {
    id: 'd4', filename: 'mueller_dachbau_re_0231.pdf', path: 'D:/Scans/Eingang/mueller_dachbau_re_0231.pdf',
    status: 'review', absender: 'Müller Dachbau GmbH', datum: '2026-03-09', betrag: '8.940,00 EUR', reNr: 'MD-2026-0231', konfidenz: 81,
    extraction: {
      absender: { value: 'Müller Dachbau GmbH', conf: 84 }, datum: { value: '2026-03-09', conf: 79 },
      rechnungsnr: { value: 'MD-2026-0231', conf: 67 }, betrag: { value: '8.940,00 EUR', conf: 72 },
      iban: { value: 'DE21 5004 0000 0312 8472 11' }, kundennr: { value: 'KN-0098' },
      mwst: { value: '19 %' }, zahlungsziel: { value: '30 Tage netto' }, dokumenttyp: { value: 'Handwerkerrechnung' },
    },
    positionen: [
      { nr: 1, beschreibung: 'Dachziegel Tonnaturrot (qm)', menge: '120', gesamt: '5.040,00 EUR' },
      { nr: 2, beschreibung: 'Arbeitsstunden Dachdecker', menge: '48', gesamt: '3.456,00 EUR' },
      { nr: 3, beschreibung: 'Entsorgung Altmaterial', menge: '1', gesamt: '444,00 EUR' },
    ],
  },
  { id: 'd5', filename: 'schneider_elektro_fehler.pdf', path: 'D:/Scans/Eingang/schneider_elektro_fehler.pdf', status: 'fehler', absender: 'Schneider Elektro', datum: '2026-03-11', betrag: '—', reNr: '—', konfidenz: 0,
    error: 'OCRError: PDF enthält nur gescannte Bilder ohne Textebene.\n  → German-OCR Backend nicht erreichbar (Ollama timeout nach 120s)\n  → at pipeline.ocr_fallback (ocr_engine.py:212)' },
  { id: 'd6', filename: 'stadtwerke_abschlag.pdf', path: 'D:/Scans/Eingang/stadtwerke_abschlag.pdf', status: 'neu', absender: 'Stadtwerke München', datum: '2026-03-14', betrag: '142,00 EUR', reNr: 'SW-554120', konfidenz: 62 },
  { id: 'd7', filename: 'amazon_rueckerstattung.pdf', path: 'D:/Scans/Ignoriert/amazon_rueckerstattung.pdf', status: 'ignoriert', absender: 'Amazon EU S.à r.l.', datum: '2026-02-28', betrag: '−24,90 EUR', reNr: 'CR-2026-0091', konfidenz: 90 },
  { id: 'd8', filename: 'newsletter_anhang.pdf', path: 'D:/Scans/Ignoriert/newsletter_anhang.pdf', status: 'ignoriert', absender: '—', datum: '2026-02-20', betrag: '—', reNr: '—', konfidenz: 0 },
];

export const SORTED_DOCS = [
  { filename: '2026-03-08_INV-2026-0390.pdf', absender: 'Amazon EU S.à r.l.', datum: '2026-03-08', betrag: '312,40 EUR', sortedTo: 'D:/Rechnungen/2026/Amazon/', processedAt: '2026-03-19 09:12' },
  { filename: '2026-03-05_RG-88004.pdf', absender: 'Telekom Deutschland GmbH', datum: '2026-03-05', betrag: '89,90 EUR', sortedTo: 'D:/Rechnungen/2026/Telekom/', processedAt: '2026-03-19 08:54' },
  { filename: '2026-03-01_SW-553980.pdf', absender: 'Stadtwerke München', datum: '2026-03-01', betrag: '142,00 EUR', sortedTo: 'D:/Rechnungen/2026/Stadtwerke/', processedAt: '2026-03-18 17:41' },
  { filename: '2026-02-26_MD-2026-0228.pdf', absender: 'Müller Dachbau GmbH', datum: '2026-02-26', betrag: '2.310,00 EUR', sortedTo: 'D:/Rechnungen/2026/Handwerker/', processedAt: '2026-03-18 14:22' },
  { filename: '2026-02-22_INV-2026-0361.pdf', absender: 'Amazon EU S.à r.l.', datum: '2026-02-22', betrag: '77,98 EUR', sortedTo: 'D:/Rechnungen/2026/Amazon/', processedAt: '2026-03-17 11:03' },
];

export const ACTIVITY_LOG = [
  { id: 'a1', type: 'auto-sortiert', filename: '2026-03-08_INV-2026-0390.pdf', details: 'Regel „Amazon → /Amazon" · Konfidenz 94%', time: '09:12', period: 'heute', undoable: true },
  { id: 'a2', type: 'bestätigt', filename: 'rechnung_amazon_4412.pdf', details: 'Felder geprüft, Template aktualisiert', time: '09:08', period: 'heute' },
  { id: 'a3', type: 'ocr', filename: 'scan_2026-03-18_093442.pdf', details: 'German-OCR · 3 Seiten · 4.812 Zeichen', time: '08:59', period: 'heute' },
  { id: 'a4', type: 'sortiert', filename: '2026-03-05_RG-88004.pdf', details: 'Telekom → /Telekom', time: '08:54', period: 'heute', undoable: true },
  { id: 'a5', type: 'scan', filename: 'Ordner „D:/Scans/Eingang"', details: '3 neue Dokumente gefunden', time: '08:50', period: 'heute' },
  { id: 'a6', type: 'fehler', filename: 'schneider_elektro_fehler.pdf', details: 'OCR-Backend timeout (120s)', time: 'Gestern 18:30', period: 'woche' },
  { id: 'a7', type: 'template-erstellt', filename: 'Müller Dachbau GmbH', details: 'Neues Template aus 2 bestätigten Dokumenten', time: 'Gestern 14:25', period: 'woche' },
  { id: 'a8', type: 'korrektur', filename: 'mueller_dachbau_re_0228.pdf', details: 'Rechnungsnr. manuell korrigiert', time: 'Gestern 14:22', period: 'woche' },
  { id: 'a9', type: 'reaktiviert', filename: 'stadtwerke_2025_dez.pdf', details: 'Aus „Ignoriert" zurückgeholt', time: 'Mo 10:11', period: 'woche' },
  { id: 'a10', type: 'ignoriert', filename: 'newsletter_anhang.pdf', details: 'Kein Rechnungsdokument', time: '12.03. 16:02', period: 'alles' },
  { id: 'a11', type: 'template', filename: 'telekom_maerz.pdf', details: 'Template „Telekom" angewendet', time: '10.03. 09:30', period: 'alles' },
  { id: 'a12', type: 'auto-sortiert', filename: '2026-02-22_INV-2026-0361.pdf', details: 'Regel „Amazon → /Amazon"', time: '28.02. 11:03', period: 'alles', undoable: true },
];

export const TEMPLATES = [
  { id: 'tpl_a1f3', absender: 'Amazon EU S.à r.l.', muster: 6, felder: 9, schwelle: 90, verwendet: 142 },
  { id: 'tpl_9b2c', absender: 'Telekom Deutschland GmbH', muster: 3, felder: 8, schwelle: 85, verwendet: 38 },
  { id: 'tpl_77de', absender: 'Stadtwerke München', muster: 2, felder: 7, schwelle: 80, verwendet: 24 },
  { id: 'tpl_0c41', absender: 'Müller Dachbau GmbH', muster: 2, felder: 9, schwelle: 75, verwendet: 6 },
];

export const RULES = [
  { id: 'r1', name: 'Amazon Rechnungen', enabled: true, conditions: [{ logic: 'WENN', field: 'Absender', operator: 'enthält', value: 'Amazon' }, { logic: 'UND', field: 'Dokumenttyp', operator: 'ist', value: 'Rechnung' }], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}', '{absender}'], nameParts: ['{datum}', '{rechnungsnr}'] },
  { id: 'r2', name: 'Große Handwerkerrechnungen', enabled: true, conditions: [{ logic: 'WENN', field: 'Betrag', operator: 'größer als', value: '1000' }, { logic: 'UND', field: 'Inhalt', operator: 'enthält', value: 'Handwerk' }], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}', 'Handwerker'], nameParts: ['{datum}', '{absender}', '{betrag}'] },
  { id: 'r3', name: 'Telekom & Stadtwerke', enabled: false, conditions: [{ logic: 'WENN', field: 'Absender', operator: 'beginnt mit', value: 'Telekom' }, { logic: 'ODER', field: 'Absender', operator: 'enthält', value: 'Stadtwerke' }], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}', '{absender}'], nameParts: ['{datum}', '{rechnungsnr}'] },
  { id: 'r4', name: 'Fallback — alles andere', enabled: true, conditions: [], baseFolder: 'D:/Rechnungen', subfolders: ['{jahr}', 'Sonstige'], nameParts: ['{datum}', '{absender}'] },
];

export const RULE_FIELDS = ['Absender', 'Betrag', 'Inhalt', 'Dokumenttyp', 'Rechnungsnr.'];
export const RULE_OPERATORS = ['enthält', 'ist', 'beginnt mit', 'größer als', 'kleiner als'];
export const RULE_LOGIC = ['UND', 'ODER'];
export const PLACEHOLDERS = ['{absender}', '{datum}', '{jahr}', '{monat}', '{tag}', '{rechnungsnr}', '{betrag}', '{typ}', '{waehrung}'];
export const SUBFOLDER_OPTIONS = ['{jahr}', '{monat}', '{absender}', '{typ}', 'Rechnungen', 'Handwerker', 'Sonstige', 'Archiv'];

export const INPUT_FOLDERS = [
  { id: 'f1', path: 'D:/Scans/Eingang', active: true, exists: true },
  { id: 'f2', path: 'D:/Downloads/Rechnungen', active: true, exists: true },
  { id: 'f3', path: 'E:/Archiv/2025', active: false, exists: false },
];

export const OCR_FIELDS = [
  { label: 'Absender', value: 'Amazon EU S.à r.l.', conf: 96 },
  { label: 'Datum', value: '2026-03-15', conf: 94 },
  { label: 'Rechnungsnr.', value: 'INV-2026-0412', conf: 91 },
  { label: 'Betrag', value: '1.234,56 EUR', conf: 88 },
  { label: 'IBAN', value: 'DE89 3704 0044 0532 0130 00', conf: 85 },
  { label: 'Kundennr.', value: 'KD-770421', conf: 82 },
  { label: 'MwSt-Satz', value: '19 %', conf: 93 },
  { label: 'Zahlungsziel', value: '14 Tage netto', conf: 77 },
  { label: 'Dokumenttyp', value: 'Rechnung', conf: 90 },
  { label: 'Währung', value: 'EUR', conf: 98 },
];

export const OCR_TEMPLATE_YAML = `template: amazon_eu
version: 3
sender_match:
  - "Amazon EU S.à r.l."
  - "amazon.de"
threshold: 90
fields:
  absender:
    anchor: "Verkauft von"
    regex: "^(.*S\\.à r\\.l\\.)$"
  datum:
    anchor: "Rechnungsdatum"
    format: "%d.%m.%Y"
  rechnungsnr:
    anchor: "Rechnungsnummer"
    regex: "INV-\\d{4}-\\d{4}"
  betrag:
    anchor: "Gesamtbetrag"
    currency: EUR
  iban:
    regex: "DE\\d{2}( \\d{4}){5}"
positions:
  table_anchor: "Beschreibung"
  columns: [pos, beschreibung, menge, gesamt]`;

export const OCR_PDF_TEXT = `Amazon EU S.à r.l.
38 avenue John F. Kennedy, L-1855 Luxembourg

RECHNUNG

Rechnungsnummer: INV-2026-0412
Rechnungsdatum: 15.03.2026
Kundennummer: KD-770421

Pos  Beschreibung                  Menge   Gesamt
1    Logitech MX Master 3S          2      199,80 EUR
2    USB-C Hub 8-in-1               1       49,90 EUR
3    Versand & Verpackung           1        4,99 EUR

Zwischensumme:        254,69 EUR
MwSt (19%):            48,39 EUR
Gesamtbetrag:      1.234,56 EUR

Zahlbar innerhalb 14 Tage netto.
IBAN: DE89 3704 0044 0532 0130 00`;

export const PREVIEW_DATA = {
  '{absender}': 'Amazon', '{datum}': '2026-03-15', '{jahr}': '2026', '{monat}': '03',
  '{tag}': '15', '{rechnungsnr}': 'INV-12345', '{betrag}': '1234,56', '{typ}': 'Rechnung', '{waehrung}': 'EUR',
};
