import os
import tempfile
import unittest
from pathlib import Path


TEST_DB = Path(tempfile.gettempdir()) / "bizforge_pro_access_test.sqlite3"
os.environ["BIZFORGE_DB_PATH"] = str(TEST_DB)
os.environ["PAYMENTS_ENABLED"] = "false"
os.environ["PRO_PRICE_NGN"] = "5000"

from backend import payment  # noqa: E402
from database import db  # noqa: E402


class ProAccessTests(unittest.TestCase):
    def setUp(self):
        db.DB = str(TEST_DB)
        if TEST_DB.exists():
            TEST_DB.unlink()
        db.init_db()
        self.client = payment.app.test_client()

    def tearDown(self):
        if TEST_DB.exists():
            TEST_DB.unlink()

    def test_price_and_pro_tools_require_verified_payment(self):
        self.assertEqual(payment._pro_price_ngn(), 5000)
        db.create_pending_payment("buyer@example.com", "pro-test-payment", 5000)

        locked = self.client.post(
            "/api/generate", json={"tool": "calendar", "email": "buyer@example.com", "topic": "delivery"}
        )
        self.assertEqual(locked.status_code, 403)
        self.assertEqual(self.client.get("/api/pro-status?email=buyer@example.com").status_code, 403)

        db.complete_payment("pro-test-payment", "verified-transaction")
        unlocked = self.client.post(
            "/api/generate", json={"tool": "calendar", "email": "buyer@example.com", "topic": "delivery"}
        )
        self.assertEqual(unlocked.status_code, 200)
        self.assertIn("Day 1", unlocked.get_json()["result"])
        self.assertEqual(self.client.get("/api/pro-status?email=buyer@example.com").status_code, 200)

    def test_checkout_is_not_started_until_payments_are_configured(self):
        response = self.client.post("/pay", json={"email": "buyer@example.com"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("not enabled", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
