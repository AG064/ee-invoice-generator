"""
ee-invoice-generator GUI v0.3.0
Single window with tabs - language changes instantly
"""
import PySimpleGUI as sg
import json
from datetime import date, datetime
from pathlib import Path

from einvoice import InvoiceGenerator, PDFGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails
from einvoice.accounting import Database

# Language strings
LANG = {
    "en": {
        "app_title": "ee-invoice-generator",
        "my_company": "My Company",
        "new_invoice": "New Invoice",
        "accounting": "Accounting",
        "invoice_history": "History",
        "language_label": "Language",
        # Company tab
        "company_info": "Company Information",
        "company_name": "Company Name *",
        "registry_code": "Registry Code *",
        "vat_number": "VAT Number",
        "address": "Address",
        "city": "City",
        "postal_code": "Postal Code",
        "email": "Email",
        "phone": "Phone",
        "bank_details": "Bank Details",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Bank Name",
        "save_company": "Save",
        "company_saved": "Company data saved!",
        # Invoice tab
        "seller_details": "Seller (Your Company)",
        "buyer_details": "Buyer (Customer)",
        "buyer_same": "Same as My Company (copy)",
        "invoice_details": "Invoice Details",
        "invoice_number": "Invoice Number *",
        "currency": "Currency",
        "invoice_date": "Invoice Date *",
        "due_date": "Due Date",
        "order_ref": "Order Reference",
        "line_items": "Line Items (enter TOTAL price with VAT)",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "total_gross": "Total (€)",
        "vat_rate": "VAT %",
        "add_line": "Add Line",
        "remove_last": "Remove",
        "notes": "Notes",
        "notes_hint": "Additional terms, bank details, etc.",
        "output_options": "Output Options",
        "output_folder": "Output Folder",
        "gen_xml": "Generate XML (e-invoice)",
        "gen_pdf": "Generate PDF",
        "generate_invoice": "Generate Invoice",
        "clear_form": "Clear",
        "confirm_generate": "Generate invoice?\n\nBuyer: {buyer}\nLines: {lines}\n\nContinue?",
        "confirm_clear": "Clear all invoice data?",
        "success": "Invoice generated successfully!",
        "error": "Error",
        "validation_error": "Please fix:\n• {}",
        "lines_added": "lines",
        # Accounting tab
        "journal": "Journal",
        "vat_calc": "VAT Calculator",
        "reports": "Reports",
        "accounts": "Accounts",
        "acc_settings": "Settings",
        # History tab
        "invoice_history_title": "Invoice History",
        "filter_from": "From",
        "filter_to": "To",
        "filter_status": "Status",
        "filter_btn": "Filter",
        "refresh_btn": "Refresh",
        "view_details": "View",
        "copy_clipboard": "Copy",
        "export_selected": "Export",
        "delete_selected": "Delete",
        "no_history": "No invoices found",
        "details_copied": "Details copied to clipboard",
        # Tooltips
        "tip_company_name": "Your registered company name, e.g., XworCore OÜ",
        "tip_registry": "Estonian registry code (8 digits)",
        "tip_vat": "KMKR number (e.g., EE123456789)",
        "tip_address": "Your legal address in Estonia",
        "tip_email": "Email for invoice replies",
        "tip_phone": "Contact phone number",
        "tip_iban": "Your IBAN (e.g., EE00 1234 5678...)",
        "tip_bic": "Bank SWIFT/BIC (8 chars, e.g., HABAEE2S)",
        "tip_invoice_num": "Auto-generated. Change if needed.",
        "tip_invoice_date": "Format: DD.MM.YYYY",
        "tip_due_date": "Leave empty for immediate payment",
        "tip_total_w_vat": "Enter TOTAL price INCLUDING VAT - system calculates net",
        "tip_same": "Copy all My Company data to buyer fields",
    },
    "ru": {
        "app_title": "ee-invoice-generator",
        "my_company": "Моя Компания",
        "new_invoice": "Новый Счёт",
        "accounting": "Бухгалтерия",
        "invoice_history": "История",
        "language_label": "Язык",
        # Company tab
        "company_info": "Информация о Компании",
        "company_name": "Название *",
        "registry_code": "Рег. Номер *",
        "vat_number": "Номер НДС",
        "address": "Адрес",
        "city": "Город",
        "postal_code": "Индекс",
        "email": "Email",
        "phone": "Телефон",
        "bank_details": "Банковские Реквизиты",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Банк",
        "save_company": "Сохранить",
        "company_saved": "Данные компании сохранены!",
        # Invoice tab
        "seller_details": "Продавец (Ваша Компания)",
        "buyer_details": "Покупатель",
        "buyer_same": "Как Моя Компания",
        "invoice_details": "Детали Счёта",
        "invoice_number": "Номер Счёта *",
        "currency": "Валюта",
        "invoice_date": "Дата Счёта *",
        "due_date": "Срок Оплаты",
        "order_ref": "Номер Заказа",
        "line_items": "Позиции (вводите ЦЕНУ С НДС)",
        "description": "Описание",
        "qty": "Кол-во",
        "unit": "Ед.",
        "total_gross": "Итого (€)",
        "vat_rate": "НДС %",
        "add_line": "Добавить",
        "remove_last": "Удалить",
        "notes": "Заметки",
        "notes_hint": "Доп. условия, реквизиты...",
        "output_options": "Настройки Вывода",
        "output_folder": "Папка",
        "gen_xml": "XML (e-invoice)",
        "gen_pdf": "PDF",
        "generate_invoice": "Создать Счёт",
        "clear_form": "Очистить",
        "confirm_generate": "Создать счёт {buyer}?\nПозиций: {lines}\n\nПродолжить?",
        "confirm_clear": "Очистить все данные счёта?",
        "success": "Счёт успешно создан!",
        "error": "Ошибка",
        "validation_error": "Исправьте:\n• {}",
        "lines_added": "поз.",
        # Accounting tab
        "journal": "Журнал",
        "vat_calc": "Калькулятор НДС",
        "reports": "Отчёты",
        "accounts": "Счета",
        "acc_settings": "Настройки",
        # History tab
        "invoice_history_title": "История Счетов",
        "filter_from": "От",
        "filter_to": "До",
        "filter_status": "Статус",
        "filter_btn": "Фильтр",
        "refresh_btn": "Обновить",
        "view_details": "Детали",
        "copy_clipboard": "Копировать",
        "export_selected": "Экспорт",
        "delete_selected": "Удалить",
        "no_history": "Счета не найдены",
        "details_copied": "Детали скопированы",
        # Tooltips
        "tip_company_name": "Название вашей компании, напр. XworCore OÜ",
        "tip_registry": "Регистрационный код (8 цифр)",
        "tip_vat": "Номер KMKR (напр., EE123456789)",
        "tip_address": "Юридический адрес в Эстонии",
        "tip_email": "Email для ответов",
        "tip_phone": "Контактный телефон",
        "tip_iban": "Ваш IBAN (напр., EE00 1234...)",
        "tip_bic": "SWIFT/BIC банка (8 символов)",
        "tip_invoice_num": "Автоматически. Можно изменить.",
        "tip_invoice_date": "Формат: ДД.ММ.ГГГГ",
        "tip_due_date": "Оставьте пустым для немедленной оплаты",
        "tip_total_w_vat": "Вводите ЦЕНУ С НДС - система вычтет налог сама",
        "tip_same": "Скопировать все данные Моей Компании в поля покупателя",
    },
    "et": {
        "app_title": "ee-invoice-generator",
        "my_company": "Minu Ettevõte",
        "new_invoice": "Uus Arve",
        "accounting": "Raamatupidamine",
        "invoice_history": "Ajalugu",
        "language_label": "Keel",
        # Company tab
        "company_info": "Ettevõte",
        "company_name": "Ettevõte Nimi *",
        "registry_code": "Registrikood *",
        "vat_number": "KMKR",
        "address": "Aadress",
        "city": "Linn",
        "postal_code": "Postiindeks",
        "email": "Email",
        "phone": "Telefon",
        "bank_details": "Panga Andmed",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Pank",
        "save_company": "Salvesta",
        "company_saved": "Ettevõte salvestatud!",
        # Invoice tab
        "seller_details": "Müüja (Teie Ettevõte)",
        "buyer_details": "Ostja (Klient)",
        "buyer_same": "Same as Minu Ettevõte",
        "invoice_details": "Arve Andmed",
        "invoice_number": "Arve Number *",
        "currency": "Valuuta",
        "invoice_date": "Arve Kuupäev *",
        "due_date": "Tähtpäev",
        "order_ref": "Tellimuse Viide",
        "line_items": "Arve Read (sisesta HIND koos käibemaksuga)",
        "description": "Kirjeldus",
        "qty": "Kogus",
        "unit": "Ühik",
        "total_gross": "Kokku (€)",
        "vat_rate": "Käibemaks %",
        "add_line": "Lisa Rida",
        "remove_last": "Eemalda",
        "notes": "Märkused",
        "notes_hint": "Lisatingimused, pangarekvisitid...",
        "output_options": "Väljundi Seaded",
        "output_folder": "Kaust",
        "gen_xml": "XML (e-arve)",
        "gen_pdf": "PDF",
        "generate_invoice": "Genereeri Arve",
        "clear_form": "Tühjenda",
        "confirm_generate": "Genereeri arve {buyer}?\nLire: {lines}\n\nJätkata?",
        "confirm_clear": "Tühjenda kõik arve andmed?",
        "success": "Arve edukalt genereeritud!",
        "error": "Viga",
        "validation_error": "Palun paranda:\n• {}",
        "lines_added": "rida",
        # Accounting tab
        "journal": "Päevik",
        "vat_calc": "Käibemaksu Kalkulaator",
        "reports": "Aruanded",
        "accounts": "Kontod",
        "acc_settings": "Seaded",
        # History tab
        "invoice_history_title": "Arvete Ajalugu",
        "filter_from": "Alates",
        "filter_to": "Kuni",
        "filter_status": "Staatus",
        "filter_btn": "Filtreeri",
        "refresh_btn": "Uuenda",
        "view_details": "Detailid",
        "copy_clipboard": "Kopeeri",
        "export_selected": " Eksport",
        "delete_selected": "Kustuta",
        "no_history": "Arveid ei leitud",
        "details_copied": "Detailid kopeeritud",
        # Tooltips
        "tip_company_name": "Teie registreeritud ettevõtte nimi",
        "tip_registry": "Eesti registrikood (8 numbrit)",
        "tip_vat": "KMKR number (näit. EE123456789)",
        "tip_address": "Juriidiline aadress",
        "tip_email": "Email arvete vastuseks",
        "tip_phone": "Kontakt-telefon",
        "tip_iban": "Teie IBAN (näit. EE00 1234...)",
        "tip_bic": "Panga SWIFT/BIC (8 tähega)",
        "tip_invoice_num": "Genereeritakse automaatselt. Võite muuta.",
        "tip_invoice_date": "Vorming: PP.KK.AAAA",
        "tip_due_date": "Tühjaks koheselt tasumiseks",
        "tip_total_w_vat": "Sisesta HIND koos käibemaksuga - süsteem arvutab netohinna ise",
        "tip_same": "Kopeeri Minu Ettevõte andmed ostja väljadele",
    },
}

# Global state
CONFIG_DIR = Path.home() / ".ee-invoice-generator"
CONFIG_FILE = CONFIG_DIR / "config.json"
LANG_FILE = CONFIG_DIR / "language.json"
DB = Database()
CURRENT_LANG = ["en"]


def tr(key):
    return LANG[CURRENT_LANG[0]].get(key, key)


def set_lang(lang):
    CURRENT_LANG[0] = lang
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LANG_FILE, "w") as f:
        json.dump({"lang": lang}, f)


def load_lang():
    if LANG_FILE.exists():
        try:
            with open(LANG_FILE) as f:
                lang = json.load(f).get("lang", "en")
                if lang in LANG:
                    CURRENT_LANG[0] = lang
        except:
            pass


load_lang()


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


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except:
        return None


def build_company_tab():
    config = load_config()
    return [
        [sg.Text(tr("company_info"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        [sg.Frame(tr("company_info"), [
            [sg.Text(tr("company_name"), size=(15, 1)),
             sg.Input(default_text=config.get("name", ""), key="-C_NAME-", size=(40, 1),
                     tooltip=tr("tip_company_name"))],
            [sg.Text(tr("registry_code"), size=(15, 1)),
             sg.Input(default_text=config.get("registry_code", ""), key="-C_REG-", size=(20, 1),
                     tooltip=tr("tip_registry"))],
            [sg.Text(tr("vat_number"), size=(15, 1)),
             sg.Input(default_text=config.get("vat_number", ""), key="-C_VAT-", size=(20, 1),
                     tooltip=tr("tip_vat"))],
            [sg.Text(tr("address"), size=(15, 1)),
             sg.Input(default_text=config.get("address", ""), key="-C_ADDR-", size=(40, 1),
                     tooltip=tr("tip_address"))],
            [sg.Text(tr("city"), size=(15, 1)),
             sg.Input(default_text=config.get("city", ""), key="-C_CITY-", size=(25, 1))],
            [sg.Text(tr("postal_code"), size=(15, 1)),
             sg.Input(default_text=config.get("postal_code", ""), key="-C_POSTAL-", size=(10, 1))],
            [sg.Text(tr("email"), size=(15, 1)),
             sg.Input(default_text=config.get("email", ""), key="-C_EMAIL-", size=(30, 1),
                     tooltip=tr("tip_email"))],
            [sg.Text(tr("phone"), size=(15, 1)),
             sg.Input(default_text=config.get("phone", ""), key="-C_PHONE-", size=(20, 1),
                     tooltip=tr("tip_phone"))],
        ])],
        
        [sg.Frame(tr("bank_details"), [
            [sg.Text(tr("iban"), size=(15, 1)),
             sg.Input(default_text=config.get("iban", ""), key="-C_IBAN-", size=(25, 1),
                     tooltip=tr("tip_iban"))],
            [sg.Text(tr("bic"), size=(15, 1)),
             sg.Input(default_text=config.get("bic", ""), key="-C_BIC-", size=(12, 1),
                     tooltip=tr("tip_bic"))],
            [sg.Text(tr("bank_name"), size=(15, 1)),
             sg.Input(default_text=config.get("bank_name", ""), key="-C_BANK-", size=(30, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        [sg.Button(tr("save_company"), key="-SAVE_COMPANY-", size=(14, 1), 
                   button_color=("white", "#2c5282"))],
        [sg.Text("", key="-COMPANY_STATUS-", text_color="green")],
    ]


def build_invoice_tab(window, lines):
    """Build invoice creation tab"""
    # Get default values from saved company
    config = load_config()
    
    return [
        [sg.Text(tr("new_invoice"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Seller section with collapsed frame
        [sg.Frame(tr("seller_details"), [
            [sg.Text(tr("company_name"), size=(15, 1)),
             sg.Input(default_text=config.get("name", ""), key="-INV_S_NAME-", size=(30, 1),
                     tooltip=tr("tip_company_name"))],
            [sg.Text(tr("registry_code"), size=(15, 1)),
             sg.Input(default_text=config.get("registry_code", ""), key="-INV_S_REG-", size=(15, 1),
                     tooltip=tr("tip_registry"))],
            [sg.Text(tr("vat_number"), size=(15, 1)),
             sg.Input(default_text=config.get("vat_number", ""), key="-INV_S_VAT-", size=(15, 1),
                     tooltip=tr("tip_vat"))],
            [sg.Text("IBAN", size=(15, 1)),
             sg.Input(default_text=config.get("iban", ""), key="-INV_S_IBAN-", size=(20, 1),
                     tooltip=tr("tip_iban"))],
            [sg.Text("BIC", size=(15, 1)),
             sg.Input(default_text=config.get("bic", ""), key="-INV_S_BIC-", size=(10, 1),
                     tooltip=tr("tip_bic"))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Buyer section
        [sg.Frame(tr("buyer_details"), [
            [sg.Checkbox(tr("buyer_same"), key="-BUYER_SAME-", enable_events=True,
                        tooltip=tr("tip_same")), sg.Text(tr("buyer_same"), text_color="#666")],
            [sg.Text(tr("company_name"), size=(15, 1)),
             sg.Input(key="-INV_B_NAME-", size=(30, 1))],
            [sg.Text(tr("registry_code"), size=(15, 1)),
             sg.Input(key="-INV_B_REG-", size=(15, 1))],
            [sg.Text(tr("vat_number"), size=(15, 1)),
             sg.Input(key="-INV_B_VAT-", size=(15, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Invoice details
        [sg.Frame(tr("invoice_details"), [
            [sg.Text(tr("invoice_number"), size=(15, 1)),
             sg.Input(default_text=DB.generate_invoice_number(), key="-INV_NUM-", size=(18, 1),
                     tooltip=tr("tip_invoice_num")),
             sg.Text(tr("currency"), size=(10, 1)),
             sg.Combo(["EUR"], default_value="EUR", key="-INV_CURR-", size=(8, 1))],
            [sg.Text(tr("invoice_date"), size=(15, 1)),
             sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-INV_DATE-", size=(15, 1),
                     tooltip=tr("tip_invoice_date")),
             sg.Text(tr("due_date"), size=(10, 1)),
             sg.Input(key="-INV_DUE-", size=(15, 1), tooltip=tr("tip_due_date"))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Line items
        [sg.Frame(tr("line_items"), [
            [sg.Text(tr("tip_total_w_vat"), font=("Helvetica", 8, "italic"), text_color="#666")],
            [sg.Text(tr("description"), size=(25, 1)),
             sg.Text(tr("qty"), size=(6, 1)),
             sg.Text(tr("unit"), size=(7, 1)),
             sg.Text(tr("total_gross"), size=(10, 1)),
             sg.Text(tr("vat_rate"), size=(8, 1))],
            [sg.Input(key="-L_DESC-", size=(25, 1), tooltip=tr("description")),
             sg.Input(default_text="1", key="-L_QTY-", size=(6, 1)),
             sg.Combo(["pcs", "h", "km", "kg", "month", "year"], default_value="pcs", key="-L_UNIT-", size=(7, 1)),
             sg.Input(default_text="0.00", key="-L_PRICE-", size=(10, 1), tooltip=tr("tip_total_w_vat")),
             sg.Combo(["0", "20", "9"], default_value="20", key="-L_VAT-", size=(8, 1))],
            [sg.Button(tr("add_line"), key="-ADD_LINE-", size=(10, 1), button_color=("white", "#2c5282")),
             sg.Button(tr("remove_last"), key="-REMOVE_LAST-", size=(10, 1))],
            [sg.Text(f"0 {tr('lines_added')}", key="-LINES_COUNT-", text_color="#666")],
            [sg.Listbox(values=[], key="-LINES_LIST-", size=(75, 6))],
        ])],
        
        [sg.Frame(tr("notes"), [
            [sg.Multiline(key="-INV_NOTES-", size=(75, 3), tooltip=tr("notes_hint"))],
        ])],
        
        [sg.HorizontalSeparator()],
        
        # Output
        [sg.Frame(tr("output_options"), [
            [sg.Text(tr("output_folder")),
             sg.Input(default_text=str(Path.home() / "Documents"), key="-OUT_DIR-", size=(35, 1)),
             sg.FolderBrowse()],
            [sg.Checkbox(tr("gen_xml"), default=True, key="-GEN_XML-"),
             sg.Checkbox(tr("gen_pdf"), default=True, key="-GEN_PDF-")],
        ])],
        
        [sg.Button(tr("generate_invoice"), key="-GENERATE-", size=(16, 2),
                  button_color=("white", "#2c5282"), font=("Helvetica", 10, "bold")),
         sg.Button(tr("clear_form"), key="-CLEAR_INV-", size=(10, 1))],
        
        [sg.Text("", key="-INV_STATUS-", text_color="green")],
    ]


def build_accounting_tab():
    return [
        [sg.Text(tr("accounting"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.TabGroup([
            [sg.Tab(tr("journal"), [
                [sg.Text("Double-entry bookkeeping journal", font=("Helvetica", 10, "italic"), text_color="#666")],
                [sg.Button("Open Full Journal", key="-OPEN_JOURNAL-", size=(15, 1))],
            ])],
            [sg.Tab(tr("vat_calc"), [
                [sg.Text("VAT calculation tools", font=("Helvetica", 10, "italic"), text_color="#666")],
            ])],
            [sg.Tab(tr("reports"), [
                [sg.Text("Financial reports", font=("Helvetica", 10, "italic"), text_color="#666")],
            ])],
            [sg.Tab(tr("accounts"), [
                [sg.Text("Chart of accounts", font=("Helvetica", 10, "italic"), text_color="#666")],
            ])],
        ])],
    ]


def build_history_tab():
    return [
        [sg.Text(tr("invoice_history_title"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Filters", [
            [sg.Text(tr("filter_from")),
             sg.Input(default_text=date.today().replace(day=1).strftime("%d.%m.%Y"), 
                      key="-HIST_FROM-", size=(12, 1)),
             sg.Text(tr("filter_to")),
             sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-HIST_TO-", size=(12, 1)),
             sg.Button(tr("filter_btn"), key="-HIST_FILTER-", size=(10, 1)),
             sg.Button(tr("refresh_btn"), key="-HIST_REFRESH-", size=(10, 1))],
        ])],
        
        [sg.Table(
            headings=["#", "Date", "Invoice #", "Buyer", "Total (€)", "Status"],
            values=[],
            key="-HIST_TABLE-",
            size=(70, 12),
            col_widths=[4, 10, 12, 20, 10, 8],
        )],
        
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Details", [
            [sg.Multiline(key="-HIST_DETAILS-", size=(75, 15), disabled=True, 
                         font=("Courier", 9), tooltip="Invoice details - selectable")],
        ])],
        
        [sg.Button(tr("view_details"), key="-HIST_VIEW-", size=(10, 1)),
         sg.Button(tr("copy_clipboard"), key="-HIST_COPY-", size=(12, 1)),
         sg.Button(tr("export_selected"), key="-HIST_EXPORT-", size=(10, 1)),
         sg.Button(tr("delete_selected"), key="-HIST_DELETE-", size=(10, 1),
                  button_color=("white", "#c53030"))],
        
        [sg.Text("", key="-HIST_STATUS-", text_color="green")],
    ]


def refresh_history(window):
    """Refresh invoice history table"""
    try:
        invoices = DB.list_invoices()
        rows = []
        for i, inv in enumerate(invoices, 1):
            inv_date = inv.get("invoice_date", "") or ""
            if "-" in inv_date:
                inv_date = ".".join(reversed(inv_date.split("-")[:3]))
            rows.append([
                str(i), inv_date, inv.get("invoice_number", ""),
                inv.get("buyer_name", ""), f"{inv.get('total_incl_vat', 0):.2f}",
                inv.get("status", "draft")
            ])
        window["-HIST_TABLE-"].update(rows)
        window["-HIST_STATUS-"].update(f"Loaded {len(invoices)} invoices")
    except Exception as e:
        window["-HIST_STATUS-"].update(f"Error: {e}", text_color="red")


def main():
    """Main single-window app with tabbed navigation"""
    lines = []
    
    while True:
        # Build tab content based on current language
        company_tab = build_company_tab()
        invoice_tab = build_invoice_tab(None, lines)
        accounting_tab = build_accounting_tab()
        history_tab = build_history_tab()
        
        lang_names = {"en": "English", "ru": "Русский", "et": "Eesti"}
        
        layout = [
            # Header with language selector
            [sg.Text("ee-invoice-generator", font=("Helvetica", 16, "bold")),
             sg.Text("  |  "),
             sg.Text(tr("language_label") + ":"),
             sg.Combo(sorted(lang_names.values()), 
                     default_value=lang_names[CURRENT_LANG[0]],
                     key="-LANG_SELECT-", size=(10, 1), enable_events=True),
             sg.Text("", size=(10, 1)),
             sg.Text("v0.3.0", text_color="#999")],
            
            [sg.HorizontalSeparator()],
            
            # Tabbed main content
            [sg.TabGroup([
                [sg.Tab(tr("my_company"), company_tab),
                 sg.Tab(tr("new_invoice"), invoice_tab),
                 sg.Tab(tr("accounting"), accounting_tab),
                 sg.Tab(tr("invoice_history"), history_tab)],
            ], key="-MAIN_TABS-")],
        ]
        
        # Create or update window
        if __name__ == "__main__" or True:
            window = sg.Window("ee-invoice-generator", layout, size=(700, 750), resizable=True)
        
        # Main event loop
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, "Exit"):
                window.close()
                return
            
            # Language change - rebuild window
            elif event == "-LANG_SELECT-":
                lang_map = {v: k for k, v in lang_names.items()}
                new_lang = lang_map.get(values["-LANG_SELECT-"], "en")
                if new_lang != CURRENT_LANG[0]:
                    set_lang(new_lang)
                    window.close()
                    break  # Break to outer loop to rebuild with new language
            
            # Company tab events
            elif event == "-SAVE_COMPANY-":
                c = {
                    "name": values["-C_NAME-"].strip(),
                    "registry_code": values["-C_REG-"].strip(),
                    "vat_number": values["-C_VAT-"].strip(),
                    "address": values["-C_ADDR-"].strip(),
                    "city": values["-C_CITY-"].strip(),
                    "postal_code": values["-C_POSTAL C-"].strip(),
                    "email": values["-C_EMAIL-"].strip(),
                    "phone": values["-C_PHONE-"].strip(),
                    "iban": values["-C_IBAN-"].strip(),
                    "bic": values["-C_BIC-"].strip(),
                    "bank_name": values["-C_BANK-"].strip(),
                }
                save_config(c)
                window["-COMPANY_STATUS-"].update(tr("company_saved"))
            
            # Invoice tab events
            elif event == "-BUYER_SAME-":
                if values["-BUYER_SAME-"]:
                    config = load_config()
                    window["-INV_B_NAME-"].update(config.get("name", ""))
                    window["-INV_B_REG-"].update(config.get("registry_code", ""))
                    window["-INV_B_VAT-"].update(config.get("vat_number", ""))
            
            elif event == "-ADD_LINE-":
                try:
                    desc = values["-L_DESC-"].strip()
                    qty = float(values["-L_QTY-"])
                    unit = values["-L_UNIT-"]
                    price_gross = float(values["-L_PRICE-"])
                    vat_rate = float(values["-L_VAT-"]) / 100
                    
                    if not desc:
                        sg.popup_error("Description required!")
                        continue
                    if qty <= 0:
                        sg.popup_error("Quantity must be positive!")
                        continue
                    if price_gross < 0:
                        sg.popup_error("Price cannot be negative!")
                        continue
                    
                    net = price_gross / (1 + vat_rate) if vat_rate > 0 else price_gross
                    lines.append(InvoiceLine(
                        description=desc, quantity=qty, unit=unit,
                        unit_price=net, vat_rate=vat_rate,
                    ))
                    
                    list_vals = []
                    for i, ln in enumerate(lines):
                        g = ln.unit_price * (1 + ln.vat_rate) * ln.quantity
                        list_vals.append(f"{i+1}. {ln.description[:35]} | qty:{ln.quantity} | €{g:.2f}")
                    window["-attrs"]["-LINES_LIST-"].update(values=list_vals) if hasattr(window, 'dict') else window["-LINES_LIST-"].update(values=list_vals)
                    window["-LINES_COUNT-"].update(f"{len(lines)} {tr('lines_added')}")
                    
                    window["-L_DESC-"].update("")
                    window["-L_QTY-"].update("1")
                    window["-L_PRICE-"].update("0.00")
                except ValueError as e:
                    sg.popup_error(f"Invalid number: {e}")
            
            elif event == "-REMOVE_LAST-":
                if lines:
                    lines.pop()
                    list_vals = []
                    for i, ln in enumerate(lines):
                        g = ln.unit_price * (1 + ln.vat_rate) * ln.quantity
                        list_vals.append(f"{i+1}. {ln.description[:35]} | qty:{ln.quantity} | €{g:.2f}")
                    window["-LINES_LIST-"].update(values=list_vals)
                    window["-LINES_COUNT-"].update(f"{len(lines)} {tr('lines_added')}")
            
            elif event == "-GENERATE-":
                # Validation
                errors = []
                if not values["-INV_S_NAME-"].strip():
                    errors.append(tr("company_name"))
                if not values["-INV_S_REG-"].strip():
                    errors.append(tr("registry_code"))
                if not values["-INV_S_IBAN-"].strip():
                    errors.append("IBAN")
                if not values["-INV_S_BIC-"].strip():
                    errors.append("BIC")
                if not values["-INV_B_NAME-"].strip():
                    errors.append(tr("buyer_details"))
                if not values["-INV_NUM-"].strip():
                    errors.append(tr("invoice_number"))
                if not lines:
                    errors.append(f"Add at least 1 {tr('lines_added')}")
                
                if errors:
                    sg.popup_error(tr("validation_error").format("\n• ".join(errors)))
                    continue
                
                # Confirmation
                confirm = sg.popup_yes_no(
                    tr("confirm_generate").format(
                        buyer=values["-INV_B_NAME-"],
                        lines=f"{len(lines)} {tr('lines_added')}"
                    ),
                    title=tr("generate_invoice")
                )
                if confirm != "Yes":
                    continue
                
                try:
                    seller = PartyDetails(
                        registry_code=values["-INV_S_REG-"].strip(),
                        name=values["-INV_S_NAME-"].strip(),
                        vat_number=values["-INV_S_VAT-"].strip() or None,
                        address=None, city=None, postal_code=None, country="EE",
                        email=values.get("-C_EMAIL-", "").strip() or None,
                        phone=values.get("-C_PHONE-", "").strip() or None,
                    )
                    buyer = PartyDetails(
                        registry_code=values["-INV_B_REG-"].strip() or None,
                        name=values["-INV_B_NAME-"].strip(),
                        vat_number=values["-INV_B_VAT-"].strip() or None,
                        address=None, city=None, postal_code=None, country="EE",
                        email=None,
                    )
                    payment = PaymentDetails(
                        iban=values["-INV_S_IBAN-"].strip(),
                        bic=values["-INV_S_BIC-"].strip(),
                        bank_name=None,
                    )
                    
                    inv_date = parse_date(values["-INV_DATE-"]) if values["-INV_DATE-"] else date.today()
                    due_date = parse_date(values["-INV_DUE-"]) if values["-INV_DUE-"] else None
                    
                    invoice_data = InvoiceData(
                        seller=seller, buyer=buyer,
                        invoice_number=values["-INV_NUM-"].strip(),
                        invoice_date=inv_date, due_date=due_date,
                        lines=lines.copy(), payment=payment,
                        order_reference=None,
                        notes=values["-INV_NOTES-"].strip() or None,
                        currency=values["-INV_CURR-"],
                    )
                    
                    output_dir = Path(values["-OUT_DIR-"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    inv_num = values["-INV_NUM-"].strip().replace("/", "-")
                    date_str = inv_date.strftime("%Y%m%d")
                    
                    generated = []
                    if values["-GEN_XML-"]:
                        xml_path = output_dir / f"invoice_{date_str}_{inv_num}.xml"
                        InvoiceGenerator(invoice_data).save(str(xml_path))
                        generated.append(f"XML: {xml_path.name}")
                    if values["-GEN_PDF-"]:
                        pdf_path = output_dir / f"invoice_{date_str}_{inv_num}.pdf"
                        PDFGenerator(invoice_data).save(str(pdf_path))
                        generated.append(f"PDF: {pdf_path.name}")
                    
                    window["-INV_STATUS-"].update(tr("success") + f" {', '.join(generated)}", text_color="green")
                    sg.popup_ok(tr("success") + "\n\n" + "\n".join(generated))
                    
                except Exception as e:
                    sg.popup_error(f"{tr("error")}: {str(e)}")
            
            elif event == "-CLEAR_INV-":
                if sg.popup_yes_no(tr("confirm_clear"), title=tr("clear_form")) == "Yes":
                    lines.clear()
                    window["-LINES_LIST-"].update(values=[])
                    window["-LINES_COUNT-"].update(f"0 {tr('lines_added')}")
                    window["-INV_NUM-"].update(DB.generate_invoice_number())
                    window["-INV_NOTES-"].update("")
                    window["-INV_STATUS-"].update("")
            
            # History tab events
            elif event == "-HIST_REFRESH-":
                refresh_history(window)
            
            elif event == "-HIST_FILTER-":
                refresh_history(window)
            
            elif event == "-HIST_VIEW-":
                selected = values["-HIST_TABLE-"]
                if selected:
                    invoices = DB.list_invoices()
                    idx = selected[0]
                    if idx < len(invoices):
                        inv = invoices[idx]
                        lines_data = inv.get("lines", [])
                        
                        details = f"""
INVOICE: {inv.get('invoice_number', '')}
Date: {inv.get('invoice_date', '')}
Buyer: {inv.get('buyer_name', '')}

LINE ITEMS:
{'#':<3} {'Description':<30} {'Qty':>6} {'Price':>10} {'VAT%':>5} {'Total':>12}
{'-'*66}
"""
                        for i, ln in enumerate(lines_data, 1):
                            details += f"{i:<3} {ln.get('description','')[:30]:<30} {ln.get('quantity',1):>6.2f} {ln.get('unit_price',0):>10.2f} {ln.get('vat_rate',0)*100:>5.0f} {ln.get('line_total',0):>12.2f}\n"
                        
                        details += f"""
{'-'*66}
Subtotal: € {inv.get('total_excl_vat', 0):.2f}
VAT: € {inv.get('vat_amount', 0):.2f}
TOTAL: € {inv.get('total_incl_vat', 0):.2f}
"""
                        window["-HIST_DETAILS-"].update(details)
            
            elif event == "-HIST_COPY-":
                details = window["-HIST_DETAILS-"].get()
                if details:
                    try:
                        import pyperclip
                        pyperclip.copy(details)
                        window["-HIST_STATUS-"].update(tr("details_copied"))
                    except:
                        pass
            
            elif event == "-HIST_DELETE-":
                selected = values["-HIST_TABLE-"]
                if selected and sg.popup_yes_no("Delete selected invoice?", 
                                               title="Confirm Delete") == "Yes":
                    window["-HIST_STATUS-"].update("Delete functionality coming soon")


if __name__ == "__main__":
    main()
