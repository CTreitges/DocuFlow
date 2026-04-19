"""Generiere Test-Rechnungen für DocuFlow OCR-Testing.

Erstellt realistische deutsche Rechnungen als PDF:
- 2x Dachdecker (Müller Dachbau)
- 2x Elektriker (Schneider Elektrotechnik)
- Jeweils mit Positionen, MwSt, IBAN, Rechnungsnummer etc.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import date, timedelta
import os


def fmt_eur(val):
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_rechnung(filename, firma, daten):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=25*mm, rightMargin=25*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(name='Firma', fontSize=14, fontName='Helvetica-Bold',
                              spaceAfter=2, leading=16))
    styles.add(ParagraphStyle(name='FirmaDet', fontSize=9, fontName='Helvetica',
                              spaceAfter=1, leading=11))
    styles.add(ParagraphStyle(name='RechnTitle', fontSize=16, fontName='Helvetica-Bold',
                              spaceAfter=12, spaceBefore=20, leading=18))
    styles.add(ParagraphStyle(name='Normal9', fontSize=9, fontName='Helvetica',
                              spaceAfter=2, leading=11))
    styles.add(ParagraphStyle(name='Bold9', fontSize=9, fontName='Helvetica-Bold',
                              spaceAfter=2, leading=11))
    styles.add(ParagraphStyle(name='Footer', fontSize=7, fontName='Helvetica',
                              spaceAfter=1, leading=9, textColor=colors.grey))

    story = []

    # Firmen-Header
    story.append(Paragraph(firma["name"], styles['Firma']))
    story.append(Paragraph(firma["straße"], styles['FirmaDet']))
    story.append(Paragraph(f"{firma['plz']} {firma['ort']}", styles['FirmaDet']))
    story.append(Paragraph(f"Tel: {firma['tel']} | E-Mail: {firma['email']}", styles['FirmaDet']))
    story.append(Spacer(1, 8*mm))

    # Empfänger
    story.append(Paragraph(daten["empfänger_name"], styles['Normal9']))
    story.append(Paragraph(daten["empfänger_straße"], styles['Normal9']))
    story.append(Paragraph(daten["empfänger_plz_ort"], styles['Normal9']))
    story.append(Spacer(1, 10*mm))

    # Rechnungs-Info
    story.append(Paragraph("RECHNUNG", styles['RechnTitle']))
    
    info_data = [
        ["Rechnungsnummer:", daten["rechnungsnr"]],
        ["Rechnungsdatum:", daten["datum"].strftime("%d.%m.%Y")],
        ["Leistungszeitraum:", daten["leistungszeitraum"]],
        ["Kundennummer:", daten["kundennummer"]],
        ["USt-IdNr.:", firma["ust_id"]],
    ]
    info_table = Table(info_data, colWidths=[55*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # Positionen
    pos_header = ["Pos.", "Beschreibung", "Menge", "Einheit", "Einzelpreis", "Gesamt"]
    pos_data = [pos_header]
    for i, pos in enumerate(daten["positionen"], 1):
        pos_data.append([
            str(i),
            pos["beschreibung"],
            str(pos["menge"]),
            pos.get("einheit", "Stk."),
            fmt_eur(pos["einzelpreis"]) + " €",
            fmt_eur(pos["menge"] * pos["einzelpreis"]) + " €"
        ])

    pos_table = Table(pos_data, colWidths=[10*mm, 55*mm, 15*mm, 15*mm, 25*mm, 25*mm])
    pos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pos_table)
    story.append(Spacer(1, 5*mm))

    # Summen
    net = sum(p["menge"] * p["einzelpreis"] for p in daten["positionen"])
    mwst_rate = daten.get("mwst_rate", 19)
    mwst = net * mwst_rate / 100
    brutto = net + mwst

    sum_data = [
        ["", "", "", "Nettobetrag:", fmt_eur(net) + " €"],
        ["", "", "", f"{mwst_rate}% MwSt.:", fmt_eur(mwst) + " €"],
        ["", "", "", "Gesamtbetrag:", fmt_eur(brutto) + " €"],
    ]
    sum_table = Table(sum_data, colWidths=[10*mm, 55*mm, 15*mm, 30*mm, 35*mm])
    sum_table.setStyle(TableStyle([
        ('FONTNAME', (3, 0), (4, 1), 'Helvetica'),
        ('FONTNAME', (3, 2), (4, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
        ('LINEABOVE', (3, 0), (4, 0), 0.5, colors.grey),
        ('LINEABOVE', (3, 2), (4, 2), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 8*mm))

    # Zahlungsinformationen
    story.append(Paragraph("Zahlungsinformationen", styles['Bold9']))
    story.append(Paragraph(f"IBAN: {firma['iban']}", styles['Normal9']))
    story.append(Paragraph(f"BIC: {firma['bic']}", styles['Normal9']))
    story.append(Paragraph(f"Bank: {firma['bank']}", styles['Normal9']))
    story.append(Spacer(1, 3*mm))
    faellig = daten["datum"] + timedelta(days=daten.get("zahlungsziel", 14))
    story.append(Paragraph(f"Zahlungsziel: {faellig.strftime('%d.%m.%Y')}", styles['Normal9']))
    story.append(Paragraph(f"Bitte verwenden Sie die Rechnungsnummer {daten['rechnungsnr']} als Verwendungszweck.", styles['Normal9']))
    story.append(Spacer(1, 10*mm))

    # Grußformel
    story.append(Paragraph("Mit freundlichen Grüßen", styles['Normal9']))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(firma["name"], styles['Bold9']))
    story.append(Spacer(1, 5*mm))

    # Footer
    story.append(Paragraph(f"Geschäftsführer: {firma.get('geschäftsführer', '')} | Amtsgericht: {firma.get('amtsgericht', '')}", styles['Footer']))
    story.append(Paragraph(f"Steuernummer: {firma.get('steuernummer', '')}", styles['Footer']))

    doc.build(story)
    print(f"  ✓ {os.path.basename(filename)} ({fmt_eur(brutto)} €)")


# === FIRMA 1: Dachdecker ===
dachdecker = {
    "name": "Müller Dachbau GmbH",
    "straße": "Dachstraße 17",
    "plz": "80331",
    "ort": "München",
    "tel": "+49 89 123456-0",
    "email": "info@mueller-dachbau.de",
    "ust_id": "DE 123 456 789",
    "iban": "DE89 3704 0044 0532 0130 00",
    "bic": "COBADEFFXXX",
    "bank": "Commerzbank München",
    "geschäftsführer": "Hans Müller",
    "amtsgericht": "München HRB 54321",
    "steuernummer": "143/222/33344",
}

# === FIRMA 2: Elektriker ===
elektriker = {
    "name": "Schneider Elektrotechnik e.K.",
    "straße": "Stromweg 42",
    "plz": "50667",
    "ort": "Köln",
    "tel": "+49 221 987654-0",
    "email": "kontakt@schneider-elektro.de",
    "ust_id": "DE 987 654 321",
    "iban": "DE42 5001 0517 5407 3249 31",
    "bic": "INGDDEFFXXX",
    "bank": "ING Köln",
    "geschäftsführer": "Peter Schneider",
    "amtsgericht": "Köln HRA 12345",
    "steuernummer": "215/888/99911",
}

empfänger = {
    "empfänger_name": "Christof Treitges",
    "empfänger_straße": "Musterstraße 10",
    "empfänger_plz_ort": "50670 Köln",
}

out_dir = "/home/chris/projekte/DocuFlow/test_rechnungen"

# === RECHNUNG 1: Dachdecker - Dachreparatur ===
generate_rechnung(
    f"{out_dir}/Mueller_Dachbau_Reparatur_2026-03.pdf",
    dachdecker,
    {
        **empfänger,
        "rechnungsnr": "RD-2026-0047",
        "datum": date(2026, 3, 15),
        "leistungszeitraum": "01.03.2026 – 10.03.2026",
        "kundennummer": "KD-2847",
        "mwst_rate": 19,
        "zahlungsziel": 14,
        "positionen": [
            {"beschreibung": "Dachziegel Tondachpfanne Altdeutsch (rot)", "menge": 85, "einzelpreis": 2.40},
            {"beschreibung": "Unterdachbahn Bitumen-Dachpappe 5m Rolle", "menge": 3, "einzelpreis": 34.90},
            {"beschreibung": "Dachlatten 24x48mm, 4m", "menge": 24, "einzelpreis": 3.20},
            {"beschreibung": "Dachreparatur Nordseite – Handwerkerleistung", "menge": 14, "einzelpreis": 52.00, "einheit": "Std."},
            {"beschreibung": "Gerüststellung 3-Etagen", "menge": 1, "einzelpreis": 480.00},
            {"beschreibung": "Anfahrt/Transportkosten", "menge": 1, "einzelpreis": 65.00},
        ],
    }
)

# === RECHNUNG 2: Dachdecker - Neueindeckung ===
generate_rechnung(
    f"{out_dir}/Mueller_Dachbau_Neueindeckung_2026-04.pdf",
    dachdecker,
    {
        **empfänger,
        "rechnungsnr": "RD-2026-0063",
        "datum": date(2026, 4, 8),
        "leistungszeitraum": "15.03.2026 – 05.04.2026",
        "kundennummer": "KD-2847",
        "mwst_rate": 19,
        "zahlungsziel": 14,
        "positionen": [
            {"beschreibung": "Biber Dachziegel engobiert anthrazit", "menge": 320, "einzelpreis": 1.95},
            {"beschreibung": "Firstziegel Rollfirst", "menge": 18, "einzelpreis": 8.50},
            {"beschreibung": "Unterdachbahn diffusionsoffen 25m", "menge": 4, "einzelpreis": 42.00},
            {"beschreibung": "Dachlatten 30x50mm Konterlatten 3m", "menge": 50, "einzelpreis": 3.80},
            {"beschreibung": "Blechabdeckung First/Grat Zink", "menge": 8, "einzelpreis": 45.00},
            {"beschreibung": "Dacheindeckung komplett – Handwerkerleistung", "menge": 40, "einzelpreis": 52.00, "einheit": "Std."},
            {"beschreibung": "Dachdecker-Geselle (2. Mann)", "menge": 32, "einzelpreis": 42.00, "einheit": "Std."},
            {"beschreibung": "Container 5m³ Bauschutt", "menge": 1, "einzelpreis": 280.00},
            {"beschreibung": "Kran/Stapler Dachbefeuerung", "menge": 1, "einzelpreis": 350.00},
        ],
    }
)

# === RECHNUNG 3: Elektriker - Installation ===
generate_rechnung(
    f"{out_dir}/Schneider_Elektro_Installation_2026-03.pdf",
    elektriker,
    {
        **empfänger,
        "rechnungsnr": "SE-2026-0112",
        "datum": date(2026, 3, 22),
        "leistungszeitraum": "10.03.2026 – 18.03.2026",
        "kundennummer": "KD-0315",
        "mwst_rate": 19,
        "zahlungsziel": 30,
        "positionen": [
            {"beschreibung": "Installation LED-Einbauspots 7W (Küche)", "menge": 8, "einzelpreis": 28.50},
            {"beschreibung": "Dimmable LED-Trafo 12V 60W", "menge": 2, "einzelpreis": 34.90},
            {"beschreibung": "Unterputz-Installation Dimmer", "menge": 2, "einzelpreis": 42.00},
            {"beschreibung": "FI-Schutzschalter 25A/30mA", "menge": 1, "einzelpreis": 38.00},
            {"beschreibung": "Leitungsschutzschalter 16A (Automat)", "menge": 6, "einzelpreis": 12.50},
            {"beschreibung": "NYM-J 5x2.5mm² Kabel (pro m)", "menge": 45, "einzelpreis": 2.80, "einheit": "m"},
            {"beschreibung": "Elektroinstallation – Meisterleistung", "menge": 16, "einzelpreis": 65.00, "einheit": "Std."},
            {"beschreibung": "Elektro-Geselle (2. Mann)", "menge": 12, "einzelpreis": 48.00, "einheit": "Std."},
        ],
    }
)

# === RECHNUNG 4: Elektriker - Smart Home ===
generate_rechnung(
    f"{out_dir}/Schneider_Elektro_SmartHome_2026-04.pdf",
    elektriker,
    {
        **empfänger,
        "rechnungsnr": "SE-2026-0134",
        "datum": date(2026, 4, 12),
        "leistungszeitraum": "01.04.2026 – 10.04.2026",
        "kundennummer": "KD-0315",
        "mwst_rate": 19,
        "zahlungsziel": 30,
        "positionen": [
            {"beschreibung": "Shelly 1PM Plus Smart-Relay", "menge": 6, "einzelpreis": 18.90},
            {"beschreibung": "Shelly Dimmer 2 PWM", "menge": 3, "einzelpreis": 29.90},
            {"beschreibung": "Shelly Door/Window Sensor", "menge": 4, "einzelpreis": 14.90},
            {"beschreibung": "Shelly H&T Temperatur/Feuchte", "menge": 3, "einzelpreis": 22.90},
            {"beschreibung": "Smart-Home Gateway/Zentrale", "menge": 1, "einzelpreis": 89.00},
            {"beschreibung": "CAT7 Netzwerkkabel (pro m)", "menge": 30, "einzelpreis": 1.90, "einheit": "m"},
            {"beschreibung": "Netzwerkdose RJ45 Unterputz", "menge": 4, "einzelpreis": 8.50},
            {"beschreibung": "Smart-Home Installation + Programmierung", "menge": 10, "einzelpreis": 72.00, "einheit": "Std."},
            {"beschreibung": "Netzwerkverkabelung – Geselle", "menge": 6, "einzelpreis": 48.00, "einheit": "Std."},
            {"beschreibung": "Einrichtung/HomeKit/Alexa-Integration", "menge": 3, "einzelpreis": 72.00, "einheit": "Std."},
        ],
    }
)

print(f"\n4 Test-Rechnungen erstellt in: {out_dir}")