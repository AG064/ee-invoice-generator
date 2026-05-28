# ee-invoice-generator

Generate Estonian e-invoices (XML) and printable invoices (PDF) from a simple GUI or CLI.

**Features:**
- Generate XML e-invoices conforming to Estonian e-invoice standard (EN 16931)
- Generate PDF invoices suitable for printing
- Simple GUI application for Windows
- CLI mode for automation
- Save company details for reuse
- Free and open source

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

The .exe will be in `dist/ee-invoice-generator/`.

## Usage

### GUI Mode

```bash
python main.py
```

1. **My Company** - Fill in your company details and save as default
2. **Buyer** - Enter customer details
3. **Invoice** - Add line items (description, qty, unit, price, VAT%)
4. **Generate** - Choose output directory and generate XML/PDF

### CLI Mode

```bash
python -m cli --json examples/invoice_example.json --output-dir ./output
```

## Configuration

On first run, enter your company details in the GUI and click "Save as Default".
Configuration is stored in `~/.ee-invoice-generator/config.json`.

## Output Files

- **XML**: Machine-readable Estonian e-invoice (EN 16931 format)
- **PDF**: Printable invoice with professional layout

## Requirements

- Python 3.8+
- reportlab (PDF generation)
- PySimpleGUI (GUI)

## License

MIT