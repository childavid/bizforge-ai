def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


# ================= INVOICE =================
def generate_invoice(client, service, description, quantity, rate, currency):

    quantity = safe_float(quantity)
    rate = safe_float(rate)

    subtotal = quantity * rate
    tax_percent = 0  # or pass from UI later
    tax_amount = subtotal * (safe_float(tax_percent) / 100)
    total = subtotal + tax_amount

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