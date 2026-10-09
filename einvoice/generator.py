"""
UBL 2.1 invoice XML generation. Receiver-specific business rules require separate validation.
"""
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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
    """Generate UBL 2.1 invoice XML with consistent monetary amounts."""

    NS_INV = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    CENT = Decimal("0.01")
    UNITS = {"pcs": "C62", "h": "HUR", "km": "KMT", "kg": "KGM", "m": "MTR", "l": "LTR"}

    def __init__(self, data: InvoiceData):
        self.data = data

    @staticmethod
    def _number(value) -> Decimal:
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invoice amounts must be numeric.") from None
        if not number.is_finite():
            raise ValueError("Invoice amounts must be finite.")
        return number

    @classmethod
    def _amounts(cls, lines: list[InvoiceLine]):
        subtotal = Decimal(0)
        taxable = {}
        for line in lines:
            quantity = cls._number(line.quantity)
            price = cls._number(line.unit_price)
            rate = cls._number(line.vat_rate)
            if price < 0 or rate < 0 or rate > 1:
                raise ValueError("Unit prices cannot be negative; VAT rates must be fractions within 0..1.")
            net = (quantity * price).quantize(cls.CENT, rounding=ROUND_HALF_UP)
            subtotal += net
            taxable[rate] = taxable.get(rate, Decimal(0)) + net
        taxes = {rate: (net * rate).quantize(cls.CENT, rounding=ROUND_HALF_UP) for rate, net in taxable.items()}
        return subtotal, taxable, taxes

    def _cbc(self, parent, name, value, **attributes):
        element = ET.SubElement(parent, f"{{{self.NS_CBC}}}{name}", attributes)
        element.text = str(value)
        return element

    def _cac(self, parent, name):
        return ET.SubElement(parent, f"{{{self.NS_CAC}}}{name}")

    def _money(self, parent, name, value):
        return self._cbc(parent, name, format(value, ".2f"), currencyID=self.data.currency)

    def _category(self, parent, name, rate):
        category = self._cac(parent, name)
        self._cbc(category, "ID", "S" if rate > 0 else "Z")
        self._cbc(category, "Percent", format(rate * 100, "f"))
        self._cbc(self._cac(category, "TaxScheme"), "ID", "VAT")

    def generate(self) -> str:
        if not self.data.lines:
            raise ValueError("An invoice requires at least one line.")
        if not self.data.invoice_number or not self.data.seller.name or not self.data.buyer.name:
            raise ValueError("Invoice number, seller name and buyer name are required.")
        ET.register_namespace("", self.NS_INV)
        ET.register_namespace("cbc", self.NS_CBC)
        ET.register_namespace("cac", self.NS_CAC)
        root = ET.Element(f"{{{self.NS_INV}}}Invoice")
        self._cbc(root, "UBLVersionID", "2.1")
        self._cbc(root, "ID", self.data.invoice_number)
        self._cbc(root, "IssueDate", self.data.invoice_date.isoformat())
        if self.data.due_date:
            self._cbc(root, "DueDate", self.data.due_date.isoformat())
        self._cbc(root, "InvoiceTypeCode", "380")
        if self.data.notes:
            self._cbc(root, "Note", self.data.notes)
        self._cbc(root, "DocumentCurrencyCode", self.data.currency)
        if self.data.order_reference:
            self._cbc(self._cac(root, "OrderReference"), "ID", self.data.order_reference)
        for name, details in [("AccountingSupplierParty", self.data.seller), ("AccountingCustomerParty", self.data.buyer)]:
            party = self._cac(self._cac(root, name), "Party")
            self._cbc(self._cac(party, "PartyName"), "Name", details.name)
            if details.address or details.city or details.postal_code or details.country:
                address = self._cac(party, "PostalAddress")
                for field, value in [("StreetName", details.address), ("CityName", details.city), ("PostalZone", details.postal_code)]:
                    if value:
                        self._cbc(address, field, value)
                if details.country:
                    self._cbc(self._cac(address, "Country"), "IdentificationCode", details.country)
            if details.vat_number:
                tax = self._cac(party, "PartyTaxScheme")
                self._cbc(tax, "CompanyID", details.vat_number)
                self._cbc(self._cac(tax, "TaxScheme"), "ID", "VAT")
            legal = self._cac(party, "PartyLegalEntity")
            self._cbc(legal, "RegistrationName", details.name)
            if details.registry_code:
                self._cbc(legal, "CompanyID", details.registry_code)
            if details.phone or details.email:
                contact = self._cac(party, "Contact")
                if details.phone:
                    self._cbc(contact, "Telephone", details.phone)
                if details.email:
                    self._cbc(contact, "ElectronicMail", details.email)
        payment = self._cac(root, "PaymentMeans")
        self._cbc(payment, "PaymentMeansCode", "31")
        if self.data.payment.payer_reference:
            self._cbc(payment, "PaymentID", self.data.payment.payer_reference)
        if self.data.payment.iban:
            account = self._cac(payment, "PayeeFinancialAccount")
            self._cbc(account, "ID", self.data.payment.iban)
            if self.data.payment.bank_name:
                self._cbc(account, "Name", self.data.payment.bank_name)
            if self.data.payment.bic:
                self._cbc(self._cac(account, "FinancialInstitutionBranch"), "ID", self.data.payment.bic)
        if self.data.payment.due_days > 0:
            self._cbc(self._cac(root, "PaymentTerms"), "Note", f"Payment due within {self.data.payment.due_days} days")
        subtotal, taxable, taxes = self._amounts(self.data.lines)
        total_tax = sum(taxes.values(), Decimal(0))
        tax = self._cac(root, "TaxTotal")
        self._money(tax, "TaxAmount", total_tax)
        for rate, net in sorted(taxable.items()):
            breakdown = self._cac(tax, "TaxSubtotal")
            self._money(breakdown, "TaxableAmount", net)
            self._money(breakdown, "TaxAmount", taxes[rate])
            self._category(breakdown, "TaxCategory", rate)
        monetary = self._cac(root, "LegalMonetaryTotal")
        self._money(monetary, "LineExtensionAmount", subtotal)
        self._money(monetary, "TaxExclusiveAmount", subtotal)
        self._money(monetary, "TaxInclusiveAmount", subtotal + total_tax)
        self._money(monetary, "PayableAmount", subtotal + total_tax)
        for index, line in enumerate(self.data.lines, 1):
            element = self._cac(root, "InvoiceLine")
            self._cbc(element, "ID", index)
            if line.line_note:
                self._cbc(element, "Note", line.line_note)
            self._cbc(element, "InvoicedQuantity", format(self._number(line.quantity), "f"), unitCode=self.UNITS.get(line.unit, line.unit))
            self._money(element, "LineExtensionAmount", (self._number(line.quantity) * self._number(line.unit_price)).quantize(self.CENT, rounding=ROUND_HALF_UP))
            item = self._cac(element, "Item")
            self._cbc(item, "Description", line.description)
            self._cbc(item, "Name", line.description)
            self._category(item, "ClassifiedTaxCategory", self._number(line.vat_rate))
            price = self._cac(element, "Price")
            self._cbc(price, "PriceAmount", format(self._number(line.unit_price), "f"), currencyID=self.data.currency)
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def save(self, filepath: str):
        xml = self.generate()
        with open(filepath, "w", encoding="utf-8") as output:
            output.write(xml)

    @classmethod
    def calculate_totals(cls, lines: list[InvoiceLine]) -> dict:
        subtotal, _taxable, taxes = cls._amounts(lines)
        total_vat = sum(taxes.values(), Decimal(0))
        return {"subtotal": float(subtotal), "vat_amounts": {float(rate): float(amount) for rate, amount in taxes.items()},
                "total_vat": float(total_vat), "total": float(subtotal + total_vat)}
