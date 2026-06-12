import os
import sys
import hashlib
import requests
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import upgrade_user

load_dotenv()

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH")

app = Flask(__name__)


@app.route("/flutterwave-webhook", methods=["POST"])
def flutterwave_webhook():
    try:
        logger.info("Webhook received")
        # Verify webhook signature
        received_hash = request.headers.get("verif-hash")

        if not received_hash:
            logger.warning("Missing verif-hash header")
            return jsonify({"error": "Missing verif-hash header"}), 401

        if not FLW_SECRET_HASH:
            logger.error("FLW_SECRET_HASH not configured")
            return jsonify({"error": "FLW_SECRET_HASH not configured"}), 500

        # Get raw request body for hash verification
        raw_body = request.get_data(as_text=True)

        # Compute SHA512 hash of the raw body
        computed_hash = hashlib.sha512(raw_body.encode()).hexdigest()

        # Verify the hash matches the received header
        if computed_hash != received_hash:
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid webhook signature"}), 401
        
        # Parse JSON data after verification
        data = request.json

        # Get transaction ID from webhook
        transaction_id = data.get("data", {}).get("id")

        if not transaction_id:
            logger.warning("No transaction ID in webhook data")
            return jsonify({"error": "No transaction ID"}), 400

        logger.info(f"Processing transaction ID: {transaction_id}")

        # Verify transaction with Flutterwave
        if not FLW_SECRET_KEY:
            return jsonify({"error": "FLW_SECRET_KEY not configured"}), 500
        
        verify_url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        
        headers = {
            "Authorization": f"Bearer {FLW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            verify_response = requests.get(verify_url, headers=headers, timeout=30)
            verify_data = verify_response.json()
            logger.info(f"Transaction verification response: {verify_response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to verify transaction with Flutterwave: {str(e)}")
            return jsonify({"error": f"Failed to verify transaction with Flutterwave: {str(e)}"}), 503
        except ValueError as e:
            logger.error(f"Invalid response from Flutterwave: {str(e)}")
            return jsonify({"error": f"Invalid response from Flutterwave: {str(e)}"}), 502

        if verify_response.status_code == 200 and verify_data.get("status") == "success":
            transaction_status = verify_data["data"]["status"]
            logger.info(f"Transaction status: {transaction_status}")

            # Extract email from customer data
            customer_data = verify_data.get("data", {}).get("customer", {})
            email = customer_data.get("email")

            if not email:
                logger.warning("No email found in transaction data")
                return jsonify({"error": "No email found in transaction data"}), 400

            # Only upgrade if payment is successful
            if transaction_status == "successful":
                try:
                    logger.info(f"Upgrading user: {email}")
                    upgrade_user(email)
                    logger.info(f"Successfully upgraded user: {email}")
                    return jsonify({"status": "ok", "message": "Payment verified and user upgraded"}), 200
                except Exception as db_error:
                    logger.error(f"Failed to upgrade user {email}: {str(db_error)}")
                    return jsonify({"error": f"Failed to upgrade user: {str(db_error)}"}), 500
            else:
                logger.info(f"Payment not successful for {email}: {transaction_status}")
                return jsonify({"status": "failed", "message": f"Payment not successful: {transaction_status}"}), 200
        else:
            error_message = verify_data.get("message", "Unknown error") if verify_data else "No response data"
            logger.error(f"Transaction verification failed: {error_message}")
            return jsonify({"error": f"Transaction verification failed: {error_message}"}), 400

    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)