import os
import tempfile
import unittest
from pathlib import Path


TEST_DB = Path(tempfile.gettempdir()) / "bizforge_db_test.sqlite3"
os.environ["BIZFORGE_DB_PATH"] = str(TEST_DB)

from database import db  # noqa: E402


class BizForgeDatabaseTests(unittest.TestCase):
    def setUp(self):
        db.DB = str(TEST_DB)
        if TEST_DB.exists():
            TEST_DB.unlink()
        db.init_db()

    def tearDown(self):
        if TEST_DB.exists():
            TEST_DB.unlink()

    def test_account_password_and_record_isolation(self):
        self.assertTrue(db.create_user("owner@example.com", "secure-password", "Owner Co"))
        self.assertTrue(db.authenticate_user("owner@example.com", "secure-password"))
        self.assertFalse(db.authenticate_user("owner@example.com", "wrong-password"))
        self.assertFalse(db.create_user("owner@example.com", "another-password", "Other Co"))

        db.add_client("owner@example.com", "Acme", "hello@acme.test")
        self.assertEqual(len(db.get_clients("owner@example.com")), 1)
        self.assertEqual(db.get_clients("other@example.com"), [])

    def test_invoice_status_and_verified_payment_lifecycle(self):
        db.create_user("owner@example.com", "secure-password", "Owner Co")
        invoice_number = db.save_invoice(
            "owner@example.com",
            "Acme",
            "Design work",
            "Invoice content",
            5000,
            due_date="2026-08-31",
        )
        invoice = db.get_invoices("owner@example.com")[0]
        self.assertTrue(invoice_number.startswith("BZF-"))
        self.assertEqual(invoice["status"], "draft")
        self.assertTrue(db.update_invoice_status("owner@example.com", invoice["id"], "sent"))
        self.assertEqual(db.get_invoices("owner@example.com")[0]["status"], "sent")

        db.create_pending_payment("owner@example.com", "test-payment", 5000)
        self.assertEqual(db.get_payment("test-payment")["status"], "pending")
        self.assertEqual(db.complete_payment("test-payment", "12345"), "owner@example.com")
        self.assertEqual(db.get_plan("owner@example.com"), "pro")


if __name__ == "__main__":
    unittest.main()
