"""
Accountancy Tab - Full bookkeeping for Estonian OÜ
"""
import PySimpleGUI as sg
from datetime import date, datetime
from pathlib import Path

from einvoice.accounting import Database, Journal, FinancialReports
from einvoice.accounting.vat import VATRate, VATCalculator
from einvoice.accounting.accounts import CHART_OF_ACCOUNTS, get_account, search_accountes
from gui.invoice_history_tab import create_invoice_history_tab, handle_invoice_history_event


def create_accounting_tab(db: Database):
    """"Create the accounting tab layout"""
    
    return [
        [sg.Text("Buchhaltung / Бухгалтерия", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Sub-tabs: Journal, VAT, Reports, Chart of Accounts, Invoice History
        [sg.TabGroup([
            [sg.Tab("Journal", create_journal_layout(db)),
             sg.Tab("VAT (Käibemaks)", create_vat_layout(db)),
             sg.Tab("Reports (Aruanded)", create_reports_layout(db)),
             sg.Tab("Accounts (Kontod)", create_accounts_layout(db)),
             sg.Tab("Invoices (Arved)", create_invoice_history_tab(db)),
             sg.Tab("Settings (Einstellungen)", create_settings_layout(db))],
        ])],
    ]


def create_journal_layout(db: Database):
    """Journal entry interface"""
    return [
        [sg.Text("General Journal - Päevik", font=("Helvetica", 11, "bold"))],
        
        # Entry form
        [sg.Frame("New Entry / Uus kanne", [
            [sg.Text("Date:"), sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-J_DATE-", size=(12, 1)),
             sg.Text("Description:"), sg.Input(key="-J_DESC-", size=(30, 1)),
             sg.Text("Ref:"), sg.Input(key="-J_REF-", size=(15, 1))],
            
            [sg.Text("Account:"), sg.Input(key="-J_ACC-", size=(8, 1)),
             sg.Text("Amount:"), sg.Input(key="-J_AMOUNT-", size=(10, 1)),
             sg.Radio("Debit", "ENTRY_TYPE", key="-J_DEBIT-", default=True, size=(8, 1)),
             sg.Radio("Credit", "ENTRY_TYPE", key="-J_CREDIT-", size=(8, 1)),
             sg.Button("Add Line", key="-J_ADD_LINE-", size=(10, 1))],
            
            [sg.Text("Lines:", size=(6, 1)), sg.Listbox(values=[], key="-J_LINES-", size=(60, 5), 
                     select_mode=sg.SELECT_MODE_SINGLE)],
            [sg.Button("Clear Entry", key="-J_CLEAR-", size=(12, 1)),
             sg.Button("Save Entry", key="-J_SAVE-", size=(12, 1), button_color=("white", "#2c5282"))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Journal list
        [sg.Text("Journal Entries / Kanded", font=("Helvetica", 11, "bold"))],
        [sg.Text("From:"), sg.Input(default_text=date.today().replace(day=1).strftime("%d.%m.%Y"), 
                   key="-J_FROM-", size=(12, 1)),
         sg.Text("To:"), sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-J_TO-", size=(12, 1)),
         sg.Button("Filter", key="-J_FILTER-", size=(8, 1)),
         sg.Button("Refresh", key="-J_REFRESH-", size=(8, 1))],
        
        [sg.Table(
            headings=["#", "Date", "Description", "Reference", "Debit", "Credit"],
            values=[],
            key="-J_TABLE-",
            size=(60, 10),
            col_widths=[5, 10, 30, 10, 12, 12],
            justification="left",
        )],
    ]


def create_vat_layout(db: Database):
    """VAT tracking and reporting"""
    return [
        [sg.Text("VAT (Käibemaks) Calculator", font=("Helvetica", 11, "bold"))],
        
        [sg.Frame("Quick VAT Calculation", [
            [sg.Text("Amount (excl. VAT):"), sg.Input(key="-VAT_AMOUNT-", size=(12, 1)),
             sg.Text("VAT Rate:"),
             sg.Combo(["20%", "9%", "0%"], default_value="20%", key="-VAT_RATE-", size=(8, 1)),
             sg.Button("Calculate", key="-VAT_CALC-", size=(10, 1))],
            [sg.Text("", key="-VAT_RESULT-", size=(40, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Text("VAT Returns (KV-deklaratsioon)", font=("Helvetica", 11, "bold"))],
        [sg.Text("Period:"),
         sg.Combo(["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"], default_value="Q2 2026", key="-VAT_Q-", size=(10, 1)),
         sg.Button("Generate Report", key="-VAT_REPORT-", size=(12, 1))],
        
        [sg.Frame("VAT Report", [
            [sg.Text("Output VAT (Käibemaks välj):", size=(25, 1)), sg.Text("", key="-VAT_OUTPUT-")],
            [sg.Text("Input VAT (Käibemaks sisse):", size=(25, 1)), sg.Text("", key="-VAT_INPUT-")],
            [sg.Text("VAT Due / To Claim:", size=(25, 1)), sg.Text("", key="-VAT_DUE-", text_color="blue")],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Text("Recent VAT Transactions", font=("Helvetica", 10, "bold"))],
        [sg.Table(
            headings=["Date", "Invoice", "Description", "Excl VAT", "VAT", "Type"],
            values=[],
            key="-VAT_TABLE-",
            size=(60, 8),
            col_widths=[10, 10, 25, 10, 8, 8],
            justification="left",
        )],
    ]


def create_reports_layout(db: Database):
    """Financial reports"""
    return [
        [sg.Text("Financial Reports - Finantsaruanded", font=("Helvetica", 11, "bold"))],
        
        [sg.Frame("Report Period", [
            [sg.Text("From:"), sg.Input(default_text=date.today().replace(day=1).strftime("%d.%m.%Y"), 
                       key="-REP_FROM-", size=(12, 1)),
             sg.Text("To:"), sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-REP_TO-", size=(12, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Button("Balance Sheet (Bilanss)", key="-REP_BALANCE-", size=(20, 1)),
         sg.Button("Income Statement (Kasumiaruanne)", key="-REP_INCOME-", size=(25, 1)),
         sg.Button("Trial Balance (Proovibilanss)", key="-REP_TRIAL-", size=(20, 1))],
        
        [sg.HorizontalSeparator()],
        
        [sg.Text("Report Output:", font=("Helvetica", 10, "bold"))],
        [sg.Multiline(key="-REP_OUTPUT-", size=(70, 20), disabled=True, font=("Courier", 9))],
        
        [sg.Button("Export to PDF", key="-REP_PDF-", size=(15, 1)),
         sg.Button("Copy to Clipboard", key="-REP_COPY-", size=(15, 1))],
    ]


def create_accounts_layout(db: Database):
    """Chart of accounts browser"""
    return [
        [sg.Text("Chart of Accounts - Kontoplaan", font=("Helvetica", 11, "bold"))],
        
        [sg.Text("Search:"), sg.Input(key="-ACC_SEARCH-", size=(25, 1)),
         sg.Button("Search", key="-ACC_SEARCH_BTN-", size=(8, 1)),
         sg.Button("Show All", key="-ACC_SHOW_ALL-", size=(10, 1))],
        
        [sg.Text("Filter by Type:"),
         sg.Combo(["All", "Asset", "Liability", "Equity", "Revenue", "Expense"], 
                  default_value="All", key="-ACC_TYPE-", size=(12, 1)),
         sg.Button("Filter", key="-ACC_FILTER-", size=(8, 1))],
        
        [sg.Table(
            headings=["Account", "Name (ET)", "Name (RU)", "Type", "VAT"],
            values=[],
            key="-ACC_TABLE-",
            size=(70, 20),
            col_widths=[8, 25, 20, 10, 8],
            justification="left",
        )],
    ]


def create_settings_layout(db: Database):
    """Accountancy settings"""
    return [
        [sg.Text("Accounting Settings", font=("Helvetica", 11, "bold"))],
        
        [sg.Frame("Fiscal Year", [
            [sg.Text("Year:"), sg.Input(default_text=str(date.today().year), key="-FY_YEAR-", size=(6, 1)),
             sg.Text("Start Month:"), sg.Input(default_text="1", key="-FY_START-", size=(4, 1)),
             sg.Text("(1-12)")],
        ])],
        
        [sg.Frame("VAT Settings", [
            [sg.Text("Default VAT Rate:"),
             sg.Combo(["20%", "9%", "0%"], default_value="20%", key="-VAT_DEFAULT-", size=(8, 1))],
            [sg.Text("VAT Payment Frequency:"),
             sg.Combo(["Monthly", "Quarterly"], default_value="Quarterly", key="-VAT_FREQ-", size=(12, 1))],
        ])],
        
        [sg.Frame("Data Management", [
            [sg.Button("Export All Data", key="-EXP_ALL-", size=(15, 1)),
             sg.Button("Import Data", key="-IMP_DATA-", size=(15, 1)),
             sg.Button("Backup Database", key="-DB_BACKUP-", size=(15, 1))],
            [sg.Text("", key="-DB_STATUS-", size=(40, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        [sg.Button("Save Settings", key="-SAVE_SETTINGS-", size=(15, 1), 
                   button_color=("white", "#2c5282"))],
    ]


def handle_accounting_event(event, values, db: Database, window):
    """Handle events in the accounting tab"""
    
    if event == "-J_ADD_LINE-":
        # Add line to current journal entry
        acc = values["-J_ACC-"].strip()
        amount_str = values["-J_AMOUNT-"].strip()
        
        if not acc or not amount_str:
            return "Account and amount required"
        
        try:
            amount = float(amount_str)
        except ValueError:
            return "Invalid amount"
        
        entry_type = "DEBIT" if values["-J_DEBIT-"] else "CREDIT"
        
        # Get account name
        acc_obj = get_account(acc)
        acc_name = acc_obj.name_et if acc_obj else "Unknown"
        
        # Add to listbox
        current_lines = window["-J_LINES-"].get_list_values()
        new_line = f"{acc} {acc_name} | {amount:.2f} | {entry_type}"
        current_lines.append(new_line)
        window["-J_LINES-"].update(values=current_lines)
        
        # Clear inputs
        window["-J_ACC-"].update("")
        window["-J_AMOUNT-"].update("")
        
    elif event == "-J_CLEAR-":
        window["-J_DATE-"].update(date.today().strftime("%d.%m.%Y"))
        window["-J_DESC-"].update("")
        window["-J_REF-"].update("")
        window["-J_LINES-"].update(values=[])
    
    elif event == "-J_SAVE-":
        # Save journal entry
        try:
            entry_date = datetime.strptime(values["-J_DATE-"], "%d.%m.%Y").date()
        except ValueError:
            return "Invalid date format"
        
        if not values["-J_DESC-"].strip():
            return "Description required"
        
        lines = window["-J_LINES-"].get_list_values()
        if not lines:
            return "Add at least one line"
        
        return "Entry saved (full save not implemented - requires database integration)"
    
    elif event == "-J_REFRESH-" or event == "-J_FILTER-":
        # Refresh journal list
        return "Journal refresh (full implementation in production)"
    
    elif event == "-VAT_CALC-":
        try:
            amount = float(values["-VAT_AMOUNT-"])
            rate_str = values["-VAT_RATE-"]
            rate = {"20%": 0.20, "9%": 0.09, "0%": 0.0}[rate_str]
            
            vat = amount * rate
            total = amount + vat
            
            window["-VAT_RESULT-"].update(
                f"Amount: €{amount:.2f} + VAT ({rate*100:.0f}%): €{vat:.2f} = Total: €{total:.2f}"
            )
        except ValueError:
            return "Invalid amount"
    
    elif event == "-VAT_REPORT-":
        return "VAT report generation (full implementation in production)"
    
    elif event == "-REP_BALANCE-":
        return "Balance sheet (full implementation in production)"
    
    elif event == "-REP_INCOME-":
        return "Income statement (full implementation in production)"
    
    elif event == "-REP_TRIAL-":
        return "Trial balance (full implementation in production)"
    
    elif event == "-ACC_SEARCH_BTN-":
        query = values["-ACC_SEARCH-"].strip()
        if query:
            results = search_accountes(query)
            acc_data = [[a.number, a.name_et, a.name_ru, a.account_type.value, "Yes" if a.vat_eligible else "No"]
                       for a in results]
            window["-ACC_TABLE-"].update(values=acc_data)
    
    elif event == "-ACC_SHOW_ALL-":
        all_accounts = [[a.number, a.name_et, a.name_ru, a.account_type.value, "Yes" if a.vat_eligible else "No"]
                        for a in CHART_OF_ACCOUNTS.values()]
        window["-ACC_TABLE-"].update(values=all_accounts)
    
    elif event == "-DB_BACKUP-":
        try:
            backup_path = db.backup()
            window["-DB_STATUS-"].update(f"Backup saved: {backup_path.name}", text_color="green")
        except Exception as e:
            window["-DB_STATUS-"].update(f"Backup failed: {e}", text_color="red")
    
    elif event == "-SAVE_SETTINGS-":
        window["-DB_STATUS-"].update("Settings saved!", text_color="green")
    
    else:
        # Check invoice history tab events
        result = handle_invoice_history_event(event, values, db, window)
        if result:
            return result
    
    return None