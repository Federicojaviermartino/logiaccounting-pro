"""
Localized invoice template.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.i18n.templates.base import LocalizedTemplate, TemplateEngine
from app.i18n.core.context import get_locale
from app.i18n.core.locale import LocaleContext
from app.i18n.translation.service import t_sync
from app.i18n.currency.formatter import format_currency
from app.i18n.datetime.formatter import format_date


@dataclass
class InvoiceItem:
    """Invoice line item."""
    description: str
    quantity: float
    unit_price: float
    tax_rate: float = 0.0
    discount: float = 0.0

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price

    @property
    def discount_amount(self) -> float:
        return self.subtotal * (self.discount / 100)

    @property
    def taxable_amount(self) -> float:
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> float:
        return self.taxable_amount * (self.tax_rate / 100)

    @property
    def total(self) -> float:
        return self.taxable_amount + self.tax_amount


@dataclass
class InvoiceAddress:
    """Address for invoice."""
    name: str
    address_line1: str
    address_line2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    tax_id: str = ""

    def format(self, locale: Optional[LocaleContext] = None) -> str:
        """Format address according to locale conventions."""
        lines = [self.name, self.address_line1]
        if self.address_line2:
            lines.append(self.address_line2)

        city_line = ""
        if self.city:
            city_line = self.city
        if self.state:
            city_line = f"{city_line}, {self.state}" if city_line else self.state
        if self.postal_code:
            city_line = f"{city_line} {self.postal_code}" if city_line else self.postal_code

        if city_line:
            lines.append(city_line)
        if self.country:
            lines.append(self.country)

        return "\n".join(lines)


@dataclass
class InvoiceData:
    """Invoice data structure."""
    invoice_number: str
    invoice_date: date
    due_date: date
    seller: InvoiceAddress
    buyer: InvoiceAddress
    items: List[InvoiceItem]
    currency: str = "USD"
    notes: str = ""
    payment_terms: str = ""
    payment_instructions: str = ""
    logo_url: str = ""

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def total_discount(self) -> float:
        return sum(item.discount_amount for item in self.items)

    @property
    def total_tax(self) -> float:
        return sum(item.tax_amount for item in self.items)

    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)


class InvoiceTemplate(LocalizedTemplate):
    """Localized invoice template."""

    @property
    def template_name(self) -> str:
        return "invoice.html"

    def get_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build invoice context."""
        locale = get_locale()
        language = locale.language

        labels = {
            "invoice": t_sync("invoices:template.header", language=language),
            "invoice_number": t_sync("invoices:invoice_number", language=language),
            "invoice_date": t_sync("invoices:invoice_date", language=language),
            "due_date": t_sync("invoices:due_date", language=language),
            "bill_to": t_sync("invoices:template.bill_to", language=language),
            "from": t_sync("invoices:template.from", language=language),
            "description": t_sync("invoices:items.description", language=language),
            "quantity": t_sync("invoices:items.quantity", language=language),
            "unit_price": t_sync("invoices:items.unit_price", language=language),
            "amount": t_sync("invoices:items.amount", language=language),
            "subtotal": t_sync("invoices:totals.subtotal", language=language),
            "tax": t_sync("invoices:totals.tax", language=language),
            "discount": t_sync("invoices:totals.discount", language=language),
            "total": t_sync("invoices:totals.total", language=language),
            "notes": t_sync("invoices:notes.title", language=language),
            "payment_terms": t_sync("invoices:payment.terms", language=language),
            "thank_you": t_sync("invoices:template.thank_you", language=language),
            "vat_number": t_sync("invoices:tax.vat_number", language=language),
        }

        return {
            **data,
            "labels": labels,
            "format_currency": lambda v: format_currency(v, data.get("currency", "USD")),
            "format_date": format_date,
        }


def generate_invoice_html(
    invoice_data: InvoiceData,
    locale: Optional[LocaleContext] = None
) -> str:
    """
    Generate localized invoice HTML.

    Args:
        invoice_data: Invoice data
        locale: Locale context (uses current if not provided)

    Returns:
        HTML string
    """
    if not locale:
        locale = get_locale()

    template = InvoiceTemplate()
    data = {
        "invoice": invoice_data,
        "currency": invoice_data.currency,
    }

    return template.render(data, locale)


INVOICE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ locale.language }}" dir="{{ direction }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ labels.invoice }} {{ invoice.invoice_number }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: #333;
            direction: {{ direction }};
        }
        .invoice-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 40px;
            {% if is_rtl %}
            flex-direction: row-reverse;
            {% endif %}
        }
        .logo img {
            max-height: 60px;
        }
        .invoice-title {
            text-align: {% if is_rtl %}left{% else %}right{% endif %};
        }
        .invoice-title h1 {
            font-size: 32px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .invoice-meta {
            color: #666;
        }
        .addresses {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            {% if is_rtl %}
            flex-direction: row-reverse;
            {% endif %}
        }
        .address-block {
            width: 45%;
        }
        .address-block h3 {
            color: #2c3e50;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 10px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }
        .address-block p {
            white-space: pre-line;
        }
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        .items-table th {
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: {% if is_rtl %}right{% else %}left{% endif %};
            font-weight: 500;
        }
        .items-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .items-table .amount {
            text-align: {% if is_rtl %}left{% else %}right{% endif %};
        }
        .totals {
            width: 300px;
            margin-{% if is_rtl %}right{% else %}left{% endif %}: auto;
        }
        .totals-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .totals-row.total {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            border-top: 2px solid #3498db;
            border-bottom: none;
            margin-top: 10px;
            padding-top: 15px;
        }
        .notes {
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .notes h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #888;
            font-size: 12px;
        }
        @media print {
            body {
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }
            .invoice-container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="invoice-container">
        <div class="header">
            {% if invoice.logo_url %}
            <div class="logo">
                <img src="{{ invoice.logo_url }}" alt="Company Logo">
            </div>
            {% endif %}
            <div class="invoice-title">
                <h1>{{ labels.invoice }}</h1>
                <div class="invoice-meta">
                    <p><strong>{{ labels.invoice_number }}:</strong> {{ invoice.invoice_number }}</p>
                    <p><strong>{{ labels.invoice_date }}:</strong> {{ format_date(invoice.invoice_date) }}</p>
                    <p><strong>{{ labels.due_date }}:</strong> {{ format_date(invoice.due_date) }}</p>
                </div>
            </div>
        </div>

        <div class="addresses">
            <div class="address-block">
                <h3>{{ labels.from }}</h3>
                <p>{{ invoice.seller.format() }}</p>
                {% if invoice.seller.tax_id %}
                <p><strong>{{ labels.vat_number }}:</strong> {{ invoice.seller.tax_id }}</p>
                {% endif %}
            </div>
            <div class="address-block">
                <h3>{{ labels.bill_to }}</h3>
                <p>{{ invoice.buyer.format() }}</p>
                {% if invoice.buyer.tax_id %}
                <p><strong>{{ labels.vat_number }}:</strong> {{ invoice.buyer.tax_id }}</p>
                {% endif %}
            </div>
        </div>

        <table class="items-table">
            <thead>
                <tr>
                    <th>{{ labels.description }}</th>
                    <th class="amount">{{ labels.quantity }}</th>
                    <th class="amount">{{ labels.unit_price }}</th>
                    <th class="amount">{{ labels.amount }}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in invoice.items %}
                <tr>
                    <td>{{ item.description }}</td>
                    <td class="amount">{{ item.quantity }}</td>
                    <td class="amount">{{ format_currency(item.unit_price) }}</td>
                    <td class="amount">{{ format_currency(item.total) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals">
            <div class="totals-row">
                <span>{{ labels.subtotal }}</span>
                <span>{{ format_currency(invoice.subtotal) }}</span>
            </div>
            {% if invoice.total_discount > 0 %}
            <div class="totals-row">
                <span>{{ labels.discount }}</span>
                <span>-{{ format_currency(invoice.total_discount) }}</span>
            </div>
            {% endif %}
            {% if invoice.total_tax > 0 %}
            <div class="totals-row">
                <span>{{ labels.tax }}</span>
                <span>{{ format_currency(invoice.total_tax) }}</span>
            </div>
            {% endif %}
            <div class="totals-row total">
                <span>{{ labels.total }}</span>
                <span>{{ format_currency(invoice.total) }}</span>
            </div>
        </div>

        {% if invoice.notes or invoice.payment_instructions %}
        <div class="notes">
            {% if invoice.notes %}
            <h3>{{ labels.notes }}</h3>
            <p>{{ invoice.notes }}</p>
            {% endif %}
            {% if invoice.payment_instructions %}
            <h3>{{ labels.payment_terms }}</h3>
            <p>{{ invoice.payment_instructions }}</p>
            {% endif %}
        </div>
        {% endif %}

        <div class="footer">
            <p>{{ labels.thank_you }}</p>
        </div>
    </div>
</body>
</html>
"""
