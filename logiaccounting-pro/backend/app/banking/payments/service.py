"""
Payment Processing Service
Business logic for payment batch processing
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.utils.datetime_utils import utc_now

from app.banking.payments.models import (
    PaymentBatch, PaymentInstruction, PaymentHistory,
    BatchStatus, PaymentMethod, BatchType, InstructionStatus
)
from app.banking.payments.schemas import (
    PaymentBatchCreate, PaymentBatchUpdate, PaymentInstructionCreate
)


class PaymentService:
    """Service for payment processing operations"""

    def __init__(self, db: Session, customer_id: UUID = None):
        self.db = db
        self.customer_id = customer_id

    def create_batch(
        self,
        data: PaymentBatchCreate,
        created_by: UUID
    ) -> PaymentBatch:
        """Create a new payment batch"""
        # Generate batch number
        batch_number = f"PAY-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"

        batch = PaymentBatch(
            customer_id=self.customer_id,
            batch_number=batch_number,
            batch_name=data.batch_name,
            bank_account_id=data.bank_account_id,
            payment_method=data.payment_method.value,
            batch_type=data.batch_type.value,
            currency=data.currency,
            payment_date=data.payment_date,
            value_date=data.value_date,
            requires_approval=data.requires_approval,
            approval_threshold=data.approval_threshold,
            notes=data.notes,
            created_by=created_by
        )

        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        return batch

    def get_batch_by_id(self, batch_id: UUID) -> PaymentBatch:
        """Get batch by ID"""
        result = self.db.execute(
            select(PaymentBatch).where(PaymentBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"Payment batch {batch_id} not found")

        return batch

    def get_batches(
        self,
        status: BatchStatus = None,
        batch_type: BatchType = None,
        start_date: date = None,
        end_date: date = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PaymentBatch], int]:
        """Get batches with filtering"""
        query = select(PaymentBatch).where(
            PaymentBatch.customer_id == self.customer_id
        )

        if status:
            query = query.where(PaymentBatch.status == status.value)

        if batch_type:
            query = query.where(PaymentBatch.batch_type == batch_type.value)

        if start_date:
            query = query.where(PaymentBatch.payment_date >= start_date)

        if end_date:
            query = query.where(PaymentBatch.payment_date <= end_date)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(PaymentBatch.payment_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        batches = list(result.scalars().all())

        return batches, total

    def update_batch(
        self,
        batch_id: UUID,
        data: PaymentBatchUpdate
    ) -> PaymentBatch:
        """Update batch details"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status not in [BatchStatus.DRAFT.value, BatchStatus.PENDING_APPROVAL.value]:
            raise ValueError("Cannot modify batch in current status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def add_instruction(
        self,
        batch_id: UUID,
        data: PaymentInstructionCreate
    ) -> PaymentInstruction:
        """Add a payment instruction to a batch"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status not in [BatchStatus.DRAFT.value]:
            raise ValueError("Cannot add instructions to batch in current status")

        # Get next line number
        result = self.db.execute(
            select(func.max(PaymentInstruction.line_number)).where(
                PaymentInstruction.batch_id == batch_id
            )
        )
        max_line = result.scalar() or 0

        instruction = PaymentInstruction(
            batch_id=batch_id,
            line_number=max_line + 1,
            source_type=data.source_type,
            source_id=data.source_id,
            payee_type=data.payee_type,
            payee_id=data.payee_id,
            payee_name=data.payee_name,
            payee_bank_name=data.payee_bank_name,
            payee_account_number=data.payee_account_number,
            payee_routing_number=data.payee_routing_number,
            payee_iban=data.payee_iban,
            payee_swift=data.payee_swift,
            currency=data.currency,
            amount=data.amount,
            payment_reference=data.payment_reference,
            remittance_info=data.remittance_info,
            notes=data.notes
        )

        if data.payee_address:
            instruction.payee_address_line1 = data.payee_address.address_line1
            instruction.payee_address_line2 = data.payee_address.address_line2
            instruction.payee_city = data.payee_address.city
            instruction.payee_state = data.payee_address.state
            instruction.payee_postal_code = data.payee_address.postal_code
            instruction.payee_country = data.payee_address.country

        self.db.add(instruction)

        # Update batch totals
        batch.payment_count += 1
        batch.total_amount += data.amount

        self.db.commit()
        self.db.refresh(instruction)

        return instruction

    def remove_instruction(self, instruction_id: UUID):
        """Remove an instruction from a batch"""
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.id == instruction_id)
        )
        instruction = result.scalar_one_or_none()

        if not instruction:
            raise ValueError(f"Payment instruction {instruction_id} not found")

        batch = self.get_batch_by_id(instruction.batch_id)

        if batch.status not in [BatchStatus.DRAFT.value]:
            raise ValueError("Cannot remove instructions from batch in current status")

        # Update batch totals
        batch.payment_count -= 1
        batch.total_amount -= instruction.amount

        self.db.delete(instruction)
        self.db.commit()

    def submit_for_approval(self, batch_id: UUID) -> PaymentBatch:
        """Submit batch for approval"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.DRAFT.value:
            raise ValueError("Batch must be in draft status")

        if batch.payment_count == 0:
            raise ValueError("Batch has no payment instructions")

        batch.status = BatchStatus.PENDING_APPROVAL.value

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def approve_batch(
        self,
        batch_id: UUID,
        approved: bool,
        approved_by: UUID,
        notes: str = None
    ) -> PaymentBatch:
        """Approve or reject a batch"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.PENDING_APPROVAL.value:
            raise ValueError("Batch must be pending approval")

        if approved:
            batch.status = BatchStatus.APPROVED.value
            batch.approved_by = approved_by
            batch.approved_at = utc_now()
        else:
            batch.status = BatchStatus.DRAFT.value

        if notes:
            batch.notes = (batch.notes or "") + f"\n[Approval] {notes}"

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def process_batch(self, batch_id: UUID) -> PaymentBatch:
        """Process an approved batch"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.APPROVED.value:
            raise ValueError("Batch must be approved before processing")

        batch.status = BatchStatus.PROCESSING.value

        # Update all instructions to approved
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.batch_id == batch_id)
        )
        for instruction in result.scalars().all():
            instruction.status = InstructionStatus.APPROVED.value

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def generate_payment_file(
        self,
        batch_id: UUID,
        file_format: str = "nacha"
    ) -> str:
        """Generate payment file for bank submission"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.PROCESSING.value:
            raise ValueError("Batch must be in processing status")

        # Generate file based on format
        if file_format == "nacha":
            file_content = self._generate_nacha(batch)
        elif file_format == "csv":
            file_content = self._generate_csv(batch)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        batch.file_format = file_format
        batch.file_generated_at = utc_now()
        batch.file_reference = f"PAY-{batch.batch_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self.db.commit()

        return file_content

    def mark_batch_sent(self, batch_id: UUID) -> PaymentBatch:
        """Mark batch as sent to bank"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.PROCESSING.value:
            raise ValueError("Batch must be in processing status")

        batch.status = BatchStatus.SENT.value
        batch.sent_at = utc_now()

        # Update all instructions
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.batch_id == batch_id)
        )
        for instruction in result.scalars().all():
            instruction.status = InstructionStatus.SENT.value

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def complete_batch(
        self,
        batch_id: UUID,
        completed_instructions: List[dict] = None
    ) -> PaymentBatch:
        """Mark batch as completed"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status != BatchStatus.SENT.value:
            raise ValueError("Batch must be in sent status")

        batch.status = BatchStatus.COMPLETED.value
        batch.completed_at = utc_now()

        # Update instructions with confirmation numbers
        if completed_instructions:
            for item in completed_instructions:
                result = self.db.execute(
                    select(PaymentInstruction).where(
                        PaymentInstruction.id == item.get("instruction_id")
                    )
                )
                instruction = result.scalar_one_or_none()
                if instruction:
                    instruction.status = InstructionStatus.COMPLETED.value
                    instruction.processed_at = utc_now()
                    instruction.confirmation_number = item.get("confirmation_number")
        else:
            # Mark all as completed
            result = self.db.execute(
                select(PaymentInstruction).where(PaymentInstruction.batch_id == batch_id)
            )
            for instruction in result.scalars().all():
                instruction.status = InstructionStatus.COMPLETED.value
                instruction.processed_at = utc_now()

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def cancel_batch(self, batch_id: UUID) -> PaymentBatch:
        """Cancel a batch"""
        batch = self.get_batch_by_id(batch_id)

        if batch.status in [BatchStatus.COMPLETED.value, BatchStatus.SENT.value]:
            raise ValueError("Cannot cancel completed or sent batch")

        batch.status = BatchStatus.CANCELLED.value

        # Cancel all instructions
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.batch_id == batch_id)
        )
        for instruction in result.scalars().all():
            instruction.status = InstructionStatus.CANCELLED.value

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def record_payment(
        self,
        document_type: str,
        document_id: UUID,
        payment_date: date,
        amount: Decimal,
        currency: str,
        payment_method: str = None,
        reference: str = None,
        instruction_id: UUID = None,
        transaction_id: UUID = None
    ) -> PaymentHistory:
        """Record a payment in history"""
        history = PaymentHistory(
            customer_id=self.customer_id,
            document_type=document_type,
            document_id=document_id,
            payment_instruction_id=instruction_id,
            bank_transaction_id=transaction_id,
            payment_date=payment_date,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            reference=reference,
            allocated_amount=amount
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def _generate_nacha(self, batch: PaymentBatch) -> str:
        """Generate NACHA ACH file format"""
        lines = []

        # File header
        lines.append("1" + "01" + " " * 10 + "9" * 10)  # Simplified

        # Batch header
        lines.append("5" + "220")  # Credits

        # Entry detail records
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.batch_id == batch.id)
        )
        for instruction in result.scalars().all():
            lines.append(
                "6" +
                "22" +  # Transaction code
                (instruction.payee_routing_number or "").ljust(9) +
                (instruction.payee_account_number or "").ljust(17) +
                str(int(instruction.amount * 100)).zfill(10) +
                instruction.payee_name[:22].ljust(22)
            )

        # Batch control
        lines.append("8" + "220")

        # File control
        lines.append("9" + "9" * 93)

        return "\n".join(lines)

    def _generate_csv(self, batch: PaymentBatch) -> str:
        """Generate CSV payment file"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Line", "Payee Name", "Bank Name", "Account Number",
            "Routing Number", "Amount", "Currency", "Reference"
        ])

        # Data
        result = self.db.execute(
            select(PaymentInstruction).where(PaymentInstruction.batch_id == batch.id)
        )
        for instruction in result.scalars().all():
            writer.writerow([
                instruction.line_number,
                instruction.payee_name,
                instruction.payee_bank_name or "",
                instruction.payee_account_number or "",
                instruction.payee_routing_number or "",
                str(instruction.amount),
                instruction.currency,
                instruction.payment_reference or ""
            ])

        return output.getvalue()
