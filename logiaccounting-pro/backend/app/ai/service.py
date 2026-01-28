"""
AI Service Aggregator
Unified interface for all AI features
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.utils.datetime_utils import utc_now
from app.ai.cashflow.service import cashflow_service
from app.ai.ocr.service import ocr_service
from app.ai.assistant.service import assistant_service
from app.ai.anomaly.service import anomaly_service
from app.ai.base import AIResult

logger = logging.getLogger(__name__)


class AIServiceAggregator:
    """Aggregates all AI services for unified access."""

    def __init__(self):
        self.cashflow = cashflow_service
        self.ocr = ocr_service
        self.assistant = assistant_service
        self.anomaly = anomaly_service

    async def get_dashboard_insights(self, customer_id: str) -> Dict:
        """Get AI insights for dashboard."""
        insights = {
            "cashflow": None,
            "anomalies": None,
            "recommendations": [],
            "generated_at": utc_now().isoformat(),
        }

        try:
            # Cash flow forecast
            cf_result = await self.cashflow.get_forecast(
                customer_id=customer_id,
                horizon_days=30,
                scenario="expected",
            )
            if cf_result.success:
                insights["cashflow"] = {
                    "current_balance": cf_result.data.get("summary", {}).get("starting_balance"),
                    "forecast_30_days": cf_result.data.get("summary", {}).get("ending_balance"),
                    "trend": cf_result.data.get("summary", {}).get("trend"),
                    "alerts": cf_result.data.get("alerts", [])[:3],
                }
        except Exception as e:
            logger.error(f"Cash flow insights failed: {e}")

        try:
            # Anomaly summary
            anomaly_summary = self.anomaly.get_alert_summary(customer_id)
            insights["anomalies"] = {
                "pending_alerts": anomaly_summary.get("pending", 0),
                "critical": anomaly_summary.get("critical_pending", 0),
                "high": anomaly_summary.get("high_pending", 0),
            }
        except Exception as e:
            logger.error(f"Anomaly insights failed: {e}")

        # Generate recommendations
        insights["recommendations"] = self._generate_recommendations(insights)

        return insights

    def _generate_recommendations(self, insights: Dict) -> List[Dict]:
        """Generate recommendations based on insights."""
        recommendations = []

        # Cash flow recommendations
        cf = insights.get("cashflow", {})
        if cf:
            if cf.get("trend") == "decreasing":
                recommendations.append({
                    "type": "cashflow",
                    "priority": "high",
                    "title": "Cash Flow Declining",
                    "description": "Your cash flow trend is decreasing. Review upcoming expenses and accelerate collections.",
                    "action": {"type": "view_cashflow"},
                })

            if cf.get("alerts"):
                recommendations.append({
                    "type": "cashflow",
                    "priority": "medium",
                    "title": f"{len(cf['alerts'])} Cash Flow Alerts",
                    "description": "Review your cash flow forecast for potential issues.",
                    "action": {"type": "view_cashflow"},
                })

        # Anomaly recommendations
        anomalies = insights.get("anomalies", {})
        if anomalies:
            if anomalies.get("critical", 0) > 0:
                recommendations.append({
                    "type": "anomaly",
                    "priority": "critical",
                    "title": f"{anomalies['critical']} Critical Alerts",
                    "description": "You have critical alerts that require immediate attention.",
                    "action": {"type": "view_anomalies"},
                })
            elif anomalies.get("pending_alerts", 0) > 0:
                recommendations.append({
                    "type": "anomaly",
                    "priority": "medium",
                    "title": f"{anomalies['pending_alerts']} Pending Alerts",
                    "description": "Review and address pending anomaly alerts.",
                    "action": {"type": "view_anomalies"},
                })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority"), 4))

        return recommendations[:5]

    async def process_new_transaction(self, customer_id: str, transaction: Dict) -> Dict:
        """Process a new transaction through AI pipeline."""
        results = {}

        # Anomaly detection
        try:
            anomaly_result = await self.anomaly.analyze_transaction(customer_id, transaction)
            results["anomaly_check"] = {
                "is_safe": anomaly_result.data.get("is_safe", True) if anomaly_result.success else True,
                "fraud_score": anomaly_result.data.get("fraud_score", {}).get("fraud_score", 0) if anomaly_result.success else 0,
                "alerts": anomaly_result.data.get("alerts_created", []) if anomaly_result.success else [],
            }
        except Exception as e:
            logger.error(f"Transaction anomaly check failed: {e}")
            results["anomaly_check"] = {"is_safe": True, "error": str(e)}

        return results

    def get_service_status(self) -> Dict:
        """Get status of all AI services."""
        return {
            "cashflow": {
                "enabled": True,
                "status": "operational",
            },
            "ocr": {
                "enabled": True,
                "status": "operational",
            },
            "assistant": {
                "enabled": True,
                "status": "operational",
            },
            "anomaly": {
                "enabled": True,
                "status": "operational",
            },
        }


# Global service instance
ai_service = AIServiceAggregator()
