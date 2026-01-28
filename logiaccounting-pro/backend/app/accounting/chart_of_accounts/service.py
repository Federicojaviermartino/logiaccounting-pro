"""
Chart of Accounts Service
Business logic for account management
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.utils.datetime_utils import utc_now

from app.accounting.chart_of_accounts.models import (
    Account, AccountType, AccountTypeEnum, DEFAULT_ACCOUNT_TYPES
)
from app.accounting.chart_of_accounts.schemas import (
    AccountCreate, AccountUpdate, AccountFilter, AccountImportRow
)

logger = logging.getLogger(__name__)


class ChartOfAccountsService:
    """Service for managing chart of accounts."""

    def __init__(self, db: Session):
        self.db = db

    # ============== Account Types ==============

    async def ensure_account_types(self) -> List[AccountType]:
        """Ensure default account types exist."""
        existing = self.db.query(AccountType).all()
        if existing:
            return existing

        account_types = []
        for type_data in DEFAULT_ACCOUNT_TYPES:
            account_type = AccountType(**type_data)
            self.db.add(account_type)
            account_types.append(account_type)

        self.db.commit()
        return account_types

    def get_account_types(self) -> List[AccountType]:
        """Get all account types."""
        return self.db.query(AccountType).order_by(AccountType.display_order).all()

    def get_account_type_by_name(self, name: str) -> Optional[AccountType]:
        """Get account type by name."""
        return self.db.query(AccountType).filter(
            AccountType.name == name
        ).first()

    # ============== Account CRUD ==============

    def create_account(
        self,
        customer_id: UUID,
        data: AccountCreate,
        created_by: UUID = None,
    ) -> Account:
        """Create a new account."""
        # Check for duplicate code
        existing = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.code == data.code.upper()
            )
        ).first()

        if existing:
            raise ValueError(f"Account with code {data.code} already exists")

        # Get parent info for hierarchy
        level = 0
        path = data.code.upper()

        if data.parent_id:
            parent = self.get_account_by_id(data.parent_id)
            if not parent:
                raise ValueError("Parent account not found")
            if parent.customer_id != customer_id:
                raise ValueError("Parent account belongs to different customer")
            level = parent.level + 1
            path = f"{parent.path}/{data.code.upper()}"

        account = Account(
            customer_id=customer_id,
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            account_type_id=data.account_type_id,
            parent_id=data.parent_id,
            level=level,
            path=path,
            currency=data.currency,
            is_reconcilable=data.is_reconcilable,
            is_header=data.is_header,
            opening_balance=data.opening_balance,
            current_balance=data.opening_balance,
            tax_code=data.tax_code,
            default_tax_rate=data.default_tax_rate,
            cost_center=data.cost_center,
            department=data.department,
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        logger.info(f"Created account: {account.code} - {account.name}")
        return account

    def get_account_by_id(self, account_id: UUID) -> Optional[Account]:
        """Get account by ID."""
        return self.db.query(Account).options(
            joinedload(Account.account_type)
        ).filter(Account.id == account_id).first()

    def get_account_by_code(
        self,
        customer_id: UUID,
        code: str,
    ) -> Optional[Account]:
        """Get account by code."""
        return self.db.query(Account).options(
            joinedload(Account.account_type)
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.code == code.upper()
            )
        ).first()

    def get_accounts(
        self,
        customer_id: UUID,
        filters: AccountFilter = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[List[Account], int]:
        """Get accounts with filtering and pagination."""
        query = self.db.query(Account).options(
            joinedload(Account.account_type)
        ).filter(Account.customer_id == customer_id)

        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Account.code.ilike(search_term),
                        Account.name.ilike(search_term),
                        Account.description.ilike(search_term)
                    )
                )

            if filters.account_type:
                account_type = self.get_account_type_by_name(filters.account_type.value)
                if account_type:
                    query = query.filter(Account.account_type_id == account_type.id)

            if filters.is_active is not None:
                query = query.filter(Account.is_active == filters.is_active)

            if filters.is_header is not None:
                query = query.filter(Account.is_header == filters.is_header)

            if filters.parent_id:
                query = query.filter(Account.parent_id == filters.parent_id)

            if filters.has_balance is not None:
                if filters.has_balance:
                    query = query.filter(Account.current_balance != 0)
                else:
                    query = query.filter(Account.current_balance == 0)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        accounts = query.order_by(Account.code).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return accounts, total

    def update_account(
        self,
        account_id: UUID,
        data: AccountUpdate,
    ) -> Account:
        """Update an account."""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("Account not found")

        if account.is_system:
            # Only allow certain updates on system accounts
            allowed_fields = {"description", "notes", "is_active"}
            update_data = data.model_dump(exclude_unset=True)
            for field in list(update_data.keys()):
                if field not in allowed_fields:
                    del update_data[field]
        else:
            update_data = data.model_dump(exclude_unset=True)

        # Handle parent change
        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]
            if new_parent_id:
                # Prevent circular reference
                if new_parent_id == account_id:
                    raise ValueError("Account cannot be its own parent")

                parent = self.get_account_by_id(new_parent_id)
                if not parent:
                    raise ValueError("Parent account not found")

                # Check for circular reference in hierarchy
                current = parent
                while current:
                    if current.id == account_id:
                        raise ValueError("Circular reference detected")
                    current = current.parent

                account.level = parent.level + 1
                account.path = f"{parent.path}/{account.code}"
            else:
                account.level = 0
                account.path = account.code

        for field, value in update_data.items():
            setattr(account, field, value)

        account.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(account)

        logger.info(f"Updated account: {account.code}")
        return account

    def deactivate_account(self, account_id: UUID) -> Account:
        """Deactivate an account (soft delete)."""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("Account not found")

        if account.is_system:
            raise ValueError("Cannot deactivate system account")

        # Check for child accounts
        if account.children.count() > 0:
            raise ValueError("Cannot deactivate account with child accounts")

        # Check for transactions
        if account.current_balance != 0:
            raise ValueError("Cannot deactivate account with non-zero balance")

        account.is_active = False
        account.updated_at = utc_now()
        self.db.commit()

        logger.info(f"Deactivated account: {account.code}")
        return account

    def delete_account(self, account_id: UUID) -> bool:
        """Permanently delete an account (only if no transactions)."""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("Account not found")

        if account.is_system:
            raise ValueError("Cannot delete system account")

        # Check for child accounts
        if account.children.count() > 0:
            raise ValueError("Cannot delete account with child accounts")

        # Check for journal lines
        if account.journal_lines:
            raise ValueError("Cannot delete account with transactions")

        self.db.delete(account)
        self.db.commit()

        logger.info(f"Deleted account: {account.code}")
        return True

    # ============== Tree Operations ==============

    def get_account_tree(
        self,
        customer_id: UUID,
        root_type: str = None,
        include_inactive: bool = False,
    ) -> List[Dict]:
        """Get hierarchical account tree."""
        query = self.db.query(Account).options(
            joinedload(Account.account_type)
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.parent_id == None  # Root accounts only
            )
        )

        if not include_inactive:
            query = query.filter(Account.is_active == True)

        if root_type:
            account_type = self.get_account_type_by_name(root_type)
            if account_type:
                query = query.filter(Account.account_type_id == account_type.id)

        root_accounts = query.order_by(Account.code).all()

        return [account.to_tree_node() for account in root_accounts]

    def get_accounts_by_type(
        self,
        customer_id: UUID,
        account_type: AccountTypeEnum,
        include_header: bool = False,
    ) -> List[Account]:
        """Get all accounts of a specific type."""
        type_record = self.get_account_type_by_name(account_type.value)
        if not type_record:
            return []

        query = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.account_type_id == type_record.id,
                Account.is_active == True
            )
        )

        if not include_header:
            query = query.filter(Account.is_header == False)

        return query.order_by(Account.code).all()

    def get_postable_accounts(self, customer_id: UUID) -> List[Account]:
        """Get accounts that can receive transactions."""
        return self.db.query(Account).options(
            joinedload(Account.account_type)
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True,
                Account.is_header == False
            )
        ).order_by(Account.code).all()

    # ============== Balance Operations ==============

    def update_balance(
        self,
        account_id: UUID,
        debit: Decimal,
        credit: Decimal,
    ) -> Account:
        """Update account balance from journal posting."""
        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("Account not found")

        # Determine effect based on normal balance
        if account.account_type.normal_balance.value == "debit":
            # Assets, Expenses: Debits increase, Credits decrease
            account.current_balance += debit - credit
        else:
            # Liabilities, Equity, Revenue: Credits increase, Debits decrease
            account.current_balance += credit - debit

        self.db.commit()
        return account

    def recalculate_balance(self, account_id: UUID) -> Decimal:
        """Recalculate account balance from all journal lines."""
        from app.accounting.journal.models import JournalLine, JournalEntry

        account = self.get_account_by_id(account_id)
        if not account:
            raise ValueError("Account not found")

        # Sum all posted journal lines
        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit")
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == account_id,
                JournalEntry.status == "posted"
            )
        ).first()

        total_debit = Decimal(str(result.total_debit))
        total_credit = Decimal(str(result.total_credit))

        # Calculate balance based on normal balance
        if account.account_type.normal_balance.value == "debit":
            balance = account.opening_balance + total_debit - total_credit
        else:
            balance = account.opening_balance + total_credit - total_debit

        account.current_balance = balance
        self.db.commit()

        return balance

    # ============== Import Operations ==============

    def import_accounts(
        self,
        customer_id: UUID,
        accounts: List[AccountImportRow],
        created_by: UUID = None,
    ) -> Dict[str, Any]:
        """Bulk import accounts."""
        created = 0
        updated = 0
        errors = []

        # First pass: create accounts without parents
        account_map = {}  # code -> account

        for row in accounts:
            try:
                account_type = self.get_account_type_by_name(row.type.value)
                if not account_type:
                    errors.append(f"Invalid account type: {row.type}")
                    continue

                existing = self.get_account_by_code(customer_id, row.code)

                if existing:
                    # Update existing
                    existing.name = row.name
                    existing.description = row.description
                    existing.is_header = row.is_header
                    self.db.commit()
                    account_map[row.code] = existing
                    updated += 1
                else:
                    # Create new (without parent for now)
                    account = Account(
                        customer_id=customer_id,
                        code=row.code.upper(),
                        name=row.name,
                        description=row.description,
                        account_type_id=account_type.id,
                        is_header=row.is_header,
                        opening_balance=row.opening_balance,
                        current_balance=row.opening_balance,
                        created_by=created_by,
                    )
                    self.db.add(account)
                    self.db.commit()
                    self.db.refresh(account)
                    account_map[row.code] = account
                    created += 1

            except Exception as e:
                errors.append(f"Error importing {row.code}: {str(e)}")

        # Second pass: set parent relationships
        for row in accounts:
            if row.parent_code and row.code in account_map:
                account = account_map[row.code]
                parent = account_map.get(row.parent_code)

                if parent:
                    account.parent_id = parent.id
                    account.level = parent.level + 1
                    account.path = f"{parent.path}/{account.code}"
                else:
                    errors.append(f"Parent {row.parent_code} not found for {row.code}")

        self.db.commit()

        return {
            "success": len(errors) == 0,
            "accounts_created": created,
            "accounts_updated": updated,
            "errors": errors,
        }


def get_chart_of_accounts_service(db: Session) -> ChartOfAccountsService:
    """Factory function for service."""
    return ChartOfAccountsService(db)
