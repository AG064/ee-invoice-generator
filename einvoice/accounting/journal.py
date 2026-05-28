"""
General Journal - double-entry bookkeeping for Estonian OÜ
Each transaction has balanced debit/credit entries
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from enum import Enum
import json
from pathlib import Path


class EntryType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class JournalEntryLine:
    """Single debit or credit entry"""
    account_number: str
    amount: float           # Always positive
    entry_type: EntryType   # DEBIT or CREDIT
    description: str = ""


@dataclass 
class JournalEntry:
    """Complete journal entry with multiple lines (balanced)"""
    date: date
    entry_number: int
    description: str
    lines: list[JournalEntryLine] = field(default_factory=list)
    reference: str = ""     # Invoice number, receipt, etc.
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_debit(self, account: str, amount: float, description: str = ""):
        self.lines.append(JournalEntryLine(account, amount, EntryType.DEBIT, description))
    
    def add_credit(self, account: str, amount: float, description: str = ""):
        self.lines.append(JournalEntryLine(account, amount, EntryType.CREDIT, description))
    
    def is_balanced(self) -> bool:
        """Check if debits equal credits"""
        debit_sum = sum(l.amount for l in self.lines if l.entry_type == EntryType.DEBIT)
        credit_sum = sum(l.amount for l in self.lines if l.entry_type == EntryType.CREDIT)
        return abs(debit_sum - credit_sum) < 0.001
    
    def total_debits(self) -> float:
        return sum(l.amount for l in self.lines if l.entry_type == EntryType.DEBIT)
    
    def total_credits(self) -> float:
        return sum(l.amount for l in self.lines if l.entry_type == EntryType.CREDIT)
    
    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "entry_number": self.entry_number,
            "description": self.description,
            "reference": self.reference,
            "lines": [
                {
                    "account": l.account_number,
                    "amount": l.amount,
                    "type": l.entry_type.value,
                    "description": l.description
                }
                for l in self.lines
            ],
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "JournalEntry":
        entry = cls(
            date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            entry_number=data["entry_number"],
            description=data["description"],
            reference=data.get("reference", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )
        for line in data["lines"]:
            entry.lines.append(JournalEntryLine(
                account_number=line["account"],
                amount=line["amount"],
                entry_type=EntryType(line["type"]),
                description=line.get("description", ""),
            ))
        return entry


class Journal:
    """
    General Journal for double-entry bookkeeping
    Entries are stored in JSON for simplicity
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".ee-invoice-generator" / "accounting"
        self.entries: list[JournalEntry] = []
        self.next_entry_number = 1
        self._load()
    
    def _load(self):
        """Load journal from disk"""
        journal_file = self.data_dir / "journal.json"
        if journal_file.exists():
            try:
                with open(journal_file) as f:
                    data = json.load(f)
                self.entries = [JournalEntry.from_dict(e) for e in data.get("entries", [])]
                self.next_entry_number = data.get("next_entry_number", 1)
            except Exception:
                pass
    
    def _save(self):
        """Save journal to disk"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        journal_file = self.data_dir / "journal.json"
        with open(journal_file, "w") as f:
            json.dump({
                "entries": [e.to_dict() for e in self.entries],
                "next_entry_number": self.next_entry_number,
            }, f, indent=2, ensure_ascii=False)
    
    def add_entry(self, entry: JournalEntry) -> int:
        """Add new journal entry, returns entry number"""
        if not entry.is_balanced():
            raise ValueError(f"Entry is not balanced: debits={entry.total_debits()}, credits={entry.total_credits()}")
        
        entry.entry_number = self.next_entry_number
        self.entries.append(entry)
        self.next_entry_number += 1
        self._save()
        return entry.entry_number
    
    def get_entry(self, entry_number: int) -> Optional[JournalEntry]:
        """Get entry by number"""
        for e in self.entries:
            if e.entry_number == entry_number:
                return e
        return None
    
    def get_entries_by_date(self, start_date: date, end_date: date) -> list[JournalEntry]:
        """Get all entries in date range"""
        return [e for e in self.entries if start_date <= e.date <= end_date]
    
    def get_entries_by_account(self, account_number: str) -> list[tuple[JournalEntry, JournalEntryLine]]:
        """Get all entries affecting an account, with the specific line"""
        result = []
        for entry in self.entries:
            for line in entry.lines:
                if line.account_number == account_number:
                    result.append((entry, line))
        return result
    
    def account_balance(self, account_number: str, as_of_date: date = None) -> float:
        """Calculate account balance as of date (debits - credits)"""
        balance = 0.0
        for entry in self.entries:
            if as_of_date and entry.date > as_of_date:
                continue
            for line in entry.lines:
                if line.account_number == account_number:
                    if line.entry_type == EntryType.DEBIT:
                        balance += line.amount
                    else:
                        balance -= line.amount
        return balance
    
    def trial_balance(self, as_of_date: date = None) -> dict[str, float]:
        """Generate trial balance"""
        accounts = {}
        for entry in self.entries:
            if as_of_date and entry.date > as_of_date:
                continue
            for line in entry.lines:
                if line.account_number not in accounts:
                    accounts[line.account_number] = {"debit": 0.0, "credit": 0.0}
                if line.entry_type == EntryType.DEBIT:
                    accounts[line.account_number]["debit"] += line.amount
                else:
                    accounts[line.account_number]["credit"] += line.amount
        return accounts
    
    def delete_entry(self, entry_number: int) -> bool:
        """Delete entry by number"""
        for i, e in enumerate(self.entries):
            if e.entry_number == entry_number:
                self.entries.pop(i)
                self._save()
                return True
        return False


# Helper functions for common Estonian business transactions
def create_sale_entry(journal: Journal, invoice_number: str, date: date,
                      customer_account: str, revenue_account: str,
                      amount_excl_vat: float, vat_amount: float) -> JournalEntry:
    """Create journal entry for sales invoice (debtor payment)"""
    entry = JournalEntry(
        date=date,
        entry_number=0,
        description=f"Müük {invoice_number}",
        reference=invoice_number,
    )
    # Debit: Customer receivable
    entry.add_debit(customer_account, amount_excl_vat + vat_amount, "Kliendi võlg")
    # Credit: Revenue
    entry.add_credit(revenue_account, amount_excl_vat, f"Müügitulu {invoice_number}")
    # Credit: VAT
    entry.add_credit("2530", vat_amount, f"Käibemaks {invoice_number}")
    
    if not entry.is_balanced():
        raise ValueError("Sale entry not balanced")
    
    return entry


def create_purchase_entry(journal: Journal, invoice_number: str, date: date,
                         supplier_account: str, expense_account: str,
                         amount_excl_vat: float, vat_amount: float) -> JournalEntry:
    """Create journal entry for purchase invoice (supplier payment)"""
    entry = JournalEntry(
        date=date,
        entry_number=0,
        description=f"Ost {invoice_number}",
        reference=invoice_number,
    )
    # Debit: Expense
    entry.add_debit(expense_account, amount_excl_vat, f"Ost {invoice_number}")
    # Debit: VAT reclaimable
    entry.add_debit("2530", vat_amount, f"Sisendkäibemaks {invoice_number}")
    # Credit: Supplier payable
    entry.add_credit(supplier_account, amount_excl_vat + vat_amount, "Tarnija võlg")
    
    if not entry.is_balanced():
        raise ValueError("Purchase entry not balanced")
    
    return entry


def create_vat_payment_entry(journal: Journal, date: date, vat_amount: float) -> JournalEntry:
    """Create journal entry for VAT payment to tax authority"""
    entry = JournalEntry(
        date=date,
        entry_number=0,
        description=f"Käibemaksu tasumine",
    )
    # Debit: VAT liability
    entry.add_debit("2530", vat_amount, "Käibemaks")
    # Credit: Bank
    entry.add_credit("2600", vat_amount, "Pank")
    
    if not entry.is_balanced():
        raise ValueError("VAT payment entry not balanced")
    
    return entry


def create_salary_entry(journal: Journal, date: date, gross_salary: float,
                       employer_taxes: float, net_salary: float) -> JournalEntry:
    """Create journal entry for salary payment"""
    entry = JournalEntry(
        date=date,
        entry_number=0,
        description=f"Palgamaksed",
    )
    # Debit: Salary expense
    entry.add_debit("6600", gross_salary, "Brutopalk")
    # Debit: Employer taxes
    entry.add_debit("6600", employer_taxes, "Tööandja maksud")
    # Credit: Net salary payable
    entry.add_credit("5200", net_salary, "Neto palk")
    # Credit: Tax withheld
    entry.add_credit("5300", gross_salary * 0.2, "Tulumaks")
    # Credit: Social tax
    entry.add_credit("5300", employer_taxes, "Sotsiaalmaks")
    # Credit: Unemployment insurance
    entry.add_credit("5300", gross_salary * 0.008, "Töötuskindlustus")
    
    if not entry.is_balanced():
        raise ValueError("Salary entry not balanced")
    
    return entry