from utils.currency import format_currency

# ---------------- SAFE CONVERTER ----------------
def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


# ================= INVOICE PDF =================
def generate_invoice_pdf(
    client,
    service,
    description,
    quantity,
    rate,
    subtotal,
    tax_amount,
    total,
    currency
):
    quantity = safe_float(quantity)
    rate = safe_float(rate)
    subtotal = safe_float(subtotal)
    tax_amount = safe_float(tax_amount)
    total = safe_float(total)

    content = f"""
================ INVOICE ================

Client: {client}
Service: {service}
Description: {description}

----------------------------------------
Quantity: {quantity}
Rate: {format_currency(rate, currency)}

----------------------------------------
Subtotal: {format_currency(subtotal, currency)}
Tax: {format_currency(tax_amount, currency)}
Total: {format_currency(total, currency)}

========================================
"""

    return content.encode("utf-8")


# ================= PROPOSAL PDF =================
def generate_proposal_pdf(
    client,
    project,
    scope,
    timeline,
    budget,
    tone,
    currency
):
    budget = safe_float(budget)

    content = f"""
============= PROPOSAL =============

Client: {client}
Project: {project}

------------------------------------
Scope:
{scope}

Timeline: {timeline}
Tone: {tone}

------------------------------------
Budget: {format_currency(budget, currency)}

====================================
"""

    return content.encode("utf-8")