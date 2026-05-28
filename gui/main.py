"""
ee-invoice-generator GUI v0.2.0
"""
import PySimpleGUI as sg
import json
import os
from datetime import date, datetime
from pathlib import Path

from einvoice import InvoiceGenerator, PDFGenerator
from einvoice.generator import InvoiceData, PartyDetails, InvoiceLine, PaymentDetails
from einvoice.accounting import Database

# Language strings
LANG = {
    "en": {
        "title": "ee-invoice-generator",
        "my_company": "My Company",
        "new_invoice": "New Invoice",
        "accounting": "Accounting",
        "invoice_history": "History",
        "language": "Language",
        # Steps
        "step1_title": "Your Company Details",
        "step2_title": "Customer Details", 
        "step3_title": "Invoice Items",
        "step4_title": "Review & Generate",
        "back": "← Back",
        "next": "Next →",
        "generate": "Generate",
        "cancel": "Cancel",
        # Labels
        "company_name": "Company Name *",
        "registry_code": "Registry Code *",
        "vat_number": "VAT Number",
        "address": "Address",
        "city": "City",
        "postal_code": "Postal Code",
        "email": "Email",
        "phone": "Phone",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Bank Name",
        "buyer_same": "Same as My Company",
        "buyer_same_hint": "(copy your company data)",
        "buyer_name": "Customer Name *",
        "buyer_registry": "Registry Code",
        "buyer_vat": "VAT Number",
        "buyer_addr": "Address",
        "buyer_city": "City",
        "buyer_postal": "Postal Code",
        "buyer_country": "Country",
        "buyer_email": "Email",
        "invoice_number": "Invoice Number *",
        "currency": "Currency",
        "invoice_date": "Invoice Date *",
        "due_date": "Due Date",
        "order_ref": "Order Reference",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "total": "Total (€)",
        "vat_rate": "VAT %",
        "add_line": "Add Line",
        "remove_last": "Remove Last",
        "lines_count": "Lines:",
        "notes": "Notes",
        "notes_hint": "Additional terms, bank details...",
        "output_folder": "Output Folder",
        "gen_xml": "Generate XML (e-invoice)",
        "gen_pdf": "Generate PDF (printable)",
        "clear_form": "Clear",
        "save_company": "Save",
        # Tooltips
        "tip_company_name": "Your registered company name, e.g., XworCore OÜ",
        "tip_registry": "Estonian registry code (8 digits)",
        "tip_vat": "KMKR number (e.g., EE123456789). Leave empty if not VAT registered.",
        "tip_address": "Your legal address in Estonia",
        "tip_email": "Email for invoice replies",
        "tip_phone": "Contact phone number",
        "tip_iban": "Your IBAN (e.g., EE00 1234 5678...)",
        "tip_bic": "Bank SWIFT/BIC code (8 chars, e.g., HABAEE2S)",
        "tip_invoice_num": "Unique invoice number. Auto-generated but editable.",
        "tip_invoice_date": "Invoice date. Format: DD.MM.YYYY",
        "tip_due_date": "Payment due date. Leave empty for immediate payment.",
        "tip_total_w_vat": "Enter TOTAL price including VAT - system calculates net",
        "status_ready": "Ready",
        "status_saved": "Company data saved!",
        "saved": "Saved",
    },
    "ru": {
        "title": "ee-invoice-generator",
        "my_company": "Моя Компания",
        "new_invoice": "Новый Счёт",
        "accounting": "Бухгалтерия",
        "invoice_history": "История",
        "language": "Язык",
        # Steps
        "step1_title": "Данные Вашей Компании",
        "step2_title": "Данные Покупателя",
        "step3_title": "Позиции Счёта",
        "step4_title": "Проверка и Генерация",
        "back": "← Назад",
        "next": "Далее →",
        "generate": "Создать",
        "cancel": "Отмена",
        # Labels
        "company_name": "Название Компании *",
        "registry_code": "Рег. Номер *",
        "vat_number": "Номер НДС",
        "address": "Адрес",
        "city": "Город",
        "postal_code": "Почтовый Индекс",
        "email": "Email",
        "phone": "Телефон",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Название Банка",
        "buyer_same": "Как Моя Компания",
        "buyer_same_hint": "(скопировать ваши данные)",
        "buyer_name": "Название Покупателя *",
        "buyer_registry": "Рег. Номер",
        "buyer_vat": "Номер НДС",
        "buyer_addr": "Адрес",
        "buyer_city": "Город",
        "buyer_postal": "Почтовый Индекс",
        "buyer_country": "Страна",
        "buyer_email": "Email",
        "invoice_number": "Номер Счёта *",
        "currency": "Валюта",
        "invoice_date": "Дата Счёта *",
        "due_date": "Срок Оплаты",
        "order_ref": "Номер Заказа",
        "description": "Описание",
        "qty": "Кол-во",
        "unit": "Ед.",
        "total": "Итого (€)",
        "vat_rate": "НДС %",
        "add_line": "Добавить",
        "remove_last": "Удалить",
        "lines_count": "Позиций:",
        "notes": "Заметки",
        "notes_hint": "Дополнительные условия, реквизиты...",
        "output_folder": "Папка",
        "gen_xml": "XML (e-invoice)",
        "gen_pdf": "PDF (печать)",
        "clear_form": "Очистить",
        "save_company": "Сохранить",
        # Tooltips
        "tip_company_name": "Название вашей компании, напр. XworCore OÜ",
        "tip_registry": "Регистрационный код (8 цифр)",
        "tip_vat": "Номер KMKR (напр., EE123456789)",
        "tip_address": "Юридический адрес в Эстонии",
        "tip_email": "Email для ответов на счета",
        "tip_phone": "Контактный телефон",
        "tip_iban": "Ваш IBAN (напр., EE00 1234 5678...)",
        "tip_bic": "SWIFT/BIC код банка (8 символов)",
        "tip_invoice_num": "Уникальный номер счёта. Вводится автоматически.",
        "tip_invoice_date": "Дата выставления счёта. Формат: ДД.ММ.ГГГГ",
        "tip_due_date": "Срок оплаты. Оставьте пустым для немедленной оплаты.",
        "tip_total_w_vat": "Вводите ЦЕНУ С НДС - система сама вычтет налог",
        "status_ready": "Готово",
        "status_saved": "Данные компании сохранены!",
        "saved": "Сохранено",
    },
    "et": {
        "title": "ee-invoice-generator",
        "my_company": "Minu Ettevõte",
        "new_invoice": "Uus Arve",
        "accounting": "Raamatupidamine",
        "invoice_history": "Ajalugu",
        "language": "Keel",
        # Steps
        "step1_title": "Teie Ettevõte",
        "step2_title": "Kliendi Andmed",
        "step3_title": "Arve Read",
        "step4_title": "Ülevaade ja Genereerimine",
        "back": "← Tagasi",
        "next": "Edasi →",
        "generate": "Genereeri",
        "cancel": "Tühistama",
        # Labels
        "company_name": "Ettevõte Nimi *",
        "registry_code": "Registrikood *",
        "vat_number": "KMKR",
        "address": "Aadress",
        "city": "Linn",
        "postal_code": "Postiindeks",
        "email": "Email",
        "phone": "Telefon",
        "iban": "IBAN *",
        "bic": "BIC/SWIFT *",
        "bank_name": "Panga Nimi",
        "buyer_same": "Same as Minu Ettevõte",
        "buyer_same_hint": "(kopeeri ettevõtte andmed)",
        "buyer_name": "Kliendi Nimi *",
        "buyer_registry": "Registrikood",
        "buyer_vat": "KMKR",
        "buyer_addr": "Aadress",
        "buyer_city": "Linn",
        "buyer_postal": "Postiindeks",
        "buyer_country": "Riik",
        "buyer_email": "Email",
        "invoice_number": "Arve Number *",
        "currency": "Valuuta",
        "invoice_date": "Arve Kuupäev *",
        "due_date": "Tähtpäev",
        "order_ref": "Tellimuse Viide",
        "description": "Kirjeldus",
        "qty": "Kogus",
        "unit": "Ühik",
        "total": "Kokku (€)",
        "vat_rate": "Käibemaks %",
        "add_line": "Lisa Rida",
        "remove_last": "Eemalda Viimane",
        "lines_count": "Read:",
        "notes": "Märkused",
        "notes_hint": "Lisatingimused, pangarekvisiidid...",
        "output_folder": "Kaust",
        "gen_xml": "XML (e-arve)",
        "gen_pdf": "PDF (prindi)",
        "clear_form": "Puhasta",
        "save_company": "Salvesta",
        # Tooltips
        "tip_company_name": "Teie registreeritud ettevõtte nimi",
        "tip_registry": "Eesti registrikood (8 numbrit)",
        "tip_vat": "KMKR number (näit. EE123456789)",
        "tip_address": "Teie juriidiline aadress",
        "tip_email": "Email arvete vastusteks",
        "tip_phone": "Kontakt-telefon",
        "tip_iban": "Teie IBAN (näit. EE00 1234...)",
        "tip_bic": "Panga SWIFT/BIC kood",
        "tip_invoice_num": "Kordumatu arve number. Genereeritakse automaatselt.",
        "tip_invoice_date": "Arve kuupäev. Vorming: DD.MM.YYYY",
        "tip_due_date": "Maksetähtpäev. Tühjaks tuvislikuks.",
        "tip_total_w_vat": "Sisesta HIND koos käibemaksuga - süsteem arvutab netohinna ise",
        "status_ready": "Valmis",
        "status_saved": "Ettevõte salvestatud!",
        "saved": "Salvestatud",
    },
}

# Global state
CONFIG_DIR = Path.home() / ".ee-invoice-generator"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB = Database()
CURRENT_LANG = ["en"]


def tr(key):
    """Get translation for current language"""
    return LANG[CURRENT_LANG[0]].get(key, key)


def set_lang(lang):
    CURRENT_LANG[0] = lang
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_DIR / "language.json", "w") as f:
        json.dump({"lang": lang}, f)


def load_lang():
    lang_file = CONFIG_DIR / "language.json"
    if lang_file.exists():
        try:
            with open(lang_file) as f:
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
# COMPANY EDITOR (standalone window)
# ============================================================
def open_company_window():
    config = load_config()
    
    layout = [
        [sg.Text(tr("step1_title"), font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        [sg.Frame("Company Information", [
            [sg.Text(tr("company_name"), size=(15, 1)),
             sg.Input(default_text=config.get("name", ""), key="-NAME-", size=(40, 1),
                     tooltip=tr("tip_company_name"))],
            [sg.Text(tr("registry_code"), size=(15, 1)),
             sg.Input(default_text=config.get("registry_code", ""), key="-REGISTRY-", size=(20, 1),
                     tooltip=tr("tip_registry"))],
            [sg.Text(tr("vat_number"), size=(15, 1)),
             sg.Input(default_text=config.get("vat_number", ""), key="-VAT-", size=(20, 1),
                     tooltip=tr("tip_vat"))],
            [sg.Text(tr("address"), size=(15, 1)),
             sg.Input(default_text=config.get("address", ""), key="-ADDR-", size=(40, 1),
                     tooltip=tr("tip_address"))],
            [sg.Text(tr("city"), size=(15, 1)),
             sg.Input(default_text=config.get("city", ""), key="-CITY-", size=(25, 1))],
            [sg.Text(tr("postal_code"), size=(15, 1)),
             sg.Input(default_text=config.get("postal_code", ""), key="-POSTAL-", size=(10, 1))],
            [sg.Text(tr("email"), size=(15, 1)),
             sg.Input(default_text=config.get("email", ""), key="-EMAIL-", size=(30, 1),
                     tooltip=tr("tip_email"))],
            [sg.Text(tr("phone"), size=(15, 1)),
             sg.Input(default_text=config.get("phone", ""), key="-PHONE-", size=(20, 1),
                     tooltip=tr("tip_phone"))],
        ])],
        
        [sg.Frame("Bank Details", [
            [sg.Text(tr("iban"), size=(15, 1)),
             sg.Input(default_text=config.get("iban", ""), key="-IBAN-", size=(25, 1),
                     tooltip=tr("tip_iban"))],
            [sg.Text(tr("bic"), size=(15, 1)),
             sg.Input(default_text=config.get("bic", ""), key="-BIC-", size=(12, 1),
                     tooltip=tr("tip_bic"))],
            [sg.Text(tr("bank_name"), size=(15, 1)),
             sg.Input(default_text=config.get("bank_name", ""), key="-BANK-", size=(30, 1))],
        ])],
        
        [sg.HorizontalSeparator()],
        [sg.Button(tr("save_company"), key="-SAVE-", size=(12, 1), button_color=("white", "#2c5282"))],
        [sg.Text("", key="-STATUS-", text_color="green")],
    ]
    
    win = sg.Window(f"ee-invoice - {tr('my_company')}", layout, size=(550, 550), modal=True)
    
    while True:
        event, values = win.read()
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        elif event == "-SAVE-":
            c = {
                "name": values["-NAME-"].strip(),
                "registry_code": values["-REGISTRY-"].strip(),
                "vat_number": values["-VAT-"].strip(),
                "address": values["-ADDR-"].strip(),
                "city": values["-CITY-"].strip(),
                "postal_code": values["-POSTAL-"].strip(),
                "email": values["-EMAIL-"].strip(),
                "phone": values["-PHONE-"].strip(),
                "iban": values["-IBAN-"].strip(),
                "bic": values["-BIC-"].strip(),
                "bank_name": values["-BANK-"].strip(),
            }
            save_config(c)
            win["-STATUS-"].update(tr("status_saved"), text_color="green")
    
    win.close()


# ============================================================
# INVOICE WIZARD (standalone window with step navigation)
# ============================================================
def open_invoice_wizard():
    """Open invoice creation wizard"""
    lines = []
    step = [1]
    content_elem = [None]
    
    def nav_buttons(step_num):
        return [
            sg.Button(tr("back"), key="-BACK-", size=(12, 1),
                     disabled=(step_num == 1)),
            sg.Text(f"{step_num}/4", font=("Helvetica", 10, "bold"), key="-STEP_NUM-"),
            sg.Button(tr("next"), key="-NEXT-", size=(12, 1),
                     button_color=("white", "#2c5282") if step_num < 4 else ("white", "#888"),
                     disabled=(step_num == 4)),
        ]
    
    def step1():
        config = load_config()
        return [
            [sg.Text(tr("step1_title"), font=("Helvetica", 14, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text(tr("tip_company_name"), font=("Helvetica", 8, "italic"), text_color="#666")],
            [sg.Frame("Company Information", [
                [sg.Text(tr("company_name"), size=(15, 1)),
                 sg.Input(default_text=config.get("name", ""), key="-S_NAME-", size=(40, 1),
                         tooltip=tr("tip_company_name"))],
                [sg.Text(tr("registry_code"), size=(15, 1)),
                 sg.Input(default_text=config.get("registry_code", ""), key="-S_REG-", size=(20, 1),
                         tooltip=tr("tip_registry"))],
                [sg.Text(tr("vat_number"), size=(15, 1)),
                 sg.Input(default_text=config.get("vat_number", ""), key="-S_VAT-", size=(20, 1),
                         tooltip=tr("tip_vat"))],
                [sg.Text(tr("address"), size=(15, 1)),
                 sg.Input(default_text=config.get("address", ""), key="-S_ADDR-", size=(40, 1),
                         tooltip=tr("tip_address"))],
                [sg.Text(tr("city"), size=(15, 1)),
                 sg.Input(default_text=config.get("city", ""), key="-S_CITY-", size=(25, 1))],
                [sg.Text(tr("postal_code"), size=(15, 1)),
                 sg.Input(default_text=config.get("postal_code", ""), key="-S_POSTAL-", size=(10, 1))],
                [sg.Text(tr("email"), size=(15, 1)),
                 sg.Input(default_text=config.get("email", ""), key="-S_EMAIL-", size=(30, 1),
                         tooltip=tr("tip_email"))],
                [sg.Text(tr("phone"), size=(15, 1)),
                 sg.Input(default_text=config.get("phone", ""), key="-S_PHONE-", size=(20, 1),
                         tooltip=tr("tip_phone"))],
            ])],
            [sg.Frame("Bank Details", [
                [sg.Text(tr("iban"), size=(15, 1)),
                 sg.Input(default_text=config.get("iban", ""), key="-S_IBAN-", size=(25, 1),
                         tooltip=tr("tip_iban"))],
                [sg.Text(tr("bic"), size=(15, 1)),
                 sg.Input(default_text=config.get("bic", ""), key="-S_BIC-", size=(12, 1),
                         tooltip=tr("tip_bic"))],
                [sg.Text(tr("bank_name"), size=(15, 1)),
                 sg.Input(default_text=config.get("bank_name", ""), key="-S_BANK-", size=(30, 1))],
            ])],
        ]
    
    def step2():
        return [
            [sg.Text(tr("step2_title"), font=("Helvetica", 14, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox(tr("buyer_same"), key="-BUYER_SAME-", enable_events=True,
                        tooltip=tr("buyer_same_hint"))],
            [sg.Frame("Customer Information", [
                [sg.Text(tr("buyer_name"), size=(15, 1)),
                 sg.Input(key="-B_NAME-", size=(40, 1), tooltip="Customer company name")],
                [sg.Text(tr("buyer_registry"), size=(15, 1)),
                 sg.Input(key="-B_REG-", size=(20, 1), tooltip="Registry code")],
                [sg.Text(tr("buyer_vat"), size=(15, 1)),
                 sg.Input(key="-B_VAT-", size=(20, 1), tooltip="VAT number")],
                [sg.Text(tr("buyer_addr"), size=(15, 1)),
                 sg.Input(key="-B_ADDR-", size=(40, 1))],
                [sg.Text(tr("buyer_city"), size=(15, 1)),
                 sg.Input(key="-B_CITY-", size=(25, 1))],
                [sg.Text(tr("buyer_postal"), size=(15, 1)),
                 sg.Input(key="-B_POSTAL-", size=(10, 1))],
                [sg.Text(tr("buyer_country"), size=(15, 1)),
                 sg.Input(default_text="EE", key="-B_COUNTRY-", size=(5, 1))],
                [sg.Text(tr("buyer_email"), size=(15, 1)),
                 sg.Input(key="-B_EMAIL-", size=(30, 1))],
            ])],
        ]
    
    def step3():
        return [
            [sg.Text(tr("step3_title"), font=("Helvetica", 14, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Text(tr("tip_total_w_vat"), font=("Helvetica", 8, "italic"), text_color="#666")],
            [sg.Frame("Invoice Meta", [
                [sg.Text(tr("invoice_number"), size=(15, 1)),
                 sg.Input(default_text=DB.generate_invoice_number(), key="-INV_NUM-", size=(20, 1),
                         tooltip=tr("tip_invoice_num")),
                 sg.Text(tr("currency"), size=(10, 1)),
                 sg.Combo(["EUR"], default_value="EUR", key="-CURR-", size=(8, 1))],
                [sg.Text(tr("invoice_date"), size=(15, 1)),
                 sg.Input(default_text=date.today().strftime("%d.%m.%Y"), key="-INV_DATE-", size=(15, 1),
                         tooltip=tr("tip_invoice_date")),
                 sg.Text(tr("due_date"), size=(10, 1)),
                 sg.Input(key="-DUE_DATE-", size=(15, 1),
                         tooltip=tr("tip_due_date"))],
                [sg.Text(tr("order_ref"), size=(15, 1)),
                 sg.Input(key="-ORDER_REF-", size=(20, 1))],
            ])],
            [sg.Frame("Line Items", [
                [sg.Text(tr("description"), size=(28, 1)),
                 sg.Text(tr("qty"), size=(6, 1)),
                 sg.Text(tr("unit"), size=(8, 1)),
                 sg.Text(tr("total"), size=(10, 1)),
                 sg.Text(tr("vat_rate"), size=(8, 1))],
                [sg.Input(key="-L_DESC-", size=(28, 1), tooltip="What was sold"),
                 sg.Input(default_text="1", key="-L_QTY-", size=(6, 1), tooltip="Quantity"),
                 sg.Combo(["pcs", "h", "km", "kg", "month", "year"], default_value="pcs", key="-L_UNIT-", size=(8, 1)),
                 sg.Input(default_text="0.00", key="-L_PRICE-", size=(10, 1), tooltip="TOTAL with VAT"),
                 sg.Combo(["0", "20", "9"], default_value="20", key="-L_VAT-", size=(8, 1), tooltip="VAT %")],
                [sg.Button(tr("add_line"), key="-ADD_LINE-", size=(12, 1), button_color=("white", "#2c5282")),
                 sg.Button(tr("remove_last"), key="-REMOVE_LAST-", size=(12, 
1))],
                [sg.Text(tr("lines_count"), size=(6, 1)),
                 sg.Listbox(values=[], key="-LINES_BOX-", size=(75, 8),
                           tooltip="Line items list")],
            ])],
            [sg.Frame(tr("notes"), [
                [sg.Multiline(key="-NOTES-", size=(70, 3), tooltip=tr("notes_hint"))],
            ])],
        ]
    
    def step4(values, lines):
        # Build invoice summary
        try:
            inv_date = parse_date(values.get("-INV_DATE-", ""))
            inv_num = values.get("-INV_NUM-", "")
            buyer = values.get("-B_NAME-", "")
            
            # Calculate totals
            subtotal = 0
            vat_amounts = {}
            for line in lines:
                net = line.unit_price
                sub = net * line.quantity
                subtotal += sub
                if line.vat_rate not in vat_amounts:
                    vat_amounts[line.vat_rate] = 0
                vat_amounts[line.vat_rate] += sub * line.vat_rate
            total_vat = sum(vat_amounts.values())
            total = subtotal + total_vat
            
            summary = f"""
INVOICE SUMMARY
{'='*50}
Invoice No.:     {inv_num}
Date:           {inv_date.strftime('%d.%m.%Y') if inv_date else ''}
Buyer:          {buyer}

LINE ITEMS:
{'='*50}
{'#':<4} {'Description':<30} {'Qty':>6} {'Unit':<5} {'Net':>8} {'VAT%':>5} {'Gross':>10}
{'-'*64}
"""
            for i, line in enumerate(lines, 1):
                gross = line.unit_price * (1 + line.vat_rate) * line.quantity
                summary += f"{i:<4} {line.description[:30]:<30} {line.quantity:>6.2f} {line.unit:<5} {line.unit_price:>8.2f} {line.vat_rate*100:>5.0f} {gross:>10.2f}\n"
            
            summary += f"""
{'='*50}
Subtotal (net):  € {subtotal:.2f}
VAT:             € {total_vat:.2f}
TOTAL (gross):   € {total:.2f}
"""
        except Exception as e:
            summary = f"Error building summary: {e}"
        
        return [
            [sg.Text(tr("step4_title"), font=("Helvetica", 14, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Frame("Invoice Preview", [
                [sg.Multiline(default_text=summary, key="-SUMMARY-", size=(80, 22),
                            disabled=True, font=("Courier", 9), tooltip="Invoice preview - select all to copy")],
            ])],
            [sg.Frame("Output", [
                [sg.Text(tr("output_folder")),
                 sg.Input(default_text=str(Path.home() / "Documents"), key="-OUT_DIR-", size=(40, 1)),
                 sg.FolderBrowse()],
                [sg.Checkbox(tr("gen_xml"), default=True, key="-GEN_XML-",
                            tooltip="Machine-readable e-invoice XML"),
                 sg.Checkbox(tr("gen_pdf"), default=True, key="-GEN_PDF-",
                            tooltip="PDF for printing")],
            ])],
        ]
    
    def rebuild_window(win, step_num, values=None):
        """Rebuild the content area for current step"""
        if step_num == 1:
            content = step1()
        elif step_num == 2:
            content = step2()
        elif step_num == 3:
            content = step3()
        else:
            content = step4(values or {}, lines)
        
        bottom_nav = nav_buttons(step_num)
        
        new_layout = [
            content,
            [sg.HorizontalSeparator()],
            bottom_nav,
            [sg.Text("", key="-WIZ_STATUS-", text_color="green")],
        ]
        
        win["-CONTENT-"].update(new_layout)
        
        # Update next button state
        if step_num == 4:
            win["-NEXT-"].update(disabled=True, button_color=("white", "#888"))
        else:
            win["-NEXT-"].update(disabled=False, button_color=("white", "#2c5282"))
        win["-BACK-"].update(disabled=(step_num == 1))
        win["-STEP_NUM-"].update(f"{step_num}/4")
    
    # Initial layout (step 1)
    initial_content = step1()
    initial_nav = nav_buttons(1)
    
    layout = [
        [sg.Column(initial_content, key="-CONTENT-")],
        [sg.HorizontalSeparator()],
        initial_nav,
        [sg.Text("", key="-WIZ_STATUS-", text_color="green")],
    ]
    
    win = sg.Window(f"ee-invoice - {tr('new_invoice')}", layout, size=(650, 650))
    
    while True:
        event, values = win.read(timeout=100)
        
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        
        elif event == "-BACK-":
            if step[0] > 1:
                step[0] -= 1
                rebuild_window(win, step[0], values)
        
        elif event == "-NEXT-":
            if step[0] < 4:
                step[0] += 1
                rebuild_window(win, step[0], values)
        
        elif event == "-BUYER_SAME-":
            if values["-BUYER_SAME-"]:
                config = load_config()
                win["-B_NAME-"].update(config.get("name", ""))
                win["-B_REG-"].update(config.get("registry_code", ""))
                win["-B_VAT-"].update(config.get("vat_number", ""))
                win["-B_ADDR-"].update(config.get("address", ""))
                win["-B_CITY-"].update(config.get("city", ""))
                win["-B_POSTAL-"].update(config.get("postal_code", ""))
                win["-B_COUNTRY-"].update("EE")
                win["-B_EMAIL-"].update(config.get("email", ""))
        
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
                
                net_unit_price = price_gross / (1 + vat_rate) if vat_rate > 0 else price_gross
                lines.append(InvoiceLine(
                    description=desc, quantity=qty, unit=unit,
                    unit_price=net_unit_price, vat_rate=vat_rate,
                ))
                
                list_values = []
                for i, line in enumerate(lines):
                    g = line.unit_price * (1 + line.vat_rate) * line.quantity
                    list_values.append(f"{i+1}. {line.description[:40]} | qty:{line.quantity} | €{g:.2f}")
                win["-LINES_BOX-"].update(values=list_values)
                
                win["-L_DESC-"].update("")
                win["-L_QTY-"].update("1")
                win["-L_PRICE-"].update("0.00")
            except ValueError as e:
                sg.popup_error(f"Invalid number: {e}")
        
        elif event == "-REMOVE_LAST-":
            if lines:
                lines.pop()
                list_values = []
                for i, line in enumerate(lines):
                    g = line.unit_price * (1 + line.vat_rate) * line.quantity
                    list_values.append(f"{i+1}. {line.description[:40]} | qty:{line.quantity} | €{g:.2f}")
                win["-LINES_BOX-"].update(values=list_values)
        
        elif event == "-GENERATE-":
            sg.popup("Click Next → to reach Step 4, then Generate button will appear.")
    
    win.close()


# ============================================================
# MAIN WINDOW
# ============================================================
def main():
    set_lang(CURRENT_LANG[0])  # Load saved language
    
    lang_combo = sg.Combo(
        ["English", "Русский", "Eesti"],
        default_value={"en": "English", "ru": "Русский", "et": "Eesti"}.get(CURRENT_LANG[0], "English"),
        key="-LANG-", size=(10, 1), enable_events=True
    )
    
    layout = [
        [sg.Text("ee-invoice-generator", font=("Helvetica", 16, "bold")),
         lang_combo, sg.Text("", size=(5, 1)), sg.Text("v0.2.0", text_color="#999")],
        [sg.HorizontalSeparator()],
        [sg.Button(tr("my_company"), key="-BTN_COMPANY-", size=(18, 2), font=("Helvetica", 11))],
        [sg.Button(tr("new_invoice"), key="-BTN_INVOICE-", size=(18, 2), font=("Helvetica", 11),
                  button_color=("white", "#2c5282"))],
        [sg.Button(tr("accounting"), key="-BTN_ACCOUNTING-", size=(18, 2), font=("Helvetica", 11))],
        [sg.Button(tr("invoice_history"), key="-BTN_HISTORY-", size=(18, 2), font=("Helvetica", 11))],
        [sg.Sizer()],
        [sg.Text("ee-invoice-generator v0.2.0 — Estonian e-invoice GUI", text_color="#999", font=("Helvetica", 8))],
    ]
    
    win = sg.Window("ee-invoice-generator", layout, size=(400, 500), finalize=True)
    
    while True:
        event, values = win.read()
        
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        
        elif event == "-LANG-":
            lang_map = {"English": "en", "Русский": "ru", "Eesti": "et"}
            new_lang = lang_map.get(values["-LANG-"], "en")
            set_lang(new_lang)
            sg.popup_ok(f"Language changed to {values['-LANG-']}. Please restart the app for full effect.",
                       title="Language")
        
        elif event == "-BTN_COMPANY-":
            open_company_window()
        
        elif event == "-BTN_INVOICE-":
            open_invoice_wizard()
        
        elif event == "-BTN_ACCOUNTING-":
            sg.popup_ok(tr("accounting") + " — opening accounting module...\n(Coming soon as separate window)")
        
        elif event == "-BTN_HISTORY-":
            sg.popup_ok(tr("invoice_history") + " — opening history...\n(Coming soon as separate window)")
    
    win.close()


if __name__ == "__main__":
    main()
