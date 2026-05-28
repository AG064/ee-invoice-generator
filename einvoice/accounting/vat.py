"""
VAT (Käibemaks) calculator for Estonian businesses
Handles VAT rates, declarations, and transactions
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional
from enum import Enum


class VATRate(Enum):
    """Standard Estonian VAT rates"""
    STANDARD = 0.20    # 20% - standard rate
    REDUCED = 0.09     # 9% - reduced rate (books, medications, etc.)
    ZERO = 0.0         # 0% - zero rate (some exports)
    EXEMPT = -1        # Exempt (no VAT)


@dataclass
class VATTransaction:
    """Single VAT-relevant transaction"""
    date: date
    invoice_number: str
    description: str
    amount_excl_vat: float
    vat_rate: VATRate
    is_output_vat: bool  # True = we charged VAT (sales), False = we paid VAT (purchases)
    counterparty: str = ""
    vat_amount: float = 0.0
    
    def __post_init__(self):
        if self.vat_amount == 0.0 and self.vat_rate.value > 0:
            self.vat_amount = self.amount_excl_vat * self.vat_rate.value


@dataclass
class VATReport:
    """VAT declaration data for a period"""
    period_start: date
    period_end: date
    total_sales_excl_vat: float = 0.0
    total_sales_vat: float = 0.0
    total_purchases_excl_vat: float = 0.0
    total_purchases_vat: float = 0.0
    adjustments: float = 0.0  # Corrections/adjustments
    
    @property
    def vat_due(self) -> float:
        """VAT to pay (positive) or reclaim (negative)"""
        return self.total_sales_vat - self.total_purchases_vat - self.adjustments
    
    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_sales_excl_vat": self.total_sales_excl_vat,
            "total_sales_vat": self.total_sales_vat,
            "total_purchases_excl_vat": self.total_purchases_excl_vat,
            "total_purchases_vat": self.total_purchases_vat,
            "adjustments": self.adjustments,
            "vat_due": self.vat_due,
        }


class VATCalculator:
    """
    VAT calculator and tracker
    Estonia: Standard 20%, Reduced 9%, Zero 0%, Exempt
    """
    
    def __init__(self):
        self.transactions: list[VATTransaction] = []
    
    def add_sale(self, date: date, invoice_number: str, amount_excl_vat: float,
                 vat_rate: VATRate = VATRate.STANDARD, counterparty: str = "") -> VATTransaction:
        """Record a sale (output VAT)"""
        tx = VATTransaction(
            date=date,
            invoice_number=invoice_number,
            description=f"Müük {invoice_number}",
            amount_excl_vat=amount_excl_vat,
            vat_rate=vat_rate,
            is_output_vat=True,
            counterparty=counterparty,
        )
        self.transactions.append(tx)
        return tx
    
    def add_purchase(self, date: date, invoice_number: str, amount_excl_vat: float,
                    vat_rate: VATRate = VATRate.STANDARD, counterparty: str = "") -> VATTransaction:
        """Record a purchase (input VAT - reclaimable)"""
        tx = VATTransaction(
            date=date,
            invoice_number=invoice_number,
            description=f"Ost {invoice_number}",
            amount_excl_vat=amount_excl_vat,
            vat_rate=vat_rate,
            is_output_vat=False,
            counterparty=counterparty,
        )
        self.transactions.append(tx)
        return tx
    
    def calculate_period(self, start_date: date, end_date: date) -> VATReport:
        """Calculate VAT for a period"""
        report = VATReport(period_start=start_date, period_end=end_date)
        
        for tx in self.transactions:
            if start_date <= tx.date <= end_date:
                if tx.is_output_vat:
                    report.total_sales_excl_vat += tx.amount_excl_vat
                    report.total_sales_vat += tx.vat_amount
                else:
                    report.total_purchases_excl_vat += tx.amount_excl_vat
                    report.total_purchases_vat += tx.vat_amount
        
        return report
    
    def vat_due_on_date(self, as_of_date: date) -> float:
        """Calculate cumulative VAT due up to a date"""
        sales_vat = sum(
            tx.vat_amount for tx in self.transactions
            if tx.is_output_vat and tx.date <= as_of_date
        )
        purchases_vat = sum(
            tx.vat_amount for tx in self.transactions
            if not tx.is_output_vat and tx.date <= as_of_date
        )
        return sales_vat - purchases_vat
    
    def get_outstanding_vat_returns(self) -> list[VATReport]:
        """Get VAT reports for quarters (Estonia pays quarterly)"""
        quarters = [
            (date(2026, 1, 1), date(2026, 3, 31)),
            (date(2026, 4, 1), date(2026, 6, 30)),
            (date(2026, 7, 1), date(2026, 9, 30)),
            (date(2026, 10, 1), date(2026, 12, 31)),
        ]
        return [self.calculate_period(start, end) for start, end in quarters]


def calculate_vat(amount_excl_vat: float, vat_rate: VATRate) -> tuple[float, float]:
    """Helper: calculate VAT amount and total from exclusive amount"""
    vat_amount = amount_excl_vat * vat_rate.value
    return vat_amount, amount_excl_vat + vat_amount


def calculate_vat_from_total(amount_incl_vat: float, vat_rate: VATRate) -> tuple[float, float]:
    """Helper: calculate VAT and exclusive amount from inclusive total"""
    if vat_rate.value == 0:
        return 0.0, amount_incl_vat
    vat_amount = amount_incl_vat * vat_rate.value / (1 + vat_rate.value)
    return vat_amount, amount_incl_vat - vat_amount