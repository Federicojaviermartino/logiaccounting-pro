# Phase 29: Integration Hub - Part 2: Payment Providers

## Overview
This part covers payment gateway integrations including Stripe and PayPal for processing invoice payments.

---

## File 1: Stripe Client
**Path:** `backend/app/integrations/providers/stripe/client.py`

```python
"""
Stripe Integration Client
Handles Stripe API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
    IntegrationError,
    SyncResult,
)
from app.integrations.registry import register_integration

logger = logging.getLogger(__name__)


@register_integration
class StripeIntegration(BaseIntegration):
    """Stripe payment gateway integration."""
    
    PROVIDER_ID = "stripe"
    PROVIDER_NAME = "Stripe"
    DESCRIPTION = "Accept credit cards, ACH, and SEPA payments"
    CATEGORY = IntegrationCategory.PAYMENTS
    ICON_URL = "/icons/integrations/stripe.svg"
    DOCS_URL = "https://stripe.com/docs"
    
    CAPABILITIES = [
        IntegrationCapability.API_KEY,
        IntegrationCapability.WEBHOOKS,
        IntegrationCapability.SYNC,
    ]
    
    # Stripe API base URL
    API_BASE = "https://api.stripe.com/v1"
    
    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._api_key = None
        self._webhook_secret = None
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to Stripe."""
        self._validate_credentials(["api_key"])
        
        self._api_key = credentials.get("api_key")
        self._webhook_secret = credentials.get("webhook_secret")
        self.credentials = credentials
        
        # Test connection
        if await self.test_connection():
            self._set_status(IntegrationStatus.CONNECTED)
            return True
        
        self._set_status(IntegrationStatus.ERROR, "Failed to connect to Stripe")
        return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Stripe."""
        self._api_key = None
        self._webhook_secret = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True
    
    async def test_connection(self) -> bool:
        """Test Stripe connection."""
        try:
            # In production, make actual API call
            # response = await self._request("GET", "/account")
            # return response.get("id") is not None
            
            # Demo mode
            if self._api_key and self._api_key.startswith("sk_"):
                return True
            return False
            
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False
    
    async def refresh_credentials(self) -> Dict[str, Any]:
        """Stripe uses API keys, no refresh needed."""
        return self.credentials
    
    # ==================== Payment Methods ====================
    
    async def create_payment_intent(self, amount: int, currency: str, customer_id: str = None, metadata: Dict = None) -> Dict:
        """Create a payment intent."""
        data = {
            "amount": amount,
            "currency": currency.lower(),
            "automatic_payment_methods": {"enabled": True},
        }
        
        if customer_id:
            data["customer"] = customer_id
        if metadata:
            data["metadata"] = metadata
        
        # In production: return await self._request("POST", "/payment_intents", data)
        
        # Demo response
        return {
            "id": f"pi_{datetime.utcnow().timestamp()}",
            "client_secret": f"pi_secret_{datetime.utcnow().timestamp()}",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
        }
    
    async def create_payment_link(self, invoice_id: str, amount: int, currency: str, description: str) -> Dict:
        """Create a payment link for invoice."""
        # Create price
        price_data = {
            "unit_amount": amount,
            "currency": currency.lower(),
            "product_data": {"name": description},
        }
        
        # Demo response
        return {
            "id": f"plink_{datetime.utcnow().timestamp()}",
            "url": f"https://pay.stripe.com/test_{invoice_id}",
            "active": True,
            "metadata": {"invoice_id": invoice_id},
        }
    
    async def get_payment(self, payment_intent_id: str) -> Dict:
        """Get payment intent details."""
        # In production: return await self._request("GET", f"/payment_intents/{payment_intent_id}")
        
        return {
            "id": payment_intent_id,
            "amount": 10000,
            "currency": "usd",
            "status": "succeeded",
        }
    
    async def refund_payment(self, payment_intent_id: str, amount: int = None, reason: str = None) -> Dict:
        """Refund a payment."""
        data = {"payment_intent": payment_intent_id}
        if amount:
            data["amount"] = amount
        if reason:
            data["reason"] = reason
        
        # Demo response
        return {
            "id": f"re_{datetime.utcnow().timestamp()}",
            "payment_intent": payment_intent_id,
            "amount": amount or 10000,
            "status": "succeeded",
        }
    
    # ==================== Customer Methods ====================
    
    async def create_customer(self, email: str, name: str = None, metadata: Dict = None) -> Dict:
        """Create a Stripe customer."""
        data = {"email": email}
        if name:
            data["name"] = name
        if metadata:
            data["metadata"] = metadata
        
        # Demo response
        return {
            "id": f"cus_{datetime.utcnow().timestamp()}",
            "email": email,
            "name": name,
            "created": int(datetime.utcnow().timestamp()),
        }
    
    async def get_customer(self, customer_id: str) -> Dict:
        """Get customer details."""
        return {
            "id": customer_id,
            "email": "customer@example.com",
            "name": "Test Customer",
        }
    
    async def update_customer(self, customer_id: str, data: Dict) -> Dict:
        """Update customer details."""
        return {"id": customer_id, **data}
    
    async def list_customers(self, limit: int = 100, starting_after: str = None) -> Dict:
        """List customers."""
        return {
            "data": [],
            "has_more": False,
        }
    
    # ==================== Invoice Methods ====================
    
    async def create_invoice(self, customer_id: str, items: List[Dict], metadata: Dict = None) -> Dict:
        """Create a Stripe invoice."""
        return {
            "id": f"in_{datetime.utcnow().timestamp()}",
            "customer": customer_id,
            "status": "draft",
            "total": sum(item.get("amount", 0) for item in items),
        }
    
    async def finalize_invoice(self, invoice_id: str) -> Dict:
        """Finalize and send invoice."""
        return {
            "id": invoice_id,
            "status": "open",
            "hosted_invoice_url": f"https://invoice.stripe.com/{invoice_id}",
        }
    
    # ==================== Sync Methods ====================
    
    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with Stripe."""
        result = SyncResult(entity_type, direction)
        
        try:
            if entity_type == "customers" and direction == "pull":
                await self._sync_customers_from_stripe(result)
            elif entity_type == "payments" and direction == "pull":
                await self._sync_payments_from_stripe(result)
            
            result.complete()
            
        except Exception as e:
            result.errors.append(str(e))
            result.complete()
        
        return result
    
    async def _sync_customers_from_stripe(self, result: SyncResult):
        """Pull customers from Stripe."""
        customers = await self.list_customers()
        
        for customer in customers.get("data", []):
            # In production: create/update local customer
            result.updated += 1
    
    async def _sync_payments_from_stripe(self, result: SyncResult):
        """Pull payments from Stripe."""
        # In production: fetch and sync payment intents
        result.updated += 0
    
    # ==================== API Helper ====================
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Stripe."""
        import aiohttp
        
        url = f"{self.API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, data=data) as response:
                result = await response.json()
                
                if response.status >= 400:
                    raise IntegrationError(
                        message=result.get("error", {}).get("message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=result.get("error", {}).get("code"),
                        details=result,
                    )
                
                return result
```

---

## File 2: Stripe Webhooks
**Path:** `backend/app/integrations/providers/stripe/webhooks.py`

```python
"""
Stripe Webhook Handler
Processes incoming Stripe webhooks
"""

from typing import Dict, Any
from datetime import datetime
import hmac
import hashlib
import logging

from app.integrations.base import WebhookEvent
from app.services.integrations.webhook_service import webhook_service

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handles Stripe webhook events."""
    
    # Stripe event types we handle
    SUPPORTED_EVENTS = [
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.canceled",
        "charge.refunded",
        "charge.dispute.created",
        "customer.created",
        "customer.updated",
        "customer.deleted",
        "invoice.paid",
        "invoice.payment_failed",
        "invoice.finalized",
        "checkout.session.completed",
    ]
    
    def __init__(self, webhook_secret: str = None):
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True
        
        try:
            # Parse signature header
            # Format: t=timestamp,v1=signature
            parts = dict(item.split("=") for item in signature.split(","))
            timestamp = parts.get("t")
            sig = parts.get("v1")
            
            if not timestamp or not sig:
                return False
            
            # Compute expected signature
            signed_payload = f"{timestamp}.{payload.decode()}"
            expected_sig = hmac.new(
                self.webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            
            return hmac.compare_digest(expected_sig, sig)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    async def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """Process incoming Stripe webhook."""
        event_type = payload.get("type")
        event_data = payload.get("data", {}).get("object", {})
        event_id = payload.get("id")
        
        logger.info(f"[Stripe] Received webhook: {event_type} ({event_id})")
        
        # Create webhook event record
        event = WebhookEvent(
            provider="stripe",
            event_type=event_type,
            payload=event_data,
        )
        
        try:
            # Route to specific handler
            handler = self._get_handler(event_type)
            if handler:
                result = await handler(event_data)
                event.processed = True
                return {"status": "processed", "result": result}
            else:
                logger.info(f"[Stripe] No handler for event: {event_type}")
                return {"status": "ignored", "reason": "No handler"}
                
        except Exception as e:
            event.error = str(e)
            logger.error(f"[Stripe] Webhook handler error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_handler(self, event_type: str):
        """Get handler for event type."""
        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "charge.refunded": self._handle_refund,
            "charge.dispute.created": self._handle_dispute,
            "customer.created": self._handle_customer_created,
            "invoice.paid": self._handle_invoice_paid,
            "checkout.session.completed": self._handle_checkout_completed,
        }
        return handlers.get(event_type)
    
    async def _handle_payment_succeeded(self, data: Dict) -> Dict:
        """Handle successful payment."""
        payment_intent_id = data.get("id")
        amount = data.get("amount")
        currency = data.get("currency")
        customer_id = data.get("customer")
        metadata = data.get("metadata", {})
        
        invoice_id = metadata.get("invoice_id")
        
        logger.info(f"[Stripe] Payment succeeded: {payment_intent_id}, amount: {amount}")
        
        # Emit internal event
        if invoice_id:
            await webhook_service.emit(
                "payment.received",
                customer_id=metadata.get("logiaccounting_customer_id", "unknown"),
                payload={
                    "invoice_id": invoice_id,
                    "payment_id": payment_intent_id,
                    "amount": amount / 100,  # Convert from cents
                    "currency": currency.upper(),
                    "method": "stripe",
                    "stripe_payment_intent": payment_intent_id,
                },
            )
        
        return {"payment_intent_id": payment_intent_id, "status": "processed"}
    
    async def _handle_payment_failed(self, data: Dict) -> Dict:
        """Handle failed payment."""
        payment_intent_id = data.get("id")
        error = data.get("last_payment_error", {})
        metadata = data.get("metadata", {})
        
        logger.warning(f"[Stripe] Payment failed: {payment_intent_id}")
        
        if metadata.get("logiaccounting_customer_id"):
            await webhook_service.emit(
                "payment.failed",
                customer_id=metadata["logiaccounting_customer_id"],
                payload={
                    "payment_id": payment_intent_id,
                    "error_code": error.get("code"),
                    "error_message": error.get("message"),
                },
            )
        
        return {"payment_intent_id": payment_intent_id, "status": "failed"}
    
    async def _handle_refund(self, data: Dict) -> Dict:
        """Handle refund."""
        charge_id = data.get("id")
        refunds = data.get("refunds", {}).get("data", [])
        
        for refund in refunds:
            logger.info(f"[Stripe] Refund processed: {refund.get('id')}")
        
        return {"charge_id": charge_id, "refunds": len(refunds)}
    
    async def _handle_dispute(self, data: Dict) -> Dict:
        """Handle dispute/chargeback."""
        dispute_id = data.get("id")
        amount = data.get("amount")
        reason = data.get("reason")
        
        logger.warning(f"[Stripe] Dispute created: {dispute_id}, reason: {reason}")
        
        # In production: create internal dispute record, notify admin
        
        return {"dispute_id": dispute_id, "reason": reason}
    
    async def _handle_customer_created(self, data: Dict) -> Dict:
        """Handle new Stripe customer."""
        customer_id = data.get("id")
        email = data.get("email")
        
        logger.info(f"[Stripe] Customer created: {customer_id}")
        
        return {"customer_id": customer_id, "email": email}
    
    async def _handle_invoice_paid(self, data: Dict) -> Dict:
        """Handle paid Stripe invoice."""
        invoice_id = data.get("id")
        amount_paid = data.get("amount_paid")
        
        logger.info(f"[Stripe] Invoice paid: {invoice_id}")
        
        return {"invoice_id": invoice_id, "amount": amount_paid}
    
    async def _handle_checkout_completed(self, data: Dict) -> Dict:
        """Handle completed checkout session."""
        session_id = data.get("id")
        payment_status = data.get("payment_status")
        metadata = data.get("metadata", {})
        
        logger.info(f"[Stripe] Checkout completed: {session_id}")
        
        return {"session_id": session_id, "payment_status": payment_status}


# Handler instance
stripe_webhook_handler = StripeWebhookHandler()
```

---

## File 3: Stripe Init
**Path:** `backend/app/integrations/providers/stripe/__init__.py`

```python
"""
Stripe Integration Provider
"""

from app.integrations.providers.stripe.client import StripeIntegration
from app.integrations.providers.stripe.webhooks import stripe_webhook_handler, StripeWebhookHandler


__all__ = [
    'StripeIntegration',
    'stripe_webhook_handler',
    'StripeWebhookHandler',
]
```

---

## File 4: PayPal Client
**Path:** `backend/app/integrations/providers/paypal/client.py`

```python
"""
PayPal Integration Client
Handles PayPal API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import base64

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
    IntegrationError,
    SyncResult,
)
from app.integrations.registry import register_integration

logger = logging.getLogger(__name__)


@register_integration
class PayPalIntegration(BaseIntegration):
    """PayPal payment gateway integration."""
    
    PROVIDER_ID = "paypal"
    PROVIDER_NAME = "PayPal"
    DESCRIPTION = "Accept PayPal and credit card payments"
    CATEGORY = IntegrationCategory.PAYMENTS
    ICON_URL = "/icons/integrations/paypal.svg"
    DOCS_URL = "https://developer.paypal.com/docs"
    
    CAPABILITIES = [
        IntegrationCapability.OAUTH,
        IntegrationCapability.WEBHOOKS,
    ]
    
    # PayPal API URLs
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    LIVE_URL = "https://api-m.paypal.com"
    
    # OAuth URLs
    OAUTH_AUTHORIZE_URL = "https://www.paypal.com/signin/authorize"
    OAUTH_TOKEN_URL = "https://api-m.paypal.com/v1/oauth2/token"
    
    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._client_id = None
        self._client_secret = None
        self._access_token = None
        self._token_expires_at = None
        self._sandbox = True
    
    @property
    def api_base(self) -> str:
        return self.SANDBOX_URL if self._sandbox else self.LIVE_URL
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to PayPal."""
        self._validate_credentials(["client_id", "client_secret"])
        
        self._client_id = credentials.get("client_id")
        self._client_secret = credentials.get("client_secret")
        self._sandbox = credentials.get("sandbox", True)
        self.credentials = credentials
        
        # Get access token
        if await self._get_access_token():
            self._set_status(IntegrationStatus.CONNECTED)
            return True
        
        self._set_status(IntegrationStatus.ERROR, "Failed to authenticate with PayPal")
        return False
    
    async def disconnect(self) -> bool:
        """Disconnect from PayPal."""
        self._client_id = None
        self._client_secret = None
        self._access_token = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True
    
    async def test_connection(self) -> bool:
        """Test PayPal connection."""
        try:
            if not self._access_token:
                await self._get_access_token()
            return self._access_token is not None
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False
    
    async def refresh_credentials(self) -> Dict[str, Any]:
        """Refresh access token."""
        if await self._get_access_token():
            return {
                **self.credentials,
                "access_token": self._access_token,
            }
        return self.credentials
    
    async def _get_access_token(self) -> bool:
        """Get PayPal access token."""
        try:
            # In production, make actual OAuth request
            # auth = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
            # response = await self._request_token(auth)
            
            # Demo mode
            if self._client_id and self._client_secret:
                self._access_token = f"A21AADemo_{datetime.utcnow().timestamp()}"
                self._token_expires_at = datetime.utcnow()
                return True
            
            return False
            
        except Exception as e:
            self._log_error(f"Failed to get access token: {e}")
            return False
    
    # ==================== Order Methods ====================
    
    async def create_order(self, amount: str, currency: str, description: str, invoice_id: str = None) -> Dict:
        """Create a PayPal order."""
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": amount,
                },
                "description": description,
            }],
        }
        
        if invoice_id:
            order_data["purchase_units"][0]["invoice_id"] = invoice_id
        
        # Demo response
        return {
            "id": f"ORDER-{datetime.utcnow().timestamp()}",
            "status": "CREATED",
            "links": [
                {
                    "href": f"https://www.sandbox.paypal.com/checkoutnow?token=ORDER-{datetime.utcnow().timestamp()}",
                    "rel": "approve",
                    "method": "GET",
                },
            ],
        }
    
    async def capture_order(self, order_id: str) -> Dict:
        """Capture payment for an order."""
        # Demo response
        return {
            "id": order_id,
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": f"CAPTURE-{datetime.utcnow().timestamp()}",
                        "status": "COMPLETED",
                        "amount": {"currency_code": "USD", "value": "100.00"},
                    }],
                },
            }],
        }
    
    async def get_order(self, order_id: str) -> Dict:
        """Get order details."""
        return {
            "id": order_id,
            "status": "APPROVED",
        }
    
    async def refund_capture(self, capture_id: str, amount: str = None, currency: str = "USD") -> Dict:
        """Refund a captured payment."""
        refund_data = {}
        if amount:
            refund_data["amount"] = {
                "currency_code": currency.upper(),
                "value": amount,
            }
        
        return {
            "id": f"REFUND-{datetime.utcnow().timestamp()}",
            "status": "COMPLETED",
            "amount": {"currency_code": currency, "value": amount or "100.00"},
        }
    
    # ==================== Invoice Methods ====================
    
    async def create_invoice(self, recipient_email: str, items: List[Dict], due_date: str = None) -> Dict:
        """Create a PayPal invoice."""
        total = sum(float(item.get("amount", 0)) * int(item.get("quantity", 1)) for item in items)
        
        return {
            "id": f"INV2-{datetime.utcnow().timestamp()}",
            "status": "DRAFT",
            "detail": {
                "invoice_number": f"INV-{int(datetime.utcnow().timestamp())}",
                "currency_code": "USD",
            },
            "amount": {"value": str(total)},
        }
    
    async def send_invoice(self, invoice_id: str) -> Dict:
        """Send invoice to recipient."""
        return {
            "href": f"https://www.paypal.com/invoice/payerView/details/{invoice_id}",
        }
    
    # ==================== Sync Methods ====================
    
    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with PayPal."""
        result = SyncResult(entity_type, direction)
        
        try:
            if entity_type == "payments" and direction == "pull":
                await self._sync_transactions(result)
            
            result.complete()
            
        except Exception as e:
            result.errors.append(str(e))
            result.complete()
        
        return result
    
    async def _sync_transactions(self, result: SyncResult):
        """Sync transactions from PayPal."""
        # In production: fetch transaction history
        result.updated += 0
    
    # ==================== API Helper ====================
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to PayPal."""
        import aiohttp
        
        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                result = await response.json()
                
                if response.status >= 400:
                    raise IntegrationError(
                        message=result.get("message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=result.get("name"),
                        details=result,
                    )
                
                return result
```

---

## File 5: PayPal Webhooks
**Path:** `backend/app/integrations/providers/paypal/webhooks.py`

```python
"""
PayPal Webhook Handler
Processes incoming PayPal webhooks
"""

from typing import Dict, Any
from datetime import datetime
import logging

from app.integrations.base import WebhookEvent
from app.services.integrations.webhook_service import webhook_service

logger = logging.getLogger(__name__)


class PayPalWebhookHandler:
    """Handles PayPal webhook events."""
    
    SUPPORTED_EVENTS = [
        "PAYMENT.CAPTURE.COMPLETED",
        "PAYMENT.CAPTURE.DENIED",
        "PAYMENT.CAPTURE.REFUNDED",
        "CHECKOUT.ORDER.APPROVED",
        "CHECKOUT.ORDER.COMPLETED",
        "INVOICING.INVOICE.PAID",
        "INVOICING.INVOICE.CANCELLED",
        "CUSTOMER.DISPUTE.CREATED",
    ]
    
    def __init__(self, webhook_id: str = None):
        self.webhook_id = webhook_id
    
    async def verify_signature(self, payload: bytes, headers: Dict) -> bool:
        """Verify PayPal webhook signature."""
        # PayPal signature verification requires API call
        # In production: verify with PayPal's verification endpoint
        return True
    
    async def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """Process incoming PayPal webhook."""
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})
        event_id = payload.get("id")
        
        logger.info(f"[PayPal] Received webhook: {event_type} ({event_id})")
        
        event = WebhookEvent(
            provider="paypal",
            event_type=event_type,
            payload=resource,
        )
        
        try:
            handler = self._get_handler(event_type)
            if handler:
                result = await handler(resource)
                event.processed = True
                return {"status": "processed", "result": result}
            else:
                return {"status": "ignored"}
                
        except Exception as e:
            event.error = str(e)
            logger.error(f"[PayPal] Webhook handler error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_handler(self, event_type: str):
        """Get handler for event type."""
        handlers = {
            "PAYMENT.CAPTURE.COMPLETED": self._handle_capture_completed,
            "PAYMENT.CAPTURE.DENIED": self._handle_capture_denied,
            "PAYMENT.CAPTURE.REFUNDED": self._handle_capture_refunded,
            "CHECKOUT.ORDER.COMPLETED": self._handle_order_completed,
            "INVOICING.INVOICE.PAID": self._handle_invoice_paid,
            "CUSTOMER.DISPUTE.CREATED": self._handle_dispute,
        }
        return handlers.get(event_type)
    
    async def _handle_capture_completed(self, data: Dict) -> Dict:
        """Handle completed payment capture."""
        capture_id = data.get("id")
        amount = data.get("amount", {})
        
        logger.info(f"[PayPal] Capture completed: {capture_id}")
        
        # Extract custom invoice ID from custom_id field
        custom_id = data.get("custom_id", "")
        if custom_id:
            await webhook_service.emit(
                "payment.received",
                customer_id="unknown",  # Would need to look up
                payload={
                    "payment_id": capture_id,
                    "amount": float(amount.get("value", 0)),
                    "currency": amount.get("currency_code", "USD"),
                    "method": "paypal",
                    "paypal_capture_id": capture_id,
                },
            )
        
        return {"capture_id": capture_id, "status": "completed"}
    
    async def _handle_capture_denied(self, data: Dict) -> Dict:
        """Handle denied payment."""
        capture_id = data.get("id")
        
        logger.warning(f"[PayPal] Capture denied: {capture_id}")
        
        return {"capture_id": capture_id, "status": "denied"}
    
    async def _handle_capture_refunded(self, data: Dict) -> Dict:
        """Handle refund."""
        capture_id = data.get("id")
        
        logger.info(f"[PayPal] Capture refunded: {capture_id}")
        
        return {"capture_id": capture_id, "status": "refunded"}
    
    async def _handle_order_completed(self, data: Dict) -> Dict:
        """Handle completed order."""
        order_id = data.get("id")
        
        logger.info(f"[PayPal] Order completed: {order_id}")
        
        return {"order_id": order_id, "status": "completed"}
    
    async def _handle_invoice_paid(self, data: Dict) -> Dict:
        """Handle paid invoice."""
        invoice_id = data.get("id")
        
        logger.info(f"[PayPal] Invoice paid: {invoice_id}")
        
        return {"invoice_id": invoice_id, "status": "paid"}
    
    async def _handle_dispute(self, data: Dict) -> Dict:
        """Handle dispute."""
        dispute_id = data.get("dispute_id")
        reason = data.get("reason")
        
        logger.warning(f"[PayPal] Dispute created: {dispute_id}, reason: {reason}")
        
        return {"dispute_id": dispute_id, "reason": reason}


# Handler instance
paypal_webhook_handler = PayPalWebhookHandler()
```

---

## File 6: PayPal Init
**Path:** `backend/app/integrations/providers/paypal/__init__.py`

```python
"""
PayPal Integration Provider
"""

from app.integrations.providers.paypal.client import PayPalIntegration
from app.integrations.providers.paypal.webhooks import paypal_webhook_handler, PayPalWebhookHandler


__all__ = [
    'PayPalIntegration',
    'paypal_webhook_handler',
    'PayPalWebhookHandler',
]
```

---

## Summary Part 2

| File | Description | Lines |
|------|-------------|-------|
| `stripe/client.py` | Stripe API client | ~280 |
| `stripe/webhooks.py` | Stripe webhook handler | ~220 |
| `stripe/__init__.py` | Stripe module init | ~15 |
| `paypal/client.py` | PayPal API client | ~260 |
| `paypal/webhooks.py` | PayPal webhook handler | ~180 |
| `paypal/__init__.py` | PayPal module init | ~15 |
| **Total** | | **~970 lines** |
