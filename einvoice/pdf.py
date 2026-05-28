"""
PDF invoice generator
Creates printable invoice documents from InvoiceData
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import date
from typing import Optional

from .generator import InvoiceData, InvoiceLine


class PDFGenerator:
    """
    Generates printable PDF invoices with professional layout
    """
    
    # Colors
    PRIMARY = HexColor("#1a365d")      # Dark blue
    SECONDARY = HexColor("#2c5282")    # Medium blue
    ACCENT = HexColor("#3182ce")       # Light blue
    LIGHT_BG = HexColor("#f7fafc")    # Light gray background
    TEXT = HexColor("#1a202c")         # Dark text
    TEXT_LIGHT = HexColor("#718096")   # Gray text
    BORDER = HexColor("#e2e8f0")      # Light border
    
    def __init__(self, data: InvoiceData):
        self.data = data
    
    def generate(self) -> bytes:
        """Generate PDF as bytes"""
        from io import BytesIO
        
        buffer = BytesIO()
        self._build_pdf(buffer)
        return buffer.getvalue()
    
    def save(self, filepath: str):
        """Save PDF to file"""
        with open(filepath, "wb") as f:
            f.write(self.generate())
    
    def _build_pdf(self, buffer):
        """Build the PDF document"""
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )
        
        # Build content
        elements = []
        
        # Header (company info + invoice title)
        elements.extend(self._build_header())
        
        # Parties (seller + buyer)
        elements.extend(self._build_parties())
        
        # Invoice details (number, date, etc)
        elements.extend(self._build_invoice_details())
        
        # Table with line items
        elements.extend(self._build_items_table())
        
        # Totals
        elements.extend(self._build_totals())
        
        # Payment info
        elements.extend(self._build_payment_info())
        
        # Notes
        if self.data.notes:
            elements.extend(self._build_notes())
        
        # Footer
        elements.extend(self._build_footer())
        
        doc.build(elements)
    
    def _build_header(self):
        """Build header with company name and title"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Title style
        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=self.PRIMARY,
            spaceAfter=5*mm,
            alignment=TA_RIGHT,
        )
        
        # Company name style
        company_style = ParagraphStyle(
            "CompanyName",
            parent=styles["Normal"],
            fontSize=14,
            textColor=self.SECONDARY,
            spaceAfter=2*mm,
            alignment=TA_RIGHT,
        )
        
        # Invoice text
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Paragraph(self.data.seller.name.upper(), company_style))
        
        if self.data.seller.address:
            addr_style = ParagraphStyle("Addr", parent=styles["Normal"], fontSize=9,
                                       textColor=self.TEXT_LIGHT, alignment=TA_RIGHT)
            elements.append(Paragraph(self.data.seller.address, addr_style))
            if self.data.seller.city:
                elements.append(Paragraph(
                    f"{self.data.seller.postal_code or ''} {self.data.seller.city}".strip(),
                    addr_style
                ))
        
        elements.append(Spacer(1, 8*mm))
        return elements
    
    def _build_parties(self):
        """Build seller and buyer info boxes"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Create two-column layout
        left_content = []
        right_content = []
        
        # Seller info
        left_content.append(Paragraph("<b>SELLER</b>", ParagraphStyle(
            "PartyLabel", fontSize=8, textColor=self.TEXT_LIGHT, spaceAfter=2*mm
        )))
        left_content.append(Paragraph(self.data.seller.name, ParagraphStyle(
            "PartyName", fontSize=11, textColor=self.PRIMARY, spaceAfter=1*mm
        )))
        if self.data.seller.registry_code:
            left_content.append(Paragraph(f"Registry code: {self.data.seller.registry_code}", 
                                         ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.seller.vat_number:
            left_content.append(Paragraph(f"VAT: {self.data.seller.vat_number}",
                                         ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.seller.address:
            left_content.append(Paragraph(self.data.seller.address,
                                         ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.seller.city:
            left_content.append(Paragraph(
                f"{self.data.seller.postal_code or ''} {self.data.seller.city}".strip(),
                ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)
            ))
        if self.data.seller.email:
            left_content.append(Paragraph(self.data.seller.email,
                                         ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        
        # Buyer info
        right_content.append(Paragraph("<b>BUYER</b>", ParagraphStyle(
            "PartyLabel", fontSize=8, textColor=self.TEXT_LIGHT, spaceAfter=2*mm
        )))
        right_content.append(Paragraph(self.data.buyer.name, ParagraphStyle(
            "PartyName", fontSize=11, textColor=self.PRIMARY, spaceAfter=1*mm
        )))
        if self.data.buyer.registry_code:
            right_content.append(Paragraph(f"Registry code: {self.data.buyer.registry_code}",
                                           ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.buyer.vat_number:
            right_content.append(Paragraph(f"VAT: {self.data.buyer.vat_number}",
                                           ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.buyer.address:
            right_content.append(Paragraph(self.data.buyer.address,
                                         ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)))
        if self.data.buyer.city:
            right_content.append(Paragraph(
                f"{self.data.buyer.postal_code or ''} {self.data.buyer.city}".strip(),
                ParagraphStyle("PartyDetail", fontSize=8, textColor=self.TEXT_LIGHT)
            ))
        
        # Put in table
        data = [[left_content, right_content]]
        table = Table(data, colWidths=[90*mm, 90*mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _build_invoice_details(self):
        """Build invoice number, date, due date row"""
        styles = getSampleStyleSheet()
        elements = []
        
        detail_style = ParagraphStyle("Detail", fontSize=9, textColor=self.TEXT)
        label_style = ParagraphStyle("Label", fontSize=8, textColor=self.TEXT_LIGHT)
        
        # Create a 3-column layout
        details_data = [
            [
                Paragraph("<b>Invoice No.</b><br/>" + self.data.invoice_number, detail_style),
                Paragraph("<b>Date</b><br/>" + self.data.invoice_date.strftime("%d.%m.%Y"), detail_style),
                Paragraph("<b>Due Date</b><br/>" + 
                         (self.data.due_date.strftime("%d.%m.%Y") if self.data.due_date else "—"), 
                         detail_style),
            ]
        ]
        
        table = Table(details_data, colWidths=[60*mm, 60*mm, 60*mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3*mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3*mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
            ("BACKGROUND", (0, 0), (-1, -1), self.LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, self.BORDER),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _build_items_table(self):
        """Build the line items table"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Table header
        header_style = ParagraphStyle("Header", fontSize=8, textColor=white, alignment=TA_LEFT)
        header_data = [
            [
                Paragraph("<b>#</b>", header_style),
                Paragraph("<b>Description</b>", header_style),
                Paragraph("<b>Qty</b>", header_style),
                Paragraph("<b>Unit</b>", header_style),
                Paragraph("<b>Price</b>", header_style),
                Paragraph("<b>VAT</b>", header_style),
                Paragraph("<b>Total</b>", header_style),
            ]
        ]
        
        # Table rows
        row_data = header_data.copy()
        for i, line in enumerate(self.data.lines, 1):
            row_style = ParagraphStyle("Row", fontSize=8, textColor=self.TEXT)
            
            # unit_price is stored as net (excl VAT) after conversion from gross input
            net_unit = line.unit_price
            vat_rate = line.vat_rate
            vat_text = f"{vat_rate * 100:.0f}%" if vat_rate > 0 else "0%"
            total_gross_for_line = net_unit * (1 + vat_rate) * line.quantity
            
            row = [
                Paragraph(str(i), row_style),
                Paragraph(line.description, row_style),
                Paragraph(f"{line.quantity:.2f}", row_style),
                Paragraph(line.unit, row_style),
                Paragraph(f"€ {net_unit:.2f}", row_style),
                Paragraph(vat_text, row_style),
                Paragraph(f"€ {total_gross_for_line:.2f}", row_style),
            ]
            row_data.append(row)
        
        # Create table
        col_widths = [10*mm, 80*mm, 20*mm, 20*mm, 30*mm, 15*mm, 30*mm]
        table = Table(row_data, colWidths=col_widths)
        
        # Style
        style_commands = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 3*mm),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 3*mm),
            # Body
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 2*mm),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 2*mm),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # Alignment
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("ALIGN", (5, 0), (5, -1), "RIGHT"),
            ("ALIGN", (6, 0), (6, -1), "RIGHT"),
            # Borders
            ("GRID", (0, 0), (-1, -1), 0.5, self.BORDER),
            ("BOX", (0, 0), (-1, -1), 1, self.PRIMARY),
            # Alternating rows
        ]
        
        # Alternating row colors
        for i in range(1, len(row_data)):
            if i % 2 == 0:
                style_commands.append(("BACKGROUND", (0, i), (-1, i), self.LIGHT_BG))
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _build_totals(self):
        """Build totals section"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Calculate
        subtotal = sum(line.quantity * line.unit_price for line in self.data.lines)
        vat_amounts = {}
        for line in self.data.lines:
            if line.vat_rate not in vat_amounts:
                vat_amounts[line.vat_rate] = 0.0
            vat_amounts[line.vat_rate] += line.quantity * line.unit_price * line.vat_rate
        total_vat = sum(vat_amounts.values())
        total = subtotal + total_vat
        
        # Subtotal
        sub_label = Paragraph("<b>Subtotal (excl. VAT)</b>", ParagraphStyle(
            "SubtotalLabel", fontSize=9, textColor=self.TEXT, alignment=TA_RIGHT
        ))
        sub_value = Paragraph(f"€ {subtotal:.2f}", ParagraphStyle(
            "SubtotalValue", fontSize=9, textColor=self.TEXT, alignment=TA_RIGHT
        ))
        
        # VAT breakdown
        vat_rows = []
        for rate, amount in sorted(vat_amounts.items()):
            vat_label = f"VAT {rate * 100:.0f}%"
            vat_value = f"€ {amount:.2f}"
            vat_rows.append([Paragraph(vat_label, ParagraphStyle(
                "VATLabel", fontSize=8, textColor=self.TEXT_LIGHT, alignment=TA_RIGHT
            )),
            Paragraph(vat_value, ParagraphStyle(
                "VATValue", fontSize=8, textColor=self.TEXT_LIGHT, alignment=TA_RIGHT
            ))])
        
        # Total
        total_label = Paragraph("<b>TOTAL</b>", ParagraphStyle(
            "TotalLabel", fontSize=12, textColor=self.PRIMARY, alignment=TA_RIGHT
        ))
        total_value = Paragraph(f"€ {total:.2f}", ParagraphStyle(
            "TotalValue", fontSize=12, textColor=self.PRIMARY, alignment=TA_RIGHT
        ))
        
        # Build table
        total_data = [[sub_label, sub_value]]
        for vr in vat_rows:
            total_data.append(vr)
        total_data.append([Spacer(1, 2*mm), Spacer(1, 2*mm)])  # Empty row
        total_data.append([total_label, total_value])
        
        table = Table(total_data, colWidths=[120*mm, 60*mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1*mm),
            ("LINEABOVE", (0, -1), (-1, -1), 1, self.PRIMARY),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _build_payment_info(self):
        """Build payment details section"""
        styles = getSampleStyleSheet()
        elements = []
        
        info_style = ParagraphStyle("Info", fontSize=9, textColor=self.TEXT)
        label_style = ParagraphStyle("Label", fontSize=8, textColor=self.TEXT_LIGHT)
        
        # Payment details table
        payment_data = [
            [
                Paragraph("Payment to:", label_style),
                Paragraph(self.data.payment.iban, info_style),
                Paragraph("BIC:", label_style),
                Paragraph(self.data.payment.bic, info_style),
            ]
        ]
        
        table = Table(payment_data, colWidths=[30*mm, 60*mm, 15*mm, 75*mm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2*mm),
            ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1*mm),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _build_notes(self):
        """Build notes section"""
        styles = getSampleStyleSheet()
        elements = []
        
        note_style = ParagraphStyle("Note", fontSize=8, textColor=self.TEXT_LIGHT)
        elements.append(Paragraph(f"<b>Notes:</b> {self.data.notes}", note_style))
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _build_footer(self):
        """Build footer"""
        styles = getSampleStyleSheet()
        elements = []
        
        footer_style = ParagraphStyle("Footer", fontSize=7, textColor=self.TEXT_LIGHT,
                                      alignment=TA_CENTER)
        
        # Separator
        elements.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER, spaceAfter=3*mm))
        
        # Generated by line
        elements.append(Paragraph(
            f"Generated by ee-invoice-generator | {self.data.seller.name}",
            footer_style
        ))
        
        return elements