"""
Chart of Accounts for Estonian small business (OÜ)
Based on Estonian accounting chart (Kontoplaan)
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AccountType(Enum):
    """Account types following Estonian accounting principles"""
    ASSET = "asset"           # Vara (varad)
    LIABILITY = "liability"   # Kohustis (kohustused)
    EQUITY = "equity"         # Omakapital
    REVENUE = "revenue"       # Tulu
    EXPENSE = "expense"       # Kulu
    off_BALANCE = "off_balance"  # Bilansiväline


@dataclass
class Account:
    """Single account in the chart of accounts"""
    number: str              # Account number (1-9999)
    name_et: str             # Estonian name
    name_ru: str             # Russian name
    account_type: AccountType
    tax_account: bool = False  # Has tax implications
    vat_eligible: bool = True   # VAT can be applied
    
    def __str__(self):
        return f"{self.number} - {self.name_et}"


# Estonian Chart of Accounts (Kontoplaan)
# Following Estonian VAS (Raamatupidamise seadus) structure
CHART_OF_ACCOUNTS = {
    # Class 1 - Long-term assets (Põhivara)
    "1000": Account("1000", "Materiaalne põhivara", "Материальные основные средства", AccountType.ASSET),
    "1010": Account("1010", "Määrdunud materiaalne põhivara", "Амортизированные материальные основные средства", AccountType.ASSET),
    "1100": Account("1100", "Immateriaalne põhivara", "Нематериальные основные средства", AccountType.ASSET),
    "1200": Account("1200", "Pikaajalised finantsinvesteeringud", "Долгосрочные финансовые инвестиции", AccountType.ASSET),
    "1300": Account("1300", "Muud pikaajalised nõuded", "Прочие долгосрочные требования", AccountType.ASSET),
    
    # Class 2 - Current assets (Käibevara)
    "2000": Account("2000", "Varud", "Запасы", AccountType.ASSET, vat_eligible=False),
    "2100": Account("2100", "Valmistoodang", "Готовая продукция", AccountType.ASSET),
    "2200": Account("2200", "Ostetud kaubad", "Купленные товары", AccountType.ASSET),
    "2300": Account("2300", "Müügivõlad (deebitorid)", "Дебиторская задолженность", AccountType.ASSET),
    "2400": Account("2400", "Muud lühiajalised nõuded", "Прочие краткосрочные требования", AccountType.ASSET),
    "2500": Account("2500", "Viitlaekumised", "Расходы будущих периодов", AccountType.ASSET),
    "2600": Account("2600", "Raha ja pangakontod", "Деньги и банковские счета", AccountType.ASSET, tax_account=True),
    
    # Class 3 - Equity (Omakapital)
    "3000": Account("3000", "Osakapital", "Уставной капитал", AccountType.EQUITY),
    "3100": Account("3100", "Mitteresidentide osalused", "Доли нерезидентов", AccountType.EQUITY),
    "3200": Account("3200", "Kohustuslik reservkapital", "Обязательный резервный капитал", AccountType.EQUITY),
    "3300": Account("3300", "Muud reservid", "Прочие резервы", AccountType.EQUITY),
    "3400": Account("3400", "Jaotamata kasum/kahjum", "Нераспределённая прибыль/убыток", AccountType.EQUITY),
    "3450": Account("3450", "Aruandeaasta kasum/kahjum", "Прибыль/убыток за отчётный год", AccountType.EQUITY),
    
    # Class 4 - Long-term liabilities (Pikaajalised kohustused)
    "4000": Account("4000", "Pikaajalised pangalaenud", "Долгосрочные банковские кредиты", AccountType.LIABILITY),
    "4100": Account("4100", "Pikaajalised võlad tarnijatele", "Долгосрочная задолженность поставщикам", AccountType.LIABILITY),
    "4200": Account("4200", "Liisingukohustused", "Обязательства по лизингу", AccountType.LIABILITY),
    
    # Class 5 - Current liabilities (Lühiajalised kohustused)
    "5000": Account("5000", "Lühiajalised pangalaenud", "Краткосрочные банковские кредиты", AccountType.LIABILITY),
    "5100": Account("5100", "Lühiajalised võlad tarnijatele", "Краткосрочная задолженность поставщикам", AccountType.LIABILITY, tax_account=True),
    "5200": Account("5200", "Võlad töötajatele", "Задолженность работникам", AccountType.LIABILITY, tax_account=True),
    "5300": Account("5300", "Maksuvõlad", "Налоговые обязательства", AccountType.LIABILITY, tax_account=True),
    "5400": Account("5400", "Saadud ettemaksed", "Полученные авансы", AccountType.LIABILITY),
    "5500": Account("5500", "Müügivõlad (kreeditorid)", "Кредиторская задолженность", AccountType.LIABILITY),
    "5600": Account("5600", "Viitvõlad", "Начисленные расходы", AccountType.LIABILITY),
    
    # Class 6 - Revenue (Tulud)
    "6000": Account("6000", "Müügitulu (kaupade müük)", "Выручка от продажи товаров", AccountType.REVENUE, vat_eligible=False),
    "6100": Account("6100", "Müügitulu (teenuste müük)", "Выручка от оказания услуг", AccountType.REVENUE, vat_eligible=False),
    "6200": Account("6200", "Tööde ja teenuste maksumus", "Себестоимость работ и услуг", AccountType.EXPENSE),
    "6300": Account("6300", "Kaupade soetusmaksumus", "Себестоимость товаров", AccountType.EXPENSE),
    "6400": Account("6400", "Turunduskulud", "Маркетинговые расходы", AccountType.EXPENSE),
    "6500": Account("6500", "Üldhalduskulud", "Общие и административные расходы", AccountType.EXPENSE),
    "6600": Account("6600", "Tööjõukulud", "Расходы на персонал", AccountType.EXPENSE, tax_account=True),
    "6700": Account("6700", "Kulum ja amortisatsioon", "Амортизация", AccountType.EXPENSE),
    "6800": Account("6800", "Muud äritulud", "Прочие операционные доходы", AccountType.REVENUE),
    "6900": Account("6900", "Finantstulud ja -kulud", "Финансовые доходы и расходы", AccountType.REVENUE),
    
    # Class 7 - Financial operations (Finants- ja erakorralised tehingud)
    "7000": Account("7000", "Intressitulud", "Процентные доходы", AccountType.REVENUE),
    "7100": Account("7100", "Intressikulud", "Процентные расходы", AccountType.EXPENSE),
    "7200": Account("7200", "Kursivoad", "Курсовые разницы", AccountType.REVENUE),
    "7300": Account("7300", "Erakorralised tulud ja kulud", "Внереализационные доходы и расходы", AccountType.REVENUE),
    
    # Class 8 - Off-balance sheet (Bilansivälised kontod)
    "8000": Account("8000", "Rentniku sisestatud põhivara", "Основные средства арендатора", AccountType.off_BALANCE),
    "8100": Account("8100", "Tagatised ja garantiid", "Гарантии и поручительства", AccountType.off_BALANCE),
    "8200": Account("8200", "Kohustused ja nõuded", "Обязательства и требования", AccountType.off_BALANCE),
}


def get_account(number: str) -> Optional[Account]:
    """Get account by number"""
    return CHART_OF_ACCOUNTS.get(number)


def get_accounts_by_type(account_type: AccountType) -> list[Account]:
    """Get all accounts of given type"""
    return [acc for acc in CHART_OF_ACCOUNTS.values() if acc.account_type == account_type]


def search_accountes(query: str) -> list[Account]:
    """Search accounts by name (Estonian or Russian)"""
    q = query.lower()
    return [
        acc for acc in CHART_OF_ACCOUNTS.values()
        if q in acc.name_et.lower() or q in acc.name_ru.lower()
    ]