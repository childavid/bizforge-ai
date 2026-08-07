"""Public utility helpers.

Keep optional dashboard/PDF dependencies lazy so the small Flask API can run
independently on a lightweight webhook host.
"""

__all__ = [
    "calculate_invoice_total",
    "format_currency",
    "generate_invoice_assist",
    "generate_invoice",
    "generate_invoice_pdf",
    "generate_proposal_assist",
    "generate_proposal",
    "generate_proposal_pdf",
    "get_currency_code",
]


_EXPORTS = {
    "calculate_invoice_total": (".generators", "calculate_invoice_total"),
    "format_currency": (".currency", "format_currency"),
    "generate_invoice_assist": (".ai_assist", "generate_invoice_assist"),
    "generate_invoice": (".generators", "generate_invoice"),
    "generate_invoice_pdf": (".pdf_generator", "generate_invoice_pdf"),
    "generate_proposal_assist": (".ai_assist", "generate_proposal_assist"),
    "generate_proposal": (".generators", "generate_proposal"),
    "generate_proposal_pdf": (".pdf_generator", "generate_proposal_pdf"),
    "get_currency_code": (".currency", "get_currency_code"),
}


def __getattr__(name):
    """Import a helper only when a caller asks for it."""
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    from importlib import import_module

    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
