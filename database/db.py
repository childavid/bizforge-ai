import os
import sqlite3
from datetime import datetime, date
import re

DB = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saas.db"))
FREE_DAILY_LIMIT = 5

print("DATABASE FILE:", DB)


# ================= VALIDATION =================
def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_text_input(text, max_length=5000):
    """Validate text input - prevent empty or excessively long strings"""
    if not text or not isinstance(text, str):
        return False
    if len(text.strip()) == 0:
        return False
    if len(text) > max_length:
        return False
    return True


def validate_number(value, min_value=0, max_value=1000000):
    """Validate numeric input - prevent negative or unrealistic values"""
    try:
        num = float(value)
        if num < min_value or num > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False


def sanitize_input(text):
    """Sanitize input to prevent SQL injection and XSS"""
    if not text or not isinstance(text, str):
        return ""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()


def connect():
    print("CONNECTING TO:", DB)
    return sqlite3.connect(DB)


# ================= INIT DB =================
def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        plan TEXT DEFAULT 'free'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        client TEXT,
        service TEXT,
        content TEXT,
        amount REAL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        client TEXT,
        project TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usage_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        feature TEXT,
        usage_count INTEGER DEFAULT 0,
        last_reset_date TEXT,
        UNIQUE(email, feature)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        recipient TEXT,
        subject TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS social_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        platform TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS business_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        category TEXT,
        idea TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        feature_type TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    
    # Print tables for debugging
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("TABLES FOUND:", cur.fetchall())
    
    conn.close()


# ================= USERS =================
def create_user(email):
    if not validate_email(email):
        raise ValueError("Invalid email format")

    email = sanitize_input(email)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (email, plan)
    VALUES (?, 'free')
    """, (email,))

    conn.commit()
    conn.close()


def get_plan(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("TABLES AVAILABLE:", cur.fetchall())

    cur.execute("SELECT plan FROM users WHERE email=?", (email,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else "free"


def upgrade_user(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET plan='pro'
    WHERE email=?
    """, (email,))

    conn.commit()
    conn.close()


# ================= INVOICE =================
def save_invoice(email, client, service, content, amount):
    if not validate_text_input(client, max_length=200):
        raise ValueError("Invalid client name")
    if not validate_text_input(service, max_length=200):
        raise ValueError("Invalid service name")
    if not validate_text_input(content, max_length=10000):
        raise ValueError("Invalid content")
    if not validate_number(amount, min_value=0, max_value=100000000):
        raise ValueError("Invalid amount")

    client = sanitize_input(client)
    service = sanitize_input(service)
    content = sanitize_input(content)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO invoices (email, client, service, content, amount, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (email, client, service, content, amount, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_invoices(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM invoices WHERE email=?", (email,))
    rows = cur.fetchall()

    conn.close()
    return rows


# ================= PROPOSAL =================
def save_proposal(email, client, project, content):
    if not validate_text_input(client, max_length=200):
        raise ValueError("Invalid client name")
    if not validate_text_input(project, max_length=200):
        raise ValueError("Invalid project name")
    if not validate_text_input(content, max_length=10000):
        raise ValueError("Invalid content")

    client = sanitize_input(client)
    project = sanitize_input(project)
    content = sanitize_input(content)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO proposals (email, client, project, content, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (email, client, project, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_proposals(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM proposals WHERE email=?", (email,))
    rows = cur.fetchall()

    conn.close()
    return rows


# ================= USAGE TRACKING =================
def get_usage(email, feature):
    """Get current usage count for a feature, auto-reset if new day"""
    conn = connect()
    cur = conn.cursor()

    today = date.today().isoformat()

    cur.execute("""
    SELECT usage_count, last_reset_date
    FROM usage_tracking
    WHERE email=? AND feature=?
    """, (email, feature))

    row = cur.fetchone()

    if not row:
        conn.close()
        return 0, today

    usage_count, last_reset = row

    # Auto-reset if new day
    if last_reset != today:
        cur.execute("""
        UPDATE usage_tracking
        SET usage_count=0, last_reset_date=?
        WHERE email=? AND feature=?
        """, (today, email, feature))
        conn.commit()
        conn.close()
        return 0, today

    conn.close()
    return usage_count, last_reset


def increment_usage(email, feature):
    """Increment usage count for a feature"""
    conn = connect()
    cur = conn.cursor()

    today = date.today().isoformat()

    # Check if record exists
    cur.execute("""
    SELECT id FROM usage_tracking
    WHERE email=? AND feature=?
    """, (email, feature))

    row = cur.fetchone()

    if row:
        cur.execute("""
        UPDATE usage_tracking
        SET usage_count=usage_count+1, last_reset_date=?
        WHERE email=? AND feature=?
        """, (today, email, feature))
    else:
        cur.execute("""
        INSERT INTO usage_tracking (email, feature, usage_count, last_reset_date)
        VALUES (?, ?, 1, ?)
        """, (email, feature, today))

    conn.commit()
    conn.close()


def can_use_feature(email, feature, plan):
    """Check if user can use a feature based on plan and usage"""
    if plan == "pro":
        return True, "unlimited"

    usage_count, _ = get_usage(email, feature)
    remaining = FREE_DAILY_LIMIT - usage_count

    if remaining > 0:
        return True, remaining
    else:
        return False, 0


def get_all_usage(email):
    """Get usage for all features for a user"""
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT feature, usage_count, last_reset_date
    FROM usage_tracking
    WHERE email=?
    """, (email,))

    rows = cur.fetchall()
    conn.close()

    usage_dict = {}
    today = date.today().isoformat()

    for feature, count, last_reset in rows:
        if last_reset == today:
            usage_dict[feature] = count
        else:
            usage_dict[feature] = 0

    return usage_dict


# ================= EMAIL =================
def save_email(email, recipient, subject, content):
    if not validate_text_input(recipient, max_length=200):
        raise ValueError("Invalid recipient name")
    if not validate_text_input(subject, max_length=500):
        raise ValueError("Invalid subject")
    if not validate_text_input(content, max_length=10000):
        raise ValueError("Invalid content")

    recipient = sanitize_input(recipient)
    subject = sanitize_input(subject)
    content = sanitize_input(content)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO emails (email, recipient, subject, content, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (email, recipient, subject, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_emails(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM emails WHERE email=?", (email,))
    rows = cur.fetchall()

    conn.close()
    return rows


# ================= SOCIAL MEDIA =================
def save_social_post(email, platform, content):
    if not validate_text_input(platform, max_length=100):
        raise ValueError("Invalid platform")
    if not validate_text_input(content, max_length=10000):
        raise ValueError("Invalid content")

    platform = sanitize_input(platform)
    content = sanitize_input(content)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO social_posts (email, platform, content, created_at)
    VALUES (?, ?, ?, ?)
    """, (email, platform, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_social_posts(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM social_posts WHERE email=?", (email,))
    rows = cur.fetchall()

    conn.close()
    return rows


# ================= BUSINESS IDEA =================
def save_business_idea(email, category, idea):
    if not validate_text_input(category, max_length=100):
        raise ValueError("Invalid category")
    if not validate_text_input(idea, max_length=10000):
        raise ValueError("Invalid idea")

    category = sanitize_input(category)
    idea = sanitize_input(idea)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO business_ideas (email, category, idea, created_at)
    VALUES (?, ?, ?, ?)
    """, (email, category, idea, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_business_ideas(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM business_ideas WHERE email=?", (email,))
    rows = cur.fetchall()

    conn.close()
    return rows


# ================= HISTORY =================
def save_to_history(email, feature_type, content):
    """Save a generated item to history"""
    if not validate_text_input(content, max_length=50000):
        raise ValueError("Invalid content")
    
    if not validate_text_input(feature_type, max_length=50):
        raise ValueError("Invalid feature type")

    content = sanitize_input(content)
    feature_type = sanitize_input(feature_type)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history (email, feature_type, content, created_at)
    VALUES (?, ?, ?, ?)
    """, (email, feature_type, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_history(email, feature_type=None):
    """Get history for a user, optionally filtered by feature type"""
    conn = connect()
    cur = conn.cursor()

    if feature_type:
        cur.execute("""
        SELECT * FROM history 
        WHERE email=? AND feature_type=?
        ORDER BY created_at DESC
        """, (email, feature_type))
    else:
        cur.execute("""
        SELECT * FROM history 
        WHERE email=?
        ORDER BY created_at DESC
        """, (email,))

    rows = cur.fetchall()
    conn.close()
    return rows


# Initialize database tables on import
init_db()