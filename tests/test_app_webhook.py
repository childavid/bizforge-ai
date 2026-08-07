import hashlib
import hmac
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TEST_DB = Path(tempfile.gettempdir()) / "bizforge_app_webhook_test.sqlite3"
os.environ["BIZFORGE_DB_PATH"] = str(TEST_DB)
os.environ["APP_WEBHOOK_SECRET"] = "test-app-webhook-secret"

from backend.webhook import app  # noqa: E402
from database import db  # noqa: E402


class AppWebhookTests(unittest.TestCase):
    def setUp(self):
        db.DB = str(TEST_DB)
        if TEST_DB.exists():
            TEST_DB.unlink()
        db.init_db()
        self.client = app.test_client()
        self.body = json.dumps(
            {"event_id": "online-001", "event": "lead.created", "data": {"source": "website"}},
            separators=(",", ":"),
        ).encode("utf-8")
        self.signature = hmac.new(
            os.environ["APP_WEBHOOK_SECRET"].encode("utf-8"), self.body, hashlib.sha256
        ).hexdigest()

    def tearDown(self):
        if TEST_DB.exists():
            TEST_DB.unlink()

    @patch("backend.webhook.notify_app_webhook_event")
    def test_signed_event_is_accepted_once(self, notify_event):
        response = self.client.post(
            "/app-webhook",
            data=self.body,
            content_type="application/json",
            headers={"X-BizForge-Signature": f"sha256={self.signature}"},
        )
        duplicate = self.client.post(
            "/app-webhook",
            data=self.body,
            content_type="application/json",
            headers={"X-BizForge-Signature": self.signature},
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.get_json()["status"], "duplicate")
        notify_event.assert_called_once_with("lead.created", "online-001", {"source": "website"})

    def test_invalid_signature_is_rejected(self):
        response = self.client.post(
            "/app-webhook",
            data=self.body,
            content_type="application/json",
            headers={"X-BizForge-Signature": "wrong"},
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
