"""Non-secret application settings.

Put live credentials in environment variables or a private .env file, never in
this source file.
"""

import os

MODE = os.getenv("BIZFORGE_MODE", "DEV")
FREE_LIMIT = 5
PRO_PRICE_NGN = int(os.getenv("PRO_PRICE_NGN", "5000"))
PRO_PRICE_USD = 5
DEFAULT_CURRENCY = "NGN"
SUPPORTED_CURRENCIES = ["NGN", "USD"]
APP_NAME = "BizForge"
ALLOW_SIGNUP = True
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
