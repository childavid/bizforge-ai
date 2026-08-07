def format_currency(amount, currency="NGN"):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"₦{amount:,.2f}"


def get_currency_code(currency="NGN"):
    """Return one of the currencies BizForge currently supports."""
    return currency if currency in {"NGN", "USD"} else "NGN"
