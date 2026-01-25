"""
Cash Flow Service
High-level service for cash flow prediction features
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.ai.base import AIResult
from app.ai.cashflow.predictor import CashFlowPredictor, cashflow_predictor

logger = logging.getLogger(__name__)


class CashFlowService:
    """Service layer for cash flow predictions."""

    def __init__(self, predictor: CashFlowPredictor = None):
        self.predictor = predictor or cashflow_predictor

    async def train_model(
        self,
        customer_id: str,
        historical_data: List[Dict],
        current_balance: float,
    ) -> AIResult:
        """Train cash flow model for customer."""
        logger.info(f"Training cash flow model for customer {customer_id}")

        # Validate data
        if not historical_data:
            return AIResult.fail("No historical data provided")

        if current_balance is None:
            return AIResult.fail("Current balance is required")

        # Train the predictor
        result = await self.predictor.train(
            customer_id=customer_id,
            historical_data=historical_data,
            current_balance=current_balance,
        )

        if result.success:
            logger.info(f"Model trained successfully for customer {customer_id}")
        else:
            logger.warning(f"Model training failed for customer {customer_id}: {result.error}")

        return result

    async def get_forecast(
        self,
        customer_id: str,
        horizon_days: int = 30,
        scenario: str = "expected",
        include_pending: bool = True,
        include_recurring: bool = True,
        pending_transactions: List[Dict] = None,
        recurring_transactions: List[Dict] = None,
    ) -> AIResult:
        """Get cash flow forecast for customer."""
        logger.info(f"Generating {horizon_days}-day forecast for customer {customer_id}")

        # Validate scenario
        valid_scenarios = ["expected", "optimistic", "pessimistic"]
        if scenario not in valid_scenarios:
            return AIResult.fail(f"Invalid scenario. Must be one of: {valid_scenarios}")

        # Generate predictions
        result = await self.predictor.predict(
            customer_id=customer_id,
            horizon_days=horizon_days,
            scenario=scenario,
            include_pending=include_pending,
            pending_transactions=pending_transactions or [],
            recurring_transactions=recurring_transactions or [] if include_recurring else [],
        )

        return result

    def get_model_status(self, customer_id: str) -> Dict:
        """Get model status for customer."""
        model_info = self.predictor.get_model_info(customer_id)

        return {
            "customer_id": customer_id,
            "trained": model_info.get("trained", False),
            "last_training": model_info.get("last_training").isoformat() if model_info.get("last_training") else None,
            "status": "ready" if model_info.get("trained") else "not_trained",
        }

    async def retrain_model(
        self,
        customer_id: str,
        historical_data: List[Dict],
        current_balance: float,
    ) -> AIResult:
        """Retrain model with new data."""
        return await self.train_model(customer_id, historical_data, current_balance)

    def clear_model(self, customer_id: str) -> bool:
        """Clear trained model for customer."""
        if hasattr(self.predictor, "_models") and customer_id in self.predictor._models:
            del self.predictor._models[customer_id]
            self.predictor._trained[customer_id] = False
            logger.info(f"Cleared model for customer {customer_id}")
            return True
        return False


# Global service instance
cashflow_service = CashFlowService()
