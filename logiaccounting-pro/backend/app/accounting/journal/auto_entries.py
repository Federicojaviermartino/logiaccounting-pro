"""
Automatic Journal Entry Generator
Creates journal entries from business transactions
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.accounting.journal.models import JournalEntry, JournalLine, EntryTypeEnum, EntryStatusEnum
from app.accounting.chart_of_accounts.models import Account, AccountTypeEnum
from app.accounting.journal.service import JournalEntryService

logger = logging.getLogger(__name__)


class AutoEntryGenerator:
    """Generates journal entries from business transactions."""

    def __init__(self, db: Session):
        self.db = db
        self.journal_service = JournalEntryService(db)

    def _get_default_account(self, customer_id: UUID, account_code: str) -> Optional[Account]:
        """Get account by code."""
        return self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.code == account_code,
            Account.is_active == True
        ).first()

    def _get_ar_account(self, customer_id: UUID) -> Account:
        """Get accounts receivable account."""
        account = self._get_default_account(customer_id, "1210")
        if not account:
            account = self._get_default_account(customer_id, "1200")
        if not account:
            raise ValueError("Accounts Receivable account not found")
        return account

    def _get_ap_account(self, customer_id: UUID) -> Account:
        """Get accounts payable account."""
        account = self._get_default_account(customer_id, "2111")
        if not account:
            account = self._get_default_account(customer_id, "2100")
        if not account:
            raise ValueError("Accounts Payable account not found")
        return account

    def _get_cash_account(self, customer_id: UUID) -> Account:
        """Get main cash account."""
        account = self._get_default_account(customer_id, "1111")
        if not account:
            account = self._get_default_account(customer_id, "1100")
        if not account:
            raise ValueError("Cash account not found")
        return account

    def _get_sales_account(self, customer_id: UUID) -> Account:
        """Get sales revenue account."""
        account = self._get_default_account(customer_id, "4110")
        if not account:
            account = self._get_default_account(customer_id, "4100")
        if not account:
            raise ValueError("Sales Revenue account not found")
        return account

    def generate_invoice_entry(
        self,
        customer_id: UUID,
        invoice_id: UUID,
        invoice_number: str,
        invoice_date: date,
        client_name: str,
        subtotal: Decimal,
        tax_amount: Decimal,
        total_amount: Decimal,
        line_items: List[Dict[str, Any]] = None,
        created_by: UUID = None,
        auto_post: bool = False,
    ) -> JournalEntry:
        """
        Generate journal entry for a sales invoice.
        DR  Accounts Receivable     [Total]
            CR  Sales Revenue           [Subtotal]
            CR  Sales Tax Payable       [Tax]
        """
        ar_account = self._get_ar_account(customer_id)
        sales_account = self._get_sales_account(customer_id)
        tax_account = self._get_default_account(customer_id, "2210")

        lines = []

        # Debit: Accounts Receivable
        lines.append({
            "account_id": ar_account.id,
            "debit_amount": total_amount,
            "credit_amount": Decimal("0"),
            "description": f"Invoice {invoice_number} - {client_name}",
        })

        # Credit: Sales Revenue
        lines.append({
            "account_id": sales_account.id,
            "debit_amount": Decimal("0"),
            "credit_amount": subtotal,
            "description": f"Sales - Invoice {invoice_number}",
        })

        # Credit: Sales Tax Payable
        if tax_amount > 0 and tax_account:
            lines.append({
                "account_id": tax_account.id,
                "debit_amount": Decimal("0"),
                "credit_amount": tax_amount,
                "description": f"Sales Tax - Invoice {invoice_number}",
            })

        from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

        entry_data = JournalEntryCreate(
            entry_date=invoice_date,
            entry_type=EntryTypeEnum.INVOICE,
            description=f"Sales Invoice {invoice_number} - {client_name}",
            reference=invoice_number,
            source_type="invoice",
            source_id=invoice_id,
            lines=[JournalLineCreate(**line) for line in lines],
        )

        entry = self.journal_service.create_entry(
            customer_id=customer_id,
            data=entry_data,
            created_by=created_by,
        )

        if auto_post and created_by:
            self.journal_service.submit_for_approval(entry.id, created_by)
            self.journal_service.approve_entry(entry.id, created_by)
            self.journal_service.post_entry(entry.id, created_by)

        logger.info(f"Generated invoice entry: {entry.entry_number}")
        return entry

    def generate_bill_entry(
        self,
        customer_id: UUID,
        bill_id: UUID,
        bill_number: str,
        bill_date: date,
        supplier_name: str,
        subtotal: Decimal,
        tax_amount: Decimal,
        total_amount: Decimal,
        expense_account_id: UUID,
        created_by: UUID = None,
        auto_post: bool = False,
    ) -> JournalEntry:
        """
        Generate journal entry for a supplier bill.
        DR  Expense/Inventory       [Subtotal + Tax]
            CR  Accounts Payable        [Total]
        """
        ap_account = self._get_ap_account(customer_id)

        lines = [
            {
                "account_id": expense_account_id,
                "debit_amount": total_amount,
                "credit_amount": Decimal("0"),
                "description": f"Bill {bill_number} - {supplier_name}",
            },
            {
                "account_id": ap_account.id,
                "debit_amount": Decimal("0"),
                "credit_amount": total_amount,
                "description": f"Bill {bill_number} - {supplier_name}",
            },
        ]

        from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

        entry_data = JournalEntryCreate(
            entry_date=bill_date,
            entry_type=EntryTypeEnum.BILL,
            description=f"Supplier Bill {bill_number} - {supplier_name}",
            reference=bill_number,
            source_type="bill",
            source_id=bill_id,
            lines=[JournalLineCreate(**line) for line in lines],
        )

        entry = self.journal_service.create_entry(
            customer_id=customer_id,
            data=entry_data,
            created_by=created_by,
        )

        if auto_post and created_by:
            self.journal_service.submit_for_approval(entry.id, created_by)
            self.journal_service.approve_entry(entry.id, created_by)
            self.journal_service.post_entry(entry.id, created_by)

        return entry

    def generate_payment_received_entry(
        self,
        customer_id: UUID,
        payment_id: UUID,
        payment_number: str,
        payment_date: date,
        client_name: str,
        amount: Decimal,
        invoice_number: str = None,
        bank_account_id: UUID = None,
        created_by: UUID = None,
        auto_post: bool = False,
    ) -> JournalEntry:
        """
        Generate journal entry for payment received.
        DR  Cash/Bank               [Amount]
            CR  Accounts Receivable     [Amount]
        """
        ar_account = self._get_ar_account(customer_id)
        cash_account = self.db.query(Account).get(bank_account_id) if bank_account_id else self._get_cash_account(customer_id)

        lines = [
            {"account_id": cash_account.id, "debit_amount": amount, "credit_amount": Decimal("0"), "description": f"Payment from {client_name}"},
            {"account_id": ar_account.id, "debit_amount": Decimal("0"), "credit_amount": amount, "description": f"Payment - {invoice_number or payment_number}"},
        ]

        from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

        entry_data = JournalEntryCreate(
            entry_date=payment_date,
            entry_type=EntryTypeEnum.PAYMENT,
            description=f"Payment received from {client_name}",
            reference=payment_number,
            source_type="payment_received",
            source_id=payment_id,
            lines=[JournalLineCreate(**line) for line in lines],
        )

        entry = self.journal_service.create_entry(customer_id=customer_id, data=entry_data, created_by=created_by)

        if auto_post and created_by:
            self.journal_service.submit_for_approval(entry.id, created_by)
            self.journal_service.approve_entry(entry.id, created_by)
            self.journal_service.post_entry(entry.id, created_by)

        return entry

    def generate_payment_made_entry(
        self,
        customer_id: UUID,
        payment_id: UUID,
        payment_number: str,
        payment_date: date,
        supplier_name: str,
        amount: Decimal,
        bill_number: str = None,
        bank_account_id: UUID = None,
        created_by: UUID = None,
        auto_post: bool = False,
    ) -> JournalEntry:
        """
        Generate journal entry for payment made.
        DR  Accounts Payable        [Amount]
            CR  Cash/Bank               [Amount]
        """
        ap_account = self._get_ap_account(customer_id)
        cash_account = self.db.query(Account).get(bank_account_id) if bank_account_id else self._get_cash_account(customer_id)

        lines = [
            {"account_id": ap_account.id, "debit_amount": amount, "credit_amount": Decimal("0"), "description": f"Payment to {supplier_name}"},
            {"account_id": cash_account.id, "debit_amount": Decimal("0"), "credit_amount": amount, "description": f"Payment - {bill_number or payment_number}"},
        ]

        from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

        entry_data = JournalEntryCreate(
            entry_date=payment_date,
            entry_type=EntryTypeEnum.PAYMENT,
            description=f"Payment to {supplier_name}",
            reference=payment_number,
            source_type="payment_made",
            source_id=payment_id,
            lines=[JournalLineCreate(**line) for line in lines],
        )

        entry = self.journal_service.create_entry(customer_id=customer_id, data=entry_data, created_by=created_by)

        if auto_post and created_by:
            self.journal_service.submit_for_approval(entry.id, created_by)
            self.journal_service.approve_entry(entry.id, created_by)
            self.journal_service.post_entry(entry.id, created_by)

        return entry


def get_auto_entry_generator(db: Session) -> AutoEntryGenerator:
    return AutoEntryGenerator(db)
