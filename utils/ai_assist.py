from .offline_ai import (
    generate_offline_invoice,
    generate_offline_proposal,
    generate_offline_email,
    generate_offline_social_post,
    generate_offline_business_interest
)


def generate_proposal_assist(idea):
    return generate_offline_proposal(idea)


def generate_invoice_assist(idea):
    return generate_offline_invoice(idea)


def generate_email_assist(purpose):
    return generate_offline_email(purpose)


def generate_social_post_assist(topic):
    return generate_offline_social_post(topic)


def generate_business_idea_assist(interest):
    return generate_offline_business_interest(interest)
