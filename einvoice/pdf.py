"""
Professional Estonian invoice layout
Based on real Estonian OÜ invoices:
- Top left: Company name/logo
- Top right: Buyer info block
- Below buyer: dates, ref number, due date
- Center: ARVE NR [number] title
- Middle: line items table (4 columns)
- Lower middle: subtotal, VAT, total
- Bottom: 3-column footer (seller | contact | bank)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                  Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from .generator import InvoiceData


# ============================================================
# ESTONIAN INVOICE TEMPLATES
# ============================================================
EST_LABELS = {
    "en": {
        "invoice": "INVOICE",
        "invoice_no": "Invoice No.",
        "buyer": "Buyer",
        "date": "Date",
        "due_date": "Due Date",
        "ref_number": "Reference No.",
        "late_fee": "Late fee",
        "line_description": "Description",
        "line_qty": "Qty",
        "line_unit": "Unit",
        "line_price": "Price",
        "line_total": "Total",
        "subtotal": "Subtotal",
        "vat": "VAT",
        "total": "TOTAL",
        "seller": "Seller",
        "reg_nr": "Reg. No.",
        "kmkr": "KMKR",
        "address": "Address",
        "phone": "Phone",
        "email": "Email",
        "bank": "Bank",
        "iban": "IBAN",
        "bic": "BIC/SWIFT",
        "footer_1": "Registered in Estonia",
        "vat_not_applicable": "VAT not applicable",
    },
    "ru": {
        "invoice": "СЧЁТ",
        "invoice_no": "Номер счёта",
        "buyer": "Покупатель",
        "date": "Дата",
        "due_date": "Срок оплаты",
        "ref_number": "Номер ссыпки",
        "late_fee": "Штраф %",
        "line_description": "Описание",
        "line_qty": "Кол",
        "line_unit": "Ед.",
        "line_price": "Цена",
        "line_total": "Итого",
        "subtotal": "Подытог",
        "vat": "НДС",
        "total": "ИТОГО",
        "seller": "Продавец",
        "reg_nr": "Рег. №",
        "kmkr": "КМКР",
        "address": "Адрес",
        "phone": "Тел.",
        "email": "Email",
        "bank": "Банк",
        "iban": "IBAN",
        "bic": "BIC",
        "footer_1": "Зарегистрировано в Эстонии",
        "vat_not_applicable": "НДС не применяется",
    },
    "et": {
        "invoice": "ARVE",
        "invoice_no": "Arve nr.",
        "buyer": "Ostja",
        "date": "Kuupäev",
        "due_date": "Maksetähtaeg",
        "ref_number": "Viitenumber",
        "late_fee": "Viivis",
        "line_description": "Kauba nimetus",
        "line_qty": "Kogus",
        "line_unit": "Ühik",
        "line_price": "Hind",
        "line_total": "Summa",
        "subtotal": "Summa",
        "vat": "Käibemaks",
        "total": "Kokku",
        "seller": "Müüja",
        "reg_nr": "Reg. nr.",
        "kmkr": "KMKR",
        "address": "Aadress",
        "phone": "Telefon",
        "email": "Email",
        "bank": "Pank",
        "iban": "IBAN",
        "bic": "SWIFT",
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
    ACCENT = HexColor("#222222")
    TABLE_HEADER_BG = HexColor("#333333")
    TABLE_ROW_ALT = HexColor("#f5f5f5")
    BORDER = HexColor("#cccccc")
    WHITE = white
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    
    elements = []
    
    # ============================================================
    # TOP HEADER ROW: Seller name (left) | Invoice title (center) | Date info (right)
    # ============================================================
    
    # Seller name - big, bold, top left
    seller_name_style = ParagraphStyle(
        "SellerName", fontSize=22, fontName="Helvetica-Bold",
        textColor=DARK, leading=26
    )
    seller_tagline = ParagraphStyle(
        "Tagline", fontSize=9, fontName="Helvetica",
        textColor=GRAY, leading=12
    )
    
    # Invoice metadata - top right
    meta_label = ParagraphStyle("MetaLabel", fontSize=8, fontName="Helvetica",
                              textColor=LIGHT_GRAY, leading=10)
    meta_value = ParagraphStyle("MetaValue", fontSize=9, fontName="Helvetica-Bold",
                                textColor=DARK, leading=11)
    
    # Buyer info - below seller or top right area
    buyer_label = ParagraphStyle("BuyerLabel", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=LIGHT_GRAY, leading=10, spaceAfter=1*mm)
    buyer_value = ParagraphStyle("BuyerValue", fontSize=9, fontName="Helvetica",
                                 textColor=DARK, leading=11)
    buyer_value_bold = ParagraphStyle("BuyerValueBold", fontSize=9, fontName="Helvetica-Bold",
                                     textColor=DARK, leading=11)
    
    # Build top header table
    # Left: company name | Right: invoice meta + buyer
    
    inv_date_str = data.invoice_date.strftime("%d.%m.%Y") if data.invoice_date else ""
    due_date_str = data.due_date.strftime("%d.%m.%Y") if data.due_date else "—"
    
    # Seller column content
    seller_col = [
        Paragraph(data.seller.name.upper() if data.seller.name else "", seller_name_style),
        Paragraph(data.seller.address or "", seller_tagline) if data.seller.address else "",
        Paragraph(f"{data.seller.postal_code or ''} {data.seller.city or ''}".strip(), seller_tagline),
    ]
    
    # Buyer column content (top right of header)
    buyer_col_items = [
        Paragraph(f"<b>{t['buyer'].upper()}</b>", buyer_label),
        Paragraph(data.buyer.name or "", buyer_value_bold),
    ]
    if data.buyer.address:
        buyer_col_items.append(Paragraph(data.buyer.address, buyer_value))
    if data.buyer.city or data.buyer.postal_code:
        buyer_col_items.append(Paragraph(
            f"{data.buyer.postal_code or ''} {data.buyer.city or ''}".strip(), buyer_value))
    if data.buyer.registry_code:
        buyer_col_items.append(Paragraph(f"{t['reg_nr']}: {data.buyer.registry_code}", buyer_value))
    if data.buyer.vat_number:
        buyer_col_items.append(Paragraph(f"{t['kmkr']}: {data.buyer.vat_number}", buyer_value))
    if data.buyer.email:
        buyer_col_items.append(Paragraph(data.buyer.email, buyer_value))
    
    buyer_col = buyer_col_items
    
    # Meta column (dates, invoice number)
    # Invoice title "ARVE NR 1234" goes in center
    inv_title_style = ParagraphStyle(
        "InvTitle", fontSize=28, fontName="Helvetica-Bold",
        textColor=DARK, leading=32, alignment=TA_CENTER
    )
    inv_title_col = [
        Paragraph(f"{t['invoice'].upper()} {t['invoice_no'].upper()}", 
                  ParagraphStyle("InvLabel", fontSize=10, fontName="Helvetica",
                                 textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=2*mm)),
        Paragraph(f"Nr. {data.invoice_number}", inv_title_style),
    ]
    
    # Date meta column (far right)
    meta_col = [
        Paragraph(f"<b>{t['date']}</b>", meta_label),
        Paragraph(inv_date_str, meta_value),
        Paragraph(f"<b>{t['due_date']}</b>", meta_label),
        Paragraph(due_date_str, meta_value),
    ]
    
    # Build 4-column header: [seller info | buyer info] / [inv title | date meta]
    # Actually from image: layout is
    # LEFT: Seller name in big letters
    # RIGHT TOP: Buyer info
    # The invoice title "ARVE NR" is left-aligned below or centered
    
    # Let's try: Header row 1: seller name (left) | empty | inv title + meta (right area)
    # Actually image shows:
    # TOP LEFT: Seller company name in big bold letters
    # TOP RIGHT: Buyer block
    # Below seller name: Invoice date info (Kuupäev, Maksetähtaeg, Viitenumber)
    # CENTER: "ARVE NR 1112" (the title)
    
    # From image more carefully:
    # TOP area split into left and right halves
    # Left side has seller name only (large)
    # Right side has buyer info and invoice meta
    # Invoice title "ARVE NR" is centered BELOW this
    
    header_row1 = [[
        # Seller name - left column, big
        [Paragraph(data.seller.name.upper() if data.seller.name else "", 
                  ParagraphStyle("BigSeller", fontSize=20, fontName="Helvetica-Bold",
                                 textColor=DARK, leading=24))],
        # Empty middle
        [""],
        # Buyer info block - right column
        [
            Paragraph(f"<b>{t['buyer'].upper()}</b>", 
                      ParagraphStyle("BL", fontSize=8, fontName="Helvetica-Bold",
                                     textColor=LIGHT_GRAY, spaceAfter=1*mm)),
            Paragraph(data.buyer.name or "", 
                      ParagraphStyle("BN", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=DARK, leading=12)),
        ],
        # Date / ref info - far right
        [
            Paragraph(f"<b>{t['date']}</b>", 
                      ParagraphStyle("DL", fontSize=8, textColor=LIGHT_GRAY, leading=10)),
            Paragraph(inv_date_str, 
                      ParagraphStyle("DV", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=DARK, leading=12)),
            Paragraph(f"<b>{t['due_date']}</b>", 
                      ParagraphStyle("DL2", fontSize=8, textColor=LIGHT_GRAY, leading=10, spaceBefore=2*mm)),
            Paragraph(due_date_str, 
                      ParagraphStyle("DV2", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=DARK, leading=12)),
        ],
    ]]
    
    header_table = Table(header_row1, colWidths=[70*mm, 20*mm, 55*mm, 35*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LINEAFTER", (0, 0), (1, 0), 0, white),  # no line
    ]))
    elements.append(header_table)
    
    # Invoice number title - centered, below header
    elements.append(Spacer(1, 6*mm))
    
    title_style = ParagraphStyle(
        "InvoiceTitle", fontSize=24, fontName="Helvetica-Bold",
        textColor=DARK, alignment=TA_CENTER, leading=28
    )
    elements.append(Paragraph(f"{t['invoice']} {t['invoice_no']}", 
                              ParagraphStyle("InvTitleL", fontSize=10, fontName="Helvetica",
                                             textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=1*mm)))
    elements.append(Paragraph(f"Nr. {data.invoice_number}", title_style))
    
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=DARK))
    elements.append(Spacer(1, 2*mm))
    
    # ============================================================
    # LINE ITEMS TABLE
    # ============================================================
    
    table_label = ParagraphStyle("TblLabel", fontSize=8, fontName="Helvetica-Bold",
                                  textColor=WHITE)
    table_value = ParagraphStyle("TblVal", fontSize=9, fontName="Helvetica",
                                  textColor=DARK, alignment=TA_RIGHT)
    table_value_left = ParagraphStyle("TblValL", fontSize=9, fontName="Helvetica",
                                      textColor=DARK)
    
    # Table header row
    col_widths = [90*mm, 20*mm, 20*mm, 30*mm, 30*mm]  # desc | qty | unit | price | total
    
    header_row = [
        Paragraph(f"<b>{t['line_description']}</b>", table_label),
        Paragraph(f"<b>{t['line_qty']}</b>", table_label),
        Paragraph(f"<b>{t['line_unit']}</b>", table_label),
        Paragraph(f"<b>{t['line_price']}</b>", table_label),
        Paragraph(f"<b>{t['line_total']}</b>", table_label),
    ]
    
    table_data = [header_row]
    subtotal = 0
    total_vat = 0
    
    for i, line in enumerate(data.lines):
        net = line.unit_price
        line_net = net * line.quantity
        line_gross = line_net * (1 + line.vat_rate)
        subtotal += line_net
        total_vat += line_net * line.vat_rate
        
        # Alternating row background
        bg = TABLE_ROW_ALT if i % 2 == 0 else WHITE
        
        vat_display = "0%" if line.vat_rate == 0 else f"{line.vat_rate*100:.0f}%"
        
        row = [
            Paragraph(line.description, table_value_left),
            Paragraph(f"{line.quantity:.2f}", table_value),
            Paragraph(line.unit, 
                      ParagraphStyle("TU", fontSize=8, textColor=LIGHT_GRAY, alignment=TA_CENTER)),
            Paragraph(f"€ {net:.2f}", table_value),
            Paragraph(f"€ {line_gross:.2f}", table_value),
        ]
        table_data.append(row)
    
    # If no lines, add empty row
    if not data.lines:
        table_data.append(["", "", "", "", ""])
    
    items_table = Table(table_data, colWidths=col_widths)
    
    style_cmds = [
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 4*mm),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4*mm),
        # Body styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 3*mm),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3*mm),
        # Alignment
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Borders
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BOX", (0, 0), (-1, -1), 1, DARK),
    ]
    
    # Alternating rows
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ROW_ALT))
    
    items_table.setStyle(TableStyle(style_cmds))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))
    
    # ============================================================
    # TOTALS (Subtotal | VAT | Total) - right aligned
    # ============================================================
    
    total_label_s = ParagraphStyle("TotL", fontSize=10, fontName="Helvetica",
                                    textColor=DARK, alignment=TA_RIGHT)
    total_value_s = ParagraphStyle("TotV", fontSize=10, fontName="Helvetica-Bold",
                                   textColor=DARK, alignment=TA_RIGHT)
    grand_label_s = ParagraphStyle("GrandL", fontSize=14, fontName="Helvetica-Bold",
                                    textColor=DARK, alignment=TA_RIGHT)
    grand_value_s = ParagraphStyle("GrandV", fontSize=14, fontName="Helvetica-Bold",
                                   textColor=DARK, alignment=TA_RIGHT)
    
    grand_total = subtotal + total_vat
    
    totals_data = [
        [Paragraph(t["subtotal"], total_label_s),
         Paragraph(f"€ {subtotal:.2f}", total_value_s)],
    ]
    
    # VAT line - show appropriate label
    if total_vat > 0:
        totals_data.append([
            Paragraph(f"{t['vat']} (20%)", total_label_s),
            Paragraph(f"€ {total_vat:.2f}", total_value_s)
        ])
    else:
        totals_data.append([
            Paragraph(t["vat_not_applicable"], total_label_s),
            Paragraph(f"€ 0.00", total_value_s)
        ])
    
    # Grand total with line above
    totals_data.append([
        Paragraph(t["total"], grand_label_s),
        Paragraph(f"€ {grand_total:.2f}", grand_value_s)
    ])
    
    totals_table = Table(totals_data, colWidths=[120*mm, 60*mm])
    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 2, DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    # Right-align the totals table
    totals_outer = Table([[totals_table]], colWidths=[180*mm])
    totals_outer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(totals_outer)
    
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 4*mm))
    
    # ============================================================
    # FOOTER - 3 columns: Seller | Contact | Bank
    # ============================================================
    
    footer_label = ParagraphStyle("FLabel", fontSize=7, fontName="Helvetica-Bold",
                                   textColor=LIGHT_GRAY, leading=9, spaceAfter=1*mm)
    footer_value = ParagraphStyle("FValue", fontSize=8, fontName="Helvetica",
                                   textColor=DARK, leading=10)
    
    def ft(label, value):
        return [Paragraph(f"<b>{label}</b>", footer_label), Paragraph(value, footer_value)]
    
    # Column 1: Seller
    sell_col = [Paragraph(f"<b>{t['seller'].upper()}</b>", 
                         ParagraphStyle("SL", fontSize=8, fontName="Helvetica-Bold",
                                        textColor=DARK, spaceAfter=2*mm))]
    if data.seller.name:
        sell_col.append(Paragraph(data.seller.name, 
                                  ParagraphStyle("SN", fontSize=9, fontName="Helvetica-Bold",
                                                 textColor=DARK)))
    if data.seller.registry_code:
        sell_col.append(Paragraph(f"{t['reg_nr']}: {data.seller.registry_code}", footer_value))
    if data.seller.vat_number:
        sell_col.append(Paragraph(f"{t['kmkr']}: {data.seller.vat_number}", footer_value))
    if data.seller.address:
        sell_col.append(Paragraph(data.seller.address, footer_value))
    if data.seller.city or data.seller.postal_code:
        sell_col.append(Paragraph(
            f"{data.seller.postal_code or ''} {data.seller.city or ''}".strip(), footer_value))
    if data.seller.country:
        sell_col.append(Paragraph(data.seller.country, footer_value))
    
    # Column 2: Contact
    contact_col = ft(t["phone"], data.seller.phone or "—")
    contact_col = ft(t["email"], data.seller.email or "—")
    
    # Column 3: Bank
    bank_col = []
    if data.payment.bank_name:
        bank_col += ft(t["bank"], data.payment.bank_name)
    if data.payment.iban:
        bank_col += ft(t["iban"], data.payment.iban)
    if data.payment.bic:
        bank_col += ft(t["bic"], data.payment.bic)
    bank_col = []
    if data.payment.bank_name:
        bank_col.append(Paragraph(f"<b>{t['bank']}</b>", footer_label))
        bank_col.append(Paragraph(data.payment.bank_name, footer_value))
    if data.payment.iban:
        bank_col.append(Paragraph(f"<b>{t['iban']}</b>", footer_label))
        bank_col.append(Paragraph(data.payment.iban, 
                                ParagraphStyle("IBAN", fontSize=9, fontName="Helvetica-Bold",
                                               textColor=DARK, leading=12)))
    if data.payment.bic:
        bank_col.append(Paragraph(f"<b>{t['bic']}</b>", footer_label))
        bank_col.append(Paragraph(data.payment.bic, footer_value))
    
    # If no bank info, show a placeholder
    if not bank_col:
        bank_col = [Paragraph("—", footer_value)]
    
    # Build footer table
    footer_data = [[sell_col, contact_col, bank_col]]
    footer_table = Table(footer_data, colWidths=[60*mm, 50*mm, 70*mm])
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (1, 0), 5*mm),
        ("RIGHTPADDING", (1, 0), (2, 0), 5*mm),
    ]))
    elements.append(footer_table)
    
    # Bottom line
    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Paragraph(
        f"A4  ·  {data.seller.name or ''}  ·  {t['footer_1']}",
        ParagraphStyle("Final", fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
    ))
    
    doc.build(elements)


# Alias for compatibility
class PDFGenerator:
    def __init__(self, data: InvoiceData):
        self.data = data
    
    def save(self, filepath: str):
        generate_invoice_pdf(self.data, filepath, lang="et")
    
    def generate(self) -> bytes:
        from io import BytesIO
        buf = BytesIO()
        generate_invoice_pdf(self.data, buf, lang="et")
        return buf.getvalue()
