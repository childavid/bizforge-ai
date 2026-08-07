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
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#f8fafc;font:16px system-ui,sans-serif}.wrap{max-width:980px;margin:auto;padding:42px 20px}h1{font-size:clamp(2rem,6vw,4rem);margin:0}p{color:#cbd5e1;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin-top:28px}.card{background:#151d35;border:1px solid #334155;border-radius:16px;padding:20px}.pro{border-color:#a78bfa;background:linear-gradient(135deg,#221b48,#151d35)}label{display:block;font-weight:700;margin:12px 0 6px}input,select,textarea{width:100%;border:1px solid #64748b;border-radius:9px;padding:11px;background:#0f172a;color:#fff;font:inherit}textarea{min-height:110px}button{width:100%;margin-top:16px;border:0;border-radius:9px;padding:12px;background:#f8fafc;color:#111827;font-weight:800;font-size:1rem;cursor:pointer}button:hover{background:#c4b5fd}.result{white-space:pre-wrap;min-height:64px;margin-top:14px;padding:12px;background:#0b1020;border-radius:9px;color:#e2e8f0}.note{font-size:.9rem}.hidden{display:none}.account{max-width:440px}.price{color:#ddd6fe;font-weight:800}</style></head>
<body><main class="wrap"><p>Free writing tools for growing businesses</p><h1>BizForge AI</h1><p>Write a polished email, plan a practical business idea, or create a ready-to-post social update.</p><section class="account"><label>Your BizForge email (for Pro access)</label><input id="account-email" type="email" placeholder="you@example.com"></section>
<div class="grid">
<section class="card"><h2>Email writer</h2><label>What do you want to say?</label><textarea id="email-purpose" placeholder="Ask a client for a meeting"></textarea><label>Recipient</label><input id="email-recipient" placeholder="Client name"><button data-tool="email">Write email</button><div class="result" id="email-result">Your draft will appear here.</div></section>
<section class="card"><h2>Business ideas</h2><label>Interest or industry</label><textarea id="idea-interest" placeholder="Beauty products"></textarea><label>Who will buy?</label><input id="idea-audience" placeholder="Students in Lagos"><label>Starting budget</label><input id="idea-budget" placeholder="₦50,000"><button data-tool="idea">Create idea</button><div class="result" id="idea-result">Your idea will appear here.</div></section>
<section class="card"><h2>Social post</h2><label>Topic</label><textarea id="social-topic" placeholder="Our new weekend delivery service"></textarea><label>Platform</label><select id="social-platform"><option>Instagram</option><option>LinkedIn</option><option>X / Twitter</option></select><button data-tool="social">Write post</button><div class="result" id="social-result">Your post will appear here.</div></section></div>
<section class="card pro"><h2>BizForge Pro</h2><p class="price">One-time upgrade: ₦{{ price }}</p><p>Verified Pro members unlock a seven-day content calendar and a customer-growth campaign planner.</p><button id="upgrade">Upgrade to Pro</button><button id="check-pro">Check Pro access</button><div class="result" id="pro-result">Pro tools stay locked until your payment is verified.</div><div id="pro-tools" class="grid hidden"><section class="card"><h3>7-day content calendar</h3><label>Business focus</label><input id="calendar-topic" placeholder="Weekend delivery"><button data-tool="calendar">Create calendar</button><div class="result" id="calendar-result"></div></section><section class="card"><h3>Customer-growth campaign</h3><label>Offer or goal</label><input id="campaign-topic" placeholder="Get more repeat customers"><button data-tool="campaign">Create campaign</button><div class="result" id="campaign-result"></div></section></div></section>
<p class="note">Pro access is applied only after secure payment verification.</p></main>
<script>const value=id=>document.getElementById(id).value;const account=()=>value('account-email').trim();const setResult=(id,text)=>document.getElementById(id+'-result').textContent=text;async function generate(tool){const result=document.getElementById(tool+'-result'),button=document.querySelector('[data-tool="'+tool+'"]');button.disabled=true;button.textContent='Writing...';try{const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tool,email:account(),purpose:value('email-purpose'),recipient:value('email-recipient'),interest:value('idea-interest'),audience:value('idea-audience'),budget:value('idea-budget'),topic:tool==='calendar'?value('calendar-topic'):tool==='campaign'?value('campaign-topic'):value('social-topic'),platform:value('social-platform')})});const data=await r.json();if(!r.ok)throw Error(data.error||'Please try again.');result.textContent=data.result}catch(error){result.textContent=error.message}finally{button.disabled=false;button.textContent={email:'Write email',idea:'Create idea',social:'Write post',calendar:'Create calendar',campaign:'Create campaign'}[tool]}}document.querySelectorAll('button[data-tool]').forEach(button=>button.onclick=()=>generate(button.dataset.tool));document.getElementById('upgrade').onclick=async()=>{try{const r=await fetch('/pay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:account()})});const data=await r.json();if(!r.ok)throw Error(data.message||'Checkout is unavailable.');location.href=data.link}catch(error){setResult('pro',error.message)}};document.getElementById('check-pro').onclick=async()=>{try{const r=await fetch('/api/pro-status?email='+encodeURIComponent(account()));const data=await r.json();if(!r.ok)throw Error(data.message||'Pro payment has not been verified yet.');document.getElementById('pro-tools').classList.remove('hidden');setResult('pro','Payment verified. Your Pro tools are unlocked.')}catch(error){document.getElementById('pro-tools').classList.add('hidden');setResult('pro',error.message)}};</script></body></html>"""


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
    return render_template_string(PUBLIC_APP_HTML, price=_pro_price_ngn())


@app.get("/health")
def health():
    return jsonify({"status": "ok", "payments_enabled": _payments_enabled()})


@app.get("/api/pro-status")
def pro_status():
    """Reveal Pro tools only for accounts upgraded by the verified webhook."""
    try:
        email = normalise_email(request.args.get("email", ""))
    except ValueError:
        return jsonify({"message": "Enter the email used for checkout."}), 400
    if get_plan(email) != "pro":
        return jsonify({"message": "Pro payment has not been verified yet."}), 403
    return jsonify({"plan": "pro"})


def _pro_calendar(topic):
    focus = topic.strip() or "your business"
    return "\n".join(
        f"Day {day}: {idea}" for day, idea in enumerate(
            [
                f"Introduce how {focus} helps customers.",
                "Share a quick behind-the-scenes tip.",
                "Answer one common customer question.",
                "Show a customer-friendly use case.",
                "Post a short testimonial or proof point.",
                "Share a practical weekend offer or reminder.",
                "Ask followers what they want next.",
            ],
            start=1,
        )
    )


def _pro_campaign(topic):
    focus = topic.strip() or "your offer"
    return (
        f"Campaign goal: {focus}\n\n"
        "1. Attract: Publish one useful post that names the customer problem.\n"
        "2. Capture: Invite interested people to message you for a simple checklist or quote.\n"
        "3. Convert: Follow up within one day with a clear next step and a personal recommendation.\n\n"
        "Measure: track enquiries, follow-ups, and completed sales each week."
    )


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
    if tool in {"calendar", "campaign"}:
        try:
            email = normalise_email(data.get("email", ""))
        except ValueError:
            return jsonify({"error": "Enter the email used for checkout."}), 400
        if get_plan(email) != "pro":
            return jsonify({"error": "This Pro tool unlocks after payment is verified."}), 403
        content = _pro_calendar(data.get("topic", "")) if tool == "calendar" else _pro_campaign(data.get("topic", ""))
        return jsonify({"result": content})
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
