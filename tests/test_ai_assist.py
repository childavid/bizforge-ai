import unittest
from unittest.mock import patch

from utils.ai_assist import (
    generate_business_idea_assist,
    generate_email_assist,
    generate_social_post_assist,
)


class AiAssistFallbackTests(unittest.TestCase):
    @patch("utils.ai_assist._generate_with_ollama", return_value=None)
    def test_email_fallback_uses_context_and_is_editable(self, _mock_ollama):
        result = generate_email_assist("follow up about the design proposal", "Ada", "Warm")

        self.assertFalse(result["used_ai"])
        self.assertIn("Ada", result["body"])
        self.assertIn("design proposal", result["body"])
        self.assertIn("[Your Name]", result["body"])

    @patch("utils.ai_assist._generate_with_ollama", return_value=None)
    def test_social_fallback_respects_the_selected_platform(self, _mock_ollama):
        result = generate_social_post_assist(
            "Our same-day delivery service", "LinkedIn", "Professional", "Get enquiries", "Swift Co"
        )

        self.assertFalse(result["used_ai"])
        self.assertEqual(result["platform"], "LinkedIn")
        self.assertIn("same-day delivery", result["post"])
        self.assertIn("Swift Co", result["post"])

    @patch("utils.ai_assist._generate_with_ollama", return_value=None)
    def test_business_idea_fallback_includes_validation_steps(self, _mock_ollama):
        result = generate_business_idea_assist("mobile laundry", "busy workers", "NGN 50,000")

        self.assertFalse(result["used_ai"])
        self.assertIn("busy workers", result["idea"])
        self.assertIn("First three steps", result["idea"])
        self.assertIn("NGN 50,000", result["idea"])


if __name__ == "__main__":
    unittest.main()
