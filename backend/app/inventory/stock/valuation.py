"""
Inventory Valuation Service
FIFO, LIFO, Average Cost calculations
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.inventory.stock.models import StockLevel, StockValuationLayer
from app.inventory.products.models import Product, ProductCategory
from app.inventory.warehouses.models import Warehouse

logger = logging.getLogger(__name__)


class ValuationService:
    """Service for inventory valuation calculations."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_fifo_cost(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: Decimal,
        lot_id: UUID = None,
    ) -> tuple[Decimal, List[dict]]:
        """
        Calculate cost using FIFO (First In, First Out).
        Returns total cost and breakdown of layers consumed.
        """
        layers = self.db.query(StockValuationLayer).filter(
            StockValuationLayer.customer_id == customer_id,
            StockValuationLayer.product_id == product_id,
            StockValuationLayer.warehouse_id == warehouse_id,
            StockValuationLayer.quantity_remaining > 0,
        )

        if lot_id:
            layers = layers.filter(StockValuationLayer.lot_id == lot_id)

        # FIFO: oldest first
        layers = layers.order_by(StockValuationLayer.layer_date.asc()).all()

        remaining = quantity
        total_cost = Decimal("0")
        breakdown = []

        for layer in layers:
            if remaining <= 0:
                break

            consume = min(remaining, layer.quantity_remaining)
            cost = consume * layer.unit_cost
            total_cost += cost

            breakdown.append({
                "layer_id": str(layer.id),
                "layer_date": layer.layer_date.isoformat(),
                "quantity_consumed": float(consume),
                "unit_cost": float(layer.unit_cost),
                "cost": float(cost),
            })

            remaining -= consume

        if remaining > 0:
            logger.warning(f"Insufficient layers for FIFO. Remaining: {remaining}")

        return total_cost, breakdown

    def calculate_lifo_cost(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID,
        quantity: Decimal,
        lot_id: UUID = None,
    ) -> tuple[Decimal, List[dict]]:
        """
        Calculate cost using LIFO (Last In, First Out).
        Returns total cost and breakdown of layers consumed.
        """
        layers = self.db.query(StockValuationLayer).filter(
            StockValuationLayer.customer_id == customer_id,
            StockValuationLayer.product_id == product_id,
            StockValuationLayer.warehouse_id == warehouse_id,
            StockValuationLayer.quantity_remaining > 0,
        )

        if lot_id:
            layers = layers.filter(StockValuationLayer.lot_id == lot_id)

        # LIFO: newest first
        layers = layers.order_by(StockValuationLayer.layer_date.desc()).all()

        remaining = quantity
        total_cost = Decimal("0")
        breakdown = []

        for layer in layers:
            if remaining <= 0:
                break

            consume = min(remaining, layer.quantity_remaining)
            cost = consume * layer.unit_cost
            total_cost += cost

            breakdown.append({
                "layer_id": str(layer.id),
                "layer_date": layer.layer_date.isoformat(),
                "quantity_consumed": float(consume),
                "unit_cost": float(layer.unit_cost),
                "cost": float(cost),
            })

            remaining -= consume

        return total_cost, breakdown

    def calculate_average_cost(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID = None,
    ) -> Decimal:
        """Calculate weighted average cost."""
        query = self.db.query(
            func.sum(StockLevel.quantity_on_hand * StockLevel.unit_cost).label("total_value"),
            func.sum(StockLevel.quantity_on_hand).label("total_qty"),
        ).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == product_id,
            StockLevel.quantity_on_hand > 0,
        )

        if warehouse_id:
            query = query.filter(StockLevel.warehouse_id == warehouse_id)

        result = query.first()

        if result.total_qty and result.total_qty > 0:
            return Decimal(str(result.total_value)) / Decimal(str(result.total_qty))

        return Decimal("0")

    def get_product_valuation(
        self,
        customer_id: UUID,
        product_id: UUID,
        as_of_date: datetime = None,
    ) -> dict:
        """Get valuation for a single product."""
        product = self.db.query(Product).get(product_id)
        if not product:
            raise ValueError("Product not found")

        # Get stock levels
        query = self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == product_id,
        )

        stocks = query.all()

        total_qty = sum(s.quantity_on_hand for s in stocks)
        total_value = sum((s.quantity_on_hand * (s.unit_cost or Decimal("0"))) for s in stocks)

        # By warehouse
        by_warehouse = {}
        for stock in stocks:
            wh_id = str(stock.warehouse_id)
            if wh_id not in by_warehouse:
                by_warehouse[wh_id] = {
                    "warehouse_id": wh_id,
                    "warehouse_code": stock.warehouse.code if stock.warehouse else None,
                    "quantity": 0,
                    "value": 0,
                }
            by_warehouse[wh_id]["quantity"] += float(stock.quantity_on_hand)
            by_warehouse[wh_id]["value"] += float(stock.quantity_on_hand * (stock.unit_cost or Decimal("0")))

        return {
            "product_id": str(product_id),
            "product_sku": product.sku,
            "product_name": product.name,
            "valuation_method": product.valuation_method,
            "total_quantity": float(total_qty),
            "total_value": float(total_value),
            "average_cost": float(total_value / total_qty) if total_qty > 0 else 0,
            "standard_cost": float(product.standard_cost) if product.standard_cost else 0,
            "by_warehouse": list(by_warehouse.values()),
        }

    def get_inventory_valuation_report(
        self,
        customer_id: UUID,
        warehouse_id: UUID = None,
        category_id: UUID = None,
        as_of_date: datetime = None,
    ) -> dict:
        """Generate inventory valuation report."""
        query = self.db.query(
            StockLevel.product_id,
            Product.sku,
            Product.name,
            Product.valuation_method,
            ProductCategory.name.label("category_name"),
            func.sum(StockLevel.quantity_on_hand).label("total_qty"),
            func.sum(StockLevel.quantity_on_hand * StockLevel.unit_cost).label("total_value"),
        ).join(
            Product, StockLevel.product_id == Product.id
        ).outerjoin(
            ProductCategory, Product.category_id == ProductCategory.id
        ).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.quantity_on_hand > 0,
        )

        if warehouse_id:
            query = query.filter(StockLevel.warehouse_id == warehouse_id)

        if category_id:
            query = query.filter(Product.category_id == category_id)

        query = query.group_by(
            StockLevel.product_id,
            Product.sku,
            Product.name,
            Product.valuation_method,
            ProductCategory.name,
        )

        results = query.all()

        # Build report
        products = []
        total_value = Decimal("0")
        total_items = 0

        by_category = {}

        for row in results:
            qty = float(row.total_qty or 0)
            value = float(row.total_value or 0)

            products.append({
                "product_id": str(row.product_id),
                "sku": row.sku,
                "name": row.name,
                "category": row.category_name,
                "valuation_method": row.valuation_method,
                "quantity": qty,
                "value": value,
                "average_cost": value / qty if qty > 0 else 0,
            })

            total_value += Decimal(str(value))
            total_items += int(qty)

            # Aggregate by category
            cat = row.category_name or "Uncategorized"
            if cat not in by_category:
                by_category[cat] = {"quantity": 0, "value": 0}
            by_category[cat]["quantity"] += qty
            by_category[cat]["value"] += value

        # Get warehouse breakdown
        wh_query = self.db.query(
            StockLevel.warehouse_id,
            Warehouse.code,
            Warehouse.name,
            func.sum(StockLevel.quantity_on_hand * StockLevel.unit_cost).label("value"),
            func.count(StockLevel.product_id.distinct()).label("product_count"),
        ).join(
            Warehouse, StockLevel.warehouse_id == Warehouse.id
        ).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.quantity_on_hand > 0,
        )

        if warehouse_id:
            wh_query = wh_query.filter(StockLevel.warehouse_id == warehouse_id)

        wh_query = wh_query.group_by(
            StockLevel.warehouse_id, Warehouse.code, Warehouse.name
        )

        by_warehouse = [
            {
                "warehouse_id": str(row.warehouse_id),
                "code": row.code,
                "name": row.name,
                "value": float(row.value or 0),
                "product_count": row.product_count,
            }
            for row in wh_query.all()
        ]

        return {
            "as_of_date": (as_of_date or datetime.utcnow()).isoformat(),
            "total_value": float(total_value),
            "total_items": total_items,
            "product_count": len(products),
            "by_product": sorted(products, key=lambda x: x["value"], reverse=True),
            "by_category": [
                {"category": k, "quantity": v["quantity"], "value": v["value"]}
                for k, v in sorted(by_category.items(), key=lambda x: x[1]["value"], reverse=True)
            ],
            "by_warehouse": by_warehouse,
        }

    def recalculate_average_cost(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID,
    ) -> Decimal:
        """Recalculate and update average cost for a product in a warehouse."""
        # Get all layers
        layers = self.db.query(StockValuationLayer).filter(
            StockValuationLayer.customer_id == customer_id,
            StockValuationLayer.product_id == product_id,
            StockValuationLayer.warehouse_id == warehouse_id,
            StockValuationLayer.quantity_remaining > 0,
        ).all()

        total_qty = sum(l.quantity_remaining for l in layers)
        total_value = sum(l.quantity_remaining * l.unit_cost for l in layers)

        avg_cost = total_value / total_qty if total_qty > 0 else Decimal("0")

        # Update stock levels
        stocks = self.db.query(StockLevel).filter(
            StockLevel.customer_id == customer_id,
            StockLevel.product_id == product_id,
            StockLevel.warehouse_id == warehouse_id,
        ).all()

        for stock in stocks:
            stock.unit_cost = avg_cost

        self.db.commit()

        return avg_cost

    def get_valuation_layers(
        self,
        customer_id: UUID,
        product_id: UUID,
        warehouse_id: UUID = None,
        include_depleted: bool = False,
    ) -> List[dict]:
        """Get valuation layers for a product."""
        query = self.db.query(StockValuationLayer).filter(
            StockValuationLayer.customer_id == customer_id,
            StockValuationLayer.product_id == product_id,
        )

        if warehouse_id:
            query = query.filter(StockValuationLayer.warehouse_id == warehouse_id)

        if not include_depleted:
            query = query.filter(StockValuationLayer.quantity_remaining > 0)

        layers = query.order_by(StockValuationLayer.layer_date.asc()).all()

        return [layer.to_dict() for layer in layers]


def get_valuation_service(db: Session) -> ValuationService:
    """Factory function."""
    return ValuationService(db)
