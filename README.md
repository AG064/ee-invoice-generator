# ee-invoice-generator

**Open-source Estonian e-invoice generator with full accounting for small businesses (OÜ)**

- Generate **XML e-invoices** conforming to Estonian e-invoice standard (EN 16931)
- Generate **PDF invoices** for printing (professional layout)
- **Full double-entry bookkeeping** with journal, VAT, and financial reports
- Simple **GUI application** for Windows
- **CLI mode** for automation
- **SQLite database** for persistent storage
- Free and open source (MIT)

## Features

### Invoice Generation
- XML e-invoice (machine-readable, EN 16931 format)
- PDF invoice for printing (professional layout)
- Support for Estonian VAT rates (20%, 9%, 0%)
- Automatic VAT calculation
- Multiple line items with different VAT rates

### Accounting (Buchhaltung)
- **General Journal** - Double-entry bookkeeping with balanced transactions
- **Chart of Accounts** - Complete Estonian chart of accounts (Kontoplaan)
- **VAT Calculator** - Track output/input VAT, quarterly returns
- **Financial Reports** - Balance Sheet, Income Statement, Trial Balance
- **SQLite Database** - Persistent storage of all accounting data

### User Interface
- 5-tab GUI: My Company | Buyer | Invoice | Generate | Accounting
- Accounting sub-tabs: Journal | VAT | Reports | Accounts | Settings
- Save company details as default
- Internationalization ready (ET/RU/EN)

## Installation

### From Source

```bash
git clone https://github.com/xworcore/ee-invoice-generator.git
cd ee-invoice-generator
pip install -r requirements.txt
python main.py
```

### Building Windows .exe

```bash
pip install -r requirements.txt
pyinstaller ee-invoice-generator.spec
```

The executable will be in `dist/ee-invoice-generator/`.

## Usage

### GUI Mode

```bash
python main.py
```

**Tabs:**
1. **My Company** - Enter your company details (XworCore OÜ), save as default
2. **Buyer** - Enter customer details for each invoice
3. **Invoice** - Add line items with description, qty, unit, price, VAT%
4. **Generate** - Choose output directory, generate XML and/or PDF
5. **Accounting** - Full bookkeeping (Journal, VAT, Reports, Accounts)

### CLI Mode

```bash
# Generate from JSON
python -m cli --json examples/invoice_example.json --output-dir ./invoices

# Preview without generating
python -m cli --json examples/invoice_example.json --preview
```

## Accounting Module

### Chart of Accounts (Kontoplaan)
Full Estonian chart of accounts following VAS (Raamatupidamise seadus):

| Class | Description | Examples |
|-------|-------------|----------|
| 1xxx | Fixed Assets (Põhivara) | Equipment, buildings |
| 2xxx | Current Assets (Käibevara) | Cash, receivables, inventory |
| 3xxx | Equity (Omakapital) | Share capital, retained earnings |
| 4xxx | Long-term Liabilities | Bank loans |
| 5xxx | Short-term Liabilities | Supplier debts, taxes |
| 6xxx | Revenue & Expenses | Sales, wages, rent |

### Journal Entries
Each transaction creates balanced debit/credit entries:
```
Entry #1 - Sales Invoice INV-001
  2300  Customer Receivable    €1,200 (Debit)
  6000  Sales Revenue         €1,000 (Credit)
  2530  VAT Liability           €200 (Credit)
```

### VAT in Estonia
- Standard rate: **20%**
- Reduced rate: **9%** (books, medications)
- Zero rate: **0%** (some exports)
- Quarterly VAT declarations to Tax Office (MTA)

### Financial Reports
- **Balance Sheet (Bilanss)** - Assets = Liabilities + Equity
- **Income Statement (Kasumiaruanne)** - Revenue - Expenses = Profit
- **Trial Balance (Proovibilanss)** - All account balances

## Project Structure

```
ee-invoice-generator/
├── einvoice/
│   ├── generator.py    # XML e-invoice generator
│   ├── pdf.py          # PDF invoice generator
│   └── accounting/     # Full bookkeeping
│       ├── accounts.py    # Chart of accounts
│       ├── journal.py     # Double-entry journal
│       ├── vat.py         # VAT calculator
│       ├── reports.py     # Financial reports
│       └── database.py    # SQLite storage
├── gui/
│   ├── main.py           # Main GUI application
│   └── accounting_tab.py # Accounting interface
├── cli/
│   └── __init__.py       # CLI interface
├── examples/
│   └── invoice_example.json
├── requirements.txt
├── README.md
└── LICENSE
```

## Configuration

On first run, enter your company details in the GUI and click "Save as Default".
Configuration is stored in `~/.ee-invoice-generator/config.json`.

Accounting data is stored in SQLite at `~/.ee-invoice-generator/accounting.db`.

## Requirements

- Python 3.8+
- reportlab (PDF generation)
- PySimpleGUI (GUI)
- sqlite3 (built-in)

## License

MIT License - See LICENSE file