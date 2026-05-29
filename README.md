# ee-invoice-generator
<img width="893" height="733" alt="image" src="https://github.com/user-attachments/assets/ab6c56e7-62c4-4a5a-a07b-a4900939157a" />

**Open-source Estonian e-invoice generator with full accounting for small businesses (OÜ)**

Generate XML e-invoices (EN 16931) and printable PDF invoices with a simple desktop GUI. Includes full double-entry bookkeeping. **No registration required** — download and run.

## Features

- **E-invoice (XML)** — Machine-readable invoice conforming to Estonian e-invoice standard
- **PDF Invoice** — Professional printable invoice with clean layout (3 languages: EN/RU/ET)
- **Full Accounting** — Journal, VAT calculator, financial reports, chart of accounts
- **Tax Portal Integration** — Direct link to e-MTA (Estonian Tax Board) for invoice submission
- **Auto-Update** — Automatic update checker with one-click update notification
- **Desktop GUI** — Simple and intuitive interface
- **Open Source** — MIT license, free for personal and commercial use

## Screenshots

### Main Window — Invoice Creation
<img width="692" height="637" alt="image" src="https://github.com/user-attachments/assets/e1763a78-4a41-413d-b250-4406543f59dd" />

*Create invoices with line items, VAT rates, and multiple output formats*

### Invoice Preview (PDF)
<img width="893" height="733" alt="image" src="https://github.com/user-attachments/assets/a37c8d7c-2707-4c80-ac87-208b65f726fb" />

*Professional PDF output conforming to Estonian standards*

### Accounting Module — Journal (TBD)
![Accounting Journal](screenshots/accounting-journal.png)
*Double-entry bookkeeping with journal entries*
<img width="695" height="669" alt="image" src="https://github.com/user-attachments/assets/7468fbc9-e8bb-47ed-bd33-03499e4c55d9" />

### Accounting Module — VAT Calculator (TBD)
![VAT Calculator](screenshots/accounting-vat.png)
*Quarterly VAT reporting and calculation*

### History module - Invoice History using a database.
<img width="692" height="669" alt="image" src="https://github.com/user-attachments/assets/2cf1b920-6faa-4c79-bd13-4408551ad693" />
*Keep track of any invoices you have made in the past and go back to them if needed. Helpful for Accounting!*
## Quick Start

### Download & Run

1. Download the latest release from [Releases](https://github.com/AG064/ee-invoice-generator/releases)
2. Double-click to run — no installation or registration needed
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
   - **Company Name** — Your company name (e.g., "XworCore OÜ")
   - **Registry Code** — 8-digit Estonian registry code
   - **VAT Number** — KMKR number (e.g., EE123456789)
   - **Address** — Legal address
   - **IBAN / BIC** — Bank account details for payment
3. Click **"Save as Default"** — Your company data will be remembered

### Step 2: Enter Customer Details

1. Click **"New Invoice"** to start
2. Enter customer information:
   - **Company Name** — Customer's company name
   - **Registry Code** — Customer's registry code
   - **VAT Number** — Customer's VAT number (if applicable)
   - **Address** — Delivery/billing address

### Step 3: Add Line Items

For each product or service:

1. Enter **Description** (e.g., "Web development — 10 hours")
2. Set **Quantity** (default: 1)
3. Choose **Unit** (pcs, hours, kg, etc.)
4. Enter **Price per unit** (without VAT)
5. Select **VAT Rate** (20%, 9%, or 0%)
6. Click **"Add Line"**
7. Repeat for additional items

### Step 4: Review & Generate

1. Verify all details on the review screen
2. Choose output format:
   - **XML** — E-invoice for digital submission
   - **PDF** — Printable invoice
3. Click **"Generate Invoice"**
4. Files are saved to your chosen directory

### Step 5: Submit to Tax Board

After generating the XML e-invoice:

1. Click **"Send E-invoice"** in the popup
2. Choose **"Open Tax Portal"** to go to e-MTA (Estonian Tax Board)
3. Upload your XML file there for official submission

## Invoice Numbering

Use consistent numbering, e.g.:
- INV-0001, INV-0002, ...
- 2026-001, 2026-002, ...
- Your format here

## VAT Rates in Estonia

| Rate | Applies to |
|------|------------|
| **20%** | Standard rate — most goods and services |
| **9%** | Reduced rate — books, medications, cultural events |
| **0%** | Zero rate — some exports, international transport |

## E-Invoice Submission

### To Estonian Tax Board (e-MTA)

1. Generate the XML e-invoice
2. Click "Send E-invoice" → "Open Tax Portal"
3. Log in to [e-MTA](https://www.emta.ee/) with your ID-card or m-ID
4. Submit the XML file through the portal

### B2B E-Invoices

For sending e-invoices directly to other businesses, use:
- Your bank's EDI service (Swedbank, SEB, Luminor, etc.)
- Commercial EDI providers (TriSoft, Maksekeskus, etc.)

## Accounting Module

The built-in accounting module provides:

- **Journal** — Record and track all business transactions
- **VAT Reports** — Quarterly VAT declarations
- **Financial Reports** — Balance sheet, income statement
- **Chart of Accounts** — Complete Estonian account plan

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

MIT License — See [LICENSE](LICENSE) for details.

---

**For questions or issues, open a [GitHub Issue](https://github.com/AG064/ee-invoice-generator/issues).**
