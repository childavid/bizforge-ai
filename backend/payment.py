"""Server-side checkout endpoints for BizForge.

This module never exposes payment secrets to the Streamlit app.  It records a
pending checkout first, then the webhook verifies the same reference before a
customer receives a Pro plan.
"""

import logging
import os
import sys
import uuid

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import (  # noqa: E402
    create_pending_payment,
    get_plan,
    init_db,
    normalise_email,
)


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
init_db()


def _payments_enabled():
    return os.getenv("PAYMENTS_ENABLED", "false").strip().lower() == "true"


def _pro_price_ngn():
    try:
        price = int(os.getenv("PRO_PRICE_NGN", "5000"))
    except ValueError as exc:
        raise ValueError("PRO_PRICE_NGN must be a whole number") from exc
    if price <= 0:
        raise ValueError("PRO_PRICE_NGN must be greater than zero")
    return price


@app.get("/")
def home():
    return jsonify({"service": "BizForge API", "status": "running"})


@app.get("/health")
def health():
    return jsonify({"status": "ok", "payments_enabled": _payments_enabled()})


@app.post("/pay")
def create_payment():
    if not _payments_enabled():
        return jsonify({"status": "error", "message": "Payments are not enabled yet."}), 503

    data = request.get_json(silent=True) or {}
    try:
        email = normalise_email(data.get("email", ""))
        amount = _pro_price_ngn()
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    secret_key = os.getenv("FLW_SECRET_KEY")
    backend_url = os.getenv("BACKEND_URL", "").rstrip("/")
    if not secret_key or not backend_url:
        logger.error("Checkout configuration is incomplete")
        return jsonify({"status": "error", "message": "Checkout is not configured."}), 503

    tx_ref = f"bizforge-{uuid.uuid4().hex}"
    try:
        create_pending_payment(email, tx_ref, amount, "NGN", "pro")
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": "NGN",
            "redirect_url": f"{backend_url}/payment-return?tx_ref={tx_ref}",
            "customer": {"email": email},
            "payment_options": "card,banktransfer,ussd,opay",
            "customizations": {
                "title": "BizForge Pro",
                "description": "BizForge Pro subscription",
            },
        }
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            json=payload,
            headers={"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"},
            timeout=20,
        )
        response_data = response.json()
    except requests.exceptions.RequestException:
        logger.exception("Could not create checkout session")
        return jsonify({"status": "error", "message": "Could not reach the payment provider."}), 503
    except ValueError:
        logger.exception("Payment provider returned invalid JSON")
        return jsonify({"status": "error", "message": "Payment provider returned an invalid response."}), 502
    except Exception:
        logger.exception("Could not prepare checkout")
        return jsonify({"status": "error", "message": "Could not prepare checkout."}), 500

    link = response_data.get("data", {}).get("link") if isinstance(response_data, dict) else None
    if response.ok and response_data.get("status") == "success" and link:
        return jsonify({"status": "success", "link": link, "tx_ref": tx_ref}), 200

    logger.warning("Payment provider rejected checkout request: status=%s", response.status_code)
    return jsonify({"status": "error", "message": "Could not create a payment link. Please try again."}), 502


@app.get("/payment-return")
def payment_return():
    """A neutral return page; access is granted only by verified webhook data."""
    return (
        "Payment received. BizForge will confirm your payment shortly. "
        "You can return to the app and refresh your plan status.",
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


@app.get("/plan/<email>")
def get_user_plan(email):
    try:
        return jsonify({"email": normalise_email(email), "plan": get_plan(email)}), 200
    except ValueError:
        return jsonify({"error": "Invalid email address"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=False)
