"""
Payment Analytics Service
"""

from datetime import datetime, timedelta
from typing import Dict, List
from app.services.payment_link_service import payment_link_service
from app.services.refund_service import refund_service


class PaymentAnalyticsService:
    """Payment analytics and reporting"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_summary(self, days: int = 30) -> dict:
        """Get payment summary statistics"""
        stats = payment_link_service.get_statistics()
        refund_stats = refund_service.get_statistics()

        # Collection rate
        total_created = stats["total_links"]
        total_paid = stats["by_status"]["paid"]
        collection_rate = (total_paid / total_created * 100) if total_created > 0 else 0

        # Refund rate
        refund_rate = (refund_stats["total_refunded"] / stats["total_collected"] * 100) if stats["total_collected"] > 0 else 0

        return {
            "period_days": days,
            "total_links_created": total_created,
            "total_paid": total_paid,
            "total_pending": stats["by_status"]["active"],
            "total_expired": stats["by_status"]["expired"],
            "gross_collected": stats["total_collected"],
            "total_fees": stats["total_fees"],
            "net_collected": stats["net_collected"],
            "total_refunded": refund_stats["total_refunded"],
            "collection_rate": round(collection_rate, 1),
            "refund_rate": round(refund_rate, 1),
            "total_views": stats["total_views"],
            "total_attempts": stats["total_attempts"],
            "conversion_rate": stats["conversion_rate"]
        }

    def get_trend(self, days: int = 30, granularity: str = "day") -> List[dict]:
        """Get collection trend over time"""
        # Simulated trend data
        trend = []
        today = datetime.utcnow().date()

        for i in range(days, -1, -1):
            date = today - timedelta(days=i)
            # Generate realistic-looking data
            base = 1000 + (i * 50)
            collected = base + (hash(str(date)) % 500)
            fees = collected * 0.03

            trend.append({
                "date": date.isoformat(),
                "gross": round(collected, 2),
                "fees": round(fees, 2),
                "net": round(collected - fees, 2),
                "count": 3 + (hash(str(date)) % 5)
            })

        return trend

    def get_by_gateway(self) -> List[dict]:
        """Get analytics by payment gateway"""
        links = payment_link_service.list_links(status="paid", limit=1000)["links"]

        by_gateway = {}
        for link in links:
            gateway = link.get("paid_via", "unknown")
            if gateway not in by_gateway:
                by_gateway[gateway] = {
                    "gateway": gateway,
                    "count": 0,
                    "gross": 0,
                    "fees": 0,
                    "net": 0
                }

            by_gateway[gateway]["count"] += 1
            by_gateway[gateway]["gross"] += link.get("paid_amount", 0)
            by_gateway[gateway]["fees"] += link.get("fee_amount", 0)
            by_gateway[gateway]["net"] += link.get("net_amount", 0)

        return [
            {**v, "gross": round(v["gross"], 2), "fees": round(v["fees"], 2), "net": round(v["net"], 2)}
            for v in by_gateway.values()
        ]

    def get_top_clients(self, limit: int = 10) -> List[dict]:
        """Get top paying clients"""
        links = payment_link_service.list_links(status="paid", limit=1000)["links"]

        by_client = {}
        for link in links:
            client = link.get("client_name") or link.get("client_id") or "Unknown"
            if client not in by_client:
                by_client[client] = {
                    "client": client,
                    "count": 0,
                    "total": 0
                }

            by_client[client]["count"] += 1
            by_client[client]["total"] += link.get("paid_amount", 0)

        sorted_clients = sorted(by_client.values(), key=lambda x: x["total"], reverse=True)
        return sorted_clients[:limit]

    def get_fee_report(self, days: int = 30) -> dict:
        """Get fee analysis report"""
        links = payment_link_service.list_links(status="paid", limit=1000)["links"]

        total_gross = sum(l.get("paid_amount", 0) for l in links)
        total_fees = sum(l.get("fee_amount", 0) for l in links)

        by_gateway = {}
        for link in links:
            gateway = link.get("paid_via", "unknown")
            if gateway not in by_gateway:
                by_gateway[gateway] = {"gross": 0, "fees": 0}
            by_gateway[gateway]["gross"] += link.get("paid_amount", 0)
            by_gateway[gateway]["fees"] += link.get("fee_amount", 0)

        gateway_fees = []
        for gateway, data in by_gateway.items():
            rate = (data["fees"] / data["gross"] * 100) if data["gross"] > 0 else 0
            gateway_fees.append({
                "gateway": gateway,
                "gross": round(data["gross"], 2),
                "fees": round(data["fees"], 2),
                "effective_rate": round(rate, 2)
            })

        avg_fee_rate = (total_fees / total_gross * 100) if total_gross > 0 else 0

        return {
            "period_days": days,
            "total_processed": round(total_gross, 2),
            "total_fees": round(total_fees, 2),
            "net_revenue": round(total_gross - total_fees, 2),
            "average_fee_rate": round(avg_fee_rate, 2),
            "by_gateway": gateway_fees
        }


payment_analytics_service = PaymentAnalyticsService()
