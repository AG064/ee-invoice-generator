"""
Professional Estonian invoice layout
Based on real Estonian OÜ invoices like ULTIMADESIGN:
- Top: Buyer on left, Date/Due date/Ref on right
- Center: ARVE NR [number] title (left-aligned below)
- Line items table
- Below price: our company info | contact | bank details
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from .generator import InvoiceData

# Currency symbol mapping
CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "SEK": "kr",
    "RUB": "₽",
    "CHF": "CHF",
    "NOK": "kr",
    "DKK": "kr",
    "PLN": "zł",
    "CZK": "Kč",
    "HUF": "Ft",
    "RON": "lei",
}

def get_currency_symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency, currency + " ")


EST_LABELS = {
    "en": {
        "invoice": "INVOICE", "invoice_no": "Invoice No.",
        "buyer": "Buyer", "date": "Date", "due_date": "Due Date",
        "ref_number": "Reference No.", "late_fee": "Late fee",
        "line_description": "Description", "line_qty": "Qty",
        "line_unit": "Unit", "line_price": "Price", "line_total": "Total",
        "subtotal": "Subtotal", "vat": "VAT", "total": "TOTAL",
        "seller": "Seller", "reg_nr": "Reg. No.", "kmkr": "KMKR", "notes_label": "Notes",
        "address": "Address", "phone": "Phone", "email": "Email",
        "bank": "Bank", "iban": "IBAN", "bic": "BIC/SWIFT",
        "footer_1": "Registered in Estonia",
        "vat_not_applicable": "VAT not applicable",
    },
    "ru": {
        "invoice": "СЧЁТ", "invoice_no": "Номер счёта",
        "buyer": "Покупатель", "date": "Дата", "due_date": "Срок оплаты",
        "ref_number": "Номер ссылки", "late_fee": "Штраф %",
        "line_description": "Описание", "line_qty": "Кол",
        "line_unit": "Ед.", "line_price": "Цена", "line_total": "Итого",
        "subtotal": "Подытог", "vat": "НДС", "total": "ИТОГО",
        "seller": "Продавец", "reg_nr": "Рег. №", "kmkr": "КМКР", "notes_label": "Заметки",
        "address": "Адрес", "phone": "Тел.", "email": "Email",
        "bank": "Банк", "iban": "IBAN", "bic": "BIC",
        "footer_1": "Зарегистрировано в Эстонии",
        "vat_not_applicable": "НДС не применяется",
    },
    "et": {
        "invoice": "ARVE", "invoice_no": "Arve nr.",
        "buyer": "Ostja", "date": "Kuupäev", "due_date": "Maksetähtaeg",
        "ref_number": "Viitenumber", "late_fee": "Viivis",
        "line_description": "Kauba nimetus", "line_qty": "Kogus",
        "line_unit": "Ühik", "line_price": "Hind", "line_total": "Summa",
        "subtotal": "Summa", "vat": "Käibemaks", "total": "Kokku",
        "seller": "Müüja", "reg_nr": "Reg. nr.", "kmkr": "KMKR", "notes_label": "Märkused",
        "address": "Aadress", "phone": "Telefon", "email": "Email",
        "bank": "Pank", "iban": "IBAN", "bic": "SWIFT",
        "footer_1": "Eestis registreeritud",
        "vat_not_applicable": "KM ei kohaldata",
    },
}


def generate_invoice_pdf(data: InvoiceData, output_path: str, lang: str = "et"):
    """Generate a professional Estonian invoice PDF"""
    
    t = EST_LABELS.get(lang, EST_LABELS["en"])
    
    # Colors
    DARK = HexColor("#111111")
    GRAY = HexColor("#555555")
    LIGHT_GRAY = HexColor("#777777")
    ACCENT = HexColor("#333333")
    TABLE_HEADER_BG = ACCENT
    TABLE_ROW_ALT = HexColor("#f5f5f5")
    BORDER = HexColor("#cccccc")
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    
    elements = []
    
    # ============================================================
    # TOP SECTION: Buyer on LEFT | Dates on RIGHT
    # ============================================================
    
    label_style = ParagraphStyle("Label", fontSize=8, fontName="Helvetica-Bold",
                                  textColor=LIGHT_GRAY, leading=10, spaceAfter=1*mm)
    value_style = ParagraphStyle("Value", fontSize=9, fontName="Helvetica-Bold",
                                  textColor=DARK, leading=11)
    buyer_name_style = ParagraphStyle("BName", fontSize=12, fontName="Helvetica-Bold",
                                       textColor=DARK, leading=14)
    buyer_text = ParagraphStyle("BText", fontSize=9, fontName="Helvetica",
                                textColor=DARK, leading=11)
    
    # Buyer block - left side
    buyer_block = [
        Paragraph(f"<b>{t['buyer'].upper()}</b>", label_style),
        Paragraph(data.buyer.name or "", buyer_name_style),
    ]
    if data.buyer.address:
        buyer_block.append(Paragraph(data.buyer.address, buyer_text))
    if data.buyer.city or data.buyer.postal_code:
        buyer_block.append(Paragraph(
            f"{data.buyer.postal_code or ''} {data.buyer.city or ''}".strip(), buyer_text))
    if data.buyer.registry_code:
        buyer_block.append(Paragraph(f"{t['reg_nr']}: {data.buyer.registry_code}", buyer_text))
    if data.buyer.vat_number:
        buyer_block.append(Paragraph(f"{t['kmkr']}: {data.buyer.vat_number}", buyer_text))
    
    # Date block - right side
    inv_date_str = data.invoice_date.strftime("%d.%m.%Y") if data.invoice_date else ""
    due_date_str = data.due_date.strftime("%d.%m.%Y") if data.due_date else "—"
    ref_str = data.order_reference or "—"
    
    date_block = [
        Paragraph(f"<b>{t['date']}</b>", label_style),
        Paragraph(inv_date_str, value_style),
        Paragraph(f"<b>{t['due_date']}</b>", label_style),
        Paragraph(due_date_str, value_style),
    ]
    if ref_str != "—":
        date_block.append(Paragraph(f"<b>{t['ref_number']}</b>", label_style))
        date_block.append(Paragraph(ref_str, value_style))
    
    # Top header table: buyer | empty | dates
    top_header = Table(
        [[buyer_block, "", date_block]],
        colWidths=[80*mm, 50*mm, 50*mm]
    )
    top_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(top_header)
    elements.append(Spacer(1, 8*mm))
    
    # ============================================================
    # INVOICE TITLE: "ARVE NR 1234" - centered
    # ============================================================
    
    title_label_style = ParagraphStyle(
        "TitleLabel", fontSize=10, fontName="Helvetica",
        textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=1*mm
    )
    title_style = ParagraphStyle(
        "Title", fontSize=28, fontName="Helvetica-Bold",
        textColor=DARK, leading=32, alignment=TA_CENTER
    )
    
    elements.append(Paragraph(f"{t['invoice']} {t['invoice_no']}", title_label_style))
    elements.append(Paragraph(f"Nr. {data.invoice_number}", title_style))
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=DARK))
    elements.append(Spacer(1, 3*mm))
    
    # ============================================================
    # LINE ITEMS TABLE
    # ============================================================
    
    th_style = ParagraphStyle("TH", fontSize=8, fontName="Helvetica-Bold",
                               textColor=white)
    td_right = ParagraphStyle("TDR", fontSize=9, fontName="Helvetica",
                              textColor=DARK, alignment=TA_RIGHT)
    td_left = ParagraphStyle("TDL", fontSize=9, fontName="Helvetica", textColor=DARK)
    td_center = ParagraphStyle("TDC", fontSize=8, fontName="Helvetica",
                               textColor=LIGHT_GRAY, alignment=TA_CENTER)
    
    # 4 columns: description | qty | unit | price (total shown only in grand total)
    col_widths = [90*mm, 22*mm, 22*mm, 35*mm]
    
    table_data = [[
        Paragraph(f"<b>{t['line_description']}</b>", th_style),
        Paragraph(f"<b>{t['line_qty']}</b>", th_style),
        Paragraph(f"<b>{t['line_unit']}</b>", th_style),
        Paragraph(f"<b>{t['line_price']}</b>", th_style),
   ]]
    
    subtotal = 0
    total_vat = 0
    
    for i, line in enumerate(data.lines):
        net = line.unit_price
        line_net = net * line.quantity
        line_gross = line_net * (1 + line.vat_rate)
        subtotal += line_net
        total_vat += line_net * line.vat_rate
        
        bg = TABLE_ROW_ALT if i % 2 == 0 else white
        
        row = [
            Paragraph(line.description, td_left),
            Paragraph(f"{line.quantity:.2f}", td_right),
            Paragraph(line.unit, td_center),
            Paragraph(f"{get_currency_symbol(data.currency)} {net:.2f}", td_right),
        ]
        table_data.append(row)
    
    if not data.lines:
        table_data.append(["", "", "", ""])
    
    items_table = Table(table_data, colWidths=col_widths)
    
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("TOPPADDING", (0, 0), (-1, 0), 4*mm),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4*mm),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 3*mm),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3*mm),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BOX", (0, 0), (-1, -1), 1, DARK),
    ]
    
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ROW_ALT))
    
    items_table.setStyle(TableStyle(style_cmds))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))
    
    # ============================================================
    # TOTALS - right aligned
    # ============================================================
    
    tl = ParagraphStyle("TL", fontSize=10, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT)
    tv = ParagraphStyle("TV", fontSize=10, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
    gl = ParagraphStyle("GL", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
    gv = ParagraphStyle("GV", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
    
    grand_total = subtotal + total_vat
    
    totals_data = [
        [Paragraph(t["subtotal"], tl), Paragraph(f"{get_currency_symbol(data.currency)} {subtotal:.2f}", tv)],
    ]
    
    if total_vat > 0:
        totals_data.append([Paragraph(f"{t['vat']} (20%)", tl), Paragraph(f"{get_currency_symbol(data.currency)} {total_vat:.2f}", tv)])
    else:
        totals_data.append([Paragraph(t["vat_not_applicable"], tl), Paragraph(f"{get_currency_symbol(data.currency)} 0.00", tv)])
    
    totals_data.append([
        Paragraph(t["total"], gl),
        Paragraph(f"{get_currency_symbol(data.currency)} {grand_total:.2f}", gv)
    ])
    
    totals_table = Table(totals_data, colWidths=[80*mm, 70*mm])
    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 2, DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
    ]))
    
    totals_outer = Table([[totals_table]], colWidths=[150*mm])
    totals_outer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(totals_outer)
    
    # ============================================================
    # NOTES (if any)
    # ============================================================
    if data.notes:
        elements.append(Spacer(1, 6*mm))
        notes_style = ParagraphStyle("Notes", fontSize=8, fontName="Helvetica",
                                    textColor=LIGHT_GRAY, leading=10)
        notes_label_style = ParagraphStyle("NotesLabel", fontSize=8, fontName="Helvetica-Bold",
                                          textColor=LIGHT_GRAY, leading=10)
        elements.append(Paragraph(f"<b>{t.get('notes_label', 'Notes')}:</b>", notes_label_style))
        elements.append(Paragraph(data.notes, notes_style))
    
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 4*mm))
    
    # ============================================================
    # FOOTER: Seller/Our company info (left) | Contact (center) | Bank (right)
    # ============================================================
    
    fl = ParagraphStyle("FL", fontSize=7, fontName="Helvetica-Bold",
                         textColor=LIGHT_GRAY, leading=8, spaceAfter=0*mm)
    fv = ParagraphStyle("FV", fontSize=8, fontName="Helvetica", textColor=DARK, leading=10)
    fv_bold = ParagraphStyle("FVB", fontSize=8, fontName="Helvetica-Bold", textColor=DARK, leading=10)
    
    # Column 1: Our company info
    col1 = [Paragraph(f"<b>{t['seller'].upper()}</b>",
                      ParagraphStyle("SL", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=DARK, spaceAfter=1*mm))]
    if data.seller.name:
        col1.append(Paragraph(data.seller.name, ParagraphStyle("SellerName", fontSize=12, 
                             fontName="Helvetica-Bold", textColor=DARK, leading=14)))
    if data.seller.registry_code:
        col1.append(Paragraph(f"{t['reg_nr']}: {data.seller.registry_code}", fv))
    if data.seller.vat_number:
        col1.append(Paragraph(f"{t['kmkr']}: {data.seller.vat_number}", fv))
    if data.seller.address:
        col1.append(Paragraph(data.seller.address, fv))
    if data.seller.city or data.seller.postal_code:
        col1.append(Paragraph(f"{data.seller.postal_code or ''} {data.seller.city or ''}".strip(), fv))
    
    # Column 2: Contact
    col2 = []
    if data.seller.phone:
        col2.append(Paragraph(f"<b>{t['phone']}</b>", fl))
        col2.append(Paragraph(data.seller.phone, fv))
    if data.seller.email:
        col2.append(Paragraph(f"<b>{t['email']}</b>", fl))
        col2.append(Paragraph(data.seller.email, fv))
    if not col2:
        col2 = [Paragraph("", fv)]
    
    # Column 3: Bank
    col3 = []
    if data.payment.bank_name:
        col3.append(Paragraph(f"<b>{t['bank']}</b>", fl))
        col3.append(Paragraph(data.payment.bank_name, fv))
    if data.payment.iban:
        col3.append(Paragraph(f"<b>{t['iban']}</b>", fl))
        col3.append(Paragraph(data.payment.iban, ParagraphStyle("IBAN", fontSize=9,
                            fontName="Helvetica-Bold", textColor=DARK, leading=12)))
    if data.payment.bic:
        col3.append(Paragraph(f"<b>{t['bic']}</b>", fl))
        col3.append(Paragraph(data.payment.bic, fv))
    if not col3:
        col3 = [Paragraph("", fv)]
    
    footer_table = Table([[col1, col2, col3]], colWidths=[60*mm, 45*mm, 75*mm])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 8*mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 8*mm),
    ]))
    elements.append(footer_table)
    
    # Final line
    elements.append(Spacer(1, 2*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Paragraph(
        f"A4  ·  {data.seller.name or 'ee-invoice-generator'}  ·  {t['footer_1']}",
        ParagraphStyle("Final", fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
    ))
    
    doc.build(elements)


class PDFGenerator:
    """Alias for compatibility"""
    def __init__(self, data: InvoiceData):
        self.data = data
    
    def save(self, filepath: str):
        generate_invoice_pdf(self.data, filepath, lang="et")
    
    def generate(self) -> bytes:
        from io import BytesIO
        buf = BytesIO()
        generate_invoice_pdf(self.data, buf, lang="et")
        return buf.getvalue()