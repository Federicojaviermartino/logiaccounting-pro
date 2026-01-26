"""Reorder Management Service"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.inventory.reorder.models import ReorderRule, PurchaseRequisition, RequisitionStatusEnum
from app.inventory.stock.models import StockLevel
from app.inventory.products.models import Product


class ReorderService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_req_number(self, customer_id: UUID) -> str:
        date_str = datetime.utcnow().strftime("%Y%m")
        last = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.customer_id == customer_id,
            PurchaseRequisition.requisition_number.like(f"REQ-{date_str}-%")
        ).order_by(PurchaseRequisition.requisition_number.desc()).first()
        seq = int(last.requisition_number.split("-")[-1]) + 1 if last else 1
        return f"REQ-{date_str}-{seq:05d}"

    def create_rule(
        self,
        customer_id: UUID,
        product_id: UUID,
        reorder_point: Decimal,
        min_order_quantity: Decimal,
        warehouse_id: UUID = None,
        safety_stock: Decimal = None,
        max_order_quantity: Decimal = None,
        order_multiple: Decimal = None,
        lead_time_days: int = 0,
        auto_create: bool = False,
    ) -> ReorderRule:
        # Check existing
        existing = self.db.query(ReorderRule).filter(
            ReorderRule.customer_id == customer_id,
            ReorderRule.product_id == product_id,
            ReorderRule.warehouse_id == warehouse_id,
        ).first()

        if existing:
            raise ValueError("Rule already exists for this product/warehouse")

        rule = ReorderRule(
            customer_id=customer_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            reorder_point=reorder_point,
            safety_stock=safety_stock or Decimal("0"),
            min_order_quantity=min_order_quantity,
            max_order_quantity=max_order_quantity,
            order_multiple=order_multiple or Decimal("1"),
            lead_time_days=lead_time_days,
            auto_create_requisition=auto_create,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def check_reorder_points(
        self,
        customer_id: UUID,
        create_requisitions: bool = False,
    ) -> List[dict]:
        """Check all products against reorder points."""
        results = []

        # Get active rules
        rules = self.db.query(ReorderRule).filter(
            ReorderRule.customer_id == customer_id,
            ReorderRule.is_active == True,
        ).all()

        for rule in rules:
            # Get available stock
            query = self.db.query(func.sum(
                StockLevel.quantity_on_hand - StockLevel.quantity_reserved
            )).filter(
                StockLevel.customer_id == customer_id,
                StockLevel.product_id == rule.product_id,
            )

            if rule.warehouse_id:
                query = query.filter(StockLevel.warehouse_id == rule.warehouse_id)

            available = query.scalar() or Decimal("0")

            # Check if below reorder point
            if available <= rule.reorder_point:
                shortage = rule.reorder_point - available + rule.safety_stock
                order_qty = max(shortage, rule.min_order_quantity)

                # Round up to order multiple
                if rule.order_multiple and rule.order_multiple > 0:
                    order_qty = (
                        (order_qty // rule.order_multiple + 1) * rule.order_multiple
                        if order_qty % rule.order_multiple != 0
                        else order_qty
                    )

                # Apply max
                if rule.max_order_quantity and order_qty > rule.max_order_quantity:
                    order_qty = rule.max_order_quantity

                result = {
                    "rule_id": str(rule.id),
                    "product_id": str(rule.product_id),
                    "product_sku": rule.product.sku if rule.product else None,
                    "warehouse_id": str(rule.warehouse_id) if rule.warehouse_id else None,
                    "available_quantity": float(available),
                    "reorder_point": float(rule.reorder_point),
                    "shortage": float(shortage),
                    "suggested_order_qty": float(order_qty),
                    "requisition_created": False,
                }

                # Auto-create requisition
                if create_requisitions and rule.auto_create_requisition:
                    req = self._create_requisition_from_rule(customer_id, rule, order_qty)
                    result["requisition_id"] = str(req.id)
                    result["requisition_created"] = True
                    rule.last_triggered_at = datetime.utcnow()

                results.append(result)

        self.db.commit()
        return results

    def _create_requisition_from_rule(
        self,
        customer_id: UUID,
        rule: ReorderRule,
        quantity: Decimal,
    ) -> PurchaseRequisition:
        req = PurchaseRequisition(
            customer_id=customer_id,
            requisition_number=self._generate_req_number(customer_id),
            source_type="reorder_rule",
            reorder_rule_id=rule.id,
            product_id=rule.product_id,
            warehouse_id=rule.warehouse_id,
            quantity_required=quantity,
            supplier_id=rule.preferred_supplier_id,
            required_date=(datetime.utcnow() + timedelta(days=rule.lead_time_days)).date() if rule.lead_time_days else None,
        )
        self.db.add(req)
        return req

    def create_requisition(
        self,
        customer_id: UUID,
        product_id: UUID,
        quantity: Decimal,
        warehouse_id: UUID = None,
        supplier_id: UUID = None,
        required_date: datetime = None,
        created_by: UUID = None,
    ) -> PurchaseRequisition:
        req = PurchaseRequisition(
            customer_id=customer_id,
            requisition_number=self._generate_req_number(customer_id),
            source_type="manual",
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_required=quantity,
            supplier_id=supplier_id,
            required_date=required_date.date() if required_date else None,
            created_by=created_by,
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def approve_requisition(
        self,
        requisition_id: UUID,
        approved_by: UUID = None,
    ) -> PurchaseRequisition:
        req = self.db.query(PurchaseRequisition).get(requisition_id)
        if not req or req.status != RequisitionStatusEnum.PENDING.value:
            raise ValueError("Cannot approve")

        req.status = RequisitionStatusEnum.APPROVED.value
        req.approved_by = approved_by
        self.db.commit()
        return req

    def get_requisitions(
        self,
        customer_id: UUID,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[PurchaseRequisition], int]:
        query = self.db.query(PurchaseRequisition).filter(
            PurchaseRequisition.customer_id == customer_id
        )

        if status:
            query = query.filter(PurchaseRequisition.status == status)

        total = query.count()
        reqs = query.options(
            joinedload(PurchaseRequisition.product)
        ).order_by(PurchaseRequisition.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

        return reqs, total

    def get_rules(self, customer_id: UUID, active_only: bool = True) -> List[ReorderRule]:
        query = self.db.query(ReorderRule).filter(
            ReorderRule.customer_id == customer_id
        )
        if active_only:
            query = query.filter(ReorderRule.is_active == True)
        return query.options(joinedload(ReorderRule.product)).all()


def get_reorder_service(db: Session) -> ReorderService:
    return ReorderService(db)
