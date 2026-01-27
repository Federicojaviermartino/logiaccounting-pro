"""
Bank Statement Importer
Parse OFX, CSV, and other formats
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
import csv
import io
import logging

from sqlalchemy.orm import Session

from app.accounting.reconciliation.models import BankStatement, BankTransaction

logger = logging.getLogger(__name__)


class StatementImporter:
    """Import bank statements from various formats."""

    def __init__(self, db: Session):
        self.db = db

    def import_csv(
        self,
        bank_account_id: UUID,
        file_content: str,
        column_mapping: Dict[str, str],
        created_by: UUID = None,
    ) -> BankStatement:
        """Import CSV bank statement."""
        reader = csv.DictReader(io.StringIO(file_content))

        transactions = []
        min_date = None
        max_date = None

        for row in reader:
            # Parse date
            date_str = row.get(column_mapping.get("date", "Date"))
            trans_date = self._parse_date(date_str)

            if not min_date or trans_date < min_date:
                min_date = trans_date
            if not max_date or trans_date > max_date:
                max_date = trans_date

            # Parse amount
            amount_str = row.get(column_mapping.get("amount", "Amount"))
            amount = self._parse_amount(amount_str)

            # Determine transaction type
            trans_type = "credit" if amount >= 0 else "debit"

            transactions.append({
                "transaction_date": trans_date,
                "amount": abs(amount),
                "description": row.get(column_mapping.get("description", "Description"), ""),
                "reference": row.get(column_mapping.get("reference", "Reference"), ""),
                "transaction_type": trans_type,
                "check_number": row.get(column_mapping.get("check_number", "Check Number")),
                "payee": row.get(column_mapping.get("payee", "Payee")),
            })

        # Calculate balances
        opening_balance = Decimal("0")  # Would need to be provided
        total_credits = sum(t["amount"] for t in transactions if t["transaction_type"] == "credit")
        total_debits = sum(t["amount"] for t in transactions if t["transaction_type"] == "debit")
        closing_balance = opening_balance + total_credits - total_debits

        # Create statement
        statement = BankStatement(
            bank_account_id=bank_account_id,
            statement_date=max_date or date.today(),
            start_date=min_date or date.today(),
            end_date=max_date or date.today(),
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            import_source="csv",
            created_by=created_by,
        )

        self.db.add(statement)
        self.db.flush()

        # Create transactions
        for trans_data in transactions:
            transaction = BankTransaction(
                statement_id=statement.id,
                **trans_data
            )
            self.db.add(transaction)

        self.db.commit()
        self.db.refresh(statement)

        logger.info(f"Imported {len(transactions)} transactions from CSV")
        return statement

    def import_ofx(
        self,
        bank_account_id: UUID,
        file_content: bytes,
        created_by: UUID = None,
    ) -> BankStatement:
        """Import OFX/QFX bank statement."""
        try:
            from ofxparse import OfxParser
        except ImportError:
            raise ImportError("ofxparse library required for OFX import")

        ofx = OfxParser.parse(io.BytesIO(file_content))

        if not ofx.accounts:
            raise ValueError("No accounts found in OFX file")

        account = ofx.accounts[0]
        statement = account.statement

        # Create statement
        bank_statement = BankStatement(
            bank_account_id=bank_account_id,
            statement_date=statement.end_date.date() if statement.end_date else date.today(),
            start_date=statement.start_date.date() if statement.start_date else date.today(),
            end_date=statement.end_date.date() if statement.end_date else date.today(),
            opening_balance=Decimal(str(statement.balance)) - self._sum_transactions(statement.transactions),
            closing_balance=Decimal(str(statement.balance)),
            import_source="ofx",
            created_by=created_by,
        )

        self.db.add(bank_statement)
        self.db.flush()

        # Create transactions
        for trans in statement.transactions:
            amount = Decimal(str(trans.amount))
            transaction = BankTransaction(
                statement_id=bank_statement.id,
                transaction_date=trans.date.date(),
                post_date=trans.date.date(),
                amount=abs(amount),
                description=trans.memo or trans.payee,
                reference=trans.id,
                transaction_type="credit" if amount >= 0 else "debit",
                check_number=trans.checknum if hasattr(trans, 'checknum') else None,
                payee=trans.payee,
            )
            self.db.add(transaction)

        self.db.commit()
        self.db.refresh(bank_statement)

        logger.info(f"Imported {len(statement.transactions)} transactions from OFX")
        return bank_statement

    def _parse_date(self, date_str: str) -> date:
        """Parse date from various formats."""
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")

    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount, handling various formats."""
        cleaned = amount_str.replace(",", "").replace("$", "").replace(" ", "").strip()
        return Decimal(cleaned)

    def _sum_transactions(self, transactions) -> Decimal:
        """Sum transaction amounts."""
        return sum(Decimal(str(t.amount)) for t in transactions)


def get_statement_importer(db: Session) -> StatementImporter:
    return StatementImporter(db)
