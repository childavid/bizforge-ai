import base64
import hashlib
import hmac
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


TEST_DB = Path(tempfile.gettempdir()) / "bizforge_payment_webhook_test.sqlite3"
os.environ["BIZFORGE_DB_PATH"] = str(TEST_DB)
os.environ["FLW_SECRET_HASH"] = "test-webhook-hash"
os.environ["FLW_SECRET_KEY"] = "test-secret-key"

from backend.app import app  # noqa: E402
from database import db  # noqa: E402


class PaymentWebhookTests(unittest.TestCase):
    def setUp(self):
        db.DB = str(TEST_DB)
        if TEST_DB.exists():
            TEST_DB.unlink()
        db.init_db()
        db.create_pending_payment("buyer@example.com", "verified-pro-payment", 5000)
        self.client = app.test_client()

    def tearDown(self):
        if TEST_DB.exists():
            TEST_DB.unlink()

    def test_verified_flutterwave_payment_unlocks_pro(self):
        body = json.dumps(
            {"data": {"id": 778899, "tx_ref": "verified-pro-payment"}}, separators=(",", ":")
        ).encode("utf-8")
        signature = base64.b64encode(
            hmac.new(b"test-webhook-hash", body, hashlib.sha256).digest()
        ).decode("ascii")
        provider_response = Mock(
            ok=True,
            json=lambda: {
                "status": "success",
                "data": {
                    "status": "successful",
                    "tx_ref": "verified-pro-payment",
                    "currency": "NGN",
                    "amount": 5000,
                    "customer": {"email": "buyer@example.com"},
                },
            },
        )

        with patch("backend.webhook.requests.get", return_value=provider_response):
            response = self.client.post(
                "/flutterwave-webhook",
                data=body,
                content_type="application/json",
                headers={"flutterwave-signature": signature},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.get_payment("verified-pro-payment")["status"], "successful")
        self.assertEqual(db.get_plan("buyer@example.com"), "pro")


if __name__ == "__main__":
    unittest.main()
