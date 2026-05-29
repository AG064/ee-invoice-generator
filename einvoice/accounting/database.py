"""
SQLite database for persistent storage of accounting data
"""
import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import json


class Database:
    """
    SQLite database for ee-invoice-generator accounting data
    Stores: invoices, journal entries, company settings, VAT transactions
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.home() / ".ee-invoice-generator"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "accounting.db"
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    registry_code TEXT UNIQUE,
                    vat_number TEXT,
                    address TEXT,
                    city TEXT,
                    postal_code TEXT,
                    country TEXT DEFAULT 'EE',
                    email TEXT,
                    phone TEXT,
                    iban TEXT,
                    bic TEXT,
                    bank_name TEXT,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Counterparties (customers/suppliers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS counterparties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    registry_code TEXT,
                    vat_number TEXT,
                    address TEXT,
                    city TEXT,
                    postal_code TEXT,
                    country TEXT DEFAULT 'EE',
                    email TEXT,
                    phone TEXT,
                    counterparty_type TEXT DEFAULT 'customer',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Invoices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    invoice_date TEXT NOT NULL,
                    due_date TEXT,
                    company_id INTEGER,
                    counterparty_id INTEGER,
                    total_excl_vat REAL DEFAULT 0,
                    vat_amount REAL DEFAULT 0,
                    total_incl_vat REAL DEFAULT 0,
                    currency TEXT DEFAULT 'EUR',
                    status TEXT DEFAULT 'draft',
                    notes TEXT,
                    xml_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (counterparty_id) REFERENCES counterparties(id)
                )
            """)
            
            # Invoice lines
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    quantity REAL DEFAULT 1,
                    unit TEXT DEFAULT 'pcs',
                    unit_price REAL DEFAULT 0,
                    vat_rate REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    line_note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """)
            
            # Journal entries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_number INTEGER UNIQUE NOT NULL,
                    entry_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    reference TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Journal entry lines
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER NOT NULL,
                    account_number TEXT NOT NULL,
                    amount REAL NOT NULL,
                    entry_type TEXT NOT NULL,
                    line_description TEXT,
                    FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
                )
            """)
            
            # VAT transactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vat_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    invoice_number TEXT,
                    description TEXT,
                    amount_excl_vat REAL NOT NULL,
                    vat_rate REAL NOT NULL,
                    vat_amount REAL NOT NULL,
                    is_output_vat INTEGER NOT NULL,
                    counterparty TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_company ON invoices(company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vat_date ON vat_transactions(date)")
            
            conn.commit()
    
    # === Company methods ===
    def save_company(self, company: dict) -> int:
        """Save or update company, returns id"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO companies 
                (name, registry_code, vat_number, address, city, postal_code, country, email, phone, iban, bic, bank_name, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company["name"], company.get("registry_code"), company.get("vat_number"),
                company.get("address"), company.get("city"), company.get("postal_code"),
                company.get("country", "EE"), company.get("email"), company.get("phone"),
                company.get("iban"), company.get("bic"), company.get("bank_name"),
                company.get("is_default", 0)
            ))
            conn.commit()
            # Get the id of inserted/updated row
            row = cursor.execute("SELECT last_insert_rowid()").fetchone()
            return row[0] if row else cursor.lastrowid
    
    def get_company(self, company_id: int = None, default: bool = True) -> Optional[dict]:
        """Get company by id or default"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if default and company_id is None:
                row = cursor.execute("SELECT * FROM companies WHERE is_default = 1 LIMIT 1").fetchone()
            elif company_id:
                row = cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
            else:
                row = cursor.execute("SELECT * FROM companies LIMIT 1").fetchone()
            
            if row:
                return dict(row)
            return None
    
    def list_companies(self) -> list[dict]:
        """List all companies"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute("SELECT * FROM companies ORDER BY name")]
    
    # === Counterparty methods ===
    def save_counterparty(self, counterparty: dict) -> int:
        """Save or update counterparty"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO counterparties 
                (name, registry_code, vat_number, address, city, postal_code, country, email, phone, counterparty_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                counterparty["name"], counterparty.get("registry_code"), counterparty.get("vat_number"),
                counterparty.get("address"), counterparty.get("city"), counterparty.get("postal_code"),
                counterparty.get("country", "EE"), counterparty.get("email"), counterparty.get("phone"),
                counterparty.get("counterparty_type", "customer")
            ))
            conn.commit()
            row = cursor.execute("SELECT last_insert_rowid()").fetchone()
            return row[0] if row else cursor.lastrowid
    
    def get_counterparty(self, counterparty_id: int) -> Optional[dict]:
        """Get counterparty by id"""
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM counterparties WHERE id = ?", (counterparty_id,)).fetchone()
            return dict(row) if row else None
    
    def list_counterparties(self, counterparty_type: str = None) -> list[dict]:
        """List all counterparties"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if counterparty_type:
                return [dict(row) for row in cursor.execute(
                    "SELECT * FROM counterparties WHERE counterparty_type = ? ORDER BY name",
                    (counterparty_type,)
                )]
            return [dict(row) for row in cursor.execute("SELECT * FROM counterparties ORDER BY name")]
    
    # === Invoice methods ===
    def save_invoice(self, invoice: dict, lines: list[dict]) -> int:
        """Save invoice with lines"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO invoices
                (invoice_number, invoice_date, due_date, company_id, counterparty_id,
                 total_excl_vat, vat_amount, total_incl_vat, currency, status, notes, xml_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice["invoice_number"], invoice["invoice_date"], invoice.get("due_date"),
                invoice.get("company_id"), invoice.get("counterparty_id"),
                invoice.get("total_excl_vat", 0), invoice.get("vat_amount", 0),
                invoice.get("total_incl_vat", 0), invoice.get("currency", "EUR"),
                invoice.get("status", "draft"), invoice.get("notes"), invoice.get("xml_data")
            ))
            
            invoice_id = cursor.lastrowid
            if not invoice_id:
                row = cursor.execute("SELECT last_insert_rowid()").fetchone()
                invoice_id = row[0] if row else None
            
            # Delete existing lines
            cursor.execute("DELETE FROM invoice_lines WHERE invoice_id = ?", (invoice_id,))
            
            # Insert new lines
            for line in lines:
                cursor.execute("""
                    INSERT INTO invoice_lines
                    (invoice_id, description, quantity, unit, unit_price, vat_rate, line_total, line_note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id, line["description"], line.get("quantity", 1), line.get("unit", "pcs"),
                    line.get("unit_price", 0), line.get("vat_rate", 0), line.get("line_total", 0),
                    line.get("line_note")
                ))
            
            conn.commit()
            return invoice_id
    
    def get_invoice(self, invoice_id: int = None, invoice_number: str = None) -> Optional[dict]:
        """Get invoice by id or number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if invoice_id:
                invoice = cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
            elif invoice_number:
                invoice = cursor.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,)).fetchone()
            else:
                return None
            
            if invoice:
                result = dict(invoice)
                # Get lines
                lines = cursor.execute(
                    "SELECT * FROM invoice_lines WHERE invoice_id = ?", (result["id"],)
                ).fetchall()
                result["lines"] = [dict(line) for line in lines]
                return result
            return None
    
    def list_invoices(self, status: str = None, company_id: int = None) -> list[dict]:
        """List invoices with company and counterparty names"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT i.*, 
                       c.name as seller_name, c.registry_code as seller_registry, 
                       c.vat_number as seller_vat, c.address as seller_address,
                       ct.name as buyer_name, ct.registry_code as buyer_registry,
                       ct.vat_number as buyer_vat, ct.address as buyer_address
                FROM invoices i
                LEFT JOIN companies c ON i.company_id = c.id
                LEFT JOIN counterparties ct ON i.counterparty_id = ct.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND i.status = ?"
                params.append(status)
            if company_id:
                query += " AND i.company_id = ?"
                params.append(company_id)
            query += " ORDER BY i.invoice_date DESC"
            return [dict(row) for row in cursor.execute(query, params)]
    
    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete invoice by id"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoice_lines WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.commit()
            return True
    
    def clear_all_invoices(self) -> bool:
        """Delete all invoices"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoice_lines")
            cursor.execute("DELETE FROM invoices")
            conn.commit()
            return True
    
    # === Journal methods ===
    def save_journal_entry(self, entry: dict, lines: list[dict]) -> int:
        """Save journal entry with lines"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO journal_entries
                (entry_number, entry_date, description, reference)
                VALUES (?, ?, ?, ?)
            """, (entry["entry_number"], entry["entry_date"], entry["description"], entry.get("reference")))
            
            entry_id = cursor.lastrowid or cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Delete existing lines
            cursor.execute("DELETE FROM journal_lines WHERE entry_id = ?", (entry_id,))
            
            # Insert new lines
            for line in lines:
                cursor.execute("""
                    INSERT INTO journal_lines
                    (entry_id, account_number, amount, entry_type, line_description)
                    VALUES (?, ?, ?, ?, ?)
                """, (entry_id, line["account_number"], line["amount"], line["entry_type"], line.get("description")))
            
            conn.commit()
            return entry_id
    
    def get_journal_entry(self, entry_id: int = None, entry_number: int = None) -> Optional[dict]:
        """Get journal entry by id or number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if entry_id:
                entry = cursor.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
            elif entry_number:
                entry = cursor.execute("SELECT * FROM journal_entries WHERE entry_number = ?", (entry_number,)).fetchone()
            else:
                return None
            
            if entry:
                result = dict(entry)
                lines = cursor.execute(
                    "SELECT * FROM journal_lines WHERE entry_id = ?", (result["id"],)
                ).fetchall()
                result["lines"] = [dict(line) for line in lines]
                return result
            return None
    
    def list_journal_entries(self, start_date: date = None, end_date: date = None) -> list[dict]:
        """List journal entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM journal_entries WHERE 1=1"
            params = []
            if start_date:
                query += " AND entry_date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND entry_date <= ?"
                params.append(end_date.isoformat())
            query += " ORDER BY entry_date, entry_number"
            
            entries = []
            for row in cursor.execute(query, params):
                entry = dict(row)
                lines = cursor.execute(
                    "SELECT * FROM journal_lines WHERE entry_id = ?", (entry["id"],)
                ).fetchall()
                entry["lines"] = [dict(line) for line in lines]
                entries.append(entry)
            return entries
    
    # === VAT methods ===
    def save_vat_transaction(self, vat_tx: dict) -> int:
        """Save VAT transaction"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vat_transactions
                (date, invoice_number, description, amount_excl_vat, vat_rate, vat_amount, is_output_vat, counterparty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vat_tx["date"], vat_tx.get("invoice_number"), vat_tx.get("description"),
                vat_tx["amount_excl_vat"], vat_tx["vat_rate"], vat_tx["vat_amount"],
                int(vat_tx["is_output_vat"]), vat_tx.get("counterparty")
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_vat_transactions(self, start_date: date = None, end_date: date = None) -> list[dict]:
        """Get VAT transactions for period"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM vat_transactions WHERE 1=1"
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND date <= ?"
                params.append(end_date.isoformat())
            query += " ORDER BY date"
            return [dict(row) for row in cursor.execute(query, params)]
    
    def calculate_vat_for_period(self, start_date: date, end_date: date) -> dict:
        """Calculate VAT for period"""
        transactions = self.get_vat_transactions(start_date, end_date)
        
        output_vat = sum(tx["vat_amount"] for tx in transactions if tx["is_output_vat"])
        input_vat = sum(tx["vat_amount"] for tx in transactions if not tx["is_output_vat"])
        
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_due": output_vat - input_vat,
        }
    
    # === Settings ===
    def generate_invoice_number(self) -> str:
        """Generate next invoice number in format YYYYMMDD-NNN"""
        today = date.today()
        date_prefix = today.strftime("%Y%m%d")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Find the highest number for today
            cursor.execute("""
                SELECT invoice_number FROM invoices 
                WHERE invoice_number LIKE ?
                ORDER BY invoice_number DESC
                LIMIT 1
            """, (f"{date_prefix}-%",))
            row = cursor.fetchone()
            
            if row:
                last_num = row["invoice_number"]
                try:
                    # Extract the counter part
                    counter = int(last_num.split("-")[-1])
                    new_counter = counter + 1
                except (ValueError, IndexError):
                    new_counter = 1
            else:
                new_counter = 1
            
            return f"{date_prefix}-{new_counter:03d}"
    
    def invoice_number_exists(self, invoice_number: str) -> bool:
        """Check if invoice number already exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM invoices WHERE invoice_number = ?", (invoice_number,))
            return cursor.fetchone() is not None
    
    def set_setting(self, key: str, value: str):
        """Save setting"""
        with self._get_connection() as conn:
            conn.cursor().execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )
            conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get setting"""
        with self._get_connection() as conn:
            row = conn.cursor().execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default
    
    # === Backup ===
    def backup(self, backup_path: Path = None):
        """Create database backup"""
        import shutil
        if backup_path is None:
            backup_path = self.data_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path