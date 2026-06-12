def format_currency(amount, currency="NGN"):
    try:
        amount = float(amount)
    except:
        amount = 0.0

    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"₦{amount:,.0f}"