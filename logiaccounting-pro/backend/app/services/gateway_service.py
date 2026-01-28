"""
Payment Gateway Service
Manages gateway configurations and connections
"""

from datetime import datetime
from typing import Dict, List, Optional
import hashlib
from app.utils.datetime_utils import utc_now
import base64


class GatewayService:
    """Manages payment gateway configurations"""

    _instance = None
    _gateways: Dict[str, dict] = {}

    SUPPORTED_GATEWAYS = {
        "stripe": {
            "name": "Stripe",
            "icon": "💳",
            "supported_currencies": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF"],
            "supported_methods": ["card", "apple_pay", "google_pay"],
            "fee_percentage": 2.9,
            "fee_fixed": 0.30,
            "fee_currency": "USD"
        },
        "paypal": {
            "name": "PayPal",
            "icon": "🅿️",
            "supported_currencies": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "BRL", "MXN"],
            "supported_methods": ["paypal", "card"],
            "fee_percentage": 3.49,
            "fee_fixed": 0.49,
            "fee_currency": "USD"
        },
        "mercadopago": {
            "name": "MercadoPago",
            "icon": "💰",
            "supported_currencies": ["ARS", "BRL", "MXN", "CLP", "COP", "PEN", "UYU"],
            "supported_methods": ["card", "bank_transfer", "cash"],
            "fee_percentage": 4.99,
            "fee_fixed": 0,
            "fee_currency": "ARS"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._gateways = {}
            cls._init_default_gateways()
        return cls._instance

    @classmethod
    def _init_default_gateways(cls):
        """Initialize default gateway configurations"""
        for provider, info in cls.SUPPORTED_GATEWAYS.items():
            cls._gateways[provider] = {
                "id": f"GW-{provider.upper()}",
                "provider": provider,
                "name": info["name"],
                "icon": info["icon"],
                "enabled": True,
                "mode": "test",  # test or live
                "credentials": {
                    "public_key": f"pk_test_{provider}_demo",
                    "secret_key": f"sk_test_{provider}_demo",
                    "webhook_secret": f"whsec_{provider}_demo"
                },
                "supported_currencies": info["supported_currencies"],
                "supported_methods": info["supported_methods"],
                "fee_percentage": info["fee_percentage"],
                "fee_fixed": info["fee_fixed"],
                "fee_currency": info["fee_currency"],
                "is_default": provider == "stripe",
                "webhook_url": f"/api/v1/webhooks/{provider}",
                "last_tested": None,
                "test_status": None,
                "created_at": utc_now().isoformat()
            }

    def get_gateway(self, provider: str) -> Optional[dict]:
        """Get gateway configuration"""
        gw = self._gateways.get(provider)
        if gw:
            # Return copy without secret credentials
            return self._mask_credentials(gw.copy())
        return None

    def _mask_credentials(self, gateway: dict) -> dict:
        """Mask sensitive credentials"""
        if "credentials" in gateway:
            masked = {}
            for key, value in gateway["credentials"].items():
                if key in ["secret_key", "webhook_secret"]:
                    masked[key] = value[:8] + "..." if value else None
                else:
                    masked[key] = value
            gateway["credentials"] = masked
        return gateway

    def list_gateways(self, enabled_only: bool = False) -> List[dict]:
        """List all gateways"""
        gateways = list(self._gateways.values())
        if enabled_only:
            gateways = [g for g in gateways if g["enabled"]]
        return [self._mask_credentials(g.copy()) for g in gateways]

    def update_gateway(self, provider: str, updates: dict) -> Optional[dict]:
        """Update gateway configuration"""
        if provider not in self._gateways:
            return None

        gateway = self._gateways[provider]

        # Handle credential updates
        if "credentials" in updates:
            for key, value in updates["credentials"].items():
                if value and not value.endswith("..."):
                    gateway["credentials"][key] = value
            del updates["credentials"]

        # Handle is_default (only one can be default)
        if updates.get("is_default"):
            for gw in self._gateways.values():
                gw["is_default"] = False

        # Update other fields
        for key, value in updates.items():
            if key in gateway and key not in ["id", "provider", "created_at"]:
                gateway[key] = value

        return self._mask_credentials(gateway.copy())

    def test_connection(self, provider: str) -> dict:
        """Test gateway connection (simulated)"""
        if provider not in self._gateways:
            return {"success": False, "error": "Gateway not found"}

        gateway = self._gateways[provider]

        # Simulate connection test
        # In production, this would make API calls to the gateway
        if gateway["mode"] == "test":
            # Test mode always succeeds
            success = True
            message = "Test connection successful (demo mode)"
        else:
            # Simulate live mode check
            has_credentials = (
                gateway["credentials"].get("public_key") and
                gateway["credentials"].get("secret_key")
            )
            success = has_credentials
            message = "Connection successful" if success else "Invalid credentials"

        # Update test status
        gateway["last_tested"] = utc_now().isoformat()
        gateway["test_status"] = "success" if success else "failed"

        return {
            "success": success,
            "message": message,
            "provider": provider,
            "mode": gateway["mode"],
            "tested_at": gateway["last_tested"]
        }

    def get_default_gateway(self) -> Optional[dict]:
        """Get the default gateway"""
        for gw in self._gateways.values():
            if gw["is_default"] and gw["enabled"]:
                return self._mask_credentials(gw.copy())
        # Fallback to first enabled gateway
        for gw in self._gateways.values():
            if gw["enabled"]:
                return self._mask_credentials(gw.copy())
        return None

    def get_gateways_for_currency(self, currency: str) -> List[dict]:
        """Get gateways that support a specific currency"""
        return [
            self._mask_credentials(gw.copy())
            for gw in self._gateways.values()
            if gw["enabled"] and currency in gw["supported_currencies"]
        ]

    def calculate_fee(self, provider: str, amount: float) -> dict:
        """Calculate gateway fee for an amount"""
        gateway = self._gateways.get(provider)
        if not gateway:
            return {"error": "Gateway not found"}

        fee_percentage = gateway["fee_percentage"]
        fee_fixed = gateway["fee_fixed"]

        fee = (amount * fee_percentage / 100) + fee_fixed
        net = amount - fee

        return {
            "gross_amount": round(amount, 2),
            "fee_percentage": fee_percentage,
            "fee_fixed": fee_fixed,
            "total_fee": round(fee, 2),
            "net_amount": round(net, 2)
        }


gateway_service = GatewayService()
