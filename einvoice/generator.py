"""
Estonian e-invoice XML generator (EN 16931)
Generates machine-readable XML invoices conforming to Estonian standard
"""
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PartyDetails:
    """Seller or Buyer details"""
    registry_code: str          # Estonian registry code (8 digits)
    name: str                   # Company name
    vat_number: Optional[str] = None  # KMKR (VAT) number (EE123456789)
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "EE"
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class InvoiceLine:
    """Single line item on invoice"""
    description: str
    quantity: float = 1.0
    unit: str = "pcs"           # Unit of measure (pcs, h, km, etc.)
    unit_price: float = 0.0     # Price per unit (excl VAT)
    vat_rate: float = 0.0       # VAT rate (0, 0.2, 0.22)
    line_note: Optional[str] = None


@dataclass
class PaymentDetails:
    """Payment information"""
    iban: str
    bic: str                    # SWIFT code
    bank_name: Optional[str] = None
    payer_reference: Optional[str] = None  # Invoice number
    due_days: int = 0           # Days until due (0 = immediate)


@dataclass
class InvoiceData:
    """Complete invoice data"""
    # Seller (your company)
    seller: PartyDetails
    
    # Buyer (customer)
    buyer: PartyDetails
    
    # Invoice metadata
    invoice_number: str
    invoice_date: date
    
    # Payment
    payment: PaymentDetails
    
    # Lines
    lines: list[InvoiceLine] = field(default_factory=list)
    
    # Optional
    due_date: Optional[date] = None
    order_reference: Optional[str] = None
    notes: Optional[str] = None
    currency: str = "EUR"


class InvoiceGenerator:
    """
    Generates Estonian e-invoice XML files conforming to EN 16931
    """
    
    # Estonian e-invoice namespace
    NS = "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"
    NS_INV = "urn:cesnet:invoice:1.0"
    NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    NS_QUAL = "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2"
    
    def __init__(self, data: InvoiceData):
        self.data = data
    
    def generate(self) -> str:
        """Generate XML string"""
        # Build invoice
        root = self._build_invoice()
        
        # Return as string
        return ET.tostring(root, encoding="unicode", xml_declaration=True)
    
    def save(self, filepath: str):
        """Save XML to file"""
        xml_str = self.generate()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_str)
    
    def _build_invoice(self) -> ET.Element:
        """Build the invoice XML tree"""
        # Root element
        Invoice = ET.Element("Invoice", {
            "xmlns": self.NS_INV,
            "xmlns:cbc": self.NS_CBC,
            "xmlns:cac": self.NS_CAC,
            "xmlns:qdt": self.NS_QUAL,
        })
        
        # Header block
        self._add_header(Invoice)
        
        # Seller/Buyer
        self._add_parties(Invoice)
        
        # Payment
        self._add_payment(Invoice)
        
        # Lines
        self._add_lines(Invoice)
        
        # Totals
        self._add_totals(Invoice)
        
        return Invoice
    
    def _add_header(self, root: ET.Element):
        """Add invoice header elements"""
        # ID
        id_elem = ET.SubElement(root, f"{{{self.NS_CBC}}}ID")
        id_elem.text = self.data.invoice_number
        
        # Issue date
        issue_date = ET.SubElement(root, f"{{{self.NS_CBC}}}IssueDate")
        issue_date.text = self.data.invoice_date.isoformat()
        
        # Due date if specified
        if self.data.due_date:
            due = ET.SubElement(root, f"{{{self.NS_CBC}}}DueDate")
            due.text = self.data.due_date.isoformat()
        
        # Invoice type code (380 = Commercial Invoice)
        type_code = ET.SubElement(root, f"{{{self.NS_CBC}}}InvoiceTypeCode")
        type_code.text = "380"
        type_code.set("listID", "UN/ECE 1001")
        
        # Notes
        if self.data.notes:
            note = ET.SubElement(root, f"{{{self.NS_CBC}}}Note")
            note.text = self.data.notes
        
        # Currency
        currency = ET.SubElement(root, f"{{{self.NS_CBC}}}DocumentCurrencyCode")
        currency.text = self.data.currency
    
    def _add_parties(self, root: ET.Element):
        """Add seller and buyer parties"""
        # Accounting supplier (seller)
        supplier = ET.SubElement(root, f"{{{self.NS_CAC}}}AccountingSupplierParty")
        self._add_party(supplier, self.data.seller, is_seller=True)
        
        # Accounting customer (buyer)
        customer = ET.SubElement(root, f"{{{self.NS_CAC}}}AccountingCustomerParty")
        self._add_party(customer, self.data.buyer, is_seller=False)
    
    def _add_party(self, parent: ET.Element, party: PartyDetails, is_seller: bool):
        """Add a single party block"""
        # Party identification
        party_id = ET.SubElement(parent, f"{{{self.NS_CAC}}}Party")
        
        # Registry code
        if party.registry_code:
            identification = ET.SubElement(party_id, f"{{{self.NS_CAC}}}EndpointID")
            identification.set("schemeID", "YY")
            identification.text = party.registry_code
        
        # Company name
        name_elem = ET.SubElement(party_id, f"{{{self.NS_CAC}}}PartyName")
        name = ET.SubElement(name_elem, f"{{{self.NS_CBC}}}Name")
        name.text = party.name
        
        # Address
        if party.address or party.city:
            postal_addr = ET.SubElement(party_id, f"{{{self.NS_CAC}}}PostalAddress")
            
            if party.address:
                street = ET.SubElement(postal_addr, f"{{{self.NS_CBC}}}StreetName")
                street.text = party.address
            
            if party.city:
                city = ET.SubElement(postal_addr, f"{{{self.NS_CBC}}}CityName")
                city.text = party.city
            
            if party.postal_code:
                postal = ET.SubElement(postal_addr, f"{{{self.NS_CBC}}}PostalZone")
                postal.text = party.postal_code
            
            if party.country:
                country = ET.SubElement(postal_addr, f"{{{self.NS_CAC}}}Country")
                country_code = ET.SubElement(country, f"{{{self.NS_CBC}}}IdentificationCode")
                country_code.text = party.country
        
        # Contact (optional)
        if party.email or party.phone:
            contact = ET.SubElement(party_id, f"{{{self.NS_CAC}}}Contact")
            if party.email:
                email = ET.SubElement(contact, f"{{{self.NS_CBC}}}ElectronicMail")
                email.text = party.email
            if party.phone:
                phone = ET.SubElement(contact, f"{{{self.NS_CBC}}}Telephone")
                phone.text = party.phone
    
    def _add_payment(self, root: ET.Element):
        """Add payment terms and method"""
        # Payment means
        payment_means = ET.SubElement(root, f"{{{self.NS_CAC}}}PaymentMeans")
        
        # Payment means code (31 = credit transfer)
        means_code = ET.SubElement(payment_means, f"{{{self.NS_CBC}}}PaymentMeansCode")
        means_code.text = "31"
        
        # Payee financial account
        if self.data.payment.iban:
            payee_fin = ET.SubElement(payment_means, f"{{{self.NS_CAC}}}PayeeFinancialAccount")
            iban_id = ET.SubElement(payee_fin, f"{{{self.NS_CBC}}}ID")
            iban_id.text = self.data.payment.iban
            iban_id.set("schemeID", "IBAN")
            
            if self.data.payment.bic:
                bic_fin = ET.SubElement(payee_fin, f"{{{self.NS_CAC}}}FinancialInstitutionBranch")
                bic_id = ET.SubElement(bic_fin, f"{{{self.NS_CBC}}}ID")
                bic_id.text = self.data.payment.bic
        
        # Payment terms
        if self.data.payment.due_days > 0:
            terms = ET.SubElement(root, f"{{{self.NS_CAC}}}PaymentTerms")
            note = ET.SubElement(terms, f"{{{self.NS_CBC}}}Note")
            note.text = f"Payment due within {self.data.payment.due_days} days"
    
    def _add_lines(self, root: ET.Element):
        """Add invoice line items"""
        for i, line in enumerate(self.data.lines, 1):
            line_elem = ET.SubElement(root, f"{{{self.NS_CAC}}}InvoiceLine")
            
            # Line ID
            line_id = ET.SubElement(line_elem, f"{{{self.NS_CBC}}}ID")
            line_id.text = str(i)
            
            # Invoiced quantity
            qty_elem = ET.SubElement(line_elem, f"{{{self.NS_CBC}}}InvoicedQuantity")
            qty_elem.set("unitCode", line.unit)
            qty_elem.text = str(line.quantity)
            
            # Line total (without VAT)
            line_ext = ET.SubElement(line_elem, f"{{{self.NS_CBC}}}LineExtensionAmount")
            line_ext.set("currencyID", self.data.currency)
            line_ext.text = f"{line.quantity * line.unit_price:.2f}"
            
            # Item details
            item = ET.SubElement(line_elem, f"{{{self.NS_CAC}}}Item")
            
            # Description
            desc = ET.SubElement(item, f"{{{self.NS_CBC}}}Description")
            desc.text = line.description
            
            # Additional text if any
            if line.line_note:
                obj_note = ET.SubElement(item, f"{{{self.NS_CBC}}}AdditionalInformation")
                obj_note.text = line.line_note
            
            # Price details
            price = ET.SubElement(line_elem, f"{{{self.NS_CAC}}}Price")
            unit_price = ET.SubElement(price, f"{{{self.NS_CBC}}}PriceAmount")
            unit_price.set("currencyID", self.data.currency)
            unit_price.text = f"{line.unit_price:.2f}"
    
    def _add_totals(self, root: ET.Element):
        """Add invoice totals and VAT breakdown"""
        # Calculate totals
        subtotal = sum(line.quantity * line.unit_price for line in self.data.lines)
        vat_amounts = {}
        
        for line in self.data.lines:
            if line.vat_rate not in vat_amounts:
                vat_amounts[line.vat_rate] = 0.0
            vat_amounts[line.vat_rate] += line.quantity * line.unit_price * line.vat_rate
        
        total_vat = sum(vat_amounts.values())
        total = subtotal + total_vat
        
        # Legal monetary total
        legal_totals = ET.SubElement(root, f"{{{self.NS_CAC}}}LegalMonetaryTotal")
        
        # Subtotal (before VAT)
        sub_elem = ET.SubElement(legal_totals, f"{{{self.NS_CBC}}}TaxExclusiveAmount")
        sub_elem.set("currencyID", self.data.currency)
        sub_elem.text = f"{subtotal:.2f}"
        
        # Tax total
        tax_total = ET.SubElement(root, f"{{{self.NS_CAC}}}TaxTotal")
        tax_amount = ET.SubElement(tax_total, f"{{{self.NS_CBC}}}TaxAmount")
        tax_amount.set("currencyID", self.data.currency)
        tax_amount.text = f"{total_vat:.2f}"
        
        # Tax subtotals by rate
        for rate, amount in sorted(vat_amounts.items()):
            subtotal_elem = ET.SubElement(tax_total, f"{{{self.NS_CBC}}}TaxSubtotal")
            
            taxable = ET.SubElement(subtotal_elem, f"{{{self.NS_CBC}}}TaxableAmount")
            taxable.set("currencyID", self.data.currency)
            taxable.text = f"{amount / (rate if rate > 0 else 1):.2f}"
            
            tax_amt = ET.SubElement(subtotal_elem, f"{{{self.NS_CBC}}}TaxAmount")
            tax_amt.set("currencyID", self.data.currency)
            tax_amt.text = f"{amount:.2f}"
            
            # Tax category
            cat = ET.SubElement(subtotal_elem, f"{{{self.NS_CAC}}}TaxCategory")
            cat_id = ET.SubElement(cat, f"{{{self.NS_CBC}}}ID")
            cat_id.text = "S" if rate == 0.2 else "Z" if rate == 0 else "E"
            
            percent = ET.SubElement(cat, f"{{{self.NS_CBC}}}Percent")
            percent.text = f"{rate * 100:.0f}"
        
        # Grand total
        grand_elem = ET.SubElement(legal_totals, f"{{{self.NS_CBC}}}TaxInclusiveAmount")
        grand_elem.set("currencyID", self.data.currency)
        grand_elem.text = f"{total:.2f}"
    
    @staticmethod
    def calculate_totals(lines: list[InvoiceLine]) -> dict:
        """Helper to calculate totals from lines"""
        subtotal = sum(line.quantity * line.unit_price for line in lines)
        vat_amounts = {}
        
        for line in lines:
            if line.vat_rate not in vat_amounts:
                vat_amounts[line.vat_rate] = 0.0
            vat_amounts[line.vat_rate] += line.quantity * line.unit_price * line.vat_rate
        
        total_vat = sum(vat_amounts.values())
        total = subtotal + total_vat
        
        return {
            "subtotal": subtotal,
            "vat_amounts": vat_amounts,
            "total_vat": total_vat,
            "total": total,
        }