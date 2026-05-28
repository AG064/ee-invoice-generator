"""
ee-invoice-generator GUI
PySimpleGUI-based desktop application for generating Estonian e-invoices
"""
import PySimpleGUI as sg
import json
import os
from datetime import date, datetime
from pathlib import Path

from einvoice import InvoiceGenerator, PDFGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails
from einvoice.accounting import Database
from gui.accounting_tab import create_accounting_tab, handle_accounting_event


# Theme
sg.theme("LightBlue")

# Default config path
CONFIG_DIR = Path.home() / ".ee-invoice-generator"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """Load saved company configuration"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    """Save company configuration"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def create_company_tab():
    """Tab for seller (your company) details"""
    config = load_config()
    
    return [
        [sg.Text("Company Details", font=("Helvetica", 12, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Company Name *"), sg.Input(default_text=config.get("name", ""), key="-SELLER_NAME-", size=(40, 1))],
        [sg.Text("Registry Code * (8 digits)"), sg.Input(default_text=config.get("registry_code", ""), key="-SELLER_REGISTRY-", size=(20, 1))],
        [sg.Text("VAT Number (KMKR)"), sg.Input(default_text=config.get("vat_number", ""), key="-SELLER_VAT-", size=(20, 1), tooltip="e.g., EE123456789")],
        [sg.Text("Address"), sg.Input(default_text=config.get("address", ""), key="-SELLER_ADDR-", size=(40, 1))],
        [sg.Text("City"), sg.Input(default_text=config.get("city", ""), key="-SELLER_CITY-", size=(25, 1))],
        [sg.Text("Postal Code"), sg.Input(default_text=config.get("postal_code", ""), key="-SELLER_POSTAL-", size=(10, 1))],
        [sg.Text("Email"), sg.Input(default_text=config.get("email", ""), key="-SELLER_EMAIL-", size=(30, 1))],
        [sg.Text("Phone"), sg.Input(default_text=config.get("phone", ""), key="-SELLER_PHONE-", size=(20, 1))],
        [sg.HorizontalSeparator()],
        [sg.Text("Bank Details", font=("Helvetica", 11, "bold"))],
        [sg.Text("IBAN *"), sg.Input(default_text=config.get("iban", ""), key="-SELLER_IBAN-", size=(25, 1))],
        [sg.Text("BIC/SWIFT *"), sg.Input(default_text=config.get("bic", ""), key="-SELLER_BIC-", size=(12, 1))],
        [sg.Text("Bank Name"), sg.Input(default_text=config.get("bank_name", ""), key="-SELLER_BANK-", size=(30, 1))],
        [sg.Button("Save as Default", key="-SAVE_CONFIG-", size=(15, 1)), 
         sg.Button("Clear", key="-CLEAR_CONFIG-", size=(15, 1))],
    ]


def create_buyer_tab():
    """Tab for buyer (customer) details"""
    return [
        [sg.Text("Buyer Details", font=("Helvetica", 12, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Checkbox("Same as My Company", key="-BUYER_SAME_SELLER-", enable_events=True),
         sg.Text("(copy data from My Company tab)")],
        [sg.Text("Company Name *"), sg.Input(key="-BUYER_NAME-", size=(40, 1))],
        [sg.Text("Registry Code"), sg.Input(key="-BUYER_REGISTRY-", size=(20, 1))],
        [sg.Text("VAT Number"), sg.Input(key="-BUYER_VAT-", size=(20, 1))],
        [sg.Text("Address"), sg.Input(key="-BUYER_ADDR-", size=(40, 1))],
        [sg.Text("City"), sg.Input(key="-BUYER_CITY-", size=(25, 1))],
        [sg.Text("Postal Code"), sg.Input(key="-BUYER_POSTAL-", size=(10, 1))],
        [sg.Text("Country (2 letters)"), sg.Input(default_text="EE", key="-BUYER_COUNTRY-", size=(5, 1))],
        [sg.Text("Email"), sg.Input(key="-BUYER_EMAIL-", size=(30, 1))],
    ]


def create_invoice_tab():
    """Tab for invoice details and line items"""
    return [
        [sg.Text("Invoice Details", font=("Helvetica", 12, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Invoice Number *"), sg.Input(key="-INV_NUMBER-", size=(20, 1)),
         sg.Text("Currency"),
         sg.Combo(["EUR", "USD", "GBP"], default_value="EUR", key="-CURRENCY-", size=(8, 1))],
        [sg.Text("Invoice Date *"), sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-INV_DATE-", size=(15, 1)),
         sg.Text("Due Date"), sg.Input(key="-DUE_DATE-", size=(15, 1), tooltip="Leave empty for immediate payment")],
        [sg.Text("Order Reference"), sg.Input(key="-ORDER_REF-", size=(20, 1))],
        [sg.HorizontalSeparator()],
        [sg.Text("Line Items", font=("Helvetica", 11, "bold"))],
        [sg.Text("Description", size=(30, 1)), sg.Text("Qty", size=(8, 1)), 
         sg.Text("Unit", size=(8, 1)), sg.Text("Price", size=(10, 1)), 
         sg.Text("VAT %", size=(8, 1))],
        [sg.Input(key="-LINE_DESC-", size=(30, 1)), 
         sg.Input(default_text="1", key="-LINE_QTY-", size=(8, 1)),
         sg.Combo(["pcs", "h", "km", "kg", "month", "year"], default_value="pcs", key="-LINE_UNIT-", size=(8, 1)),
         sg.Input(default_text="0.00", key="-LINE_PRICE-", size=(10, 1)),
         sg.Combo(["0", "20"], default_value="20", key="-LINE_VAT-", size=(8, 1))],
        [sg.Button("Add Line", key="-ADD_LINE-", size=(12, 1)),
         sg.Button("Remove Last", key="-REMOVE_LINE-", size=(12, 1))],
        [sg.Text("Lines added:", key="-LINES_COUNT-"), sg.Text("0 items")],
        [sg.HorizontalSeparator()],
        [sg.Text("Notes / Additional Info")],
        [sg.Multiline(key="-NOTES-", size=(60, 3))],
    ]


def create_output_tab():
    """Tab for output options"""
    return [
        [sg.Text("Output Options", font=("Helvetica", 12, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Output Directory"), 
         sg.Input(default_text=str(Path.home() / "Documents"), key="-OUTPUT_DIR-", size=(35, 1)),
         sg.FolderBrowse("Browse", key="-BROWSE_DIR-")],
        [sg.Checkbox("Generate XML (e-invoice)", default=True, key="-GEN_XML-")],
        [sg.Checkbox("Generate PDF (printable)", default=True, key="-GEN_PDF-")],
        [sg.HorizontalSeparator()],
        [sg.Button("Generate Invoice", key="-GENERATE-", size=(20, 2), 
                   button_color=("white", "#2c5282")),
         sg.Button("Clear Form", key="-CLEAR_ALL-", size=(15, 2))],
        [sg.HorizontalSeparator()],
        [sg.Text("Status:", key="-STATUS_LABEL-"), sg.Text("", key="-STATUS-", text_color="green")],
    ]


def parse_date(date_str):
    """Parse date from dd.mm.yyyy format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except:
        return None


def validate_inputs(values, lines):
    """Validate all required inputs"""
    errors = []
    
    # Seller required fields
    if not values["-SELLER_NAME-"].strip():
        errors.append("Company name is required")
    if not values["-SELLER_REGISTRY-"].strip():
        errors.append("Registry code is required")
    if not values["-SELLER_IBAN-"].strip():
        errors.append("IBAN is required")
    if not values["-SELLER_BIC-"].strip():
        errors.append("BIC/SWIFT is required")
    
    # Buyer required fields
    if not values["-BUYER_NAME-"].strip():
        errors.append("Buyer name is required")
    
    # Invoice details
    if not values["-INV_NUMBER-"].strip():
        errors.append("Invoice number is required")
    if not parse_date(values["-INV_DATE-"]):
        errors.append("Valid invoice date is required (dd.mm.yyyy)")
    if values["-DUE_DATE-"] and not parse_date(values["-DUE_DATE-"]):
        errors.append("Due date must be in dd.mm.yyyy format or empty")
    
    # At least one line
    if not lines:
        errors.append("Add at least one line item")
    
    return errors


def main():
    """Main GUI application"""
    
    # Line items storage
    lines = []
    
    # Database for accounting
    db = Database()
    
    # Layout
    layout = [
        [sg.Text("ee-invoice-generator", font=("Helvetica", 16, "bold")),
         sg.Text("Estonian e-invoice generator", font=("Helvetica", 10))],
        [sg.TabGroup([
            [sg.Tab("My Company", create_company_tab()),
             sg.Tab("Buyer", create_buyer_tab()),
             sg.Tab("Invoice", create_invoice_tab()),
             sg.Tab("Generate", create_output_tab()),
             sg.Tab("Accounting", create_accounting_tab(db))],
        ])],
    ]
    
    window = sg.Window("ee-invoice-generator", layout, size=(650, 600),
                       resizable=True, finalize=True)
    
    # Store line items in element
    window["-LINES_COUNT-"].update("Lines added: 0 items")
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        
        elif event == "-BUYER_SAME_SELLER-":
            if values["-BUYER_SAME_SELLER-"]:
                # Auto-fill buyer from seller config
                config = load_config()
                window["-BUYER_NAME-"].update(config.get("name", ""))
                window["-BUYER_REGISTRY-"].update(config.get("registry_code", ""))
                window["-BUYER_VAT-"].update(config.get("vat_number", ""))
                window["-BUYER_ADDR-"].update(config.get("address", ""))
                window["-BUYER_CITY-"].update(config.get("city", ""))
                window["-BUYER_POSTAL-"].update(config.get("postal_code", ""))
                window["-BUYER_COUNTRY-"].update("EE")
                window["-BUYER_EMAIL-"].update(config.get("email", ""))
            window["-STATUS-"].update("Buyer data copied from My Company" if values["-BUYER_SAME_SELLER-"] else "")
        
        elif event == "-SAVE_CONFIG-":
            config = {
                "name": values["-SELLER_NAME-"],
                "registry_code": values["-SELLER_REGISTRY-"],
                "vat_number": values["-SELLER_VAT-"],
                "address": values["-SELLER_ADDR-"],
                "city": values["-SELLER_CITY-"],
                "postal_code": values["-SELLER_POSTAL-"],
                "email": values["-SELLER_EMAIL-"],
                "phone": values["-SELLER_PHONE-"],
                "iban": values["-SELLER_IBAN-"],
                "bic": values["-SELLER_BIC-"],
                "bank_name": values["-SELLER_BANK-"],
            }
            save_config(config)
            window["-STATUS-"].update("Configuration saved!")
        
        elif event == "-CLEAR_CONFIG-":
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            window["-STATUS-"].update("Configuration cleared")
        
        elif event == "-ADD_LINE-":
            try:
                desc = values["-LINE_DESC-"].strip()
                qty = float(values["-LINE_QTY-"])
                unit = values["-LINE_UNIT-"]
                price = float(values["-LINE_PRICE-"])
                vat = float(values["-LINE_VAT-"]) / 100
                
                if not desc:
                    window["-STATUS-"].update("Description required", text_color="red")
                    continue
                if qty <= 0:
                    window["-STATUS-"].update("Quantity must be positive", text_color="red")
                    continue
                if price < 0:
                    window["-STATUS-"].update("Price cannot be negative", text_color="red")
                    continue
                
                # User enters TOTAL price (including VAT), we calculate net price
                gross_total = price
                net_unit_price = gross_total / (1 + vat) if vat > 0 else gross_total
                
                lines.append(InvoiceLine(
                    description=desc,
                    quantity=qty,
                    unit=unit,
                    unit_price=net_unit_price,
                    vat_rate=vat,
                ))
                
                window["-LINES_COUNT-"].update(f"Lines added: {len(lines)} items")
                window["-STATUS-"].update(f"Added: {desc[:30]}...", text_color="green")
                
                # Clear line inputs
                window["-LINE_DESC-"].update("")
                window["-LINE_QTY-"].update("1")
                window["-LINE_PRICE-"].update("0.00")
                
            except ValueError as e:
                window["-STATUS-"].update(f"Invalid number: {e}", text_color="red")
        
        elif event == "-REMOVE_LINE-":
            if lines:
                lines.pop()
                window["-LINES_COUNT-"].update(f"Lines added: {len(lines)} items")
                window["-STATUS-"].update(f"Removed last line ({len(lines)} remaining)")
        
        elif event == "-CLEAR_ALL-":
            lines.clear()
            window["-LINES_COUNT-"].update("Lines added: 0 items")
            window["-STATUS-"].update("Form cleared")
        
        elif event == "-GENERATE-":
            window["-STATUS-"].update("Validating...")
            
            errors = validate_inputs(values, lines)
            if errors:
                window["-STATUS-"].update(f"Errors: {errors[0]}", text_color="red")
                continue
            
            try:
                # Build invoice data
                seller = PartyDetails(
                    registry_code=values["-SELLER_REGISTRY-"].strip(),
                    name=values["-SELLER_NAME-"].strip(),
                    vat_number=values["-SELLER_VAT-"].strip() or None,
                    address=values["-SELLER_ADDR-"].strip() or None,
                    city=values["-SELLER_CITY-"].strip() or None,
                    postal_code=values["-SELLER_POSTAL-"].strip() or None,
                    country="EE",
                    email=values["-SELLER_EMAIL-"].strip() or None,
                    phone=values["-SELLER_PHONE-"].strip() or None,
                )
                
                buyer = PartyDetails(
                    registry_code=values["-BUYER_REGISTRY-"].strip() or None,
                    name=values["-BUYER_NAME-"].strip(),
                    vat_number=values["-BUYER_VAT-"].strip() or None,
                    address=values["-BUYER_ADDR-"].strip() or None,
                    city=values["-BUYER_CITY-"].strip() or None,
                    postal_code=values["-BUYER_POSTAL-"].strip() or None,
                    country=values["-BUYER_COUNTRY-"].strip() or "EE",
                    email=values["-BUYER_EMAIL-"].strip() or None,
                )
                
                payment = PaymentDetails(
                    iban=values["-SELLER_IBAN-"].strip(),
                    bic=values["-SELLER_BIC-"].strip(),
                    bank_name=values["-SELLER_BANK-"].strip() or None,
                )
                
                invoice_data = InvoiceData(
                    seller=seller,
                    buyer=buyer,
                    invoice_number=values["-INV_NUMBER-"].strip(),
                    invoice_date=parse_date(values["-INV_DATE-"]),
                    due_date=parse_date(values["-DUE_DATE-"]) if values["-DUE_DATE-"] else None,
                    lines=lines.copy(),
                    payment=payment,
                    order_reference=values["-ORDER_REF-"].strip() or None,
                    notes=values["-NOTES-"].strip() or None,
                    currency=values["-CURRENCY-"],
                )
                
                output_dir = Path(values["-OUTPUT_DIR-"])
                output_dir.mkdir(parents=True, exist_ok=True)
                
                invoice_num = values["-INV_NUMBER-"].strip().replace("/", "-")
                date_str = invoice_data.invoice_date.strftime("%Y%m%d")
                
                generated = []
                
                if values["-GEN_XML-"]:
                    xml_path = output_dir / f"invoice_{date_str}_{invoice_num}.xml"
                    gen = InvoiceGenerator(invoice_data)
                    gen.save(str(xml_path))
                    generated.append(f"XML: {xml_path.name}")
                
                if values["-GEN_PDF-"]:
                    pdf_path = output_dir / f"invoice_{date_str}_{invoice_num}.pdf"
                    pdf_gen = PDFGenerator(invoice_data)
                    pdf_gen.save(str(pdf_path))
                    generated.append(f"PDF: {pdf_path.name}")
                
                window["-STATUS-"].update(
                    f"Generated: {', '.join(generated)}",
                    text_color="green"
                )
                
            except Exception as e:
                window["-STATUS-"].update(f"Error: {str(e)}", text_color="red")
        
        else:
            # Check accounting tab events
            result = handle_accounting_event(event, values, db, window)
            if result:
                window["-STATUS-"].update(result, text_color="red" if "Error" in result else "green")
    
    window.close()


if __name__ == "__main__":
    main()