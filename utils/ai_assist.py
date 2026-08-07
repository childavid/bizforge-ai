"""Free local-AI helpers for BizForge's writing tools.

When Ollama is installed and running, these helpers use the selected model on
the same computer.  Ollama is optional: if it is unavailable, the application
still produces a tailored, editable draft without making a remote AI request.
"""

import json
import os
import re
from typing import Any

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
AI_PROVIDER = os.getenv("BIZFORGE_AI_PROVIDER", "ollama").strip().lower()


def _clean_text(value: str, fallback: str) -> str:
    """Return a compact, user-safe value for a prompt or local draft."""
    cleaned = " ".join((value or "").strip().split())
    return cleaned[:600] if cleaned else fallback


def _parse_json_response(response_text: str, required_keys: set[str]) -> dict[str, str] | None:
    """Accept JSON from a model even if it wrapped the object in a code fence."""
    candidate = response_text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)

    if not candidate.startswith("{"):
        match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
        if not match:
            return None
        candidate = match.group(0)

    try:
        payload = json.loads(candidate)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict) or not required_keys.issubset(payload):
        return None

    cleaned = {key: str(payload[key]).strip() for key in required_keys}
    return cleaned if all(cleaned.values()) else None


def _generate_with_ollama(prompt: str, required_keys: set[str]) -> dict[str, str] | None:
    """Generate structured text with a free local Ollama model when available."""
    if AI_PROVIDER != "ollama":
        return None

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.7},
            },
            timeout=(2, 45),
        )
        response.raise_for_status()
        return _parse_json_response(response.json().get("response", ""), required_keys)
    except (requests.RequestException, ValueError, AttributeError):
        return None


def _title_case_phrase(value: str) -> str:
    words = _clean_text(value, "your business").split()
    return " ".join(words[:8]).title()


def _classify_business(interest: str) -> str:
    lower_interest = interest.lower()
    if any(word in lower_interest for word in ("app", "software", "tech", "digital", "ai")):
        return "Technology"
    if any(word in lower_interest for word in ("food", "restaurant", "catering", "baking")):
        return "Food & Hospitality"
    if any(word in lower_interest for word in ("fashion", "beauty", "hair", "clothing")):
        return "Lifestyle & Retail"
    if any(word in lower_interest for word in ("coach", "consult", "service", "agency")):
        return "Professional Services"
    return "Small Business"


def _email_fallback(purpose: str, recipient: str, tone: str) -> dict[str, str]:
    topic = _clean_text(purpose, "your message")
    name = _clean_text(recipient, "there")
    subject = f"Regarding {_title_case_phrase(topic)}"
    opening = "I hope you are well." if tone == "Professional" else "I hope you are having a good day."
    body = (
        f"Dear {name},\n\n"
        f"{opening} I am writing regarding {topic}.\n\n"
        "I would be glad to share the relevant details and answer any questions you may have. "
        "Please let me know a convenient time to discuss the next step.\n\n"
        "Thank you for your time. I look forward to hearing from you.\n\n"
        "Best regards,\n[Your Name]"
    )
    return {"subject": subject, "body": body}


def generate_email_assist(purpose: str, recipient: str = "", tone: str = "Professional") -> dict[str, Any]:
    """Create a personal business-email draft using local AI where possible."""
    topic = _clean_text(purpose, "your message")
    name = _clean_text(recipient, "there")
    prompt = f"""You write concise, useful business emails. Create one editable email draft.
Return valid JSON only with exactly these string fields: subject, body.
The body must greet {name!r}, use blank lines between paragraphs, have a clear next step,
and end with 'Best regards,\\n[Your Name]'. Do not use markdown, placeholders other than
[Your Name], or make promises the sender did not provide.
Tone: {tone}.
Purpose: {topic}
"""
    generated = _generate_with_ollama(prompt, {"subject", "body"})
    if generated:
        generated["used_ai"] = True
        return generated
    fallback = _email_fallback(topic, name, tone)
    fallback["used_ai"] = False
    return fallback


def _social_fallback(topic: str, platform: str, tone: str, goal: str, business_name: str) -> str:
    business = _clean_text(business_name, "our business")
    call_to_action = {
        "Drive sales": "Send us a message to learn more or place an order.",
        "Get enquiries": "Send us a message and let us know how we can help.",
        "Build awareness": "Follow along for more practical updates.",
        "Grow engagement": "What is your experience? Tell us in the comments.",
    }.get(goal, "Send us a message to learn more.")
    hashtags = "#SmallBusiness #BusinessGrowth #SupportLocal"
    if platform == "LinkedIn":
        return f"{business}: {topic}\n\nWe are focused on delivering real value for our customers. {call_to_action}\n\n{hashtags}"
    if platform == "X / Twitter":
        return f"{business}: {topic}\n\n{call_to_action}\n\n{hashtags}"
    return f"{topic}\n\nAt {business}, we are making it easier to get the support you need. {call_to_action}\n\n{hashtags}"


def generate_social_post_assist(
    topic: str,
    platform: str = "Instagram",
    tone: str = "Friendly",
    goal: str = "Build awareness",
    business_name: str = "",
) -> dict[str, Any]:
    """Create a platform-aware social post with a clear, user-specified goal."""
    clean_topic = _clean_text(topic, "your update")
    clean_business = _clean_text(business_name, "our business")
    prompt = f"""You are a thoughtful social-media copywriter for a small business.
Return valid JSON only with exactly one string field: post.
Write one ready-to-edit post for {platform}. Tone: {tone}. Goal: {goal}.
Mention the business naturally when useful: {clean_business}.
Topic: {clean_topic}
Use a strong opening, specific customer value, one clear call to action, and 3-5 relevant hashtags.
Keep it under 130 words for X / Twitter or 180 words for other platforms. Do not make up prices,
results, dates, or limited offers. Do not use markdown headings.
"""
    generated = _generate_with_ollama(prompt, {"post"})
    if generated:
        return {"platform": platform, "post": generated["post"], "used_ai": True}
    return {
        "platform": platform,
        "post": _social_fallback(clean_topic, platform, tone, goal, clean_business),
        "used_ai": False,
    }


def _business_idea_fallback(interest: str, audience: str, budget: str) -> str:
    customer = _clean_text(audience, "a focused local or online customer group")
    starting_budget = _clean_text(budget, "a small test budget")
    title = f"{_title_case_phrase(interest)} Starter Service"
    return (
        f"{title}\n\n"
        f"Customer: {customer}\n"
        f"Problem to solve: Customers need a simpler, more reliable way to access {interest}.\n"
        f"Offer: Start with a focused {interest} service or product bundle that solves one urgent customer problem well.\n\n"
        "How it earns: Charge per sale or service, then add a repeat package or monthly plan for regular customers.\n"
        f"Lean starting point: Use {starting_budget} to test demand with a simple landing page, social posts, and direct customer conversations.\n\n"
        "First three steps:\n"
        "1. Speak to 10 potential customers and record their biggest frustration.\n"
        "2. Create one clear offer that solves that frustration and set a test price.\n"
        "3. Sell a small pilot, collect feedback, and improve before spending more.\n\n"
        "Why it can stand out: Be specific about the customer, make the buying process easy, and provide dependable follow-up."
    )


def generate_business_idea_assist(
    interest: str, audience: str = "", starting_budget: str = ""
) -> dict[str, Any]:
    """Develop a practical business idea with concrete first steps and constraints."""
    clean_interest = _clean_text(interest, "local business services")
    clean_audience = _clean_text(audience, "a focused local or online customer group")
    clean_budget = _clean_text(starting_budget, "a small test budget")
    prompt = f"""You are a practical small-business adviser. Return valid JSON only with exactly
these string fields: category, idea. Create one realistic business concept, not a list.
Interest or industry: {clean_interest}
Target customer: {clean_audience}
Available starting budget: {clean_budget}
In the idea, include a memorable name, customer problem, specific offer, revenue model,
lean validation plan with three steps, and one differentiator. Keep it below 300 words.
Do not invent market statistics, guaranteed income, legal claims, or required licences.
"""
    generated = _generate_with_ollama(prompt, {"category", "idea"})
    if generated:
        generated["used_ai"] = True
        return generated
    return {
        "category": _classify_business(clean_interest),
        "idea": _business_idea_fallback(clean_interest, clean_audience, clean_budget),
        "used_ai": False,
    }


# The invoice and proposal helpers retain the existing offline rules because
# those documents require deterministic prices and scope information.
def generate_proposal_assist(idea: str):
    from .offline_ai import generate_offline_proposal

    return generate_offline_proposal(idea)


def generate_invoice_assist(idea: str):
    from .offline_ai import generate_offline_invoice

    return generate_offline_invoice(idea)
