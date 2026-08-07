"""Legacy-compatible helpers that now return real PDF bytes."""

from utils.currency import format_currency
from utils.export_utils import build_pdf


def generate_invoice_pdf(client, service, description, quantity, rate, subtotal, tax_amount, total, currency):
    content = (
        "INVOICE\n\n"
        f"Client: {client}\nService: {service}\nDescription: {description}\n\n"
        f"Quantity: {float(quantity):g}\nRate: {format_currency(rate, currency)}\n\n"
        f"Subtotal: {format_currency(subtotal, currency)}\n"
        f"Tax: {format_currency(tax_amount, currency)}\n"
        f"Total: {format_currency(total, currency)}"
    )
    return build_pdf(content, "Invoice")


def generate_proposal_pdf(client, project, scope, timeline, budget, tone, currency):
    content = (
        "PROPOSAL\n\n"
        f"Client: {client}\nProject: {project}\n\nScope:\n{scope}\n\n"
        f"Timeline: {timeline}\nTone: {tone}\nBudget: {format_currency(budget, currency)}"
    )
    return build_pdf(content, "Proposal")
