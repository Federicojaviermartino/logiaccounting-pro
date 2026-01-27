"""
Bank Account Service
Business logic for bank account management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import Session

from app.banking.accounts.models import BankAccount, BankAccountBalance, AccountType
from app.banking.accounts.schemas import (
    BankAccountCreate, BankAccountUpdate, BankAccountFilter,
    BankAccountSummary, CashPositionResponse
)


class BankAccountService:
    """Service for bank account operations"""

    def __init__(self, db: Session, customer_id: UUID = None):
        self.db = db
        self.customer_id = customer_id

    def create_account(
        self,
        data: BankAccountCreate,
        created_by: UUID
    ) -> BankAccount:
        """Create a new bank account"""
        # Check for duplicate account code
        existing = self.db.execute(
            select(BankAccount).where(
                and_(
                    BankAccount.customer_id == self.customer_id,
                    BankAccount.account_code == data.account_code
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError(f"Account code {data.account_code} already exists")

        # If this is set as primary, unset other primary accounts
        if data.is_primary:
            self._unset_primary_accounts()

        # Create account
        account = BankAccount(
            customer_id=self.customer_id,
            account_code=data.account_code,
            account_name=data.account_name,
            bank_name=data.bank_name,
            bank_code=data.bank_code,
            branch_code=data.branch_code,
            branch_name=data.branch_name,
            account_number=data.account_number,
            iban=data.iban,
            routing_number=data.routing_number,
            sort_code=data.sort_code,
            currency=data.currency,
            account_type=data.account_type.value,
            overdraft_limit=data.overdraft_limit,
            daily_limit=data.daily_limit,
            current_balance=data.opening_balance,
            available_balance=data.opening_balance + data.overdraft_limit,
            last_balance_date=date.today(),
            gl_account_id=data.gl_account_id,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            is_primary=data.is_primary,
            notes=data.notes,
            created_by=created_by
        )

        # Add bank address if provided
        if data.bank_address:
            account.bank_address_line1 = data.bank_address.address_line1
            account.bank_address_line2 = data.bank_address.address_line2
            account.bank_city = data.bank_address.city
            account.bank_state = data.bank_address.state
            account.bank_postal_code = data.bank_address.postal_code
            account.bank_country = data.bank_address.country

        self.db.add(account)

        # Create initial balance record
        initial_balance = BankAccountBalance(
            account_id=account.id,
            balance_date=date.today(),
            opening_balance=data.opening_balance,
            closing_balance=data.opening_balance
        )
        self.db.add(initial_balance)

        self.db.commit()
        self.db.refresh(account)

        return account

    def update_account(
        self,
        account_id: UUID,
        data: BankAccountUpdate
    ) -> BankAccount:
        """Update bank account details"""
        account = self.get_account_by_id(account_id)

        # Handle primary flag
        if data.is_primary is True and not account.is_primary:
            self._unset_primary_accounts()

        # Update fields
        update_data = data.model_dump(exclude_unset=True, exclude={"bank_address"})
        for field, value in update_data.items():
            setattr(account, field, value)

        # Update bank address if provided
        if data.bank_address:
            account.bank_address_line1 = data.bank_address.address_line1
            account.bank_address_line2 = data.bank_address.address_line2
            account.bank_city = data.bank_address.city
            account.bank_state = data.bank_address.state
            account.bank_postal_code = data.bank_address.postal_code
            account.bank_country = data.bank_address.country

        self.db.commit()
        self.db.refresh(account)

        return account

    def get_account_by_id(self, account_id: UUID) -> BankAccount:
        """Get bank account by ID"""
        result = self.db.execute(
            select(BankAccount).where(BankAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Bank account {account_id} not found")

        return account

    def get_accounts(
        self,
        filters: BankAccountFilter = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[BankAccount], int]:
        """Get bank accounts with filtering"""
        query = select(BankAccount).where(
            BankAccount.customer_id == self.customer_id
        )

        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        BankAccount.account_name.ilike(search_term),
                        BankAccount.account_code.ilike(search_term),
                        BankAccount.bank_name.ilike(search_term)
                    )
                )

            if filters.currency:
                query = query.where(BankAccount.currency == filters.currency.upper())

            if filters.account_type:
                query = query.where(BankAccount.account_type == filters.account_type.value)

            if filters.is_active is not None:
                query = query.where(BankAccount.is_active == filters.is_active)

            if filters.is_primary is not None:
                query = query.where(BankAccount.is_primary == filters.is_primary)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(BankAccount.is_primary.desc(), BankAccount.account_name)
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        accounts = list(result.scalars().all())

        return accounts, total

    def get_accounts_summary(
        self,
        currency: str = None
    ) -> List[BankAccountSummary]:
        """Get account summary for dropdowns"""
        query = select(BankAccount).where(
            and_(
                BankAccount.customer_id == self.customer_id,
                BankAccount.is_active == True
            )
        )

        if currency:
            query = query.where(BankAccount.currency == currency.upper())

        query = query.order_by(BankAccount.is_primary.desc(), BankAccount.account_name)

        result = self.db.execute(query)
        accounts = result.scalars().all()

        return [
            BankAccountSummary(
                id=acc.id,
                account_code=acc.account_code,
                account_name=acc.account_name,
                bank_name=acc.bank_name,
                currency=acc.currency,
                current_balance=acc.current_balance,
                is_primary=acc.is_primary
            )
            for acc in accounts
        ]

    def get_balance_history(
        self,
        account_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[BankAccountBalance]:
        """Get balance history for an account"""
        result = self.db.execute(
            select(BankAccountBalance).where(
                and_(
                    BankAccountBalance.account_id == account_id,
                    BankAccountBalance.balance_date >= start_date,
                    BankAccountBalance.balance_date <= end_date
                )
            ).order_by(BankAccountBalance.balance_date)
        )
        return list(result.scalars().all())

    def update_daily_balance(
        self,
        account_id: UUID,
        transaction_date: date,
        amount: Decimal,
        is_debit: bool
    ):
        """Update daily balance record after a transaction"""
        result = self.db.execute(
            select(BankAccountBalance).where(
                and_(
                    BankAccountBalance.account_id == account_id,
                    BankAccountBalance.balance_date == transaction_date
                )
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            # Get previous day's closing balance
            prev_result = self.db.execute(
                select(BankAccountBalance).where(
                    and_(
                        BankAccountBalance.account_id == account_id,
                        BankAccountBalance.balance_date < transaction_date
                    )
                ).order_by(BankAccountBalance.balance_date.desc()).limit(1)
            )
            prev_balance = prev_result.scalar_one_or_none()

            opening = prev_balance.closing_balance if prev_balance else Decimal("0")

            balance = BankAccountBalance(
                account_id=account_id,
                balance_date=transaction_date,
                opening_balance=opening,
                closing_balance=opening
            )
            self.db.add(balance)

        # Update totals
        abs_amount = abs(amount)
        if is_debit:
            balance.total_debits += abs_amount
            balance.debit_count += 1
            balance.closing_balance -= abs_amount
        else:
            balance.total_credits += abs_amount
            balance.credit_count += 1
            balance.closing_balance += abs_amount

        # Update account current balance
        account = self.get_account_by_id(account_id)
        account.update_balance(balance.closing_balance, transaction_date)

        self.db.commit()

    def get_cash_position(
        self,
        base_currency: str = "USD"
    ) -> CashPositionResponse:
        """Get cash position across all accounts"""
        accounts = self.get_accounts_summary()

        # Group by currency
        by_currency = {}
        total_cash = Decimal("0")

        for acc in accounts:
            if acc.currency not in by_currency:
                by_currency[acc.currency] = Decimal("0")
            by_currency[acc.currency] += acc.current_balance
            total_cash += acc.current_balance

        return CashPositionResponse(
            total_cash=total_cash,
            total_cash_base_currency=total_cash,
            base_currency=base_currency,
            accounts=accounts,
            by_currency=by_currency,
            snapshot_date=date.today()
        )

    def set_primary_account(self, account_id: UUID) -> BankAccount:
        """Set an account as the primary account"""
        account = self.get_account_by_id(account_id)
        self._unset_primary_accounts()
        account.is_primary = True
        self.db.commit()
        self.db.refresh(account)
        return account

    def deactivate_account(self, account_id: UUID) -> BankAccount:
        """Deactivate a bank account"""
        account = self.get_account_by_id(account_id)
        account.is_active = False
        if account.is_primary:
            account.is_primary = False
        self.db.commit()
        self.db.refresh(account)
        return account

    def _unset_primary_accounts(self):
        """Unset primary flag on all accounts for a customer"""
        self.db.execute(
            update(BankAccount)
            .where(
                and_(
                    BankAccount.customer_id == self.customer_id,
                    BankAccount.is_primary == True
                )
            )
            .values(is_primary=False)
        )
