def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def calculate_invoice_total(quantity, rate, tax_percent=0):
    """Return subtotal, tax, and total for callers that need invoice math."""
    subtotal = safe_float(quantity) * safe_float(rate)
    tax_amount = subtotal * (safe_float(tax_percent) / 100)
    return subtotal, tax_amount, subtotal + tax_amount


# ================= INVOICE =================
def generate_invoice(client, service, description, quantity, rate, currency):

    quantity = safe_float(quantity)
    rate = safe_float(rate)

    subtotal, tax_amount, total = calculate_invoice_total(quantity, rate)

    return f"Invoice for {client} - {service}"


# ================= PROPOSAL =================
def generate_proposal(client, project, scope, timeline, budget, tone, currency):
    budget = safe_float(budget)
    return f"Proposal for {client} - {project}"


def generate_proposal_assist(idea):
    return {
        "scope": idea,
        "timeline": "2 weeks",
        "budget": 5000,
        "tone": "Professional"
    }
