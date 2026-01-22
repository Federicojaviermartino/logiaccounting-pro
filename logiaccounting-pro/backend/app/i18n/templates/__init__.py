"""
Localized document templates module.
"""
from app.i18n.templates.invoice import InvoiceTemplate, generate_invoice_html
from app.i18n.templates.base import LocalizedTemplate, TemplateEngine

__all__ = [
    "InvoiceTemplate",
    "generate_invoice_html",
    "LocalizedTemplate",
    "TemplateEngine",
]
