"""Production WSGI entry point for BizForge."""

from backend.payment import app
from backend.webhook import register_webhook

register_webhook(app)
