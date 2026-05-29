"""
ee-invoice-generator GUI v0.6.47
Single window, language affects PDF, compact invoice tab
"""
import PySimpleGUI as sg
import json
import sys
import urllib.request
import urllib.error
import webbrowser
import subprocess
from datetime import date, datetime
from pathlib import Path

from einvoice import InvoiceGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails
from einvoice.accounting import Database

# ============================================================
# UPDATE CHECKER & SELF-UPDATER
# ============================================================

CURRENT_VERSION = "0.6.47"
GITHUB_REPO = "AG064/ee-invoice-generator"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def check_for_updates():
    """Check GitHub for newer version. Returns (new_version, download_url, asset_url) or None."""
    try:
        req = urllib.request.Request(
            UPDATE_CHECK_URL,
            headers={"User-Agent": "ee-invoice-generator"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            latest = data.get("tag_name", "").lstrip("v")
            if latest and tuple(map(int, latest.split("."))) > tuple(map(int, CURRENT_VERSION.split("."))):
                # Find the .exe asset
                assets = data.get("assets", [])
                exe_url = None
                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        exe_url = asset.get("browser_download_url")
                        break
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                return latest, html_url, exe_url
    except Exception:
        pass
    return None


def download_and_update(new_version, download_url, parent_window=None):
    """Download new version and replace exe. Silent if possible."""
    import tempfile
    import os
    import time
    import subprocess
    
    if not download_url:
        sg.popup(f"Update available: v{new_version}\n\nDownload manually:\n{_UPDATE_MANUAL_URL}",
                 title="Update Available")
        return False
    
    if not getattr(sys, 'frozen', False):
        sg.popup("Update only works for installed version", title="Error")
        return False
    
    current_exe = sys.executable
    temp_dir = tempfile.mkdtemp()
    new_exe_path = os.path.join(temp_dir, "update.exe")
    
    # Progress window - NON-blocking so app can close
    layout = [
        [sg.Text(f"Updating to v{new_version}...", key="-PROG-")],
        [sg.Text("Please wait.", text_color="gray")],
    ]
    win = sg.Window("Updating", layout, modal=True, finalize=True)
    
    try:
        # Download to temp FIRST while app is still running
        win["-PROG-"].update("Downloading...")
        win.refresh()
        req = urllib.request.Request(download_url, headers={"User-Agent": "ee-invoice-generator"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(new_exe_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
        
        win["-PROG-"].update("Installing...")
        win.refresh()
        
        # Close progress window
        win.close()
        win = None
        
        # Close main window - this triggers app exit
        if parent_window:
            try:
                parent_window.close()
            except:
                pass
        
        # Wait for app to fully close - longer wait for Windows to release file
        time.sleep(4)
        
        # Try to copy with retries
        import shutil
        copied = False
        for attempt in range(15):  # 15 attempts = up to 30 seconds waiting
            try:
                # Try renaming old exe first (helps on Windows)
                bak_path = current_exe + ".bak"
                if os.path.exists(bak_path):
                    os.remove(bak_path)
                if os.path.exists(current_exe):
                    os.rename(current_exe, bak_path)
                shutil.copy2(new_exe_path, current_exe)
                try:
                    os.remove(bak_path)
                except:
                    pass
                copied = True
                break
            except (PermissionError, OSError) as e:
                if attempt < 14:
                    time.sleep(2)
                else:
                    raise
        
        if not copied:
            raise Exception("Failed to replace exe after multiple attempts")
        
        # Launch new version
        try:
            subprocess.Popen([current_exe])
        except:
            pass
        
        # Exit - use os._exit to bypass any exception handlers
        os._exit(0)
        
    except SystemExit:
        # sys.exit() was called - this is expected during update, do not show error
        os._exit(0)
        
    except Exception as e:
        if win:
            try:
                win.close()
            except:
                pass
        # Cleanup temp (best effort, ignore errors)
        try:
            os.remove(new_exe_path)
        except:
            pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
        sg.popup(f"Update failed: {e}\n\nDownload manually:\n{download_url}", title="Error")
    
    return True


_UPDATE_MANUAL_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"


def get_update_button():
    """Button layout for update check."""
    return [sg.Button("Check Updates", key="-CHECK_UPDATE-", size=(12, 1), button_color=("#4a5568", "#e2e8f0"))]

# ============================================================
# INVOICE TEXT TEMPLATES (language-specific)
# ============================================================
INVOICE_LANG = {
    "en": {
        "invoice": "INVOICE",
        "invoice_no": "Invoice No.",
        "date": "Date",
        "date_required": "Date is required",
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
        "date_required": "Дата обязательна",
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
        "send_einvoice": "Send E-invoice",
        "open_mta": "Open Tax Portal",
        "open_file": "Open File",
        "einvoice_sent": "E-invoice ready for submission",
        "xml_location": "XML file:",
        "unit_service": "service",
        "unit_project": "project",
        "unit_hour": "hour",
        "unit_day": "day",
        "unit_campaign": "campaign",
        "unit_fixed": "fixed fee",
        "unit_consulting": "consulting",
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
        "send_einvoice": "Отправить счёт",
        "open_mta": "Открыть налоговую",
        "open_file": "Открыть файл",
        "einvoice_sent": "Счёт готов к отправке",
        "xml_location": "XML файл:",
        "unit_service": "услуга",
        "unit_project": "проект",
        "unit_hour": "час",
        "unit_day": "день",
        "unit_campaign": "кампания",
        "unit_fixed": "фикс. ставка",
        "unit_consulting": "консалтинг",
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
        "send_einvoice": "Saada e-arve",
        "open_mta": "Ava MTA portaal",
        "open_file": "Ava fail",
        "einvoice_sent": "E-arve valmis esitamiseks",
        "xml_location": "XML fail:",
        "unit_service": "teenus",
        "unit_project": "projekt",
        "unit_hour": "tund",
        "unit_day": "päev",
        "unit_campaign": "kampaania",
        "unit_fixed": "fikseeritud",
        "unit_consulting": "konsultatsioon",
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
        [sg.Text("", key="-COMPANY_STATUS-", text_color="#333")],
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
                [sg.Text(tr("currency"), size=(12, 1)),
                 sg.Combo(["EUR", "USD", "GBP", "SEK", "RUB", "CHF", "NOK", "DKK", "PLN", "CZK", "HUF", "RON"],
                         default_value="EUR", key="-INV_CURRENCY-", size=(8, 1))],
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
                 sg.Combo(["N/A", "0%", "20%", "9%"], default_value="N/A", key="-L_VAT-", size=(8, 1),
                    tooltip="N/A = not VAT registered (turnover < €40k). 20% = standard, 9% = reduced (books, medicine)")],
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
        [sg.Text("", key="-INV_STATUS-", text_color="#333")],
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
         sg.Button(tr("copy_clipboard"), key="-HIST_COPY-", size=(10, 1)),
         sg.Button("Delete", key="-HIST_DELETE-", size=(8, 1), button_color=("#c53030", "#e2e8f0")),
         sg.Button("Clear All", key="-HIST_CLEAR-", size=(8, 1), button_color=("#c53030", "#e2e8f0"))],
        [sg.Text("", key="-HIST_STATUS-", text_color="#333")],
    ]


def refresh_history(window):
    try:
        invoices = DB.list_invoices()
        rows = []
        for i, inv in enumerate(invoices, 1):
            d = inv.get("invoice_date", "") or ""
            if "-" in d:
                d = ".".join(reversed(d.split("-")[:3]))
            buyer = inv.get("buyer_name", "")
            if not buyer or buyer == "None":
                # Try to get from xml_data JSON
                import json
                xml = inv.get("xml_data", "")
                if xml:
                    try:
                        data = json.loads(xml)
                        buyer = data.get("buyer", {}).get("name", "") or ""
                    except:
                        buyer = ""
            status = inv.get("status", "draft")
            if status == "completed":
                status = "OK"
            rows.append([str(i), d, inv.get("invoice_number", ""),
                        buyer, f"{inv.get('total_incl_vat', 0):.2f}",
                        status])
        window["-HIST_TABLE-"].update(rows)
        window["-HIST_STATUS-"].update(f"{len(invoices)} invoices")
    except Exception as e:
        window["-HIST_STATUS-"].update(f"Error: {e}", text_color="red")


class ProfessionalInvoiceGenerator:
    """Generate professional minimalist PDF invoices based on Estonian OÜ standard"""
    
    def __init__(self, data: InvoiceData, inv_lang="en"):
        self.data = data
        self.inv_lang = inv_lang
        self.t = INVOICE_LANG[inv_lang]  # INVOICE_LANG from gui/main.py
    
    def build_pdf(self, buffer):
        """Build professional PDF invoice in Estonian format"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
        
        t = self.t  # Use INVOICE_LANG from main module
        
        DARK = HexColor("#111111")
        GRAY = HexColor("#555555")
        LIGHT_GRAY = HexColor("#777777")
        ACCENT = HexColor("#333333")
        TABLE_HEADER_BG = ACCENT
        TABLE_ROW_ALT = HexColor("#f5f5f5")
        BORDER = HexColor("#cccccc")
        
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=15*mm, leftMargin=15*mm,
            topMargin=12*mm, bottomMargin=12*mm,
        )
        
        elements = []
        
        # ============================================================
        # TOP: Buyer on LEFT | Dates on RIGHT
        # ============================================================
        
        label_style = ParagraphStyle("Label", fontSize=8, fontName="Helvetica-Bold",
                                      textColor=LIGHT_GRAY, leading=10, spaceAfter=1*mm)
        value_style = ParagraphStyle("Value", fontSize=9, fontName="Helvetica-Bold",
                                      textColor=DARK, leading=11)
        buyer_name_style = ParagraphStyle("BName", fontSize=12, fontName="Helvetica-Bold",
                                           textColor=DARK, leading=14)
        buyer_text = ParagraphStyle("BText", fontSize=9, fontName="Helvetica",
                                     textColor=DARK, leading=11)
        
        buyer_block = [
            Paragraph(f"<b>{t.get('buyer', 'Buyer').upper()}</b>", label_style),
            Paragraph(self.data.buyer.name or "", buyer_name_style),
        ]
        if self.data.buyer.address:
            buyer_block.append(Paragraph(self.data.buyer.address, buyer_text))
        if self.data.buyer.city or self.data.buyer.postal_code:
            buyer_block.append(Paragraph(
                f"{self.data.buyer.postal_code or ''} {self.data.buyer.city or ''}".strip(), buyer_text))
        if self.data.buyer.registry_code:
            buyer_block.append(Paragraph(f"{t.get('registry', 'Reg.')}: {self.data.buyer.registry_code}", buyer_text))
        if self.data.buyer.vat_number:
            buyer_block.append(Paragraph(f"{t.get('vat', 'VAT')}: {self.data.buyer.vat_number}", buyer_text))
        
        inv_date_str = self.data.invoice_date.strftime("%d.%m.%Y") if self.data.invoice_date else ""
        due_date_str = self.data.due_date.strftime("%d.%m.%Y") if self.data.due_date else "—"
        ref_str = self.data.order_reference or "—"
        
        date_block = [
            Paragraph(f"<b>{t.get('date', 'Date')}</b>", label_style),
            Paragraph(inv_date_str, value_style),
            Paragraph(f"<b>{t.get('due_date', 'Due Date')}</b>", label_style),
            Paragraph(due_date_str, value_style),
        ]
        if ref_str != "—":
            date_block.append(Paragraph(f"<b>{t.get('ref_number', 'Ref')}</b>", label_style))
            date_block.append(Paragraph(ref_str, value_style))
        
        top_header = Table([[buyer_block, "", date_block]], colWidths=[70*mm, 45*mm, 65*mm])
        top_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(top_header)
        elements.append(Spacer(1, 8*mm))
        
        # ============================================================
        # INVOICE TITLE: "ARVE NR 1234" - centered
        # ============================================================
        
        title_label_style = ParagraphStyle("TitleLabel", fontSize=10, fontName="Helvetica",
                                            textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=1*mm)
        title_style = ParagraphStyle("Title", fontSize=28, fontName="Helvetica-Bold",
                                      textColor=DARK, leading=32, alignment=TA_CENTER)
        
        elements.append(Paragraph(f"<b>{t.get('invoice', 'INVOICE')}</b>", title_label_style))
        elements.append(Paragraph(f"Nr. {self.data.invoice_number}", title_style))
        elements.append(Spacer(1, 6*mm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=DARK))
        elements.append(Spacer(1, 3*mm))
        
        # ============================================================
        # LINE ITEMS TABLE
        # ============================================================
        
        th_style = ParagraphStyle("TH", fontSize=8, fontName="Helvetica-Bold", textColor=white)
        td_right = ParagraphStyle("TDR", fontSize=9, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT)
        td_left = ParagraphStyle("TDL", fontSize=9, fontName="Helvetica", textColor=DARK)
        td_center = ParagraphStyle("TDC", fontSize=8, fontName="Helvetica", textColor=LIGHT_GRAY, alignment=TA_CENTER)
        
        col_widths = [90*mm, 22*mm, 22*mm, 35*mm]
        
        table_data = [[
            Paragraph(f"<b>{t.get('description', 'Description')}</b>", th_style),
            Paragraph(f"<b>{t.get('qty', 'Qty')}</b>", th_style),
            Paragraph(f"<b>{t.get('unit', 'Unit')}</b>", th_style),
            Paragraph(f"<b>{t.get('price', 'Price')}</b>", th_style),
        ]]
        
        subtotal = 0
        total_vat = 0
        
        for i, line in enumerate(self.data.lines):
            net = line.unit_price
            line_net = net * line.quantity
            line_gross = line_net * (1 + line.vat_rate)
            subtotal += line_net
            total_vat += line_net * line.vat_rate
            
            bg = TABLE_ROW_ALT if i % 2 == 0 else white
            
            row = [
                Paragraph(line.description, td_left),
                Paragraph(f"{line.quantity:.2f}", td_right),
                Paragraph(line.unit, td_center),
                Paragraph(f"€ {net:.2f}", td_right),
            ]
            table_data.append(row)
        
        if not self.data.lines:
            table_data.append(["", "", "", ""])
        
        items_table = Table(table_data, colWidths=col_widths)
        
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("TOPPADDING", (0, 0), (-1, 0), 4*mm),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4*mm),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TOPPADDING", (0, 1), (-1, -1), 3*mm),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3*mm),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("BOX", (0, 0), (-1, -1), 1, DARK),
        ]
        
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ROW_ALT))
        
        items_table.setStyle(TableStyle(style_cmds))
        elements.append(items_table)
        elements.append(Spacer(1, 4*mm))
        
        # ============================================================
        # TOTALS - right aligned
        # ============================================================
        
        # TOTALS - single column with label on left, value on right, big gap between them
        # alignment=TA_RIGHT on the cell keeps everything right-aligned
        tl = ParagraphStyle("TL", fontSize=10, fontName="Helvetica", textColor=DARK, alignment=TA_RIGHT)
        tv = ParagraphStyle("TV", fontSize=10, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
        gl = ParagraphStyle("GL", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
        
        grand_total = subtotal + total_vat
        
        lines_data = []
        if total_vat > 0:
            label1 = f"{t.get('subtotal', 'Subtotal')}"
            label2 = f"{t.get('vat', 'VAT')} (20%)"
        else:
            label1 = f"{t.get('subtotal', 'Subtotal')}"
            label2 = vat_na if self.inv_lang != "en" and self.inv_lang != "ru" else ("VAT not applicable" if self.inv_lang == "en" else "НДС не применяется")
        label3 = f"{t.get('total', 'TOTAL')}"
        
        val1 = f"€{subtotal:.2f}"
        val2 = f"€{total_vat:.2f}" if total_vat > 0 else "€0.00"
        val3 = f"€{grand_total:.2f}"
        
        # Use 2-column table: label | value with proper spacing
        # Label width = 80mm, Value width = 89mm, gap = space between
        tl_val = ParagraphStyle("TLV", fontSize=10, fontName="Helvetica", textColor=DARK, alignment=TA_LEFT)
        tv_val = ParagraphStyle("TVV", fontSize=10, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_LEFT)
        gl_val = ParagraphStyle("GLV", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_LEFT)
        
        tv_val_right = ParagraphStyle("TVVR", fontSize=10, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
        gl_val_right = ParagraphStyle("GLVR", fontSize=14, fontName="Helvetica-Bold", textColor=DARK, alignment=TA_RIGHT)
        
        # 2 columns: label (left-aligned) | value (right-aligned)
        totals_data = [
            [Paragraph(label1, tl_val), Paragraph(val1, tv_val_right)],
            [Paragraph(label2, tv_val), Paragraph(val2, tv_val_right)],
            [Paragraph(label3, gl_val), Paragraph(val3, gl_val_right)],
        ]
        
        totals_table = Table(totals_data, colWidths=[90*mm, 79*mm])
        totals_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 3*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("LINEABOVE", (0, 2), (-1, 2), 2, DARK),
        ]))
        elements.append(totals_table)
        # ============================================================
        # NOTES (if any)
        # ============================================================
        if self.data.notes:
            elements.append(Spacer(1, 6*mm))
            notes_label_style = ParagraphStyle("NotesLabel", fontSize=8, fontName="Helvetica-Bold",
                                              textColor=LIGHT_GRAY, leading=10)
            notes_style = ParagraphStyle("NotesText", fontSize=8, fontName="Helvetica",
                                          textColor=LIGHT_GRAY, leading=10)
            elements.append(Paragraph(f"<b>{t.get('notes', 'Notes')}:</b>", notes_label_style))
            elements.append(Paragraph(self.data.notes, notes_style))
        
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        elements.append(Spacer(1, 4*mm))
        
        # ============================================================
        # FOOTER: Seller/Our company (left) | Contact (center) | Bank (right)
        # ============================================================
        
        fl = ParagraphStyle("FL", fontSize=7, fontName="Helvetica-Bold", textColor=LIGHT_GRAY, leading=9, spaceAfter=1*mm)
        fv = ParagraphStyle("FV", fontSize=8, fontName="Helvetica", textColor=DARK, leading=10)
        fv_bold = ParagraphStyle("FVB", fontSize=8, fontName="Helvetica-Bold", textColor=DARK, leading=10)
        
        seller = self.data.seller
        
        # Seller company name - no label, just name in bold
        col1 = []
        if seller.name:
            col1.append(Paragraph(seller.name, fv_bold))
        if seller.registry_code:
            col1.append(Paragraph(f"{t.get('registry', 'Reg.')}: {seller.registry_code}", fv))
        if seller.vat_number:
            col1.append(Paragraph(f"{t.get('vat', 'VAT')}: {seller.vat_number}", fv))
        if seller.address:
            col1.append(Paragraph(seller.address, fv))
        if seller.city or seller.postal_code:
            col1.append(Paragraph(f"{seller.postal_code or ''} {seller.city or ''}".strip(), fv))
        
        col2 = []
        if seller.phone:
            col2.append(Paragraph(f"<b>{t.get('phone', 'Phone')}</b>", fl))
            col2.append(Paragraph(seller.phone, ParagraphStyle("PV", fontSize=9, fontName="Helvetica", textColor=DARK, leading=12)))
        if seller.email:
            col2.append(Spacer(1, 3*mm))  # More space between Phone and Email
            col2.append(Paragraph(f"<b>{t.get('email', 'Email')}</b>", fl))
            col2.append(Paragraph(seller.email, ParagraphStyle("EV", fontSize=9, fontName="Helvetica", textColor=DARK, leading=12)))
        if not col2:
            col2 = [Paragraph("", fv)]
        
        col3 = []
        if self.data.payment.bank_name:
            col3.append(Paragraph(f"<b>{t.get('bank', 'Bank')}</b>", fl))
            col3.append(Paragraph(self.data.payment.bank_name, fv))
        if self.data.payment.iban:
            col3.append(Paragraph(f"<b>{t.get('iban', 'IBAN')}</b>", fl))
            col3.append(Paragraph(self.data.payment.iban, ParagraphStyle("IBAN", fontSize=9,
                                fontName="Helvetica-Bold", textColor=DARK, leading=12)))
        if self.data.payment.bic:
            col3.append(Paragraph(f"<b>{t.get('bic', 'BIC')}</b>", fl))
            col3.append(Paragraph(self.data.payment.bic, fv))
        if not col3:
            col3 = [Paragraph("", fv)]
        
        # Footer: 3 columns on page - company LEFT, contact CENTER, bank RIGHT
        # Each column 1/3 of page width (169mm total = items table width)
        footer_table = Table([[col1, col2, col3]], colWidths=[56*mm, 57*mm, 56*mm])
        footer_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),     # company left-aligned
            ("ALIGN", (1, 0), (1, 0), "CENTER"),   # contact center-aligned  
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),    # bank right-aligned
        ]))
        elements.append(footer_table)
        
        elements.append(Spacer(1, 2*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        
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
             sg.Text("", size=(5, 1)),
             sg.Button("Check Updates", key="-CHECK_UPDATE-", size=(12, 1), button_color=("#4a5568", "#e2e8f0")),
             sg.Text("", size=(2, 1)),
             sg.Text(f"v{CURRENT_VERSION}", text_color="#999")], 
            [sg.HorizontalSeparator()],
            [sg.TabGroup([
                [sg.Tab(tr("my_company"), company_tab),
                 sg.Tab(tr("new_invoice"), invoice_tab),
                 sg.Tab(tr("accounting"), accounting_tab),
                 sg.Tab(tr("invoice_history"), history_tab)],
            ])],
        ]
        
        window = sg.Window("ee-invoice-generator", layout, size=(700, 650), resizable=True)
        
        # Check for updates on startup (non-blocking)
        update_info = check_for_updates()
        if update_info:
            new_ver, html_url, exe_url = update_info
            # Show startup notification but don't auto-download
            sg.popup_non_blocking(
                f"🎉 New version available: v{new_ver}\n\n"
                f"Click 'Check Updates' to download and install.",
                title="Update Available"
            )
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, "Exit"):
                return
            
            elif event == "-CHECK_UPDATE-":
                update_info = check_for_updates()
                if update_info:
                    new_ver, html_url, exe_url = update_info
                    # Ask user if they want to update
                    choice = sg.popup_yes_no(
                        f"🎉 New version available: v{new_ver}\n\n"
                        f"You have: v{CURRENT_VERSION}\n\n"
                        f"Download and install now?\n"
                        f"(Program will restart automatically)",
                        title="Update Available"
                    )
                    if choice == "Yes":
                        if download_and_update(new_ver, exe_url):
                            window.close()  # Close and let updater handle restart
                            return
                else:
                    sg.popup(f"You're running the latest version (v{CURRENT_VERSION})",
                             title="No Update")
            
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
                    vat_str = values["-L_VAT-"] or "N/A"
                    if vat_str in ("N/A", "0%", "0"):
                        vat_rate = 0.0
                    elif vat_str == "20%" or vat_str == "20":
                        vat_rate = 0.20
                    elif vat_str == "9%" or vat_str == "9":
                        vat_rate = 0.09
                    else:
                        vat_rate = 0.0
                    
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
                    
                    inv_date_str = values["-INV_DATE-"].strip()
                    if not inv_date_str:
                        sg.popup_error(tr("date_required") + " (format: DD.MM.YYYY)")
                        continue
                    inv_date = parse_date(inv_date_str)
                    if not inv_date:
                        sg.popup_error("Invalid date! Use format: DD.MM.YYYY (e.g. 28.05.2026)")
                        continue
                    
                    due_date = None
                    if values["-INV_DUE-"].strip():
                        due_date = parse_date(values["-INV_DUE-"].strip())
                        if not due_date:
                            sg.popup_error("Invalid due date! Use format: DD.MM.YYYY")
                            continue
                    
                    invoice_data = InvoiceData(
                        seller=seller, buyer=buyer,
                        invoice_number=values["-INV_NUM-"].strip(),
                        invoice_date=inv_date, due_date=due_date,
                        lines=lines.copy(), payment=payment,
                        order_reference=None,
                        notes=values["-INV_NOTES-"].strip() or None,
                        currency=values.get("-INV_CURRENCY-", "EUR"),
                    )
                    
                    output_dir = Path(values["-OUT_DIR-"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    inv_num = values["-INV_NUM-"].strip().replace("/", "-")
                    date_str = inv_date.strftime("%Y%m%d")
                    
                    # Auto-increment if invoice number already exists in DB
                    base_inv_num = inv_num
                    counter = 1
                    while DB.invoice_number_exists(inv_num):
                        counter += 1
                        inv_num = f"{base_inv_num}-{counter:03d}"
                    
                    # Calculate totals from lines for DB save
                    calc_subtotal = sum(l.unit_price * l.quantity for l in lines)
                    calc_total_vat = sum(l.unit_price * l.quantity * l.vat_rate for l in lines)
                    calc_grand_total = calc_subtotal + calc_total_vat
                    calc_currency = invoice_data.currency if hasattr(invoice_data, 'currency') else "EUR"
                    
                    # Save to DB history with all invoice data
                    try:
                        import json
                        # Store full buyer/seller/payment data as JSON for reconstruction
                        full_data = {
                            "buyer": {
                                "name": invoice_data.buyer.name if invoice_data.buyer else None,
                                "address": invoice_data.buyer.address if invoice_data.buyer else None,
                                "city": invoice_data.buyer.city if invoice_data.buyer else None,
                                "postal_code": invoice_data.buyer.postal_code if invoice_data.buyer else None,
                                "registry_code": invoice_data.buyer.registry_code if invoice_data.buyer else None,
                                "vat_number": invoice_data.buyer.vat_number if invoice_data.buyer else None,
                            },
                            "seller": {
                                "name": invoice_data.seller.name if invoice_data.seller else None,
                                "address": invoice_data.seller.address if invoice_data.seller else None,
                                "city": invoice_data.seller.city if invoice_data.seller else None,
                                "postal_code": invoice_data.seller.postal_code if invoice_data.seller else None,
                                "registry_code": invoice_data.seller.registry_code if invoice_data.seller else None,
                                "vat_number": invoice_data.seller.vat_number if invoice_data.seller else None,
                                "phone": invoice_data.seller.phone if invoice_data.seller else None,
                                "email": invoice_data.seller.email if invoice_data.seller else None,
                            },
                            "payment": {
                                "bank_name": invoice_data.payment.bank_name if invoice_data.payment else None,
                                "iban": invoice_data.payment.iban if invoice_data.payment else None,
                                "bic": invoice_data.payment.bic if invoice_data.payment else None,
                            },
                        }
                        
                        invoice_record = {
                            "invoice_number": inv_num,
                            "invoice_date": inv_date.isoformat() if inv_date else "",
                            "due_date": due_date.isoformat() if due_date else None,
                            "total_excl_vat": calc_subtotal,
                            "vat_amount": calc_total_vat,
                            "total_incl_vat": calc_grand_total,
                            "currency": calc_currency,
                            "status": "completed",
                            "notes": invoice_data.notes,
                            "xml_data": json.dumps(full_data),  # Store buyer/seller/payment as JSON
                        }
                        DB.save_invoice(invoice_record, [
                            {"description": l.description, "quantity": l.quantity, 
                             "unit": l.unit, "unit_price": l.unit_price,
                             "vat_rate": l.vat_rate, "line_total": l.unit_price * l.quantity * (1 + l.vat_rate)}
                            for l in lines
                        ])
                    except Exception as db_err:
                        sg.popup_error(f"Database save error / Andmebaasi viga: {db_err}")
                    
                    generated = []
                    xml_path = None
                    if values.get("-GEN_XML-"):
                        xml_path = output_dir / f"invoice_{inv_num}.xml"
                        InvoiceGenerator(invoice_data).save(str(xml_path))
                        generated.append(f"XML")
                    if values.get("-GEN_PDF-"):
                        pdf_path = output_dir / f"invoice_{inv_num}.pdf"
                        ProfessionalInvoiceGenerator(invoice_data, CURRENT_LANG[0]).save(str(pdf_path))
                        generated.append(f"PDF")
                    
                    window["-INV_STATUS-"].update(tr("success"), text_color="#333")
                    
                    # Build result message
                    msg = tr("success") + "\n\n" + "\n".join(generated)
                    if xml_path:
                        msg += f"\n\n{tr('xml_location')}\n{str(xml_path)}"
                    
                    # Offer e-invoice submission options if XML was generated
                    if xml_path and xml_path.exists():
                        msg += "\n\n" + tr("einvoice_sent") + "\n\nOpen Tax Portal (e-MTA)?"
                        choice = sg.popup_yes_no(msg, title=tr("success"))
                        if choice == "Yes":
                            webbrowser.open("https://www.emta.ee/")
                        # Always offer to open file location
                        if sys.platform == "win32":
                            subprocess.run(["explorer", str(xml_path.parent)])
                        else:
                            subprocess.run(["xdg-open", str(xml_path.parent)])
                    else:
                        sg.popup_ok(msg)
                    
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
            
            elif event == "-HIST_DELETE-":
                selected = values["-HIST_TABLE-"]
                if not selected:
                    return
                invoices = DB.list_invoices()
                idx = selected[0]
                if idx >= len(invoices):
                    return
                inv = invoices[idx]
                inv_num = inv.get("invoice_number", "")
                
                if sg.popup_yes_no(
                    f"Delete invoice {inv_num}?\n\nThis cannot be undone.",
                    title="Confirm Delete"
                ) == "Yes":
                    try:
                        DB.delete_invoice(inv.get("id"))
                        refresh_history(window)
                        window["-HIST_DETAILS-"].update("")
                        window["-HIST_STATUS-"].update(f"Deleted {inv_num}", text_color="green")
                    except Exception as e:
                        sg.popup_error(f"Delete failed: {e}")
            
            elif event == "-HIST_CLEAR-":
                if sg.popup_yes_no(
                    "Delete ALL invoices?\n\nThis removes all history and cannot be undone.",
                    title="Confirm Clear All"
                ) == "Yes":
                    if sg.popup_yes_no(
                        "Are you absolutely sure?\n\nType 'yes' in the next popup to confirm.",
                        title="Final Confirmation"
                    ) == "Yes":
                        try:
                            DB.clear_all_invoices()
                            refresh_history(window)
                            window["-HIST_DETAILS-"].update("")
                            window["-HIST_STATUS-"].update("All invoices cleared", text_color="green")
                        except Exception as e:
                            sg.popup_error(f"Clear failed: {e}")


if __name__ == "__main__":
    main()
