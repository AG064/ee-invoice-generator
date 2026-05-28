# ee-invoice-generator

**Open-source Estonian e-invoice generator with full accounting for small businesses (OÜ)**

Generate XML e-invoices (EN 16931) and printable PDF invoices with a simple desktop GUI. Includes full double-entry bookkeeping.

## Features

- **E-invoice (XML)** - Machine-readable invoice conforming to Estonian e-invoice standard
- **PDF Invoice** - Professional printable invoice with clean layout
- **Full Accounting** - Journal, VAT calculator, financial reports, chart of accounts
- **Step-by-step Wizard** - Easy guided flow for creating invoices
- **Estonian VAT** - Support for 20%, 9%, and 0% VAT rates
- **Desktop GUI** - Simple and intuitive interface for Windows
- **Open Source** - MIT license, free for personal and commercial use

## Quick Start

### Download & Run

1. Download the latest `.exe` from [Releases](https://github.com/AG064/ee-invoice-generator/releases)
2. Double-click to run - no installation needed
3. Start creating invoices!

### Build from Source

```bash
git clone https://github.com/AG064/ee-invoice-generator.git
cd ee-invoice-generator
pip install -r requirements.txt
python main.py
```

### Build Windows Executable

```bash
pip install -r requirements.txt
pyinstaller ee-invoice-generator.spec
# Find .exe in dist/ee-invoice-generator.exe
```

## Tutorial: Creating Your First Invoice

### Step 1: Set Up Your Company

Before creating invoices, configure your company details:

1. Click **"My Company"** in the top menu
2. Fill in your company information:
   - **Company Name** - Your company name (e.g., "XworCore OÜ")
   - **Registry Code** - 8-digit Estonian registry code
   - **VAT Number** - KMKR number (e.g., EE123456789)
   - **Address** - Legal address
   - **IBAN / BIC** - Bank account details for payment
3. Click **"Save as Default"** - Your company data will be remembered

### Step 2: Enter Customer Details

1. Click **"New Invoice"** to start
2. Enter customer information:
   - **Company Name** - Customer's company name
   - **Registry Code** - Customer's registry code
   - **VAT Number** - Customer's VAT number (if applicable)
   - **Address** - Delivery/billing address

### Step 3: Add Line Items

For each product or service:

1. Enter **Description** (e.g., "Web development - 10 hours")
2. Set **Quantity** (default: 1)
3. Choose **Unit** (pcs, hours, kg, etc.)
4. Enter **Price per unit** (without VAT)
5. Select **VAT Rate** (20%, 9%, or 0%)
6. Click **"Add Line"**
7. Repeat for additional items

### Step 4: Review & Generate

1. Verify all details on the review screen
2. Choose output format:
   - **XML** - E-invoice for digital submission
   - **PDF** - Printable invoice
3. Click **"Generate Invoice"**
4. Files are saved to your chosen directory

## Invoice Numbering

Use consistent numbering, e.g.:
- INV-0001, INV-0002, ...
- 2026-001, 2026-002, ...
- Your format here

## VAT Rates in Estonia

| Rate | Applies to |
|------|------------|
| **20%** | Standard rate - most goods and services |
| **9%** | Reduced rate - books, medications, cultural events |
| **0%** | Zero rate - some exports, international transport |

## Accounting Module

The built-in accounting module provides:

- **Journal** - Record and track all business transactions
- **VAT Reports** - Quarterly VAT declarations
- **Financial Reports** - Balance sheet, income statement
- **Chart of Accounts** - Complete Estonian account plan

### Key Accounts

| Account | Name | Type |
|---------|------|------|
| 1000 | Fixed Assets | Asset |
| 2300 | Customer Receivables | Asset |
| 2600 | Bank Account | Asset |
| 3000 | Share Capital | Equity |
| 5100 | Supplier Payables | Liability |
| 5300 | Tax Liabilities | Liability |
| 6000 | Sales Revenue | Revenue |
| 6600 | Salary Expenses | Expense |

## Configuration

- Company data: `~/.ee-invoice-generator/config.json`
- Accounting data: `~/.ee-invoice-generator/accounting.db`

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+S | Save current form |
| Ctrl+G | Generate invoice |
| Esc | Cancel / Close dialog |

## Troubleshooting

**"Module not found" error:**
- Download the latest release from GitHub
- Ensure all dependencies are installed: `pip install -r requirements.txt`

**PDF doesn't open:**
- Try regenerating with "Generate PDF" option
- Ensure no other program has the file open

**GUI looks wrong on Windows:**
- Try running in Windows 10/11 compatibility mode
- Update your graphics drivers

## Development

### Project Structure

```
ee-invoice-generator/
├── main.py              # Application entry point
├── gui/
│   └── main.py          # Main GUI implementation
├── einvoice/
│   ├── generator.py      # XML e-invoice generator
│   ├── pdf.py            # PDF invoice generator
│   └── accounting/       # Accounting module
│       ├── accounts.py   # Chart of accounts
│       ├── journal.py    # Double-entry journal
│       ├── vat.py        # VAT calculator
│       ├── reports.py    # Financial reports
│       └── database.py   # SQLite storage
├── requirements.txt
├── README.md
└── LICENSE
```

### Requirements

- Python 3.8+
- reportlab (PDF generation)
- PySimpleGUI (GUI)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**For questions or issues, open a GitHub Issue.**