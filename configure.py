# =========================
# 🧠 BUSINESS AI CONFIG
# =========================

# MODE (important for payments later)
# DEV = testing (fake payments allowed)
# LIVE = real money mode (Flutterwave)
MODE = "DEV"


# =========================
# 💰 SUBSCRIPTION SETTINGS
# =========================

FREE_LIMIT = 3  # number of invoices/proposals free users can create

PRO_PRICE_NGN = 5000
PRO_PRICE_USD = 5


# =========================
# 💱 CURRENCY SETTINGS
# =========================

DEFAULT_CURRENCY = "NGN"

SUPPORTED_CURRENCIES = ["NGN", "USD"]


# =========================
# 🔐 APP SETTINGS
# =========================

APP_NAME = "BizPilot SaaS"

ALLOW_SIGNUP = True


# =========================
# 💳 FLUTTERWAVE (PLACEHOLDERS)
# =========================

FLW_PUBLIC_KEY = "YOUR_PUBLIC_KEY"
FLW_SECRET_KEY = "YOUR_SECRET_KEY"


# =========================
# 📧 EMAIL SETTINGS (future use)
# =========================

SEND_EMAIL_RECEIPTS = False

PRO_PRICE_NGN = 5000
PRO_PRICE_USD = 5

FLW_SECRET_KEY = "YOUR_FLUTTERWAVE_SECRET"