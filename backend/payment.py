import os
import sys
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_plan

load_dotenv()

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")

print("FLW_SECRET_KEY loaded:", bool(FLW_SECRET_KEY))
print("BACKEND_URL:", BACKEND_URL)

app = Flask(__name__)


@app.route("/pay", methods=["POST"])
def create_payment():
    try:
        data = request.json
        print("Request JSON:", data)
        email = data.get("email")
        tx_ref = data.get("tx_ref")
        print("Email:", email)
        print("tx_ref:", tx_ref)

        if not email:
            return jsonify({"error": "email is required"}), 400

        # FIXED PRICE: Enforce 100 NGN for PRO upgrade
        # Ignore any amount/currency sent from frontend for security
        FIXED_AMOUNT = 100
        FIXED_CURRENCY = "NGN"

        url = "https://api.flutterwave.com/v3/payments"

        headers = {
            "Authorization": f"Bearer {FLW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "tx_ref": tx_ref,
            "amount": FIXED_AMOUNT,
            "currency": FIXED_CURRENCY,
            "redirect_url": BACKEND_URL,  # Redirect back to Streamlit after payment
            "customer": {
                "email": email
            },
            "payment_options": "card",
            "customizations": {
                "title": "BizPilot SaaS Upgrade",
                "description": "Upgrade to PRO plan"
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        res = response.json()
        print("Flutterwave response:", res)

        if response.status_code == 200 and res.get("status") == "success":
            return jsonify({
                "status": "success",
                "data": res.get("data")
            }), 200
        else:
            error_message = res.get("message", "Payment request failed")
            print("Flutterwave error message:", error_message)
            return jsonify({
                "status": "error",
                "message": error_message
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/plan/<email>", methods=["GET"])
def get_user_plan(email):
    try:
        plan = get_plan(email)
        return jsonify({"email": email, "plan": plan}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)