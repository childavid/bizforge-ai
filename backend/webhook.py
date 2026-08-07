"""Flutterwave webhook verification for BizForge."""

import base64
import hashlib
import hmac
import logging
import os
import sys
from decimal import Decimal, InvalidOperation

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import complete_payment, get_payment, init_db, normalise_email  # noqa: E402
from database.db import record_app_webhook_event  # noqa: E402
from utils.notifications import notify_app_webhook_event, notify_successful_payment  # noqa: E402


load_dotenv()
logger = logging.getLogger(__name__)
init_db()


def _same_amount(left, right):
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, ValueError):
        return False


def flutterwave_webhook():
    secret_hash = os.getenv("FLW_SECRET_HASH")
    legacy_signature = request.headers.get("verif-hash")
    modern_signature = request.headers.get("flutterwave-signature")
    raw_body = request.get_data()
    modern_expected = base64.b64encode(
        hmac.new(secret_hash.encode("utf-8"), raw_body, hashlib.sha256).digest()
    ).decode("ascii") if secret_hash else ""
    valid_signature = bool(
        secret_hash
        and (
            (legacy_signature and hmac.compare_digest(legacy_signature, secret_hash))
            or (modern_signature and hmac.compare_digest(modern_signature, modern_expected))
        )
    )
    if not valid_signature:
        logger.warning("Rejected webhook with an invalid signature")
        return jsonify({"error": "Invalid webhook signature"}), 401

    payload = request.get_json(silent=True) or {}
    event_data = payload.get("data", {})
    transaction_id = event_data.get("id")
    tx_ref = event_data.get("tx_ref")
    if not transaction_id or not tx_ref:
        return jsonify({"error": "Payment event is missing transaction details"}), 400

    expected = get_payment(tx_ref)
    if not expected:
        logger.warning("Rejected unknown payment reference")
        return jsonify({"error": "Unknown payment reference"}), 400

    secret_key = os.getenv("FLW_SECRET_KEY")
    if not secret_key:
        logger.error("Webhook payment verification is not configured")
        return jsonify({"error": "Payment verification is unavailable"}), 503

    try:
        verification = requests.get(
            f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
            headers={"Authorization": f"Bearer {secret_key}"},
            timeout=20,
        )
        verified = verification.json()
    except requests.exceptions.RequestException:
        logger.exception("Could not verify payment transaction")
        return jsonify({"error": "Could not verify payment"}), 503
    except ValueError:
        logger.exception("Payment verification returned invalid JSON")
        return jsonify({"error": "Invalid payment verification response"}), 502

    details = verified.get("data", {}) if verification.ok and verified.get("status") == "success" else {}
    customer = details.get("customer", {})
    valid = all(
        (
            details.get("status") == "successful",
            details.get("tx_ref") == expected["tx_ref"],
            details.get("currency") == expected["currency"],
            _same_amount(details.get("amount"), expected["amount"]),
            customer.get("email") and normalise_email(customer["email"]) == expected["email"],
        )
    )
    if not valid:
        logger.warning("Rejected payment that did not match its expected checkout")
        return jsonify({"error": "Payment details do not match checkout"}), 400

    is_newly_completed = expected["status"] != "successful"
    try:
        complete_payment(expected["tx_ref"], transaction_id)
    except Exception:
        logger.exception("Could not finish verified payment")
        return jsonify({"error": "Could not apply payment"}), 500

    # Flutterwave may resend the same webhook. Alert only for the first
    # verified completion; a notification failure must not undo a payment.
    if is_newly_completed:
        notify_successful_payment(
            expected["email"], expected["amount"], expected["currency"], str(transaction_id)
        )
    return jsonify({"status": "ok"}), 200


def app_event_webhook():
    """Accept signed events from online integrations without changing account state."""
    secret = os.getenv("APP_WEBHOOK_SECRET", "")
    if not secret:
        logger.error("App webhook is not configured")
        return jsonify({"error": "App webhook is not configured"}), 503

    raw_body = request.get_data()
    supplied_signature = request.headers.get("X-BizForge-Signature", "")
    if supplied_signature.startswith("sha256="):
        supplied_signature = supplied_signature.removeprefix("sha256=")
    expected_signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not supplied_signature or not hmac.compare_digest(supplied_signature, expected_signature):
        logger.warning("Rejected app webhook with an invalid signature")
        return jsonify({"error": "Invalid webhook signature"}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Webhook payload must be a JSON object"}), 400
    event_id = payload.get("event_id")
    event_type = payload.get("event")
    data = payload.get("data", {})
    if not isinstance(event_id, str) or not isinstance(event_type, str) or not isinstance(data, dict):
        return jsonify({"error": "event_id, event, and object data are required"}), 400

    try:
        is_new_event = record_app_webhook_event(event_id, event_type)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not is_new_event:
        return jsonify({"status": "duplicate", "event_id": event_id}), 200

    # The endpoint is intentionally notification-only. Online callers cannot
    # create accounts, alter plans, or complete payments through this route.
    notify_app_webhook_event(event_type, event_id, data)
    return jsonify({"status": "accepted", "event_id": event_id}), 202


def register_webhook(flask_app):
    flask_app.add_url_rule("/flutterwave-webhook", "flutterwave_webhook", flutterwave_webhook, methods=["POST"])
    flask_app.add_url_rule("/app-webhook", "app_event_webhook", app_event_webhook, methods=["POST"])
    return flask_app


# This keeps the webhook runnable on its own for hosts that point directly to it.
app = Flask(__name__)
register_webhook(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
