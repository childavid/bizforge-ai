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
from flask import Flask, jsonify, render_template_string, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import (  # noqa: E402
    create_pending_payment,
    get_plan,
    init_db,
    normalise_email,
)
from utils.ai_assist import (  # noqa: E402
    generate_business_idea_assist,
    generate_email_assist,
    generate_social_post_assist,
)


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
init_db()


PUBLIC_APP_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BizForge AI</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#f8fafc;font:16px system-ui,sans-serif}.wrap{max-width:900px;margin:auto;padding:42px 20px}h1{font-size:clamp(2rem,6vw,4rem);margin:0}p{color:#cbd5e1;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin-top:28px}.card{background:#151d35;border:1px solid #334155;border-radius:16px;padding:20px}label{display:block;font-weight:700;margin:12px 0 6px}input,select,textarea{width:100%;border:1px solid #64748b;border-radius:9px;padding:11px;background:#0f172a;color:#fff;font:inherit}textarea{min-height:110px}button{width:100%;margin-top:16px;border:0;border-radius:9px;padding:12px;background:#f8fafc;color:#111827;font-weight:800;font-size:1rem;cursor:pointer}button:hover{background:#c4b5fd}.result{white-space:pre-wrap;min-height:64px;margin-top:14px;padding:12px;background:#0b1020;border-radius:9px;color:#e2e8f0}.note{font-size:.9rem}.hidden{display:none}</style></head>
<body><main class="wrap"><p>Free writing tools for growing businesses</p><h1>BizForge AI</h1><p>Write a polished email, plan a practical business idea, or create a ready-to-post social update.</p>
<div class="grid">
<section class="card"><h2>Email writer</h2><label>What do you want to say?</label><textarea id="email-purpose" placeholder="Ask a client for a meeting"></textarea><label>Recipient</label><input id="email-recipient" placeholder="Client name"><button data-tool="email">Write email</button><div class="result" id="email-result">Your draft will appear here.</div></section>
<section class="card"><h2>Business ideas</h2><label>Interest or industry</label><textarea id="idea-interest" placeholder="Beauty products"></textarea><label>Who will buy?</label><input id="idea-audience" placeholder="Students in Lagos"><label>Starting budget</label><input id="idea-budget" placeholder="₦50,000"><button data-tool="idea">Create idea</button><div class="result" id="idea-result">Your idea will appear here.</div></section>
<section class="card"><h2>Social post</h2><label>Topic</label><textarea id="social-topic" placeholder="Our new weekend delivery service"></textarea><label>Platform</label><select id="social-platform"><option>Instagram</option><option>LinkedIn</option><option>X / Twitter</option></select><button data-tool="social">Write post</button><div class="result" id="social-result">Your post will appear here.</div></section></div>
<p class="note">Payments are enabled only after secure payment-provider setup.</p></main>
<script>const value=id=>document.getElementById(id).value;document.querySelectorAll('button[data-tool]').forEach(button=>button.onclick=async()=>{const tool=button.dataset.tool,result=document.getElementById(tool+'-result');button.disabled=true;button.textContent='Writing...';try{const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tool,purpose:value('email-purpose'),recipient:value('email-recipient'),interest:value('idea-interest'),audience:value('idea-audience'),budget:value('idea-budget'),topic:value('social-topic'),platform:value('social-platform')})});const data=await r.json();if(!r.ok)throw Error(data.error||'Please try again.');result.textContent=data.result}catch(error){result.textContent=error.message}finally{button.disabled=false;button.textContent=tool==='email'?'Write email':tool==='idea'?'Create idea':'Write post'}})</script></body></html>"""


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
    return render_template_string(PUBLIC_APP_HTML)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "payments_enabled": _payments_enabled()})


@app.post("/api/generate")
def generate_public_content():
    """Provide the three core writing tools to the lightweight public page."""
    data = request.get_json(silent=True) or {}
    tool = data.get("tool")

    if tool == "email":
        result = generate_email_assist(data.get("purpose", ""), data.get("recipient", ""))
        return jsonify({"result": f"Subject: {result['subject']}\n\n{result['body']}"})
    if tool == "idea":
        result = generate_business_idea_assist(
            data.get("interest", ""), data.get("audience", ""), data.get("budget", "")
        )
        return jsonify({"result": f"{result['category']}\n\n{result['idea']}"})
    if tool == "social":
        result = generate_social_post_assist(data.get("topic", ""), data.get("platform", "Instagram"))
        return jsonify({"result": result["post"]})
    return jsonify({"error": "Choose email, idea, or social."}), 400


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
