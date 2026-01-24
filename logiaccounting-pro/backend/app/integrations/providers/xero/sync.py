"""
Xero Sync Utilities
Field mappings and sync helpers
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class XeroFieldMapper:
    """Maps fields between LogiAccounting and Xero."""

    # Customer to Contact mapping
    CUSTOMER_TO_CONTACT = {
        "name": "Name",
        "email": "EmailAddress",
        "first_name": "FirstName",
        "last_name": "LastName",
        "phone": "Phones[0].PhoneNumber",
        "company_name": "CompanyName",
        "tax_number": "TaxNumber",
    }

    CONTACT_TO_CUSTOMER = {v: k for k, v in CUSTOMER_TO_CONTACT.items()}

    # Invoice mapping
    INVOICE_TO_XERO = {
        "number": "InvoiceNumber",
        "customer_id": "Contact.ContactID",
        "due_date": "DueDate",
        "issue_date": "Date",
        "currency": "CurrencyCode",
        "reference": "Reference",
        "notes": "LineAmountTypes",
    }

    # Invoice status mapping
    INVOICE_STATUS_MAP = {
        "draft": "DRAFT",
        "sent": "AUTHORISED",
        "paid": "PAID",
        "voided": "VOIDED",
    }

    XERO_STATUS_MAP = {v: k for k, v in INVOICE_STATUS_MAP.items()}

    @classmethod
    def customer_to_xero(cls, customer: Dict) -> Dict:
        """Convert LogiAccounting customer to Xero contact."""
        contact = {}

        for local_field, xero_field in cls.CUSTOMER_TO_CONTACT.items():
            value = customer.get(local_field)
            if value:
                if "." in xero_field:
                    # Handle nested fields like Phones[0].PhoneNumber
                    parts = xero_field.split(".")
                    # Simplified - in production handle arrays properly
                    contact[parts[0].split("[")[0]] = [{"PhoneType": "DEFAULT", "PhoneNumber": value}]
                else:
                    contact[xero_field] = value

        # Handle address
        if customer.get("address"):
            addr = customer["address"]
            contact["Addresses"] = [{
                "AddressType": "POBOX",
                "AddressLine1": addr.get("line1", ""),
                "AddressLine2": addr.get("line2", ""),
                "City": addr.get("city", ""),
                "Region": addr.get("state", ""),
                "PostalCode": addr.get("postal_code", ""),
                "Country": addr.get("country", ""),
            }]

        return contact

    @classmethod
    def xero_to_customer(cls, contact: Dict) -> Dict:
        """Convert Xero contact to LogiAccounting customer."""
        customer = {
            "external_id": contact.get("ContactID"),
            "external_provider": "xero",
        }

        # Direct mappings
        customer["name"] = contact.get("Name")
        customer["email"] = contact.get("EmailAddress")
        customer["first_name"] = contact.get("FirstName")
        customer["last_name"] = contact.get("LastName")
        customer["company_name"] = contact.get("CompanyName")
        customer["tax_number"] = contact.get("TaxNumber")

        # Phone
        phones = contact.get("Phones", [])
        if phones:
            customer["phone"] = phones[0].get("PhoneNumber")

        # Address
        addresses = contact.get("Addresses", [])
        if addresses:
            addr = addresses[0]
            customer["address"] = {
                "line1": addr.get("AddressLine1"),
                "line2": addr.get("AddressLine2"),
                "city": addr.get("City"),
                "state": addr.get("Region"),
                "postal_code": addr.get("PostalCode"),
                "country": addr.get("Country"),
            }

        return customer

    @classmethod
    def invoice_to_xero(cls, invoice: Dict, contact_id: str) -> Dict:
        """Convert LogiAccounting invoice to Xero invoice."""
        xero_invoice = {
            "Type": "ACCREC",
            "Contact": {"ContactID": contact_id},
            "Status": cls.INVOICE_STATUS_MAP.get(invoice.get("status"), "DRAFT"),
            "LineAmountTypes": "Exclusive",  # Tax exclusive
        }

        if invoice.get("number"):
            xero_invoice["InvoiceNumber"] = invoice["number"]
        if invoice.get("due_date"):
            xero_invoice["DueDate"] = invoice["due_date"]
        if invoice.get("issue_date"):
            xero_invoice["Date"] = invoice["issue_date"]
        if invoice.get("currency"):
            xero_invoice["CurrencyCode"] = invoice["currency"].upper()
        if invoice.get("reference"):
            xero_invoice["Reference"] = invoice["reference"]

        # Line items
        xero_invoice["LineItems"] = []
        for item in invoice.get("items", []):
            xero_invoice["LineItems"].append({
                "Description": item.get("description"),
                "Quantity": item.get("quantity", 1),
                "UnitAmount": item.get("unit_price"),
                "AccountCode": item.get("account_code", "200"),
                "TaxType": item.get("tax_type", "OUTPUT"),
            })

        return xero_invoice

    @classmethod
    def xero_to_invoice(cls, xero_invoice: Dict) -> Dict:
        """Convert Xero invoice to LogiAccounting invoice."""
        invoice = {
            "external_id": xero_invoice.get("InvoiceID"),
            "external_provider": "xero",
            "number": xero_invoice.get("InvoiceNumber"),
            "status": cls.XERO_STATUS_MAP.get(xero_invoice.get("Status"), "draft"),
            "total": xero_invoice.get("Total"),
            "subtotal": xero_invoice.get("SubTotal"),
            "tax": xero_invoice.get("TotalTax"),
            "amount_due": xero_invoice.get("AmountDue"),
            "amount_paid": xero_invoice.get("AmountPaid"),
            "currency": xero_invoice.get("CurrencyCode"),
            "due_date": xero_invoice.get("DueDate"),
            "issue_date": xero_invoice.get("Date"),
        }

        # Contact reference
        contact = xero_invoice.get("Contact", {})
        invoice["external_customer_id"] = contact.get("ContactID")

        # Line items
        invoice["items"] = []
        for item in xero_invoice.get("LineItems", []):
            invoice["items"].append({
                "description": item.get("Description"),
                "quantity": item.get("Quantity"),
                "unit_price": item.get("UnitAmount"),
                "total": item.get("LineAmount"),
                "account_code": item.get("AccountCode"),
            })

        return invoice
