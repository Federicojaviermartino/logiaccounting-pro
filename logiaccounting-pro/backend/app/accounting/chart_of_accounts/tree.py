"""
Account Tree Operations
Hierarchical operations for chart of accounts
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account, AccountTypeEnum


class AccountTreeBuilder:
    """Build and manipulate account tree structures."""

    def __init__(self, db: Session):
        self.db = db

    def build_tree(
        self,
        customer_id: UUID,
        include_balances: bool = True,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Build complete account tree for a customer."""
        # Get all accounts in one query
        query = self.db.query(Account).filter(
            Account.customer_id == customer_id
        )

        if not include_inactive:
            query = query.filter(Account.is_active == True)

        accounts = query.order_by(Account.code).all()

        # Build lookup dictionaries
        account_dict = {str(a.id): a for a in accounts}
        children_dict = defaultdict(list)

        for account in accounts:
            if account.parent_id:
                children_dict[str(account.parent_id)].append(account)

        # Build tree from root nodes
        root_accounts = [a for a in accounts if not a.parent_id]

        def build_node(account: Account) -> Dict[str, Any]:
            children = children_dict.get(str(account.id), [])
            children_nodes = [build_node(c) for c in sorted(children, key=lambda x: x.code)]

            # Calculate total balance including children
            total_balance = account.current_balance
            if children_nodes:
                total_balance += sum(c.get("total_balance", 0) for c in children_nodes)

            node = {
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "type": account.account_type.name if account.account_type else None,
                "level": account.level,
                "is_header": account.is_header,
                "is_active": account.is_active,
                "children": children_nodes,
            }

            if include_balances:
                node["balance"] = float(account.current_balance)
                node["total_balance"] = float(total_balance)

            return node

        return [build_node(a) for a in sorted(root_accounts, key=lambda x: x.code)]

    def get_ancestors(self, account_id: UUID) -> List[Account]:
        """Get all ancestor accounts."""
        account = self.db.query(Account).get(account_id)
        if not account:
            return []

        ancestors = []
        current = account.parent
        while current:
            ancestors.append(current)
            current = current.parent

        return list(reversed(ancestors))

    def get_descendants(
        self,
        account_id: UUID,
        include_self: bool = False,
    ) -> List[Account]:
        """Get all descendant accounts."""
        account = self.db.query(Account).get(account_id)
        if not account:
            return []

        descendants = []
        if include_self:
            descendants.append(account)

        def collect_children(parent: Account):
            for child in parent.children:
                descendants.append(child)
                collect_children(child)

        collect_children(account)
        return descendants

    def get_subtree_balance(self, account_id: UUID) -> Decimal:
        """Get total balance of account and all descendants."""
        descendants = self.get_descendants(account_id, include_self=True)
        return sum(a.current_balance for a in descendants)

    def move_account(
        self,
        account_id: UUID,
        new_parent_id: Optional[UUID],
    ) -> Account:
        """Move account to new parent."""
        account = self.db.query(Account).get(account_id)
        if not account:
            raise ValueError("Account not found")

        if new_parent_id:
            new_parent = self.db.query(Account).get(new_parent_id)
            if not new_parent:
                raise ValueError("New parent not found")

            # Validate same customer
            if new_parent.customer_id != account.customer_id:
                raise ValueError("Cannot move to different customer")

            # Check for circular reference
            ancestors = self.get_ancestors(new_parent_id)
            if any(a.id == account_id for a in ancestors):
                raise ValueError("Cannot move account to its own descendant")

            # Check same account type
            if new_parent.account_type_id != account.account_type_id:
                raise ValueError("Cannot move to different account type")

            account.parent_id = new_parent_id
            account.level = new_parent.level + 1
            account.path = f"{new_parent.path}/{account.code}"
        else:
            account.parent_id = None
            account.level = 0
            account.path = account.code

        # Update descendants paths
        self._update_descendant_paths(account)

        self.db.commit()
        return account

    def _update_descendant_paths(self, account: Account):
        """Recursively update paths of descendants."""
        for child in account.children:
            child.level = account.level + 1
            child.path = f"{account.path}/{child.code}"
            self._update_descendant_paths(child)

    def flatten_tree(
        self,
        customer_id: UUID,
        type_filter: AccountTypeEnum = None,
    ) -> List[Dict[str, Any]]:
        """Get flat list with indentation info for dropdowns."""
        query = self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.is_active == True,
        )

        if type_filter:
            query = query.join(Account.account_type).filter(
                Account.account_type.has(name=type_filter.value)
            )

        accounts = query.order_by(Account.path).all()

        return [
            {
                "id": str(a.id),
                "code": a.code,
                "name": a.name,
                "display_name": f"{'  ' * a.level}{a.code} - {a.name}",
                "level": a.level,
                "type": a.account_type.name if a.account_type else None,
                "can_post": not a.is_header,
            }
            for a in accounts
        ]


def get_account_tree_builder(db: Session) -> AccountTreeBuilder:
    """Factory function."""
    return AccountTreeBuilder(db)
