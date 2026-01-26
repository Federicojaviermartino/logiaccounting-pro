"""
Bank Transaction Service
Business logic for bank transaction management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
import csv
import io

from app.banking.transactions.models import (
    BankTransaction, BankStatementImport, TransactionType, MatchStatus, Direction
)
from app.banking.transactions.schemas import (
    BankTransactionCreate, BankTransactionUpdate, BankTransactionFilter,
    BankTransactionResponse
)
from app.banking.accounts.service import BankAccountService


class BankTransactionService:
    """Service for bank transaction operations"""

    def __init__(self, db: Session, customer_id: UUID = None):
        self.db = db
        self.customer_id = customer_id

    def create_transaction(
        self,
        data: BankTransactionCreate,
        created_by: UUID = None
    ) -> BankTransaction:
        """Create a manual bank transaction"""
        # Generate internal reference
        internal_ref = f"TXN-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"

        transaction = BankTransaction(
            customer_id=self.customer_id,
            account_id=data.account_id,
            internal_ref=internal_ref,
            transaction_ref=data.transaction_ref,
            transaction_date=data.transaction_date,
            value_date=data.value_date,
            transaction_type=data.transaction_type.value,
            direction=data.direction.value,
            amount=data.amount,
            currency=data.currency,
            payee_payer_name=data.payee_payer_name,
            payee_payer_account=data.payee_payer_account,
            payee_payer_bank=data.payee_payer_bank,
            description=data.description,
            memo=data.memo,
            check_number=data.check_number,
            category=data.category,
            notes=data.notes
        )

        self.db.add(transaction)

        # Update account balance
        account_service = BankAccountService(self.db, self.customer_id)
        account_service.update_daily_balance(
            account_id=data.account_id,
            transaction_date=data.transaction_date,
            amount=data.amount,
            is_debit=data.direction == Direction.DEBIT
        )

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_transaction_by_id(self, transaction_id: UUID) -> BankTransaction:
        """Get transaction by ID"""
        result = self.db.execute(
            select(BankTransaction).where(BankTransaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        return transaction

    def get_transactions(
        self,
        filters: BankTransactionFilter = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[BankTransaction], int]:
        """Get transactions with filtering"""
        query = select(BankTransaction).where(
            BankTransaction.customer_id == self.customer_id
        )

        if filters:
            if filters.account_id:
                query = query.where(BankTransaction.account_id == filters.account_id)

            if filters.start_date:
                query = query.where(BankTransaction.transaction_date >= filters.start_date)

            if filters.end_date:
                query = query.where(BankTransaction.transaction_date <= filters.end_date)

            if filters.transaction_type:
                query = query.where(
                    BankTransaction.transaction_type == filters.transaction_type.value
                )

            if filters.direction:
                query = query.where(BankTransaction.direction == filters.direction.value)

            if filters.match_status:
                query = query.where(BankTransaction.match_status == filters.match_status.value)

            if filters.is_reconciled is not None:
                query = query.where(BankTransaction.is_reconciled == filters.is_reconciled)

            if filters.category:
                query = query.where(BankTransaction.category == filters.category)

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        BankTransaction.description.ilike(search_term),
                        BankTransaction.payee_payer_name.ilike(search_term),
                        BankTransaction.transaction_ref.ilike(search_term)
                    )
                )

            if filters.min_amount:
                query = query.where(BankTransaction.amount >= filters.min_amount)

            if filters.max_amount:
                query = query.where(BankTransaction.amount <= filters.max_amount)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(
            BankTransaction.transaction_date.desc(),
            BankTransaction.created_at.desc()
        )
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total

    def update_transaction(
        self,
        transaction_id: UUID,
        data: BankTransactionUpdate
    ) -> BankTransaction:
        """Update transaction details"""
        transaction = self.get_transaction_by_id(transaction_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def match_transaction(
        self,
        transaction_id: UUID,
        match_type: str,
        match_id: UUID
    ) -> BankTransaction:
        """Match a transaction to an invoice, bill, or journal entry"""
        transaction = self.get_transaction_by_id(transaction_id)

        if match_type == "invoice":
            transaction.matched_invoice_id = match_id
        elif match_type == "bill":
            transaction.matched_bill_id = match_id
        elif match_type == "journal":
            transaction.matched_journal_id = match_id
        elif match_type == "transfer":
            transaction.matched_transfer_id = match_id
        else:
            raise ValueError(f"Invalid match type: {match_type}")

        transaction.match_status = MatchStatus.MATCHED.value

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def unmatch_transaction(self, transaction_id: UUID) -> BankTransaction:
        """Remove match from a transaction"""
        transaction = self.get_transaction_by_id(transaction_id)

        transaction.matched_invoice_id = None
        transaction.matched_bill_id = None
        transaction.matched_journal_id = None
        transaction.matched_transfer_id = None
        transaction.match_status = MatchStatus.UNMATCHED.value

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def categorize_transactions(
        self,
        transaction_ids: List[UUID],
        category: str
    ) -> int:
        """Categorize multiple transactions"""
        count = 0
        for txn_id in transaction_ids:
            try:
                transaction = self.get_transaction_by_id(txn_id)
                transaction.category = category
                count += 1
            except ValueError:
                continue

        self.db.commit()
        return count

    def import_csv_statement(
        self,
        account_id: UUID,
        file_content: bytes,
        file_name: str,
        imported_by: UUID
    ) -> BankStatementImport:
        """Import transactions from CSV file"""
        import_record = BankStatementImport(
            customer_id=self.customer_id,
            account_id=account_id,
            file_name=file_name,
            file_format="csv",
            file_size=len(file_content),
            status="processing",
            imported_by=imported_by
        )
        self.db.add(import_record)
        self.db.flush()

        try:
            content = file_content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))

            imported = 0
            duplicates = 0
            errors = 0
            transactions = []

            for row_num, row in enumerate(reader, start=1):
                try:
                    # Parse CSV row - adjust field names based on your format
                    txn_date = datetime.strptime(
                        row.get('Date', row.get('date', '')), '%Y-%m-%d'
                    ).date()
                    amount = Decimal(row.get('Amount', row.get('amount', '0')))
                    description = row.get('Description', row.get('description', ''))

                    # Determine direction
                    if amount < 0:
                        direction = Direction.DEBIT.value
                        amount = abs(amount)
                    else:
                        direction = Direction.CREDIT.value

                    # Check for duplicates
                    existing = self.db.execute(
                        select(BankTransaction).where(
                            and_(
                                BankTransaction.account_id == account_id,
                                BankTransaction.transaction_date == txn_date,
                                BankTransaction.amount == amount,
                                BankTransaction.description == description
                            )
                        )
                    ).scalar_one_or_none()

                    if existing:
                        duplicates += 1
                        continue

                    transaction = BankTransaction(
                        customer_id=self.customer_id,
                        account_id=account_id,
                        transaction_date=txn_date,
                        transaction_type=TransactionType.DEPOSIT.value if direction == Direction.CREDIT.value else TransactionType.WITHDRAWAL.value,
                        direction=direction,
                        amount=amount,
                        currency="USD",
                        description=description,
                        payee_payer_name=row.get('Payee', row.get('payee', '')),
                        import_batch_id=import_record.id,
                        import_row_number=row_num,
                        raw_data=dict(row)
                    )
                    transactions.append(transaction)
                    imported += 1

                except Exception as e:
                    errors += 1
                    continue

            # Bulk insert
            self.db.add_all(transactions)

            import_record.status = "completed"
            import_record.transactions_imported = imported
            import_record.transactions_duplicates = duplicates
            import_record.transactions_errors = errors
            import_record.total_transactions = imported + duplicates + errors

            self.db.commit()

        except Exception as e:
            import_record.status = "failed"
            import_record.error_message = str(e)
            self.db.commit()
            raise

        self.db.refresh(import_record)
        return import_record

    def get_unmatched_transactions(
        self,
        account_id: UUID = None,
        days_back: int = 30
    ) -> List[BankTransaction]:
        """Get unmatched transactions for reconciliation"""
        from_date = date.today() - timedelta(days=days_back)

        query = select(BankTransaction).where(
            and_(
                BankTransaction.customer_id == self.customer_id,
                BankTransaction.match_status == MatchStatus.UNMATCHED.value,
                BankTransaction.transaction_date >= from_date
            )
        )

        if account_id:
            query = query.where(BankTransaction.account_id == account_id)

        query = query.order_by(BankTransaction.transaction_date.desc())

        result = self.db.execute(query)
        return list(result.scalars().all())


from datetime import timedelta
