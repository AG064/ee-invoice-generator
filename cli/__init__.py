"""
CLI interface for ee-invoice-generator
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from einvoice import InvoiceGenerator, PDFGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails


def load_json_config(filepath):
    """Load invoice data from JSON file"""
    with open(filepath) as f:
        data = json.load(f)
    
    # Parse dates
    if "invoice_date" in data:
        data["invoice_date"] = datetime.strptime(data["invoice_date"], "%Y-%m-%d").date()
    if "due_date" in data and data["due_date"]:
        data["due_date"] = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
    
    # Parse nested objects
    data["seller"] = PartyDetails(**data["seller"])
    data["buyer"] = PartyDetails(**data["buyer"])
    data["payment"] = PaymentDetails(**data["payment"])
    data["lines"] = [InvoiceLine(**line) for line in data["lines"]]
    
    return InvoiceData(**data)


def main():
    parser = argparse.ArgumentParser(description="Generate Estonian e-invoices")
    parser.add_argument("--json", "-j", type=str, help="Input JSON file with invoice data")
    parser.add_argument("--output-dir", "-o", type=str, default=".", help="Output directory")
    parser.add_argument("--no-xml", action="store_true", help="Skip XML generation")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    parser.add_argument("--preview", action="store_true", help="Preview invoice data without generating")
    
    args = parser.parse_args()
    
    if args.json:
        # Load from JSON
        invoice_data = load_json_config(args.json)
    else:
        print("Error: --json required for CLI mode", file=sys.stderr)
        print("Use --help for more information", file=sys.stderr)
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    invoice_num = invoice_data.invoice_number.replace("/", "-")
    date_str = invoice_data.invoice_date.strftime("%Y%m%d")
    
    if args.preview:
        # Just print what would be generated
        print("Invoice Preview:")
        print(f"  Number: {invoice_data.invoice_number}")
        print(f"  Date: {invoice_data.invoice_date}")
        print(f"  Seller: {invoice_data.seller.name}")
        print(f"  Buyer: {invoice_data.buyer.name}")
        print(f"  Lines: {len(invoice_data.lines)}")
        for i, line in enumerate(invoice_data.lines, 1):
            total = line.quantity * line.unit_price * (1 + line.vat_rate)
            print(f"    {i}. {line.description}: {line.quantity} x €{line.unit_price:.2f} = €{total:.2f}")
        return
    
    generated = []
    
    if not args.no_xml:
        xml_path = output_dir / f"invoice_{date_str}_{invoice_num}.xml"
        gen = InvoiceGenerator(invoice_data)
        gen.save(str(xml_path))
        print(f"Generated XML: {xml_path}")
        generated.append("XML")
    
    if not args.no_pdf:
        pdf_path = output_dir / f"invoice_{date_str}_{invoice_num}.pdf"
        pdf_gen = PDFGenerator(invoice_data)
        pdf_gen.save(str(pdf_path))
        print(f"Generated PDF: {pdf_path}")
        generated.append("PDF")
    
    if not generated:
        print("Nothing generated (use --xml and/or --pdf)")
    else:
        print(f"Done! Generated: {', '.join(generated)}")


if __name__ == "__main__":
    main()