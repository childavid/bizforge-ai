import os
import unittest
from unittest.mock import MagicMock, patch

from utils import notifications


class OwnerNotificationTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "NOTIFICATION_RECIPIENT": "owner@example.test",
            "SMTP_HOST": "smtp.example.test",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "sender@example.test",
            "SMTP_PASSWORD": "app-password",
            "SMTP_FROM_EMAIL": "sender@example.test",
        },
        clear=True,
    )
    @patch("utils.notifications.ssl.create_default_context")
    @patch("utils.notifications.smtplib.SMTP_SSL")
    def test_signup_notification_uses_configured_owner_recipient(self, smtp_ssl, _ssl_context):
        server = MagicMock()
        smtp_ssl.return_value.__enter__.return_value = server

        sent = notifications.notify_new_signup("new@example.test", "New Co")

        self.assertTrue(sent)
        server.login.assert_called_once_with("sender@example.test", "app-password")
        message = server.send_message.call_args.args[0]
        self.assertEqual(message["To"], "owner@example.test")
        self.assertEqual(message["Subject"], "BizForge: new account sign-up")
        self.assertIn("new@example.test", message.get_content())

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_mail_configuration_does_not_interrupt_the_app(self):
        self.assertFalse(notifications.notify_successful_payment("buyer@example.test", 5000, "NGN", "123"))


if __name__ == "__main__":
    unittest.main()
