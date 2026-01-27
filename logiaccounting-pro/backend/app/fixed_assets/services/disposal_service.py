"""
Asset disposal processing service.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.fixed_assets.models.asset import FixedAsset, AssetStatus, DisposalType
from app.fixed_assets.models.transaction import AssetTransaction, TransactionType, TransactionStatus
from app.fixed_assets.schemas.transaction import DisposalCreate, TransferCreate, RevaluationCreate


class NotFoundError(Exception):
    """Resource not found."""
    pass


class ValidationError(Exception):
    """Validation error."""
    pass


class BusinessRuleError(Exception):
    """Business rule violation."""
    pass


class DisposalService:
    """Service for asset disposal and transfers."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==================== Disposal ====================

    async def create_disposal(
        self,
        data: DisposalCreate,
        user_id: UUID
    ) -> AssetTransaction:
        """Create asset disposal."""
        asset = await self._get_asset(data.asset_id)

        if asset.status == AssetStatus.DISPOSED:
            raise BusinessRuleError("Asset is already disposed")

        # Calculate gain/loss
        book_value = asset.book_value
        proceeds = data.proceeds or Decimal(0)
        gain_loss = proceeds - book_value

        # Generate transaction number
        transaction_number = await self._generate_transaction_number("DIS")

        # Create transaction
        transaction = AssetTransaction(
            customer_id=self.customer_id,
            asset_id=asset.id,
            transaction_number=transaction_number,
            transaction_type=TransactionType.DISPOSAL,
            transaction_date=data.disposal_date,
            amount=proceeds,

            disposal_type=data.disposal_type.value,
            proceeds=proceeds,
            book_value_at_disposal=book_value,
            accumulated_at_disposal=asset.accumulated_depreciation,
            gain_loss=gain_loss,
            buyer_name=data.buyer_name,
            buyer_contact=data.buyer_contact,

            notes=data.notes,
            status=TransactionStatus.DRAFT,
            created_by=user_id,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    async def approve_disposal(
        self,
        disposal_id: UUID,
        user_id: UUID
    ) -> AssetTransaction:
        """Approve disposal."""
        transaction = await self._get_transaction(disposal_id)

        if transaction.transaction_type != TransactionType.DISPOSAL:
            raise ValidationError("Transaction is not a disposal")

        if transaction.status != TransactionStatus.DRAFT:
            raise BusinessRuleError("Only draft transactions can be approved")

        transaction.status = TransactionStatus.APPROVED
        transaction.approved_by = user_id
        transaction.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    async def post_disposal(
        self,
        disposal_id: UUID,
        user_id: UUID
    ) -> AssetTransaction:
        """Post disposal transaction."""
        transaction = await self._get_transaction(disposal_id)

        if transaction.transaction_type != TransactionType.DISPOSAL:
            raise ValidationError("Transaction is not a disposal")

        if transaction.status == TransactionStatus.POSTED:
            raise BusinessRuleError("Transaction already posted")

        asset = await self._get_asset(transaction.asset_id)

        # Update transaction
        transaction.status = TransactionStatus.POSTED

        # Update asset
        asset.status = AssetStatus.DISPOSED
        asset.disposal_date = transaction.transaction_date
        asset.disposal_type = DisposalType(transaction.disposal_type)
        asset.disposal_amount = transaction.proceeds
        asset.disposal_reason = transaction.notes

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    async def cancel_disposal(self, disposal_id: UUID) -> AssetTransaction:
        """Cancel disposal."""
        transaction = await self._get_transaction(disposal_id)

        if transaction.status == TransactionStatus.POSTED:
            raise BusinessRuleError("Cannot cancel posted transaction")

        transaction.status = TransactionStatus.CANCELLED

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    async def get_disposal_by_id(self, disposal_id: UUID) -> AssetTransaction:
        """Get disposal by ID."""
        return await self._get_transaction(disposal_id)

    async def get_disposals(
        self,
        status: Optional[str] = None,
        disposal_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AssetTransaction], int]:
        """Get asset disposals."""
        query = select(AssetTransaction).where(
            AssetTransaction.customer_id == self.customer_id,
            AssetTransaction.transaction_type == TransactionType.DISPOSAL
        )

        if status:
            query = query.where(AssetTransaction.status == status)

        if disposal_type:
            query = query.where(AssetTransaction.disposal_type == disposal_type)

        if date_from:
            query = query.where(AssetTransaction.transaction_date >= date_from)

        if date_to:
            query = query.where(AssetTransaction.transaction_date <= date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(AssetTransaction.transaction_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        disposals = result.scalars().all()

        return disposals, total

    # ==================== Transfer ====================

    async def transfer_asset(
        self,
        data: TransferCreate,
        user_id: UUID
    ) -> AssetTransaction:
        """Create asset transfer."""
        asset = await self._get_asset(data.asset_id)

        if asset.status == AssetStatus.DISPOSED:
            raise BusinessRuleError("Cannot transfer disposed asset")

        transaction_number = await self._generate_transaction_number("TRF")

        transaction = AssetTransaction(
            customer_id=self.customer_id,
            asset_id=asset.id,
            transaction_number=transaction_number,
            transaction_type=TransactionType.TRANSFER,
            transaction_date=data.transfer_date,
            amount=Decimal(0),

            from_location=asset.location,
            to_location=data.to_location,
            from_department_id=asset.department_id,
            to_department_id=data.to_department_id,
            from_responsible_id=asset.responsible_person_id,
            to_responsible_id=data.to_responsible_id,

            notes=data.notes,
            status=TransactionStatus.APPROVED,  # Auto-approve transfers
            created_by=user_id,
        )

        self.db.add(transaction)

        # Update asset location
        if data.to_location:
            asset.location = data.to_location
        if data.to_department_id:
            asset.department_id = data.to_department_id
        if data.to_responsible_id:
            asset.responsible_person_id = data.to_responsible_id

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    # ==================== Helpers ====================

    async def _get_asset(self, asset_id: UUID) -> FixedAsset:
        """Get asset by ID."""
        query = select(FixedAsset).where(
            FixedAsset.id == asset_id,
            FixedAsset.customer_id == self.customer_id
        )
        result = self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            raise NotFoundError(f"Asset not found: {asset_id}")

        return asset

    async def _get_transaction(self, transaction_id: UUID) -> AssetTransaction:
        """Get transaction by ID."""
        query = select(AssetTransaction).where(
            AssetTransaction.id == transaction_id,
            AssetTransaction.customer_id == self.customer_id
        )
        result = self.db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise NotFoundError(f"Transaction not found: {transaction_id}")

        return transaction

    async def _generate_transaction_number(self, prefix: str) -> str:
        """Generate transaction number."""
        year = datetime.now().year % 100

        count_query = select(func.count(AssetTransaction.id)).where(
            AssetTransaction.customer_id == self.customer_id,
            AssetTransaction.transaction_number.like(f"{prefix}-{year}-%")
        )
        count = self.db.execute(count_query).scalar() or 0

        return f"{prefix}-{year}-{(count + 1):05d}"
