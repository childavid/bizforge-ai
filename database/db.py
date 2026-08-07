"""Database and account helpers for BizForge.

The application uses SQLite for its first release.  Every query is scoped to
the signed-in account, and this module upgrades existing local databases
without removing any saved records.
"""

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import date, datetime


DEFAULT_DB = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saas.db")
)
DB = os.getenv("BIZFORGE_DB_PATH", DEFAULT_DB)
FREE_DAILY_LIMIT = 5
# Existing hashes store their own iteration count, so lowering this only makes
# new accounts faster; older accounts remain compatible and protected.
PASSWORD_ITERATIONS = 120_000
VALID_INVOICE_STATUSES = {"draft", "sent", "paid", "overdue", "cancelled"}


def connect():
    """Open a database connection with foreign-key support enabled."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    return re.fullmatch(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", email.strip()) is not None


def normalise_email(email):
    if not validate_email(email):
        raise ValueError("Enter a valid email address")
    return email.strip().lower()


def validate_text_input(text, max_length=5000):
    return isinstance(text, str) and bool(text.strip()) and len(text.strip()) <= max_length


def validate_number(value, min_value=0, max_value=1_000_000):
    try:
        return min_value <= float(value) <= max_value
    except (ValueError, TypeError):
        return False


def sanitize_input(text):
    """Trim user input without changing legitimate names, punctuation, or content."""
    return text.strip() if isinstance(text, str) else ""


def _hash_password(password, salt=None):
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Use a password with at least 8 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(
        (
            str(PASSWORD_ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        )
    )


def _password_matches(password, stored_hash):
    if not password or not stored_hash:
        return False
    try:
        iterations, encoded_salt, encoded_digest = stored_hash.split("$", 2)
        salt = base64.b64decode(encoded_salt.encode("ascii"))
        expected = base64.b64decode(encoded_digest.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def _ensure_column(cursor, table, column, definition):
    columns = {row["name"] for row in cursor.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    """Create the schema and make non-destructive upgrades to older databases."""
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free',
            password_hash TEXT,
            business_name TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            contact_email TEXT,
            phone TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(email, name)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            client TEXT NOT NULL,
            service TEXT NOT NULL,
            content TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            invoice_number TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            due_date TEXT,
            currency TEXT NOT NULL DEFAULT 'NGN'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            client TEXT NOT NULL,
            project TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            feature TEXT NOT NULL,
            usage_count INTEGER NOT NULL DEFAULT 0,
            last_reset_date TEXT,
            UNIQUE(email, feature)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS social_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS business_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            idea TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            feature_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_ref TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            transaction_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            received_at TEXT NOT NULL
        )
        """
    )

    # Existing installations have older versions of these tables.
    _ensure_column(cur, "users", "password_hash", "TEXT")
    _ensure_column(cur, "users", "business_name", "TEXT")
    _ensure_column(cur, "users", "created_at", "TEXT")
    _ensure_column(cur, "invoices", "invoice_number", "TEXT")
    _ensure_column(cur, "invoices", "status", "TEXT NOT NULL DEFAULT 'draft'")
    _ensure_column(cur, "invoices", "due_date", "TEXT")
    _ensure_column(cur, "invoices", "currency", "TEXT NOT NULL DEFAULT 'NGN'")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_invoices_email ON invoices(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_email ON history(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_email ON payments(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_app_webhook_events_type ON app_webhook_events(event_type)")
    conn.commit()
    conn.close()


def create_user(email, password, business_name):
    email = normalise_email(email)
    if not validate_text_input(business_name, max_length=120):
        raise ValueError("Enter your business name")
    password_hash = _hash_password(password)
    now = datetime.now().isoformat()
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO users (email, plan, password_hash, business_name, created_at)
            VALUES (?, 'free', ?, ?, ?)
            """,
            (email, password_hash, sanitize_input(business_name), now),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def authenticate_user(email, password):
    try:
        email = normalise_email(email)
    except ValueError:
        return False
    conn = connect()
    row = conn.execute("SELECT password_hash FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return bool(row and _password_matches(password, row["password_hash"]))


def ensure_billing_user(email):
    """Create a minimal server-side plan record when checkout is started."""
    email = normalise_email(email)
    conn = connect()
    conn.execute(
        "INSERT OR IGNORE INTO users (email, plan, created_at) VALUES (?, 'free', ?)",
        (email, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_plan(email):
    try:
        email = normalise_email(email)
    except ValueError:
        return "free"
    conn = connect()
    row = conn.execute("SELECT plan FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return row["plan"] if row else "free"


def get_business_name(email):
    conn = connect()
    row = conn.execute("SELECT business_name FROM users WHERE email=?", (normalise_email(email),)).fetchone()
    conn.close()
    return row["business_name"] if row and row["business_name"] else "Your Business"


def upgrade_user(email):
    email = normalise_email(email)
    ensure_billing_user(email)
    conn = connect()
    conn.execute("UPDATE users SET plan='pro' WHERE email=?", (email,))
    conn.commit()
    conn.close()


def add_client(email, name, contact_email="", phone="", address="", notes=""):
    email = normalise_email(email)
    if not validate_text_input(name, max_length=200):
        raise ValueError("Enter a client name")
    if contact_email and not validate_email(contact_email):
        raise ValueError("Enter a valid client email address")
    now = datetime.now().isoformat()
    conn = connect()
    conn.execute(
        """
        INSERT INTO clients (email, name, contact_email, phone, address, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email, name) DO UPDATE SET
            contact_email=excluded.contact_email,
            phone=excluded.phone,
            address=excluded.address,
            notes=excluded.notes,
            updated_at=excluded.updated_at
        """,
        (
            email,
            sanitize_input(name),
            normalise_email(contact_email) if contact_email else "",
            sanitize_input(phone),
            sanitize_input(address),
            sanitize_input(notes),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()


def get_clients(email):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM clients WHERE email=? ORDER BY name COLLATE NOCASE", (normalise_email(email),)
    ).fetchall()
    conn.close()
    return rows


def _next_invoice_number(email):
    year = datetime.now().year
    conn = connect()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM invoices WHERE email=? AND created_at LIKE ?",
        (normalise_email(email), f"{year}%"),
    ).fetchone()
    conn.close()
    return f"BZF-{year}-{row['count'] + 1:04d}"


def save_invoice(email, client, service, content, amount, due_date=None, currency="NGN", status="draft", invoice_number=None):
    email = normalise_email(email)
    if not validate_text_input(client, 200) or not validate_text_input(service, 200):
        raise ValueError("Client and service are required")
    if not validate_text_input(content, 10_000) or not validate_number(amount, 0, 100_000_000):
        raise ValueError("Enter valid invoice details")
    if status not in VALID_INVOICE_STATUSES:
        raise ValueError("Invalid invoice status")
    if currency not in {"NGN", "USD"}:
        raise ValueError("Invalid currency")
    invoice_number = invoice_number or _next_invoice_number(email)
    conn = connect()
    conn.execute(
        """
        INSERT INTO invoices (email, client, service, content, amount, created_at, invoice_number, status, due_date, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            sanitize_input(client),
            sanitize_input(service),
            content.strip(),
            float(amount),
            datetime.now().isoformat(),
            invoice_number,
            status,
            due_date.isoformat() if hasattr(due_date, "isoformat") else due_date,
            currency,
        ),
    )
    conn.commit()
    conn.close()
    return invoice_number


def get_invoices(email):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM invoices WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)
    ).fetchall()
    conn.close()
    return rows


def update_invoice_status(email, invoice_id, status):
    if status not in VALID_INVOICE_STATUSES:
        raise ValueError("Invalid invoice status")
    conn = connect()
    result = conn.execute(
        "UPDATE invoices SET status=? WHERE id=? AND email=?",
        (status, invoice_id, normalise_email(email)),
    )
    conn.commit()
    conn.close()
    return result.rowcount == 1


def save_proposal(email, client, project, content):
    email = normalise_email(email)
    if not all((validate_text_input(client, 200), validate_text_input(project, 200), validate_text_input(content, 10_000))):
        raise ValueError("Enter valid proposal details")
    conn = connect()
    conn.execute(
        "INSERT INTO proposals (email, client, project, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (email, sanitize_input(client), sanitize_input(project), content.strip(), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_proposals(email):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM proposals WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)
    ).fetchall()
    conn.close()
    return rows


def get_usage(email, feature):
    email = normalise_email(email)
    today = date.today().isoformat()
    conn = connect()
    row = conn.execute(
        "SELECT usage_count, last_reset_date FROM usage_tracking WHERE email=? AND feature=?", (email, feature)
    ).fetchone()
    if not row:
        conn.close()
        return 0, today
    if row["last_reset_date"] != today:
        conn.execute(
            "UPDATE usage_tracking SET usage_count=0, last_reset_date=? WHERE email=? AND feature=?",
            (today, email, feature),
        )
        conn.commit()
        conn.close()
        return 0, today
    conn.close()
    return row["usage_count"], row["last_reset_date"]


def increment_usage(email, feature):
    email = normalise_email(email)
    today = date.today().isoformat()
    conn = connect()
    conn.execute(
        """
        INSERT INTO usage_tracking (email, feature, usage_count, last_reset_date)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(email, feature) DO UPDATE SET usage_count=usage_count + 1, last_reset_date=excluded.last_reset_date
        """,
        (email, feature, today),
    )
    conn.commit()
    conn.close()


def can_use_feature(email, feature, plan):
    if plan == "pro":
        return True, "unlimited"
    usage_count, _ = get_usage(email, feature)
    remaining = max(0, FREE_DAILY_LIMIT - usage_count)
    return remaining > 0, remaining


def get_all_usage(email):
    email = normalise_email(email)
    today = date.today().isoformat()
    conn = connect()
    rows = conn.execute(
        "SELECT feature, usage_count, last_reset_date FROM usage_tracking WHERE email=?", (email,)
    ).fetchall()
    conn.close()
    return {row["feature"]: row["usage_count"] if row["last_reset_date"] == today else 0 for row in rows}


def _save_content(table, email, fields, values):
    conn = connect()
    columns = ", ".join(["email", *fields, "created_at"])
    placeholders = ", ".join("?" for _ in range(len(values) + 2))
    conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        (normalise_email(email), *values, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def save_email(email, recipient, subject, content):
    if not all((validate_text_input(recipient, 200), validate_text_input(subject, 500), validate_text_input(content, 10_000))):
        raise ValueError("Enter valid email details")
    _save_content("emails", email, ["recipient", "subject", "content"], [sanitize_input(recipient), sanitize_input(subject), content.strip()])


def get_emails(email):
    conn = connect()
    rows = conn.execute("SELECT * FROM emails WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)).fetchall()
    conn.close()
    return rows


def save_social_post(email, platform, content):
    if not all((validate_text_input(platform, 100), validate_text_input(content, 10_000))):
        raise ValueError("Enter valid social post details")
    _save_content("social_posts", email, ["platform", "content"], [sanitize_input(platform), content.strip()])


def get_social_posts(email):
    conn = connect()
    rows = conn.execute("SELECT * FROM social_posts WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)).fetchall()
    conn.close()
    return rows


def save_business_idea(email, category, idea):
    if not all((validate_text_input(category, 100), validate_text_input(idea, 10_000))):
        raise ValueError("Enter valid business idea details")
    _save_content("business_ideas", email, ["category", "idea"], [sanitize_input(category), idea.strip()])


def get_business_ideas(email):
    conn = connect()
    rows = conn.execute("SELECT * FROM business_ideas WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)).fetchall()
    conn.close()
    return rows


def save_to_history(email, feature_type, content):
    if not all((validate_text_input(feature_type, 50), validate_text_input(content, 50_000))):
        raise ValueError("Enter valid history details")
    _save_content("history", email, ["feature_type", "content"], [sanitize_input(feature_type), content.strip()])


def get_history(email, feature_type=None):
    conn = connect()
    if feature_type:
        rows = conn.execute(
            "SELECT * FROM history WHERE email=? AND feature_type=? ORDER BY created_at DESC",
            (normalise_email(email), feature_type),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM history WHERE email=? ORDER BY created_at DESC", (normalise_email(email),)).fetchall()
    conn.close()
    return rows


def create_pending_payment(email, tx_ref, amount, currency="NGN", plan="pro"):
    email = normalise_email(email)
    if not validate_number(amount, 1, 100_000_000) or currency != "NGN":
        raise ValueError("Invalid payment details")
    ensure_billing_user(email)
    now = datetime.now().isoformat()
    conn = connect()
    conn.execute(
        """
        INSERT INTO payments (tx_ref, email, plan, amount, currency, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (tx_ref, email, plan, float(amount), currency, now, now),
    )
    conn.commit()
    conn.close()


def get_payment(tx_ref):
    conn = connect()
    row = conn.execute("SELECT * FROM payments WHERE tx_ref=?", (tx_ref,)).fetchone()
    conn.close()
    return row


def complete_payment(tx_ref, transaction_id):
    """Mark a verified payment complete and upgrade exactly the matching user."""
    payment = get_payment(tx_ref)
    if not payment:
        raise ValueError("Payment reference was not created by BizForge")
    if payment["status"] == "successful":
        return payment["email"]
    conn = connect()
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE payments SET status='successful', transaction_id=?, updated_at=? WHERE tx_ref=?",
        (str(transaction_id), now, tx_ref),
    )
    conn.execute("UPDATE users SET plan='pro' WHERE email=?", (payment["email"],))
    conn.commit()
    conn.close()
    return payment["email"]


def record_app_webhook_event(event_id, event_type):
    """Record an accepted external event once; repeated delivery is harmless."""
    if not all((validate_text_input(event_id, 160), validate_text_input(event_type, 100))):
        raise ValueError("Webhook event ID and event type are required")
    conn = connect()
    try:
        result = conn.execute(
            """
            INSERT INTO app_webhook_events (event_id, event_type, received_at)
            VALUES (?, ?, ?)
            ON CONFLICT(event_id) DO NOTHING
            """,
            (sanitize_input(event_id), sanitize_input(event_type), datetime.now().isoformat()),
        )
        conn.commit()
        return result.rowcount == 1
    finally:
        conn.close()
