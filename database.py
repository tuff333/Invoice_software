import sqlite3
import os

class Database:
    """
    SQLite database wrapper for the Portable Invoice Software.
    Handles:
    - Vendors
    - Signatures
    - Invoices + Items
    - Company Settings
    - HST/GST Settings
    """

    def __init__(self):
        """Initialize database connection and ensure directory exists."""
        self.db_path = os.path.join(os.path.dirname(__file__), 'data', 'invoices.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        print("✅ Connected to SQLite database")

    # ============================================================
    # Database Initialization
    # ============================================================

    def init(self):
        """Create all required tables if they do not exist."""
        cursor = self.conn.cursor()

        # ---------------- Vendors ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                contact TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- Signatures ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                image_path TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- Invoices ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                vendor_id INTEGER,
                hst_gst_number TEXT,
                comments TEXT,
                terms_conditions TEXT,
                signature_id INTEGER,
                shipping_method TEXT,
                shipping_terms TEXT,
                delivery_date TEXT,
                tax_rate REAL DEFAULT 13.0,
                shipping_cost REAL DEFAULT 0,
                notes TEXT,
                status TEXT DEFAULT 'Draft',
                created_by TEXT,
                pdf_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id),
                FOREIGN KEY (signature_id) REFERENCES signatures(id)
            )
        ''')

        # ---------------- Invoice Items ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                lot_number TEXT,
                item TEXT NOT NULL,
                quantity REAL NOT NULL,
                units TEXT NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')

        # ---------------- Company Settings ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings_extended (
                id INTEGER PRIMARY KEY,
                company_name TEXT DEFAULT 'Medicine Wheel Ranch Inc.',
                company_address TEXT DEFAULT '443 North Russell Road, Russell, ON, Canada - K4R 1E5',
                company_phone TEXT DEFAULT '(613) 266-4806',
                default_logo_path TEXT,
                default_shipping_method TEXT DEFAULT 'Seller',
                default_shipping_terms TEXT DEFAULT 'Seller'
            )
        ''')

        cursor.execute("INSERT OR IGNORE INTO settings_extended (id) VALUES (1)")

        # ---------------- HST/GST Settings ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                default_hst_gst_number TEXT
            )
        ''')

        cursor.execute("""
            INSERT OR IGNORE INTO settings (id, default_hst_gst_number)
            VALUES (1, '747957900 RT0001')
        """)

        self.conn.commit()
        print("✅ Database tables initialized")

    # ============================================================
    # HST / GST Settings
    # ============================================================

    def get_default_hst_gst(self):
        """Return the stored HST/GST number."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT default_hst_gst_number FROM settings WHERE id = 1")
        row = cursor.fetchone()
        return row['default_hst_gst_number'] if row else '747957900 RT0001'

    def set_default_hst_gst(self, number):
        """Update the HST/GST number."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE settings SET default_hst_gst_number = ? WHERE id = 1", (number,))
        self.conn.commit()

    # ============================================================
    # Signatures
    # ============================================================

    def get_all_signatures(self):
        """Return all signatures."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signatures ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_default_signature(self):
        """Return the default signature."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM signatures WHERE is_default = 1 LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_signature(self, name, position, image_path):
        """Insert a new signature."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO signatures (name, position, image_path)
            VALUES (?, ?, ?)
        ''', (name, position, image_path))
        self.conn.commit()
        return cursor.lastrowid

    def set_default_signature(self, signature_id):
        """Set a signature as default."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE signatures SET is_default = 0")
        cursor.execute("UPDATE signatures SET is_default = 1 WHERE id = ?", (signature_id,))
        self.conn.commit()

    def update_signature(self, sig_id, name, position):
        self.query("UPDATE signatures SET name=?, position=? WHERE id=?", (name, position, sig_id))

    def delete_signature(self, sig_id):
        self.query("DELETE FROM signatures WHERE id=?", (sig_id,))

    # ✅ ADD THESE TWO FUNCTIONS RIGHT HERE
    def update_signature(self, sig_id, name, position):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE signatures SET name=?, position=? WHERE id=?",
            (name, position, sig_id)
        )
        conn.commit()
        conn.close()


    def delete_signature(self, sig_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM signatures WHERE id=?", (sig_id,))
        conn.commit()
        conn.close()


    # ============================================================
    # Vendors
    # ============================================================

    def get_all_vendors(self):
        """Return all vendors sorted alphabetically."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vendors ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

    def add_vendor(self, name, address, contact):
        """Insert a new vendor."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO vendors (name, address, contact)
            VALUES (?, ?, ?)
        """, (name, address, contact))
        self.conn.commit()
        return cursor.lastrowid

    def update_vendor(self, vendor_id, name, address, contact):
        """Update vendor details."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE vendors
            SET name = ?, address = ?, contact = ?
            WHERE id = ?
        """, (name, address, contact, vendor_id))
        self.conn.commit()

    def delete_vendor(self, vendor_id):
        """Delete a vendor."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
        self.conn.commit()

    # ============================================================
    # Invoices
    # ============================================================

    def get_next_invoice_number(self):
        """Generate the next invoice number in the format MWR-XXX."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(CAST(SUBSTR(invoice_number, 5) AS INTEGER)) AS max_num FROM invoices")
        row = cursor.fetchone()
        next_num = (row['max_num'] or 0) + 1
        return f"MWR-{str(next_num).zfill(3)}"

    def save_invoice(self, invoice_data):
        """Insert invoice and its items."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO invoices (
                invoice_number, date, type, vendor_id, hst_gst_number,
                comments, terms_conditions, signature_id, shipping_method,
                shipping_terms, delivery_date, tax_rate, shipping_cost,
                notes, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_data['invoice_number'],
            invoice_data['date'],
            invoice_data['type'],
            invoice_data.get('vendor_id'),
            invoice_data.get('hst_gst_number'),
            invoice_data.get('comments'),
            invoice_data.get('terms_conditions'),
            invoice_data.get('signature_id'),
            invoice_data.get('shipping_method'),
            invoice_data.get('shipping_terms'),
            invoice_data.get('delivery_date'),
            invoice_data.get('tax_rate', 13.0),
            invoice_data.get('shipping_cost', 0),
            invoice_data.get('notes'),
            invoice_data.get('created_by', 'User')
        ))

        invoice_id = cursor.lastrowid

        # Insert invoice items
        for item in invoice_data.get('items', []):
            cursor.execute('''
                INSERT INTO invoice_items (invoice_id, lot_number, item, quantity, units, unit_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id,
                item.get('lot_number'),
                item['item'],
                item['quantity'],
                item['units'],
                item['unit_price']
            ))

        self.conn.commit()
        return invoice_id

    def update_invoice_pdf_path(self, invoice_id, pdf_path):
        """Store the generated PDF path."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?", (pdf_path, invoice_id))
        self.conn.commit()

    def get_all_invoices(self):
        """Return all invoices with vendor + signature info."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT i.*, 
                   v.name AS vendor_name, 
                   v.address AS vendor_address,
                   s.name AS signature_name, 
                   s.position AS signature_position
            FROM invoices i
            LEFT JOIN vendors v ON i.vendor_id = v.id
            LEFT JOIN signatures s ON i.signature_id = s.id
            ORDER BY i.created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # Company Settings
    # ============================================================

    def get_settings(self):
        """Return company settings."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM settings_extended WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else {}

    def update_settings(self, data):
        """Update company settings."""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE settings_extended
            SET company_name = ?,
                company_address = ?,
                company_phone = ?,
                default_logo_path = ?,
                default_shipping_method = ?,
                default_shipping_terms = ?
            WHERE id = 1
        ''', (
            data.get('company_name'),
            data.get('company_address'),
            data.get('company_phone'),
            data.get('default_logo_path'),
            data.get('default_shipping_method'),
            data.get('default_shipping_terms')
        ))
        self.conn.commit()


# Create global instance
db = Database()
