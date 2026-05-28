"""
ee-invoice-generator GUI - Step-by-step wizard interface
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
from gui.invoice_history_tab import create_invoice_history_tab, handle_invoice_history_event


# Theme
sg.theme("LightBlue")

# Paths
CONFIG_DIR = Path.home() / ".ee-invoice-generator"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB = Database()


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def create_tooltip(text):
    """Create a hint text that appears on hover"""
    return sg.Text(text, tooltip=text, font=("Helvetica", 8, "italic"), text_color="#666")


# ============================================================
# STEP 1: My Company (Seller Details)
# ============================================================
def step1_layout():
    config = load_config()
    return [
        [sg.Text("Step 1: My Company", font=("Helvetica", 14, "bold"))],
        [sg.Text("Enter your company details - this data will be saved and used on all invoices")],
        [sg.HorizontalSeparator()],
        
        # Company Info
        [sg.Frame("Company Information", [
            [sg.Text("Company Name *", size=(15, 1)), 
             sg.Input(default_text=config.get("name", ""), key="-SELLER_NAME-", size=(40, 1),
                     tooltip="Your registered company name, e.g., 'XworCore OÜ'")],
            [sg.Text("Registry Code *", size=(15, 1)), 
             sg.Input(default_text=config.get("registry_code", ""), key="-SELLER_REGISTRY-", size=(20, 1),
                     tooltip="Estonian registry code (8 digits). Found in e-business register.")],
            [sg.Text("VAT Number", size=(15, 1)), 
             sg.Input(default_text=config.get("vat_number", ""), key="-SELLER_VAT-", size=(20, 1),
                     tooltip="KMKR number (e.g., EE123456789). Leave empty if not VAT registered.")],
            [sg.Text("Address", size=(15, 1)), 
             sg.Input(default_text=config.get("address", ""), key="-SELLER_ADDR-", size=(40, 1),
                     tooltip="Your legal address as registered in Estonia.")],
            [sg.Text("City", size=(15, 1)), 
             sg.Input(default_text=config.get("city", ""), key="-SELLER_CITY-", size=(25, 1))],
            [sg.Text("Postal Code", size=(15, 1)), 
             sg.Input(default_text=config.get("postal_code", ""), key="-SELLER_POSTAL-", size=(10, 1))],
            [sg.Text("Email", size=(15, 1)), 
             sg.Input(default_text=config.get("email", ""), key="-SELLER_EMAIL-", size=(30, 1),
                     tooltip="Email for receiving invoice replies.")],
            [sg.Text("Phone", size=(15, 1)), 
             sg.Input(default_text=config.get("phone", ""), key="-SELLER_PHONE-", size=(20, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Bank Info
        [sg.Frame("Bank Details for Payment", [
            [sg.Text("IBAN *", size=(15, 1)), 
             sg.Input(default_text=config.get("iban", ""), key="-SELLER_IBAN-", size=(25, 1),
                     tooltip="Your IBAN bank account. Format: EE00 1234 5678 9012 3456 7890")],
            [sg.Text("BIC/SWIFT *", size=(15, 1)), 
             sg.Input(default_text=config.get("bic", ""), key="-SELLER_BIC-", size=(12, 1),
                     tooltip="Bank SWIFT/BIC code (8 or 11 characters). E.g., HABAEE2S")],
            [sg.Text("Bank Name", size=(15, 1)), 
             sg.Input(default_text=config.get("bank_name", ""), key="-SELLER_BANK-", size=(30, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        [sg.Button("Save Company Data", key="-SAVE_CONFIG-", size=(15, 1)),
         sg.Button("Clear Data", key="-CLEAR_CONFIG-", size=(12, 1))],
    ]


# ============================================================
# STEP 2: Buyer Details
# ============================================================
def step2_layout():
    return [
        [sg.Text("Step 2: Customer Details", font=("Helvetica", 14, "bold"))],
        [sg.Text("Enter your customer's company information")],
        [sg.HorizontalSeparator()],
        
        [sg.Checkbox("Same as My Company", key="-BUYER_SAME_SELLER-", enable_events=True,
                   tooltip="Click to copy all data from Step 1 (your company)"),
         sg.Text("(copies your company data to buyer fields)")],
        
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Buyer Company Information", [
            [sg.Text("Company Name *", size=(15, 1)), 
             sg.Input(key="-BUYER_NAME-", size=(40, 1),
                     tooltip="Customer's registered company name")],
            [sg.Text("Registry Code", size=(15, 1)), 
             sg.Input(key="-BUYER_REGISTRY-", size=(20, 1),
                     tooltip="Customer's registry code (8 digits)")],
            [sg.Text("VAT Number", size=(15, 1)), 
             sg.Input(key="-BUYER_VAT-", size=(20, 1),
                     tooltip="Customer's KMKR/VAT number. Leave empty if not VAT registered.")],
            [sg.Text("Address", size=(15, 1)), 
             sg.Input(key="-BUYER_ADDR-", size=(40, 1))],
            [sg.Text("City", size=(15, 1)), 
             sg.Input(key="-BUYER_CITY-", size=(25, 1))],
            [sg.Text("Postal Code", size=(15, 1)), 
             sg.Input(key="-BUYER_POSTAL-", size=(10, 1))],
            [sg.Text("Country", size=(15, 1)), 
             sg.Input(default_text="EE", key="-BUYER_COUNTRY-", size=(5, 1),
                     tooltip="2-letter country code (EE for Estonia)")],
            [sg.Text("Email", size=(15, 1)), 
             sg.Input(key="-BUYER_EMAIL-", size=(30, 1),
                     tooltip="Customer's email for sending the invoice")],
        ])],
    ]


# ============================================================
# STEP 3: Invoice Details
# ============================================================
def step3_layout():
    db = Database()
    suggested_number = db.generate_invoice_number()
    
    return [
        [sg.Text("Step 3: Invoice Details", font=("Helvetica", 14, "bold"))],
        [sg.Text("Enter invoice details and line items (prices include VAT)")],
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Invoice Meta", [
            [sg.Text("Invoice Number *", size=(15, 1)), 
             sg.Input(default_text=suggested_number, key="-INV_NUMBER-", size=(20, 1),
                     tooltip="Unique invoice identifier. Auto-generated but you can change it."),
             sg.Text("Currency", size=(10, 1)), 
             sg.Combo(["EUR"], default_value="EUR", key="-CURRENCY-", size=(8, 1))],
            [sg.Text("Invoice Date *", size=(15, 1)), 
             sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-INV_DATE-", size=(15, 1),
                     tooltip="Date of invoice issuance. Format: DD.MM.YYYY"),
             sg.Text("Due Date", size=(10, 1)), 
             sg.Input(key="-DUE_DATE-", size=(15, 1),
                     tooltip="Payment due date. Leave empty if immediate payment.")],
            [sg.Text("Order Reference", size=(15, 1)), 
             sg.Input(key="-ORDER_REF-", size=(20, 1),
                     tooltip="Your internal order reference number (optional)")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Line Items (Amount = Total with VAT)", [
            [sg.Text("Enter price INCLUDING VAT - system will calculate net automatically", 
                    font=("Helvetica", 8, "italic"), text_color="#666")],
            [sg.Text("Description", size=(28, 1)), 
             sg.Text("Qty", size=(6, 1)), 
             sg.Text("Unit", size=(8, 1)), 
             sg.Text("Total (€)", size=(10, 1)), 
             sg.Text("VAT %", size=(8, 1))],
            [sg.Input(key="-LINE_DESC-", size=(28, 1), tooltip="What was sold/provided"),
             sg.Input(default_text="1", key="-LINE_QTY-", size=(6, 1), tooltip="Quantity"),
             sg.Combo(["pcs", "h", "km", "kg", "month", "year"], default_value="pcs", key="-LINE_UNIT-", size=(8, 1)),
             sg.Input(default_text="0.00", key="-LINE_PRICE-", size=(10, 1), tooltip="TOTAL price including VAT"),
             sg.Combo(["0", "20", "9"], default_value="20", key="-LINE_VAT-", size=(8, 1), tooltip="VAT rate in %")],
            [sg.Button("Add Line ↓", key="-ADD_LINE-", size=(12, 1), button_color=("white", "#2c5282")),
             sg.Button("Remove Last", key="-REMOVE_LINE-", size=(12, 1))],
            [sg.Text("Lines:", size=(6, 1)), sg.Listbox(values=[], key="-LINES_LIST-", size=(70, 6),
                   select_mode=sg.LIST_SELECT_SINGLE, tooltip="Added line items - double-click to remove")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Notes (Optional)", [
            [sg.Multiline(key="-NOTES-", size=(70, 3), tooltip="Additional terms, bank details, or notes")],
        ])],
    ]


# ============================================================
# STEP 4: Review & Generate
# ============================================================
def step4_layout():
    return [
        [sg.Text("Step 4: Review & Generate", font=("Helvetica", 14, "bold"))],
        [sg.Text("Review invoice data before generating XML and/or PDF")],
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Invoice Summary", [
            [sg.Multiline(key="-INVOICE_SUMMARY-", size=(75, 20), disabled=True, 
                        font=("Courier", 9), tooltip="Full invoice preview - select all to copy")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Output Options", [
            [sg.Text("Output Folder"), 
             sg.Input(default_text=str(Path.home() / "Documents"), key="-OUTPUT_DIR-", size=(40, 1)),
             sg.FolderBrowse("Browse")],
            [sg.Checkbox("Generate XML (e-invoice)", default=True, key="-GEN_XML-",
                       tooltip="Machine-readable invoice for digital submission"),
             sg.Checkbox("Generate PDF (printable)", default=True, key="-GEN_PDF-",
                       tooltip="PDF document for printing/sending via email")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Button("Generate Invoice", key="-GENERATE-", size=(18, 2), 
                   button_color=("white", "#2c5282"), font=("Helvetica", 11, "bold"),
                   tooltip="Generate invoice files (shows confirmation dialog first)"),
             sg.Button("Clear Form", key="-CLEAR_ALL-", size=(12, 1))],
        
        [sg.Text("", key="-STATUS-", text_color="green", font=("Helvetica", 10))],
    ]


# ============================================================
# Main window with buttons + wizard content
# ============================================================
def main():
    """Main wizard GUI"""
    
    # Line items storage
    lines = []
    current_step = [1]  # Mutable container for current step
    
    # Line items listbox reference
    lines_listbox = None
    
    # Top navigation buttons
    top_nav = [
        sg.Button("🏢 My Company", key="-NAV_COMPANY-", size=(15, 1)),
        sg.Button("📄 New Invoice", key="-NAV_INVOICE-", size=(15, 1)),
        sg.Button("📊 Accounting", key="-NAV_ACCOUNTING-", size=(15, 1)),
        sg.Button("📋 Invoice History", key="-NAV_HISTORY-", size=(15, 1)),
        sg.Text("", size=(20, 1)),  # Spacer
        sg.Text("v0.1.0", text_color="#999", font=("Helvetica", 8)),
    ]
    
    # Step indicator
    step_indicator = [
        sg.Text("Step 1", key="-STEP_LABEL-", font=("Helvetica", 10, "bold")),
        sg.Text("", key="-STEP_DESC-", font=("Helvetica", 9)),
    ]
    
    # Navigation buttons at bottom
    nav_buttons = [
        sg.Button("← Back", key="-BACK-", size=(12, 1), disabled=True),
        sg.Button("Next →", key="-NEXT-", size=(12, 1), button_color=("white", "#2c5282")),
    ]
    
    # Build layout
    main_content = [
        step1_layout()
    ]
    
    layout = [
        top_nav,
        [sg.HorizontalSeparator()],
        step_indicator,
        main_content,
        [sg.HorizontalSeparator()],
        nav_buttons,
    ]
    
    window = sg.Window("ee-invoice-generator v0.1.0", layout, size=(700, 700), resizable=True)
    
    # Store references
    window["-LINES_LIST-"] = sg.Listbox(values=[], key="-LINES_LIST-", size=(70, 6))
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        
        elif event in ("-NAV_COMPANY-", "-NAV_INVOICE-", "-NAV_ACCOUNTING-", "-NAV_HISTORY-"):
            # These open separate windows for now
            if event == "-NAV_COMPANY-":
                sg.popup("My Company data is entered in Step 1.\nClick 'New Invoice' to start a new invoice.")
            elif event == "-NAV_ACCOUNTING-":
                sg.popup_ok("Accounting module opens in the main window when you complete Steps 1-4.")
        
        elif event == "-BUYER_SAME_SELLER-":
            if values["-BUYER_SAME_SELLER-"]:
                config = load_config()
                window["-BUYER_NAME-"].update(config.get("name", ""))
                window["-BUYER_REGISTRY-"].update(config.get("registry_code", ""))
                window["-BUYER_VAT-"].update(config.get("vat_number", ""))
                window["-BUYER_ADDR-"].update(config.get("address", ""))
                window["-BUYER_CITY-"].update(config.get("city", ""))
                window["-BUYER_POSTAL-"].update(config.get("postal_code", ""))
                window["-BUYER_COUNTRY-"].update("EE")
                window["-BUYER_EMAIL-"].update(config.get("email", ""))
        
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
            sg.popup_ok("Company data saved!", title="Saved")
        
        elif event == "-CLEAR_CONFIG-":
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            sg.popup_ok("Company data cleared.")
        
        elif event == "-ADD_LINE-":
            try:
                desc = values["-LINE_DESC-"].strip()
                qty = float(values["-LINE_QTY-"])
                unit = values["-LINE_UNIT-"]
                price_gross = float(values["-LINE_PRICE-"])
                vat_rate = float(values["-LINE_VAT-"]) / 100
                
                if not desc:
                    sg.popup_error("Description required!")
                    continue
                if qty <= 0:
                    sg.popup_error("Quantity must be positive!")
                    continue
                if price_gross < 0:
                    sg.popup_error("Price cannot be negative!")
                    continue
                
                # User enters price INCLUDING VAT
                net_unit_price = price_gross / (1 + vat_rate) if vat_rate > 0 else price_gross
                
                lines.append(InvoiceLine(
                    description=desc,
                    quantity=qty,
                    unit=unit,
                    unit_price=net_unit_price,
                    vat_rate=vat_rate,
                ))
                
                # Update listbox
                list_values = []
                for i, line in enumerate(lines):
                    total = line.unit_price * (1 + line.vat_rate) * line.quantity
                    list_values.append(f"{i+1}. {line.description[:40]} | qty:{line.quantity} | €{total:.2f} ({line.vat_rate*100:.0f}% VAT)")
                window["-LINES_LIST-"].update(values=list_values)
                
                # Clear inputs
                window["-LINE_DESC-"].update("")
                window["-LINE_QTY-"].update("1")
                window["-LINE_PRICE-"].update("0.00")
                
            except ValueError as e:
                sg.popup_error(f"Invalid number: {e}")
        
        elif event == "-REMOVE_LINE-":
            if lines:
                lines.pop()
                list_values = []
                for i, line in enumerate(lines):
                    total = line.unit_price * (1 + line.vat_rate) * line.quantity
                    list_values.append(f"{i+1}. {line.description[:40]} | qty:{line.quantity} | €{total:.2f} ({line.vat_rate*100:.0f}% VAT)")
                window["-LINES_LIST-"].update(values=list_values)
        
        elif event == "-NEXT-":
            # Advance to next step (simplified - just show step 4 for "Generate" flow)
            # For now, Next just shows a different layout
            pass
        
        elif event == "-GENERATE-":
            # Validation
            errors = []
            if not values["-SELLER_NAME-"].strip():
                errors.append("Company name is required")
            if not values["-SELLER_REGISTRY-"].strip():
                errors.append("Your registry code is required")
            if not values["-SELLER_IBAN-"].strip():
                errors.append("IBAN is required")
            if not values["-SELLER_BIC-"].strip():
                errors.append("BIC is required")
            if not values["-BUYER_NAME-"].strip():
                errors.append("Buyer name is required")
            if not values["-INV_NUMBER-"].strip():
                errors.append("Invoice number is required")
            if not lines:
                errors.append("Add at least one line item")
            
            if errors:
                sg.popup_error("Please fix:\n• " + "\n• ".join(errors))
                continue
            
            # Confirmation dialog
            confirm = sg.popup_yes_no(
                f"Generate invoice {values['-INV_NUMBER-']}?\n\n"
                f"Buyer: {values['-BUYER_NAME-']}\n"
                f"Lines: {len(lines)} item(s)\n\n"
                f"Output: {values['-OUTPUT_DIR-']}\n"
                f"XML: {'Yes' if values['-GEN_XML-'] else 'No'}\n"
                f"PDF: {'Yes' if values['-GEN_PDF-'] else 'No'}",
                title="Confirm Generate"
            )
            if confirm != "Yes":
                continue
            
            try:
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
                
                inv_date = parse_date(values["-INV_DATE-"]) if values["-INV_DATE-"] else date.today()
                due_date = parse_date(values["-DUE_DATE-"]) if values["-DUE_DATE-"] else None
                
                invoice_data = InvoiceData(
                    seller=seller,
                    buyer=buyer,
                    invoice_number=values["-INV_NUMBER-"].strip(),
                    invoice_date=inv_date,
                    due_date=due_date,
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
                
                window["-STATUS-"].update(f"✓ Generated: {', '.join(generated)}", text_color="green")
                sg.popup_ok(f"Invoice generated!\n\n" + "\n".join(generated), title="Success")
                
            except Exception as e:
                sg.popup_error(f"Error: {str(e)}")
        
        elif event == "-CLEAR_ALL-":
            confirm = sg.popup_yes_no("Clear all invoice data?", title="Confirm Clear")
            if confirm == "Yes":
                lines.clear()
                window["-LINES_LIST-"].update(values=[])
                window["-INV_NUMBER-"].update(DB.generate_invoice_number())
                window["-NOTES-"].update("")
        
        # Accounting tab events
        result = handle_accounting_event(event, values, DB, window)
        if result:
            window["-STATUS-"].update(result, text_color=("red" if "Error" in result else "green"))
        
        # Invoice history events
        result = handle_invoice_history_event(event, values, DB, window)
        if result:
            window["-STATUS-"].update(result, text_color=("red" if "Error" in result else "green"))
    
    window.close()


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except:
        return None


if __name__ == "__main__":
    main()
