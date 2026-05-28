"""
ee-invoice-generator GUI v0.4.0
Single window, language affects PDF, compact invoice tab
"""
import PySimpleGUI as sg
import json
from datetime import date, datetime
from pathlib import Path

from einvoice import InvoiceGenerator, PDFGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails
from einvoice.accounting import Database

# ============================================================
# INVOICE TEXT TEMPLATES (language-specific)
# ============================================================
INVOICE_LANG = {
    "en": {
        "invoice": "INVOICE",
        "invoice_no": "Invoice No.",
        "date": "Date",
        "due_date": "Due Date",
        "seller": "SELLER",
        "buyer": "BUYER",
        "company": "Company",
        "registry": "Registry Code",
        "vat": "VAT",
        "address": "Address",
        "email": "Email",
        "payment_to": "Payment to",
        "iban": "IBAN",
        "bic": "BIC",
        "line_items": "LINE ITEMS",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "price": "Price",
        "vat_rate": "VAT",
        "total": "Total",
        "subtotal": "Subtotal",
        "vat_amount": "VAT",
        "grand_total": "GRAND TOTAL",
        "notes": "Notes",
        "generated_by": "Generated with ee-invoice-generator",
        "vat_not_applicable": "VAT not applicable",
        "seller_not_vat_registered": "Seller is not VAT registered",
        "period": "Period",
        "total_gross": "Total (incl. VAT)",
    },
    "ru": {
        "invoice": "СЧЁТ",
        "invoice_no": "Номер счёта",
        "date": "Дата",
        "due_date": "Срок оплаты",
        "seller": "ПРОДАВЕЦ",
        "buyer": "ПОКУПАТЕЛЬ",
        "company": "Компания",
        "registry": "Рег. номер",
        "vat": "НДС",
        "address": "Адрес",
        "email": "Email",
        "payment_to": "Оплата на",
        "iban": "IBAN",
        "bic": "BIC",
        "line_items": "ПОЗИЦИИ",
        "description": "Описание",
        "qty": "Кол-во",
        "unit": "Ед.",
        "price": "Цена",
        "vat_rate": "НДС",
        "total": "Итого",
        "subtotal": "Подытог",
        "vat_amount": "НДС",
        "grand_total": "ИТОГО",
        "notes": "Заметки",
        "generated_by": "Создано с ee-invoice-generator",
        "vat_not_applicable": "НДС не применяется",
        "seller_not_vat_registered": "Продавец не зарегистрирован как плательщик НДС",
        "period": "Период",
        "total_gross": "Всего (с НДС)",
    },
    "et": {
        "invoice": "ARVE",
        "invoice_no": "Arve nr.",
        "date": "Kuupäev",
        "due_date": "Tähtpäev",
        "seller": "MÜÜJA",
        "buyer": "OSTJA",
        "company": "Ettevõte",
        "registry": "Registrikood",
        "vat": "KMKR",
        "address": "Aadress",
        "email": "Email",
        "payment_to": "Makse vastu",
        "iban": "IBAN",
        "bic": "BIC",
        "line_items": "READ",
        "description": "Kirjeldus",
        "qty": "Kogus",
        "unit": "Ühik",
        "price": "Hind",
        "vat_rate": "KM",
        "total": "Kokku",
        "subtotal": "Vahesumma",
        "vat_amount": "KM",
        "grand_total": "KOGUSUMMA",
        "notes": "Märkused",
        "generated_by": "Loodud: ee-invoice-generator",
        "vat_not_applicable": "KM ei kohaldata",
        "seller_not_vat_registered": "Müüja ei ole KMKR-ga registreeritud",
        "period": "Periood",
        "total_gross": "Kokku (koos KM-ga)",
    },
}

# ============================================================
# APP UI TRANSLATIONS
# ============================================================
LANG = {
    "en": {
        "app_title": "ee-invoice-generator",
        "my_company": "My Company",
        "new_invoice": "New Invoice",
        "accounting": "Accounting",
        "invoice_history": "History",
        "language_label": "Language",
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
        "seller_details": "Seller",
        "buyer_details": "Buyer",
        "buyer_same": "Same as My Company",
        "invoice_details": "Invoice Details",
        "invoice_number": "Invoice No. *",
        "currency": "Currency",
        "invoice_date": "Date *",
        "due_date": "Due Date",
        "order_ref": "Order Ref.",
        "line_items": "Line Items (enter price WITH VAT)",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "total_gross": "Price",
        "vat_rate": "VAT%",
        "add_line": "Add",
        "remove_last": "Remove",
        "notes": "Notes",
        "notes_hint": "Terms, bank details...",
        "output_options": "Output",
        "output_folder": "Folder",
        "gen_xml": "XML",
        "gen_pdf": "PDF",
        "generate_invoice": "Generate",
        "clear_form": "Clear",
        "confirm_generate": "Generate invoice for {buyer}?\n{lines} line items\n\nContinue?",
        "confirm_clear": "Clear invoice data?",
        "success": "Invoice generated!",
        "error": "Error",
        "validation_error": "Please fill:\n• {}",
        "lines_added": "lines",
        "journal": "Journal",
        "vat_calc": "VAT",
        "reports": "Reports",
        "accounts": "Accounts",
        "acc_settings": "Settings",
        "invoice_history_title": "Invoice History",
        "filter_from": "From",
        "filter_to": "To",
        "filter_btn": "Filter",
        "refresh_btn": "Refresh",
        "view_details": "Details",
        "copy_clipboard": "Copy",
        "no_history": "No invoices",
        "details_copied": "Copied!",
    },
    "ru": {
        "app_title": "ee-invoice-generator",
        "my_company": "Моя Компания",
        "new_invoice": "Новый Счёт",
        "accounting": "Бухгалтерия",
        "invoice_history": "История",
        "language_label": "Язык",
        "company_info": "Данные Компании",
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
        "company_saved": "Сохранено!",
        "seller_details": "Продавец",
        "buyer_details": "Покупатель",
        "buyer_same": "Как Моя Компания",
        "invoice_details": "Детали Счёта",
        "invoice_number": "Номер *",
        "currency": "Валюта",
        "invoice_date": "Дата *",
        "due_date": "Срок",
        "order_ref": "Заказ #",
        "line_items": "Позиции (цена С НДС)",
        "description": "Описание",
        "qty": "Кол",
        "unit": "Ед.",
        "total_gross": "Цена",
        "vat_rate": "НДС%",
        "add_line": "Добавить",
        "remove_last": "Удалить",
        "notes": "Заметки",
        "notes_hint": "Условия, реквизиты...",
        "output_options": "Вывод",
        "output_folder": "Папка",
        "gen_xml": "XML",
        "gen_pdf": "PDF",
        "generate_invoice": "Создать",
        "clear_form": "Очистить",
        "confirm_generate": "Создать счёт для {buyer}?\n{lines} позиций\n\nПродолжить?",
        "confirm_clear": "Очистить данные счёта?",
        "success": "Счёт создан!",
        "error": "Ошибка",
        "validation_error": "Заполните:\n• {}",
        "lines_added": "поз.",
        "journal": "Журнал",
        "vat_calc": "НДС",
        "reports": "Отчёты",
        "accounts": "Счета",
        "acc_settings": "Настройки",
        "invoice_history_title": "История",
        "filter_from": "От",
        "filter_to": "До",
        "filter_btn": "Фильтр",
        "refresh_btn": "Обновить",
        "view_details": "Детали",
        "copy_clipboard": "Копировать",
        "no_history": "Нет счетов",
        "details_copied": "Скопировано!",
    },
    "et": {
        "app_title": "ee-invoice-generator",
        "my_company": "Minu Ettevõte",
        "new_invoice": "Uus Arve",
        "accounting": "Raamatupidamine",
        "invoice_history": "Ajalugu",
        "language_label": "Keel",
        "company_info": "Ettevõte",
        "company_name": "Nimi *",
        "registry_code": "Reg. kood *",
        "vat_number": "KMKR",
        "address": "Aadress",
        "city": "Linn",
        "postal_code": "Indeks",
        "email": "Email",
        "phone": "Telefon",
        "bank_details": "Pank",
        "iban": "IBAN *",
        "bic": "BIC *",
        "bank_name": "Pank",
        "save_company": "Salvesta",
        "company_saved": "Salvestatud!",
        "seller_details": "Müüja",
        "buyer_details": "Ostja",
        "buyer_same": "Same as Minu Ettevõte",
        "invoice_details": "Arve",
        "invoice_number": "Arve nr. *",
        "currency": " Valuuta",
        "invoice_date": "Kuupäev *",
        "due_date": "Täht",
        "order_ref": "Tellimus",
        "line_items": "Read ( hind koos KM-ga)",
        "description": "Kirjeldus",
        "qty": "Kog",
        "unit": "Ühik",
        "total_gross": "Hind",
        "vat_rate": "KM%",
        "add_line": "Lisa",
        "remove_last": "Eemalda",
        "notes": "Märkused",
        "notes_hint": " Tingimused...",
        "output_options": "Väljund",
        "output_folder": "Kaust",
        "gen_xml": "XML",
        "gen_pdf": "PDF",
        "generate_invoice": "Genereeri",
        "clear_form": "Tühjenda",
        "confirm_generate": "Genereeri arve {buyer}?\n{lines} rida\n\nJätkata?",
        "confirm_clear": "Tühjenda arve andmed?",
        "success": "Arve genereeritud!",
        "error": "Viga",
        "validation_error": "Täida:\n• {}",
        "lines_added": "rida",
        "journal": "Päevik",
        "vat_calc": "KM",
        "reports": "Aruanded",
        "accounts": "Kontod",
        "acc_settings": "Seaded",
        "invoice_history_title": "Ajalugu",
        "filter_from": "Alates",
        "filter_to": "Kuni",
        "filter_btn": "Filtreeri",
        "refresh_btn": "Uuenda",
        "view_details": "Detailid",
        "copy_clipboard": "Kopeeri",
        "no_history": "Arveid pole",
        "details_copied": "Kopeeritud!",
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


def inv_tr(key):
    return INVOICE_LANG[CURRENT_LANG[0]].get(key, key)


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


# ============================================================
# COMPANY TAB
# ============================================================
def build_company_tab():
    config = load_config()
    return [
        [sg.Text(tr("company_info"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Two columns: company info + bank details
        [
            sg.Column([
                [sg.Frame(tr("company_info"), [
                    [sg.Text(tr("company_name"), size=(12, 1)),
                     sg.Input(default_text=config.get("name", ""), key="-C_NAME-", size=(30, 1))],
                    [sg.Text(tr("registry_code"), size=(12, 1)),
                     sg.Input(default_text=config.get("registry_code", ""), key="-C_REG-", size=(15, 1))],
                    [sg.Text(tr("vat_number"), size=(12, 1)),
                     sg.Input(default_text=config.get("vat_number", ""), key="-C_VAT-", size=(15, 1))],
                    [sg.Text(tr("address"), size=(12, 1)),
                     sg.Input(default_text=config.get("address", ""), key="-C_ADDR-", size=(30, 1))],
                    [sg.Text(tr("city"), size=(12, 1)),
                     sg.Input(default_text=config.get("city", ""), key="-C_CITY-", size=(20, 1)),
                     sg.Text(tr("postal_code"), size=(8, 1)),
                     sg.Input(default_text=config.get("postal_code", ""), key="-C_POSTAL-", size=(8, 1))],
                    [sg.Text(tr("email"), size=(12, 1)),
                     sg.Input(default_text=config.get("email", ""), key="-C_EMAIL-", size=(25, 1))],
                    [sg.Text(tr("phone"), size=(12, 1)),
                     sg.Input(default_text=config.get("phone", ""), key="-C_PHONE-", size=(15, 1))],
                ])],
            ]),
            sg.Column([
                [sg.Frame(tr("bank_details"), [
                    [sg.Text(tr("iban"), size=(10, 1)),
                     sg.Input(default_text=config.get("iban", ""), key="-C_IBAN-", size=(22, 1))],
                    [sg.Text(tr("bic"), size=(10, 1)),
                     sg.Input(default_text=config.get("bic", ""), key="-C_BIC-", size=(12, 1))],
                    [sg.Text(tr("bank_name"), size=(10, 1)),
                     sg.Input(default_text=config.get("bank_name", ""), key="-C_BANK-", size=(22, 1))],
                ])],
                [sg.Frame(tr("output_options"), [
                    [sg.Text(tr("output_folder")),
                     sg.Input(default_text=str(Path.home() / "Documents"), key="-OUT_DIR-", size=(22, 1)),
                     sg.FolderBrowse()],
                    [sg.Checkbox(tr("gen_xml"), default=True, key="-GEN_XML-"),
                     sg.Checkbox(tr("gen_pdf"), default=True, key="-GEN_PDF-")],
                ])],
            ]),
        ],
        
        [sg.HorizontalSeparator()],
        [sg.Button(tr("save_company"), key="-SAVE_COMPANY-", size=(14, 1),
                  button_color=("white", "#2c5282"))],
        [sg.Text("", key="-COMPANY_STATUS-", text_color="green")],
    ]


# ============================================================
# INVOICE TAB (compact layout)
# ============================================================
def build_invoice_tab():
    config = load_config()
    return [
        [sg.Text(tr("new_invoice"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Row 1: Seller + Buyer side by side
        [
            sg.Frame(tr("seller_details"), [
                [sg.Text(tr("company_name"), size=(12, 1)),
                 sg.Input(default_text=config.get("name", ""), key="-INV_S_NAME-", size=(25, 1))],
                [sg.Text(tr("registry_code"), size=(12, 1)),
                 sg.Input(default_text=config.get("registry_code", ""), key="-INV_S_REG-", size=(12, 1))],
                [sg.Text(tr("address"), size=(12, 1)),
                 sg.Input(default_text=config.get("address", ""), key="-INV_S_ADDR-", size=(25, 1))],
                [sg.Text(tr("iban"), size=(12, 1)),
                 sg.Input(default_text=config.get("iban", ""), key="-INV_S_IBAN-", size=(20, 1))],
            ]),
            sg.Frame(tr("buyer_details"), [
                [sg.Checkbox(tr("buyer_same"), key="-BUYER_SAME-", enable_events=True)],
                [sg.Text(tr("company_name"), size=(12, 1)),
                 sg.Input(key="-INV_B_NAME-", size=(25, 1))],
                [sg.Text(tr("registry_code"), size=(12, 1)),
                 sg.Input(key="-INV_B_REG-", size=(12, 1))],
                [sg.Text(tr("address"), size=(12, 1)),
                 sg.Input(key="-INV_B_ADDR-", size=(25, 1))],
            ]),
        ],
        
        # Row 2: Invoice meta + Line items side by side
        [
            sg.Frame(tr("invoice_details"), [
                [sg.Text(tr("invoice_number"), size=(12, 1)),
                 sg.Input(default_text=DB.generate_invoice_number(), key="-INV_NUM-", size=(15, 1))],
                [sg.Text(tr("invoice_date"), size=(12, 1)),
                 sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-INV_DATE-", size=(12, 1))],
                [sg.Text(tr("due_date"), size=(12, 1)),
                 sg.Input(key="-INV_DUE-", size=(12, 1))],
            ]),
            sg.Frame(tr("line_items"), [
                [sg.Text(tr("description"), size=(20, 1)),
                 sg.Text(tr("qty"), size=(4, 1)),
                 sg.Text(tr("unit"), size=(7, 1)),
                 sg.Text(tr("total_gross"), size=(8, 1)),
                 sg.Text(tr("vat_rate"), size=(6, 1))],
                [sg.Input(key="-L_DESC-", size=(20, 1)),
                 sg.Input(default_text="1", key="-L_QTY-", size=(4, 1)),
                 sg.Combo(["service", "project", "campaign", "fixed fee", "consulting", "pcs", "h", "km", "kg"],
                         default_value="service", key="-L_UNIT-", size=(7, 1)),
                 sg.Input(default_text="0.00", key="-L_PRICE-", size=(8, 1)),
                 sg.Combo(["0", "20", "9"], default_value="0", key="-L_VAT-", size=(6, 1))],
                [sg.Button(tr("add_line"), key="-ADD_LINE-", size=(8, 1), button_color=("white", "#2c5282")),
                 sg.Button(tr("remove_last"), key="-REMOVE_LAST-", size=(8, 1))],
                [sg.Listbox(values=[], key="-LINES_LIST-", size=(60, 5))],
            ]),
        ],
        
        # Row 3: Notes + action buttons
        [
            sg.Frame(tr("notes"), [
                [sg.Multiline(key="-INV_NOTES-", size=(45, 3), tooltip=tr("notes_hint"))],
            ]),
            sg.Column([
                [sg.Button(tr("generate_invoice"), key="-GENERATE-", size=(12, 2),
                          button_color=("white", "#2c5282"), font=("Helvetica", 10, "bold"))],
                [sg.Button(tr("clear_form"), key="-CLEAR_INV-", size=(12, 1))],
            ]),
        ],
        
        [sg.Text(f"0 {tr('lines_added')}", key="-LINES_COUNT-", text_color="#666")],
        [sg.Text("", key="-INV_STATUS-", text_color="green")],
    ]


# ============================================================
# ACCOUNTING TAB
# ============================================================
def build_accounting_tab():
    return [
        [sg.Text(tr("accounting"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.TabGroup([
            [sg.Tab(tr("journal"), [
                [sg.Text("Double-entry bookkeeping journal", text_color="#666")],
            ])],
            [sg.Tab(tr("vat_calc"), [
                [sg.Text("VAT calculator", text_color="#666")],
            ])],
            [sg.Tab(tr("reports"), [
                [sg.Text("Financial reports", text_color="#666")],
            ])],
            [sg.Tab(tr("accounts"), [
                [sg.Text("Chart of accounts", text_color="#666")],
            ])],
        ])],
    ]


# ============================================================
# HISTORY TAB
# ============================================================
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
             sg.Button(tr("filter_btn"), key="-HIST_FILTER-", size=(8, 1)),
             sg.Button(tr("refresh_btn"), key="-HIST_REFRESH-", size=(8, 1))],
        ])],
        [sg.Table(
            headings=["#", "Date", inv_tr("invoice_no"), inv_tr("buyer"), "Total", "Status"],
            values=[], key="-HIST_TABLE-", size=(65, 10),
            col_widths=[3, 9, 11, 18, 9, 7],
        )],
        [sg.Frame(inv_tr("notes"), [
            [sg.Multiline(key="-HIST_DETAILS-", size=(65, 12), disabled=True, font=("Courier", 9))],
        ])],
        [sg.Button(tr("view_details"), key="-HIST_VIEW-", size=(8, 1)),
         sg.Button(tr("copy_clipboard"), key="-HIST_COPY-", size=(10, 1))],
        [sg.Text("", key="-HIST_STATUS-", text_color="green")],
    ]


def refresh_history(window):
    try:
        invoices = DB.list_invoices()
        rows = []
        for i, inv in enumerate(invoices, 1):
            d = inv.get("invoice_date", "") or ""
            if "-" in d:
                d = ".".join(reversed(d.split("-")[:3]))
            rows.append([str(i), d, inv.get("invoice_number", ""),
                        inv.get("buyer_name", ""), f"{inv.get('total_incl_vat', 0):.2f}",
                        inv.get("status", "draft")])
        window["-HIST_TABLE-"].update(rows)
        window["-HIST_STATUS-"].update(f"{len(invoices)} invoices")
    except Exception as e:
        window["-HIST_STATUS-"].update(f"Error: {e}", text_color="red")


class ProfessionalInvoiceGenerator:
    """Generate professional minimalist PDF invoices"""
    
    def __init__(self, data: InvoiceData, inv_lang="en"):
        self.data = data
        self.inv_lang = inv_lang
        self.t = INVOICE_LANG[inv_lang]
    
    def build_pdf(self, buffer):
        """Build professional PDF invoice"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                       Paragraph, Spacer, HRFlowable)
        from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
        
        # Colors - minimalist Nordic
        DARK_BLUE = HexColor("#1a365d")
        MID_BLUE = HexColor("#2c5282")
        LIGHT_GRAY = HexColor("#f7fafc")
        TEXT_DARK = HexColor("#1a202c")
        TEXT_GRAY = HexColor("#718096")
        BORDER = HexColor("#e2e8f0")
        
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm,
        )
        
        elements = []
        
        # === HEADER: Invoice label + Seller info ===
        title_style = ParagraphStyle("Title", fontSize=24, textColor=DARK_BLUE,
                                      fontName="Helvetica-Bold", alignment=TA_RIGHT)
        company_style = ParagraphStyle("Company", fontSize=14, textColor=MID_BLUE,
                                       fontName="Helvetica-Bold", alignment=TA_RIGHT)
        addr_style = ParagraphStyle("Addr", fontSize=9, textColor=TEXT_GRAY, alignment=TA_RIGHT)
        
        # Header table: Invoice title | Seller info
        seller = self.data.seller
        seller_addr_lines = []
        if seller.address:
            seller_addr_lines.append(seller.address)
        if seller.city or seller.postal_code:
            seller_addr_lines.append(f"{seller.postal_code or ''} {seller.city or ''}".strip())
        if seller_addr_lines and seller.country:
            seller_addr_lines.append(seller.country)
        
        header_data = [
            [
                # Invoice label column
                Paragraph(self.t["invoice"], title_style),
                # Seller column-right aligned
                Paragraph(seller.name.upper() if seller.name else "", company_style),
            ],
            [
                # Nothing under invoice label
                "",
                # Seller address
                Paragraph("<br/>".join(seller_addr_lines), addr_style),
            ],
        ]
        
        header_table = Table(header_data, colWidths=[80*mm, 90*mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10*mm))
        
        # === Invoice Meta Row ===
        meta_style = ParagraphStyle("Meta", fontSize=10, textColor=TEXT_DARK)
        label_style = ParagraphStyle("Label", fontSize=8, textColor=TEXT_GRAY)
        
        inv_date_str = self.data.invoice_date.strftime("%d.%m.%Y") if self.data.invoice_date else ""
        due_date_str = self.data.due_date.strftime("%d.%m.%Y") if self.data.due_date else self.t["due_date"]
        
        meta_data = [[
            Paragraph(f"<b>{self.t['invoice_no']}</b><br/>{self.data.invoice_number}", meta_style),
            Paragraph(f"<b>{self.t['date']}</b><br/>{inv_date_str}", meta_style),
            Paragraph(f"<b>{self.t['due_date']}</b><br/>{due_date_str}", meta_style),
        ]]
        meta_table = Table(meta_data, colWidths=[60*mm, 50*mm, 60*mm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 4*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 4*mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4*mm),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8*mm))
        
        # === Seller + Buyer side by side ===
        buyer = self.data.buyer
        buyer_addr_lines = []
        if buyer.address:
            buyer_addr_lines.append(buyer.address)
        if buyer.city or buyer.postal_code:
            buyer_addr_lines.append(f"{buyer.postal_code or ''} {buyer.city or ''}".strip())
        
        def party_block(label, name, reg, vat, address_lines):
            pieces = [Paragraph(f"<b>{label}</b>", ParagraphStyle("PLabel", fontSize=8, 
                              textColor=TEXT_GRAY, spaceAfter=1*mm))]
            pieces.append(Paragraph(name or "", ParagraphStyle("PName", fontSize=11,
                               textColor=DARK_BLUE, spaceAfter=1*mm)))
            if reg:
                pieces.append(Paragraph(f"{self.t['registry']}: {reg}",
                             ParagraphStyle("PReg", fontSize=9, textColor=TEXT_GRAY)))
            if vat:
                pieces.append(Paragraph(f"{self.t['vat']}: {vat}",
                             ParagraphStyle("PVat", fontSize=9, textColor=TEXT_GRAY)))
            if address_lines:
                pieces.append(Paragraph("<br/>".join(address_lines),
                             ParagraphStyle("PAddr", fontSize=9, textColor=TEXT_GRAY)))
            return pieces
        
        parties_data = [[
            party_block(self.t["seller"], seller.name or "", seller.registry_code or "",
                       seller.vat_number or "", seller_addr_lines),
            party_block(self.t["buyer"], buyer.name or "", buyer.registry_code or "",
                       buyer.vat_number or "", buyer_addr_lines),
        ]]
        parties_table = Table(parties_data, colWidths=[85*mm, 85*mm])
        parties_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 8*mm))
        
        # === Line Items Table ===
        seq_style = ParagraphStyle("Seq", fontSize=8, textColor=TEXT_GRAY, alignment=TA_CENTER)
        desc_style_style = ParagraphStyle("DescH", fontSize=8, textColor=white)
        num_style = ParagraphStyle("Num", fontSize=8, textColor=TEXT_DARK, alignment=TA_RIGHT)
        header_row = [
            Paragraph(f"<b>#</b>", desc_style_style),
            Paragraph(f"<b>{self.t['description']}</b>", desc_style_style),
            Paragraph(f"<b>{self.t['qty']}</b>", desc_style_style),
            Paragraph(f"<b>{self.t['unit']}</b>", desc_style_style),
            Paragraph(f"<b>{self.t['price']}</b>", desc_style_style),
            Paragraph(f"<b>{self.t['vat_rate']}</b>", desc_style_style),
            Paragraph(f"<b>{self.t['total']}</b>", desc_style_style),
        ]
        
        rows = [header_row]
        subtotal = 0
        vat_amounts = {}
        
        for i, line in enumerate(self.data.lines, 1):
            net = line.unit_price
            gross = net * (1 + line.vat_rate) * line.quantity
            subtotal += net * line.quantity
            
            if line.vat_rate not in vat_amounts:
                vat_amounts[line.vat_rate] = 0
            vat_amounts[line.vat_rate] += net * line.quantity * line.vat_rate
            
            row_style = ParagraphStyle("Row", fontSize=8, textColor=TEXT_DARK, alignment=TA_RIGHT)
            row_desc_style = ParagraphStyle("RowDesc", fontSize=8, textColor=TEXT_DARK)
            
            vat_display = f"0%" if line.vat_rate == 0 else f"{line.vat_rate*100:.0f}%"
            
            if i % 2 == 0:
                bg = LIGHT_GRAY
            else:
                bg = white
            
            rows.append([
                Paragraph(str(i), seq_style),
                Paragraph(line.description, row_desc_style),
                Paragraph(f"{line.quantity:.1f}", row_style),
                Paragraph(line.unit, ParagraphStyle("U", fontSize=8, textColor=TEXT_GRAY, alignment=TA_CENTER)),
                Paragraph(f"€ {net:.2f}", row_style),
                Paragraph(vat_display, ParagraphStyle("V", fontSize=8, textColor=TEXT_GRAY, alignment=TA_CENTER)),
                Paragraph(f"€ {gross:.2f}", row_style),
            ])
        
        # If no lines, show empty table
        if not self.data.lines:
            rows.append([Paragraph("", row_desc_style)] * 7)
        
        col_widths = [10*mm, 60*mm, 20*mm, 20*mm, 30*mm, 15*mm, 30*mm]
        items_table = Table(rows, colWidths=col_widths)
        
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 3*mm),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 3*mm),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 2*mm),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 2*mm),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 0), (5, -1), "RIGHT"),
            ("ALIGN", (6, 0), (6, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("BOX", (0, 0), (-1, -1), 1, DARK_BLUE),
        ]
        
        # Alternating rows
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))
        
        items_table.setStyle(TableStyle(style_cmds))
        elements.append(items_table)
        elements.append(Spacer(1, 5*mm))
        
        # === Totals ===
        total_vat = sum(vat_amounts.values())
        grand_total = subtotal + total_vat
        
        totals_data = [
            [Paragraph(self.t["subtotal"], ParagraphStyle("TL", fontSize=9, textColor=TEXT_DARK, alignment=TA_RIGHT)),
             Paragraph(f"€ {subtotal:.2f}", ParagraphStyle("TV", fontSize=9, textColor=TEXT_DARK, alignment=TA_RIGHT))],
        ]
        
        # VAT lines
        if vat_amounts:
            for rate, amt in sorted(vat_amounts.items()):
                label = f"{self.t['vat_amount']} ({rate*100:.0f}%)"
                if rate == 0:
                    label = self.t["vat_not_applicable"]
                totals_data.append([
                    Paragraph(label, ParagraphStyle("VL", fontSize=8, textColor=TEXT_GRAY, alignment=TA_RIGHT)),
                    Paragraph(f"€ {amt:.2f}", ParagraphStyle("VV", fontSize=8, textColor=TEXT_GRAY, alignment=TA_RIGHT)),
                ])
        
        # Grand total
        totals_data.append([
            Paragraph(self.t["grand_total"], ParagraphStyle("GTL", fontSize=12, textColor=DARK_BLUE, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph(f"€ {grand_total:.2f}", ParagraphStyle("GTV", fontSize=12, textColor=DARK_BLUE, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ])
        
        totals_table = Table(totals_data, colWidths=[120*mm, 60*mm])
        totals_table.setStyle(TableStyle([
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, DARK_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 8*mm))
        
        # === Payment details ===
        pay_style = ParagraphStyle("Pay", fontSize=9, textColor=TEXT_DARK)
        pay_label = ParagraphStyle("PayL", fontSize=8, textColor=TEXT_GRAY)
        
        pay_data = [[
            Paragraph(f"<b>{self.t['payment_to']}</b>", pay_label),
            Paragraph(self.data.payment.iban or "", pay_style),
            Paragraph("BIC:", pay_label),
            Paragraph(self.data.payment.bic or "", pay_style),
        ]]
        pay_table = Table(pay_data, colWidths=[30*mm, 65*mm, 15*mm, 70*mm])
        pay_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2*mm),
            ("TOPPADDING", (0, 0), (-1, -1), 1*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1*mm),
        ]))
        elements.append(pay_table)
        
        # === Notes ===
        if self.data.notes:
            elements.append(Spacer(1, 5*mm))
            elements.append(Paragraph(self.t["notes"], ParagraphStyle("NotesL", fontSize=8, textColor=TEXT_GRAY, spaceAfter=1*mm)))
            elements.append(Paragraph(self.data.notes, ParagraphStyle("Notes", fontSize=9, textColor=TEXT_DARK)))
        
        doc.build(elements)
    
    def save(self, filepath):
        from io import BytesIO
        buffer = BytesIO()
        self.build_pdf(buffer)
        with open(filepath, "wb") as f:
            f.write(buffer.getvalue())


# ============================================================
# MAIN
# ============================================================
def main():
    lines = []
    
    while True:
        company_tab = build_company_tab()
        invoice_tab = build_invoice_tab()
        accounting_tab = build_accounting_tab()
        history_tab = build_history_tab()
        
        lang_names = {"en": "English", "ru": "Русский", "et": "Eesti"}
        
        layout = [
            [sg.Text("ee-invoice-generator", font=("Helvetica", 16, "bold")),
             sg.Text("  |  "),
             sg.Text(tr("language_label") + ":"),
             sg.Combo(sorted(lang_names.values()),
                     default_value=lang_names[CURRENT_LANG[0]],
                     key="-LANG_SELECT-", size=(10, 1), enable_events=True),
             sg.Text("", size=(10, 1)),
             sg.Text("v0.4.0", text_color="#999")],
            [sg.HorizontalSeparator()],
            [sg.TabGroup([
                [sg.Tab(tr("my_company"), company_tab),
                 sg.Tab(tr("new_invoice"), invoice_tab),
                 sg.Tab(tr("accounting"), accounting_tab),
                 sg.Tab(tr("invoice_history"), history_tab)],
            ])],
        ]
        
        window = sg.Window("ee-invoice-generator", layout, size=(700, 650), resizable=True)
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, "Exit"):
                return
            
            elif event == "-LANG_SELECT-":
                lang_map = {v: k for k, v in lang_names.items()}
                new_lang = lang_map.get(values["-LANG_SELECT-"], "en")
                if new_lang != CURRENT_LANG[0]:
                    set_lang(new_lang)
                window.close()
                break  # Rebuild with new language
            
            elif event == "-SAVE_COMPANY-":
                c = {
                    "name": values["-C_NAME-"].strip(),
                    "registry_code": values["-C_REG-"].strip(),
                    "vat_number": values["-C_VAT-"].strip(),
                    "address": values["-C_ADDR-"].strip(),
                    "city": values["-C_CITY-"].strip(),
                    "postal_code": values["-C_POSTAL-"].strip(),
                    "email": values["-C_EMAIL-"].strip(),
                    "phone": values["-C_PHONE-"].strip(),
                    "iban": values["-C_IBAN-"].strip(),
                    "bic": values["-C_BIC-"].strip(),
                    "bank_name": values["-C_BANK-"].strip(),
                }
                save_config(c)
                window["-COMPANY_STATUS-"].update(tr("company_saved"))
            
            elif event == "-BUYER_SAME-":
                if values["-BUYER_SAME-"]:
                    config = load_config()
                    window["-INV_B_NAME-"].update(config.get("name", ""))
                    window["-INV_B_REG-"].update(config.get("registry_code", ""))
                    window["-INV_B_ADDR-"].update(config.get("address", ""))
            
            elif event == "-ADD_LINE-":
                try:
                    desc = values["-L_DESC-"].strip()
                    qty = float(values["-L_QTY-"])
                    unit = values["-L_UNIT-"]
                    price_gross = float(values["-L_PRICE-"])
                    vat_rate = float(values["-L_VAT-"] or 0) / 100
                    
                    if not desc:
                        sg.popup_error("Description required!")
                        continue
                    if qty <= 0:
                        sg.popup_error("Quantity must be positive!")
                        continue
                    
                    net = price_gross / (1 + vat_rate) if vat_rate > 0 else price_gross
                    lines.append(InvoiceLine(
                        description=desc, quantity=qty, unit=unit,
                        unit_price=net, vat_rate=vat_rate,
                    ))
                    
                    list_vals = []
                    for i, ln in enumerate(lines):
                        g = ln.unit_price * (1 + ln.vat_rate) * ln.quantity
                        list_vals.append(f"{i+1}. {ln.description[:35]} | €{g:.2f}")
                    window["-LINES_LIST-"].update(values=list_vals)
                    window["-LINES_COUNT-"].update(f"{len(lines)} {tr('lines_added')}")
                    
                    window["-L_DESC-"].update("")
                    window["-L_QTY-"].update("1")
                    window["-L_PRICE-"].update("0.00")
                except ValueError as e:
                    sg.popup_error(f"Invalid: {e}")
            
            elif event == "-REMOVE_LAST-":
                if lines:
                    lines.pop()
                    list_vals = []
                    for i, ln in enumerate(lines):
                        g = ln.unit_price * (1 + ln.vat_rate) * ln.quantity
                        list_vals.append(f"{i+1}. {ln.description[:35]} | €{g:.2f}")
                    window["-LINES_LIST-"].update(values=list_vals)
                    window["-LINES_COUNT-"].update(f"{len(lines)} {tr('lines_added')}")
            
            elif event == "-GENERATE-":
                errors = []
                if not values["-INV_S_NAME-"].strip():
                    errors.append(tr("company_name"))
                if not values["-INV_S_REG-"].strip():
                    errors.append(tr("registry_code"))
                if not values["-INV_B_NAME-"].strip():
                    errors.append(tr("buyer_details"))
                if not values["-INV_NUM-"] .strip():
                    errors.append(tr("invoice_number"))
                if not lines:
                    errors.append(f"1+ {tr('lines_added')}")
                
                if errors:
                    sg.popup_error(tr("validation_error").format("\n• ".join(errors)))
                    continue
                
                confirm = sg.popup_yes_no(
                    tr("confirm_generate").format(
                        buyer=values["-INV_B_NAME-"],
                        lines=str(len(lines))
                    )
                )
                if confirm != "Yes":
                    continue
                
                try:
                    seller = PartyDetails(
                        registry_code=values["-INV_S_REG-"].strip(),
                        name=values["-INV_S_NAME-"].strip(),
                        vat_number=values.get("-C_VAT-", "").strip() or None,
                        address=values.get("-C_ADDR-", "").strip() or None,
                        city=values.get("-C_CITY-", "").strip() or None,
                        postal_code=values.get("-C_POSTAL-", "").strip() or None,
                        country="EE",
                        email=values.get("-C_EMAIL-", "").strip() or None,
                        phone=values.get("-C_PHONE-", "").strip() or None,
                    )
                    buyer = PartyDetails(
                        registry_code=values["-INV_B_REG-"].strip() or None,
                        name=values["-INV_B_NAME-"].strip(),
                        vat_number=None,
                        address=values["-INV_B_ADDR-"].strip() or None,
                        city=None, postal_code=None, country="EE", email=None,
                    )
                    payment = PaymentDetails(
                        iban=values["-INV_S_IBAN-"].strip(),
                        bic=values["-INV_S_BIC-"].strip() if "-INV_S_BIC-" in values else "",
                        bank_name=values.get("-C_BANK-", "").strip() or None,
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
                        currency="EUR",
                    )
                    
                    output_dir = Path(values["-OUT_DIR-"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    inv_num = values["-INV_NUM-"].strip().replace("/", "-")
                    date_str = inv_date.strftime("%Y%m%d")
                    
                    generated = []
                    if values.get("-GEN_XML-"):
                        xml_path = output_dir / f"invoice_{inv_num}.xml"
                        InvoiceGenerator(invoice_data).save(str(xml_path))
                        generated.append(f"XML")
                    if values.get("-GEN_PDF-"):
                        pdf_path = output_dir / f"invoice_{inv_num}.pdf"
                        ProfessionalInvoiceGenerator(invoice_data, CURRENT_LANG[0]).save(str(pdf_path))
                        generated.append(f"PDF")
                    
                    window["-INV_STATUS-"].update(tr("success"), text_color="green")
                    sg.popup_ok(tr("success") + "\n\n" + "\n".join(generated))
                    
                except Exception as e:
                    sg.popup_error(f"{tr('error')}: {e}")
            
            elif event == "-CLEAR_INV-":
                if sg.popup_yes_no(tr("confirm_clear")) == "Yes":
                    lines.clear()
                    window["-LINES_LIST-"].update(values=[])
                    window["-LINES_COUNT-"].update(f"0 {tr('lines_added')}")
                    window["-INV_NUM-"].update(DB.generate_invoice_number())
                    window["-INV_NOTES-"].update("")
                    window["-INV_STATUS-"].update("")
            
            elif event == "-HIST_REFRESH-":
                refresh_history(window)
            
            elif event == "-HIST_VIEW-":
                selected = values["-HIST_TABLE-"]
                if selected:
                    invoices = DB.list_invoices()
                    idx = selected[0]
                    if idx < len(invoices):
                        inv = invoices[idx]
                        lines_data = inv.get("lines", [])
                        inv_date = inv.get("invoice_date", "")
                        if "-" in inv_date:
                            inv_date = ".".join(reversed(inv_date.split("-")[:3]))
                        
                        details = f"""INVOICE: {inv.get('invoice_number', '')}
Date: {inv_date}
Buyer: {inv.get('buyer_name', '')}

LINE ITEMS:
{'#':<3} {'Description':<30} {'Qty':>6} {'Price':>10} {'VAT':>6} {'Total':>12}
{'-'*70}
"""
                        for i, ln in enumerate(lines_data, 1):
                            details += f"{i:<3} {ln.get('description','')[:30]:<30} {ln.get('quantity',1):>6.1f} {ln.get('unit_price',0):>10.2f} {ln.get('vat_rate',0)*100:>5.0f}% {ln.get('line_total',0):>12.2f}\n"
                        
                        details += f"""
{'-'*70}
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


if __name__ == "__main__":
    main()
