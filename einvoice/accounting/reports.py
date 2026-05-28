"""
Financial reports generator for Estonian small business
Generates: Balance Sheet (Bilanss), Income Statement (Kasumiaruanne), Cash Flow
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .journal import Journal, EntryType
from .accounts import CHART_OF_ACCOUNTS, AccountType


@dataclass
class BalanceSheet:
    """Balance Sheet - Bilanss (assets = liabilities + equity)"""
    as_of_date: date
    
    # Assets
    fixed_assets: float = 0.0       # Põhivara
    current_assets: float = 0.0    # Käibevara
    total_assets: float = 0.0
    
    # Liabilities
    long_term_liabilities: float = 0.0   # Pikaajalised kohustused
    short_term_liabilities: float = 0.0  # Lühiajalised kohustused
    total_liabilities: float = 0.0
    
    # Equity
    equity: float = 0.0
    total_liabilities_equity: float = 0.0
    
    @property
    def is_balanced(self) -> bool:
        return abs(self.total_assets - self.total_liabilities_equity) < 0.01


@dataclass
class IncomeStatement:
    """Income Statement - Kasumiaruanne"""
    start_date: date
    end_date: date
    
    revenue: float = 0.0          # Tulud
    other_income: float = 0.0     # Muud tulud
    expenses: float = 0.0         # Kulud
    profit_before_tax: float = 0.0
    tax: float = 0.0
    net_profit: float = 0.0


@dataclass
class CashFlow:
    """Cash Flow Statement - Rahavoogude aruanne"""
    start_date: date
    end_date: date
    
    opening_cash: float = 0.0
    cash_from_operations: float = 0.0
    cash_from_investing: float = 0.0
    cash_from_financing: float = 0.0
    closing_cash: float = 0.0
    
    @property
    def net_change(self) -> float:
        return self.cash_from_operations + self.cash_from_investing + self.cash_from_financing


class FinancialReports:
    """
    Generate financial statements from journal entries
    Estonian accounting format
    """
    
    def __init__(self, journal: Journal):
        self.journal = journal
    
    def generate_balance_sheet(self, as_of_date: date) -> BalanceSheet:
        """Generate Balance Sheet as of given date"""
        bs = BalanceSheet(as_of_date=as_of_date)
        
        # Get trial balance
        trial = self.journal.trial_balance(as_of_date)
        
        # Classify accounts
        for acc_num, amounts in trial.items():
            debit = amounts["debit"]
            credit = amounts["credit"]
            net = debit - credit
            
            acc = CHART_OF_ACCOUNTS.get(acc_num)
            if acc is None:
                continue
            
            # Assets (debit positive)
            if acc.account_type == AccountType.ASSET:
                if acc_num.startswith("1"):  # Fixed assets (1000-1399)
                    bs.fixed_assets += net
                else:  # Current assets
                    bs.current_assets += net
            
            # Liabilities (credit positive)
            elif acc.account_type == AccountType.LIABILITY:
                if acc_num.startswith("4"):  # Long-term
                    bs.long_term_liabilities += net
                else:  # Short-term
                    bs.short_term_liabilities += net
            
            # Equity
            elif acc.account_type == AccountType.EQUITY:
                bs.equity += net
        
        bs.total_assets = bs.fixed_assets + bs.current_assets
        bs.total_liabilities = bs.long_term_liabilities + bs.short_term_liabilities
        bs.total_liabilities_equity = bs.total_liabilities + bs.equity
        
        return bs
    
    def generate_income_statement(self, start_date: date, end_date: date) -> IncomeStatement:
        """Generate Income Statement for period"""
        is_stmt = IncomeStatement(start_date=start_date, end_date=end_date)
        
        entries = self.journal.get_entries_by_date(start_date, end_date)
        
        for entry in entries:
            for line in entry.lines:
                acc = CHART_OF_ACCOUNTS.get(line.account_number)
                if acc is None:
                    continue
                
                amount = line.amount
                if line.entry_type == EntryType.CREDIT:
                    amount = -amount
                
                # Revenue accounts (6xxx)
                if line.account_number.startswith("6") and acc.account_type == AccountType.REVENUE:
                    is_stmt.revenue += amount
                elif line.account_number.startswith("68"):
                    is_stmt.other_income += amount
                
                # Expense accounts
                elif line.account_number.startswith("6") and acc.account_type == AccountType.EXPENSE:
                    is_stmt.expenses += amount
        
        is_stmt.profit_before_tax = is_stmt.revenue + is_stmt.other_income - is_stmt.expenses
        # Estonia corporate tax is 20% on distributed profits
        is_stmt.net_profit = is_stmt.profit_before_tax
        
        return is_stmt
    
    def generate_cash_flow(self, start_date: date, end_date: date) -> CashFlow:
        """Generate Cash Flow Statement (simplified direct method)"""
        cf = CashFlow(start_date=start_date, end_date=end_date)
        
        # Opening cash (balance of 2600 at start of period)
        cf.opening_cash = self.journal.account_balance("2600", self._prev_date(start_date))
        
        entries = self.journal.get_entries_by_date(start_date, end_date)
        
        for entry in entries:
            for line in entry.lines:
                # Cash flow from operations (bank account 2600)
                if line.account_number == "2600":
                    if line.entry_type == EntryType.DEBIT:
                        cf.cash_from_operations += line.amount
                    else:
                        cf.cash_from_operations -= line.amount
        
        cf.closing_cash = cf.opening_cash + cf.net_change
        
        return cf
    
    def _prev_date(self, d: date) -> Optional[date]:
        """Get day before given date"""
        from datetime import timedelta
        return d - timedelta(days=1)
    
    def format_balance_sheet(self, bs: BalanceSheet) -> str:
        """Format balance sheet as readable text"""
        lines = [
            "=" * 50,
            "BILANSS (Bilanss)",
            f"Kuupäev: {bs.as_of_date.strftime('%d.%m.%Y')}",
            "=" * 50,
            "",
            "VARA (Assets)",
            "-" * 40,
            f"  Põhivara:           € {bs.fixed_assets:>12.2f}",
            f"  Käibevara:          € {bs.current_assets:>12.2f}",
            f"  Kokku vara:         € {bs.total_assets:>12.2f}",
            "",
            "KOHUSTISED JA OMAKAPITAL (Liabilities + Equity)",
            "-" * 40,
            f"  Pikaajalised:       € {bs.long_term_liabilities:>12.2f}",
            f"  Lühiajalised:       € {bs.short_term_liabilities:>12.2f}",
            f"  Kokku kohustised:   € {bs.total_liabilities:>12.2f}",
            f"  Omakapital:         € {bs.equity:>12.2f}",
            f"  Kokku:              € {bs.total_liabilities_equity:>12.2f}",
            "",
            f" Kontroll: {'OK' if bs.is_balanced else 'VIGA'} (Vara = {bs.total_assets:.2f})",
            "=" * 50,
        ]
        return "\n".join(lines)
    
    def format_income_statement(self, is_stmt: IncomeStatement) -> str:
        """Format income statement as readable text"""
        lines = [
            "=" * 50,
            "KASUMIARUANNE (Income Statement)",
            f" Periood: {is_stmt.start_date.strftime('%d.%m.%Y')} - {is_stmt.end_date.strftime('%d.%m.%Y')}",
            "=" * 50,
            "",
            f"  Müügitulu:          € {is_stmt.revenue:>12.2f}",
            f"  Muud tulud:         € {is_stmt.other_income:>12.2f}",
            f"  Kulud:              € {is_stmt.expenses:>12.2f}",
            "-" * 40,
            f"  Kasum enne makse:   € {is_stmt.profit_before_tax:>12.2f}",
            f"  Maksukohustus:      € {is_stmt.tax:>12.2f}",
            f"  Puhaskasum:         € {is_stmt.net_profit:>12.2f}",
            "=" * 50,
        ]
        return "\n".join(lines)