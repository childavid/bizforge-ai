PROPOSAL_RULES = [
    {
        "keywords": ["website", "web", "landing page", "online store", "ecommerce"],
        "scope": (
            "Design and build a professional website with clear page structure, "
            "responsive layouts, service/product sections, contact details, and "
            "basic launch support."
        ),
        "timeline": "2-4 weeks",
        "tone": "Professional",
        "budget": 1500.0,
        "proposal_text": (
            "This proposal covers planning, design, development, review, and launch "
            "support for a polished web presence that helps the business present "
            "its offer clearly and convert visitors into enquiries."
        ),
    },
    {
        "keywords": ["logo", "brand", "branding", "identity"],
        "scope": (
            "Create a brand identity package including logo concepts, color direction, "
            "typography suggestions, final logo files, and simple usage guidance."
        ),
        "timeline": "1-2 weeks",
        "tone": "Professional",
        "budget": 650.0,
        "proposal_text": (
            "This proposal focuses on building a clear and memorable visual identity "
            "that can be used consistently across digital and printed materials."
        ),
    },
    {
        "keywords": ["social media", "instagram", "facebook", "content", "posts"],
        "scope": (
            "Plan and create social media content, including post ideas, captions, "
            "basic creative direction, scheduling recommendations, and performance review."
        ),
        "timeline": "2-3 weeks",
        "tone": "Friendly",
        "budget": 900.0,
        "proposal_text": (
            "This proposal supports a more consistent social media presence with "
            "clear messaging, useful content, and a practical publishing plan."
        ),
    },
    {
        "keywords": ["app", "mobile app", "software", "dashboard", "portal"],
        "scope": (
            "Define, design, and develop an application workflow with key screens, "
            "core features, user-friendly navigation, testing, and handover guidance."
        ),
        "timeline": "4-8 weeks",
        "tone": "Formal",
        "budget": 4500.0,
        "proposal_text": (
            "This proposal covers a structured application build that turns the idea "
            "into a usable product with clear features, dependable workflows, and "
            "room for future improvements."
        ),
    },
]

INVOICE_RULES = [
    {
        "keywords": ["website", "web", "landing page", "online store", "ecommerce"],
        "description": "Website design and development services",
        "pricing": "Includes planning, page design, responsive development, revisions, and launch support.",
        "invoice_text": "Payment requested for completed website design and development work.",
        "quantity": 1.0,
        "rate": 1500.0,
    },
    {
        "keywords": ["logo", "brand", "branding", "identity"],
        "description": "Logo and brand identity design services",
        "pricing": "Includes concept development, revisions, final logo files, and basic brand guidance.",
        "invoice_text": "Payment requested for completed brand identity and logo design services.",
        "quantity": 1.0,
        "rate": 650.0,
    },
    {
        "keywords": ["social media", "instagram", "facebook", "content", "posts"],
        "description": "Social media content planning and creation",
        "pricing": "Includes content planning, caption writing, creative direction, and scheduling recommendations.",
        "invoice_text": "Payment requested for completed social media content support.",
        "quantity": 1.0,
        "rate": 900.0,
    },
    {
        "keywords": ["app", "mobile app", "software", "dashboard", "portal"],
        "description": "Application design and development services",
        "pricing": "Includes workflow planning, interface design, core feature development, testing, and handover.",
        "invoice_text": "Payment requested for completed application design and development work.",
        "quantity": 1.0,
        "rate": 4500.0,
    },
]

GENERIC_PROPOSAL = {
    "scope": (
        "Review the business goals, define the project requirements, prepare the "
        "main deliverables, complete the work in agreed stages, and provide final "
        "handover support."
    ),
    "timeline": "2-4 weeks",
    "tone": "Professional",
    "budget": 1200.0,
    "proposal_text": (
        "This proposal outlines a practical business service package designed to "
        "deliver clear outcomes, professional presentation, and reliable execution."
    ),
}

GENERIC_INVOICE = {
    "description": "Professional business services",
    "pricing": "Includes planning, delivery, review, and final handover.",
    "invoice_text": "Payment requested for completed professional business services.",
    "quantity": 1.0,
    "rate": 1200.0,
}


def _find_rule(text, rules, fallback):
    normalized = text.lower()
    for rule in rules:
        if any(keyword in normalized for keyword in rule["keywords"]):
            return rule
    return fallback


def generate_offline_proposal(idea):
    rule = _find_rule(idea, PROPOSAL_RULES, GENERIC_PROPOSAL)
    return {
        "scope": rule["scope"],
        "timeline": rule["timeline"],
        "tone": rule["tone"],
        "budget": rule["budget"],
        "proposal_text": rule["proposal_text"],
    }


def generate_offline_invoice(idea):
    rule = _find_rule(idea, INVOICE_RULES, GENERIC_INVOICE)
    description = (
        f"{rule['description']}\n\n"
        f"Pricing breakdown:\n{rule['pricing']}\n\n"
        f"Invoice text:\n{rule['invoice_text']}"
    )
    return {
        "description": description,
        "pricing": rule["pricing"],
        "invoice_text": rule["invoice_text"],
        "quantity": rule["quantity"],
        "rate": rule["rate"],
    }


# ================= EMAIL GENERATOR =================
EMAIL_TEMPLATES = [
    {
        "keywords": ["follow up", "follow-up", "checking in", "check in"],
        "subject": "Following Up on Our Conversation",
        "body": (
            "Dear [Name],\n\n"
            "I hope this email finds you well. I wanted to follow up on our recent conversation regarding [Topic].\n\n"
            "I wanted to check if you had a chance to review the information I shared and if you have any questions or need further clarification.\n\n"
            "Please let me know a convenient time to discuss this further. I'm available [Availability].\n\n"
            "Looking forward to hearing from you.\n\n"
            "Best regards,\n[Your Name]"
        ),
    },
    {
        "keywords": ["proposal", "quote", "estimate", "bid"],
        "subject": "Business Proposal for [Project]",
        "body": (
            "Dear [Name],\n\n"
            "Thank you for the opportunity to submit a proposal for [Project].\n\n"
            "Based on our discussion, I've outlined the scope, timeline, and investment details below:\n\n"
            "[Scope Details]\n\n"
            "Timeline: [Timeline]\n"
            "Investment: [Amount]\n\n"
            "I'm confident this approach will deliver the results you're looking for. Please review and let me know if you have any questions.\n\n"
            "I'm available for a call to discuss this further at your convenience.\n\n"
            "Best regards,\n[Your Name]"
        ),
    },
    {
        "keywords": ["meeting", "schedule", "appointment", "call"],
        "subject": "Meeting Request: [Purpose]",
        "body": (
            "Dear [Name],\n\n"
            "I hope you're doing well. I'd like to request a meeting to discuss [Topic].\n\n"
            "I believe a [Duration] meeting would be sufficient to cover the key points. I'm available on the following days/times:\n\n"
            "[Availability Options]\n\n"
            "Please let me know what works best for you, or feel free to suggest an alternative time.\n\n"
            "Looking forward to our discussion.\n\n"
            "Best regards,\n[Your Name]"
        ),
    },
    {
        "keywords": ["thank you", "appreciate", "gratitude"],
        "subject": "Thank You for [Reason]",
        "body": (
            "Dear [Name],\n\n"
            "I wanted to express my sincere gratitude for [Reason].\n\n"
            "[Specific Details]\n\n"
            "I truly appreciate your [Support/Help/Partnership] and look forward to our continued collaboration.\n\n"
            "Please don't hesitate to reach out if there's anything I can do to return the favor.\n\n"
            "Best regards,\n[Your Name]"
        ),
    },
]

GENERIC_EMAIL = {
    "subject": "Business Communication",
    "body": (
        "Dear [Name],\n\n"
        "I hope this email finds you well. I'm reaching out regarding [Topic].\n\n"
        "[Main Content]\n\n"
        "Please let me know if you have any questions or need further information.\n\n"
        "Best regards,\n[Your Name]"
    ),
}


def generate_offline_email(purpose):
    rule = _find_rule(purpose, EMAIL_TEMPLATES, GENERIC_EMAIL)
    return {
        "subject": rule["subject"],
        "body": rule["body"],
    }


# ================= SOCIAL MEDIA POST GENERATOR =================
SOCIAL_MEDIA_TEMPLATES = [
    {
        "keywords": ["product", "launch", "new", "release"],
        "platform": "General",
        "post": (
            "🚀 EXCITING NEWS! 🚀\n\n"
            "We're thrilled to announce the launch of [Product/Service]!\n\n"
            "✨ [Key Feature 1]\n"
            "✨ [Key Feature 2]\n"
            "✨ [Key Feature 3]\n\n"
            "This has been a labor of love, and we can't wait for you to experience it.\n\n"
            "👉 [Call to Action/Link]\n\n"
            "Let us know what you think in the comments!\n\n"
            "#Launch #NewProduct #[Industry]"
        ),
    },
    {
        "keywords": ["tip", "advice", "how to", "guide"],
        "platform": "Educational",
        "post": (
            "💡 PRO TIP OF THE DAY 💡\n\n"
            "Here's something that has transformed how we approach [Topic]:\n\n"
            "[Tip/Advice]\n\n"
            "Why this works:\n"
            "• [Reason 1]\n"
            "• [Reason 2]\n"
            "• [Reason 3]\n\n"
            "Save this for later and share with someone who needs it!\n\n"
            "#Tips #[Industry] #BusinessGrowth"
        ),
    },
    {
        "keywords": ["behind the scenes", "team", "culture", "office"],
        "platform": "Behind the Scenes",
        "post": (
            "👥 BEHIND THE SCENES 👥\n\n"
            "Ever wondered what goes on at [Company Name]?\n\n"
            "Today we're giving you a sneak peek into our [Office/Team/Process]!\n\n"
            "[Description of what's happening]\n\n"
            "Our team is passionate about [Mission/Value], and it shows in everything we do.\n\n"
            "Drop a comment if you'd like to see more behind-the-scenes content!\n\n"
            "#BehindTheScenes #TeamCulture #[CompanyName]"
        ),
    },
    {
        "keywords": ["promotion", "sale", "discount", "offer"],
        "platform": "Promotional",
        "post": (
            "🔥 LIMITED TIME OFFER 🔥\n\n"
            "For a limited time, get [Discount]% off [Product/Service]!\n\n"
            "✅ [Benefit 1]\n"
            "✅ [Benefit 2]\n"
            "✅ [Benefit 3]\n\n"
            "Use code: [PROMO_CODE]\n\n"
            "Offer ends: [Date]\n\n"
            "Don't miss out! Link in bio 👆\n\n"
            "#Sale #Discount #SpecialOffer #[Industry]"
        ),
    },
]

GENERIC_SOCIAL_POST = {
    "platform": "General",
    "post": (
        "📢 UPDATE 📢\n\n"
        "We have some exciting news to share!\n\n"
        "[Your Announcement]\n\n"
        "Stay tuned for more updates!\n\n"
        "#Business #Update #[Industry]"
    ),
}


def generate_offline_social_post(topic):
    rule = _find_rule(topic, SOCIAL_MEDIA_TEMPLATES, GENERIC_SOCIAL_POST)
    return {
        "platform": rule["platform"],
        "post": rule["post"],
    }


# ================= BUSINESS IDEA GENERATOR =================
BUSINESS_IDEA_TEMPLATES = [
    {
        "keywords": ["tech", "software", "app", "digital"],
        "category": "Technology",
        "idea": (
            "AI-Powered [Industry] Solution\n\n"
            "Develop an artificial intelligence platform that helps [Target Audience] "
            "solve [Specific Problem] through automated [Feature 1], [Feature 2], and [Feature 3].\n\n"
            "Revenue Model: Subscription-based SaaS with tiered pricing\n\n"
            "Market Potential: High demand for automation in [Industry]\n\n"
            "Key Differentiators:\n"
            "• Advanced AI algorithms\n"
            "• User-friendly interface\n"
            "• Integration with existing tools"
        ),
    },
    {
        "keywords": ["service", "consulting", "agency", "freelance"],
        "category": "Service Business",
        "idea": (
            "Specialized [Niche] Consulting Agency\n\n"
            "Offer premium consulting services to [Target Market] focusing on "
            "[Specific Service Area]. Provide strategic guidance, implementation support, "
            "and ongoing optimization.\n\n"
            "Revenue Model: Project-based fees + retainer options\n\n"
            "Market Potential: Growing demand for specialized expertise\n\n"
            "Key Differentiators:\n"
            "• Industry-specific knowledge\n"
            "• Proven track record\n"
            "• Customized solutions"
        ),
    },
    {
        "keywords": ["ecommerce", "store", "retail", "product"],
        "category": "E-Commerce",
        "idea": (
            "Niche [Product Category] Online Store\n\n"
            "Build a specialized e-commerce platform selling [Product Type] to "
            "[Target Audience]. Focus on quality, curation, and exceptional customer experience.\n\n"
            "Revenue Model: Product sales + subscription box option\n\n"
            "Market Potential: Growing niche market with passionate community\n\n"
            "Key Differentiators:\n"
            "• Curated product selection\n"
            "• Educational content\n"
            "• Community building"
        ),
    },
    {
        "keywords": ["education", "course", "training", "coaching"],
        "category": "Education & Training",
        "idea": (
            "Online [Subject] Academy\n\n"
            "Create comprehensive online courses and training programs for [Target Audience] "
            "looking to master [Skill/Topic]. Include video lessons, workbooks, and live coaching.\n\n"
            "Revenue Model: Course sales + membership community\n\n"
            "Market Potential: High demand for online learning\n\n"
            "Key Differentiators:\n"
            "• Expert instructors\n"
            "• Practical curriculum\n"
            "• Ongoing support"
        ),
    },
]

GENERIC_BUSINESS_IDEA = {
    "category": "General Business",
    "idea": (
        "Innovative [Industry] Solution\n\n"
        "Develop a unique business that addresses [Problem] for [Target Audience].\n\n"
        "Core Offering: [Main Product/Service]\n\n"
        "Revenue Model: [Pricing Strategy]\n\n"
        "Market Potential: [Market Analysis]\n\n"
        "Key Differentiators:\n"
        "• [Unique Selling Point 1]\n"
        "• [Unique Selling Point 2]\n"
        "• [Unique Selling Point 3]"
    ),
}


def generate_offline_business_interest(interest):
    rule = _find_rule(interest, BUSINESS_IDEA_TEMPLATES, GENERIC_BUSINESS_IDEA)
    return {
        "category": rule["category"],
        "idea": rule["idea"],
    }
