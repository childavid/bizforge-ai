"""Non-blocking owner email notifications for important BizForge events."""

import logging
import os
import smtplib
import ssl
import json
from datetime import datetime, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


def _settings():
    """Read mail settings at send time so deployments can update environment values."""
    return {
        "recipient": os.getenv("NOTIFICATION_RECIPIENT", "").strip(),
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "465")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", "").strip(),
    }


def email_notifications_configured() -> bool:
    """Return whether the server can send transactional email without exposing secrets."""
    try:
        settings = _settings()
    except ValueError:
        return False
    return all(settings[key] for key in ("host", "username", "password", "from_email"))


def _send_email(recipient: str, subject: str, body: str) -> bool:
    """Send one transactional email without allowing a mail failure to break the app."""
    try:
        settings = _settings()
    except ValueError:
        logger.error("Email notification is not configured with a valid SMTP port")
        return False

    if not recipient or not email_notifications_configured():
        logger.info("Email notifications are not configured; event email was skipped")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings["from_email"]
    message["To"] = recipient
    message.set_content(body)

    try:
        context = ssl.create_default_context()
        if settings["port"] == 465:
            with smtplib.SMTP_SSL(settings["host"], settings["port"], context=context, timeout=15) as server:
                server.login(settings["username"], settings["password"])
                server.send_message(message)
        else:
            with smtplib.SMTP(settings["host"], settings["port"], timeout=15) as server:
                server.starttls(context=context)
                server.login(settings["username"], settings["password"])
                server.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Could not send notification email")
        return False
    return True


def send_admin_notification(subject: str, body: str) -> bool:
    """Email the configured owner without interrupting a sign-up or payment flow."""
    try:
        settings = _settings()
    except ValueError:
        logger.error("Email notification is not configured with a valid SMTP port")
        return False
    return _send_email(settings["recipient"], subject, body)


def notify_new_signup(account_email: str, business_name: str) -> bool:
    """Tell the owner that a new BizForge account was created."""
    created_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    return send_admin_notification(
        "BizForge: new account sign-up",
        "A new BizForge account was created.\n\n"
        f"Business: {business_name.strip() or 'Not provided'}\n"
        f"Account email: {account_email}\n"
        f"Created: {created_at}\n",
    )


def notify_successful_payment(account_email: str, amount, currency: str, transaction_id: str) -> bool:
    """Tell the owner only after the payment webhook has verified the transaction."""
    paid_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    return send_admin_notification(
        "BizForge: verified payment received",
        "A BizForge Pro payment was verified and the account was upgraded.\n\n"
        f"Account email: {account_email}\n"
        f"Amount: {amount} {currency}\n"
        f"Transaction ID: {transaction_id}\n"
        f"Verified: {paid_at}\n",
    )


def notify_app_webhook_event(event_type: str, event_id: str, data: dict) -> bool:
    """Send the owner a compact record of a signed external integration event."""
    received_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    details = json.dumps(data, ensure_ascii=False, indent=2, default=str)[:4_000]
    return send_admin_notification(
        f"BizForge integration event: {event_type}",
        "BizForge accepted a signed app-integration webhook.\n\n"
        f"Event: {event_type}\n"
        f"Event ID: {event_id}\n"
        f"Received: {received_at}\n\n"
        f"Data:\n{details}\n",
    )


def notify_schedule_due(account_email: str, title: str, due_at: str, timezone_name: str, notes: str = "") -> bool:
    """Send the account owner one private schedule reminder."""
    try:
        due = datetime.fromisoformat(due_at)
        due_label = due.astimezone(ZoneInfo(timezone_name)).strftime("%d %b %Y, %H:%M")
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        due_label = due_at
    return _send_email(
        account_email,
        f"BizForge reminder: {title}",
        "Your BizForge schedule reminder is ready.\n\n"
        f"Schedule: {title}\n"
        f"Due: {due_label} ({timezone_name})\n"
        f"Notes: {notes or 'None'}\n",
    )
