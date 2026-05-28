"""
Invoice History Tab - View all generated invoices
"""
import PySimpleGUI as sg
from datetime import date, datetime
import json


def create_invoice_history_tab(db):
    """Create invoice history tab layout"""
    
    return [
        [sg.Text("Invoice History / Arvete Ajalugu", font=("Helvetica", 12, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Filters
        [sg.Frame("Filters / Filtrid", [
            [sg.Text("From:"), sg.Input(default_text=date.today().replace(day=1).strftime("%d.%m.%Y"), 
                       key="-IH_FROM-", size=(12, 1)),
             sg.Text("To:"), sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-IH_TO-", size=(12, 1)),
             sg.Text("Status:"), sg.Combo(["all", "draft", "sent", "paid"], default_value="all", 
                       key="-IH_STATUS-", size=(10, 1)),
             sg.Button("Filter", key="-IH_FILTER-", size=(8, 1)),
             sg.Button("Refresh", key="-IH_REFRESH-", size=(10, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Invoice table
        [sg.Table(
            headings=["#", "Date", "Invoice No.", "Buyer", "Total (€)", "Status", "Actions"],
            values=[],
            key="-IH_TABLE-",
            size=(70, 12),
            col_widths=[4, 10, 12, 20, 10, 8, 10],
            justification="left",
            enable_click_events=True,
            tooltip="Click to select an invoice",
        )],
        
        [sg.HorizontalSeparator()],
        
        # Selected invoice details
        [sg.Frame("Invoice Details / Arvete Detailid", [
            [sg.Multiline(key="-IH_DETAILS-", size=(75, 15), disabled=True, 
                        font=("Courier", 9),
                        tooltip="Full invoice details - selectable text for copying")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Action buttons
        [sg.Button("View Details", key="-IH_VIEW-", size=(12, 1)),
         sg.Button("Copy to Clipboard", key="-IH_COPY-", size=(14, 1)),
         sg.Button("Export Selected", key="-IH_EXPORT-", size=(14, 1)),
         sg.Button("Delete", key="-IH_DELETE-", size=(10, 1), button_color=("white", "#c53030"))],
        
        [sg.Text("", key="-IH_STATUS-", text_color="green")],
    ]


def handle_invoice_history_event(event, values, db, window):
    """Handle events for invoice history tab"""
    
    if event == "-IH_REFRESH-" or event == "-IH_FILTER-":
        try:
            # Parse dates
            from_date = None
            to_date = None
            
            try:
                if values["-IH_FROM-"]:
                    from_date = datetime.strptime(values["-IH_FROM-"].strip(), "%d.%m.%Y").date()
                if values["-IH_TO-"]:
                    to_date = datetime.strptime(values["-IH_TO-"].strip(), "%d.%m.%Y").date()
            except ValueError:
                pass
            
            # Get invoices
            status = values.get("-IH_STATUS-", "all")
            invoices = db.list_invoices()
            
            # Filter
            if status != "all":
                invoices = [inv for inv in invoices if inv.get("status") == status]
            if from_date:
                invoices = [inv for inv in invoices if inv.get("invoice_date") >= from_date.isoformat()]
            if to_date:
                invoices = [inv for inv in invoices if inv.get("invoice_date") <= to_date.isoformat()]
            
            # Build table rows
            rows = []
            for i, inv in enumerate(invoices, 1):
                inv_date = inv.get("invoice_date", "")
                if inv_date and len(inv_date) > 10:
                    inv_date = inv_date[:10]
                if inv_date and "-" in inv_date:
                    inv_date = ".".join(reversed(inv_date.split("-")))  # Convert YYYY-MM-DD to DD.MM.YYYY
                
                row = [
                    str(i),
                    inv_date or "",
                    inv.get("invoice_number", ""),
                    inv.get("buyer_name", ""),
                    f"{inv.get('total_incl_vat', 0):.2f}",
                    inv.get("status", "draft"),
                ]
                rows.append(row)
            
            window["-IH_TABLE-"].update(rows)
            window["-IH_STATUS-"].update(f"Loaded {len(invoices)} invoices")
            
        except Exception as e:
            window["-IH_STATUS-"].update(f"Error: {str(e)}", text_color="red")
    
    elif event == "-IH_VIEW-" or event == "-IH_TABLE-":
        try:
            selected = values["-IH_TABLE-"]
            if not selected:
                window["-IH_STATUS-"].update("Select an invoice first", text_color="orange")
                return
            
            invoices = db.list_invoices()
            status = values.get("-IH_STATUS-", "all")
            if status != "all":
                invoices = [inv for inv in invoices if inv.get("status") == status]
            
            idx = selected[0]
            if idx < len(invoices):
                inv = invoices[idx]
                
                # Fetch full details including lines
                full_inv = db.get_invoice(invoice_id=inv.get("id"))
                
                # Build details text
                details = []
                details.append("=" * 60)
                details.append(f"INVOICE DETAILS")
                details.append("=" * 60)
                details.append(f"Invoice No.:     {inv.get('invoice_number', '')}")
                
                inv_date = inv.get("invoice_date", "")
                if inv_date and "-" in inv_date:
                    inv_date = ".".join(reversed(inv_date.split("-")))
                details.append(f"Date:           {inv_date}")
                
                if inv.get("due_date"):
                    due = inv.get("due_date", "")
                    if "-" in due:
                        due = ".".join(reversed(due.split("-")))
                    details.append(f"Due Date:       {due}")
                
                details.append(f"Status:         {inv.get('status', 'draft')}")
                details.append(f"Currency:       {inv.get('currency', 'EUR')}")
                details.append("")
                details.append("-" * 40)
                details.append("SELLER / MÜÜJA:")
                details.append(f"  Name:          {inv.get('seller_name', 'N/A')}")
                details.append(f"  Registry:      {inv.get('seller_registry', '')}")
                details.append(f"  VAT:           {inv.get('seller_vat', '')}")
                details.append(f"  Address:       {inv.get('seller_address', '')}")
                details.append("")
                details.append("-" * 40)
                details.append("BUYER / OSTJA:")
                details.append(f"  Name:          {inv.get('buyer_name', '')}")
                details.append(f"  Registry:      {inv.get('buyer_registry', '')}")
                details.append(f"  VAT:           {inv.get('buyer_vat', '')}")
                details.append(f"  Address:       {inv.get('buyer_address', '')}")
                details.append("")
                details.append("-" * 40)
                details.append("LINE ITEMS:")
                details.append(f"{'#':<4} {'Description':<30} {'Qty':>6} {'Unit':<5} {'Price':>10} {'VAT%':>5} {'Total':>12}")
                details.append("-" * 60)
                
                lines = inv.get("lines", full_inv.get("lines", []) if full_inv else [])
                for j, line in enumerate(lines, 1):
                    details.append(
                        f"{j:<4} {line.get('description', '')[:30]:<30} "
                        f"{line.get('quantity', 1):>6.2f} {line.get('unit', 'pcs'):<5} "
                        f"{line.get('unit_price', 0):>10.2f} {line.get('vat_rate', 0) * 100:>5.0f} "
                        f"{line.get('line_total', 0):>12.2f}"
                    )
                
                details.append("-" * 60)
                details.append(f"{'Subtotal:':>50} {inv.get('total_excl_vat', 0):>12.2f}")
                details.append(f"{'VAT Amount:':>50} {inv.get('vat_amount', 0):>12.2f}")
                details.append(f"{'TOTAL:':>50} {inv.get('total_incl_vat', 0):>12.2f}")
                
                if inv.get("notes"):
                    details.append("")
                    details.append("-" * 40)
                    details.append(f"Notes: {inv.get('notes', '')}")
                
                details.append("=" * 60)
                
                window["-IH_DETAILS-"].update("\n".join(details))
                window["-IH_STATUS-"].update("Invoice details loaded - select all text to copy")
        
        except Exception as e:
            window["-IH_STATUS-"].update(f"Error: {str(e)}", text_color="red")
    
    elif event == "-IH_COPY-":
        try:
            details = values.get("-IH_DETAILS-", "")
            if details:
                import pyperclip
                pyperclip.copy(details)
                window["-IH_STATUS-"].update("Copied to clipboard!")
            else:
                window["-IH_STATUS-"].update("No details to copy", text_color="orange")
        except ImportError:
            window["-IH_STATUS-"].update("Install pyperclip for clipboard support", text_color="orange")
        except Exception as e:
            window["-IH_STATUS-"].update(f"Error: {str(e)}", text_color="red")
    
    elif event == "-IH_DELETE-":
        try:
            selected = values["-IH_TABLE-"]
            if not selected:
                window["-IH_STATUS-"].update("Select an invoice first", text_color="orange")
                return
            
            invoices = db.list_invoices()
            status = values.get("-IH_STATUS-", "all")
            if status != "all":
                invoices = [inv for inv in invoices if inv.get("status") == status]
            
            idx = selected[0]
            if idx < len(invoices):
                inv = invoices[idx]
                inv_number = inv.get("invoice_number", "")
                
                # Delete from database
                from einvoice.accounting import Database
                db_conn = Database()
                db_conn.cursor.execute("DELETE FROM invoices WHERE id = ?", (inv.get("id"),))
                db_conn.conn.commit()
                
                window["-IH_STATUS-"].update(f"Deleted invoice {inv_number}")
                
                # Refresh table
                window["-IH_TABLE-"].update([])
                window["-IH_DETAILS-"].update("")
        
        except Exception as e:
            window["-IH_STATUS-"].update(f"Error: {str(e)}", text_color="red")


def handle_invoice_history_click(event, values, db, window):
    """Handle click events in invoice history"""
    if isinstance(event, tuple) and event[0] == "-IH_TABLE-":
        if event[2][0] >= 0:  # Row clicked
            handle_invoice_history_event("-IH_VIEW-", values, db, window)
