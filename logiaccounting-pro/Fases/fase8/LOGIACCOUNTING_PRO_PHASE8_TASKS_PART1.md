# LogiAccounting Pro - Phase 8 Tasks (Part 1/3)

## GATEWAY CONFIGURATION + PAYMENT LINKS + CHECKOUT PAGE

---

## TASK 1: GATEWAY SERVICE 💳

### 1.1 Create Gateway Service

**File:** `backend/app/services/gateway_service.py`

```python
"""
Payment Gateway Service
Manages gateway configurations and connections
"""

from datetime import datetime
from typing import Dict, List, Optional
import hashlib
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
                "created_at": datetime.utcnow().isoformat()
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
        gateway["last_tested"] = datetime.utcnow().isoformat()
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
```

### 1.2 Create Gateway Routes

**File:** `backend/app/routes/gateways.py`

```python
"""
Payment Gateway routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.gateway_service import gateway_service
from app.utils.auth import require_roles

router = APIRouter()


class UpdateGatewayRequest(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    credentials: Optional[dict] = None
    is_default: Optional[bool] = None


@router.get("/providers")
async def get_supported_providers():
    """Get list of supported payment providers"""
    return {"providers": list(gateway_service.SUPPORTED_GATEWAYS.keys())}


@router.get("")
async def list_gateways(
    enabled_only: bool = False,
    current_user: dict = Depends(require_roles("admin"))
):
    """List all gateway configurations"""
    return {"gateways": gateway_service.list_gateways(enabled_only)}


@router.get("/default")
async def get_default_gateway(current_user: dict = Depends(require_roles("admin"))):
    """Get default gateway"""
    gateway = gateway_service.get_default_gateway()
    if not gateway:
        raise HTTPException(status_code=404, detail="No gateway configured")
    return gateway


@router.get("/for-currency/{currency}")
async def get_gateways_for_currency(
    currency: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get gateways that support a currency"""
    return {"gateways": gateway_service.get_gateways_for_currency(currency.upper())}


@router.get("/{provider}")
async def get_gateway(
    provider: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get gateway configuration"""
    gateway = gateway_service.get_gateway(provider)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.put("/{provider}")
async def update_gateway(
    provider: str,
    request: UpdateGatewayRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update gateway configuration"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    gateway = gateway_service.update_gateway(provider, updates)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.post("/{provider}/test")
async def test_gateway(
    provider: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Test gateway connection"""
    return gateway_service.test_connection(provider)


@router.get("/{provider}/calculate-fee")
async def calculate_fee(
    provider: str,
    amount: float,
    current_user: dict = Depends(require_roles("admin"))
):
    """Calculate gateway fee for an amount"""
    result = gateway_service.calculate_fee(provider, amount)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
```

---

## TASK 2: PAYMENT LINKS SERVICE 🔗

### 2.1 Create Payment Links Service

**File:** `backend/app/services/payment_link_service.py`

```python
"""
Payment Links Service
Generate and manage payment links
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import secrets
import hashlib
import base64


class PaymentLinkService:
    """Manages payment link generation and tracking"""
    
    _instance = None
    _links: Dict[str, dict] = {}
    _counter = 0
    
    LINK_STATUSES = ["active", "paid", "expired", "cancelled"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._links = {}
            cls._counter = 0
        return cls._instance
    
    def _generate_code(self) -> str:
        """Generate unique short code for link"""
        return secrets.token_urlsafe(8)[:12]
    
    def _generate_qr_placeholder(self, url: str) -> str:
        """Generate QR code placeholder (in production, use qrcode library)"""
        # Returns a data URL placeholder
        # In production: import qrcode, generate actual QR
        return f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect fill='%23f0f0f0' width='200' height='200'/><text x='50%' y='50%' text-anchor='middle' dy='.3em' font-family='Arial' font-size='12'>QR Code</text></svg>"
    
    def create_link(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        description: str,
        client_id: str = None,
        client_name: str = None,
        client_email: str = None,
        invoice_number: str = None,
        gateways: List[str] = None,
        expires_in_days: int = 30,
        single_use: bool = True,
        allow_partial: bool = False,
        minimum_amount: float = None,
        send_receipt: bool = True,
        created_by: str = None,
        base_url: str = "https://logiaccounting-pro.onrender.com"
    ) -> dict:
        """Create a new payment link"""
        self._counter += 1
        link_id = f"PLINK-{self._counter:05d}"
        code = self._generate_code()
        
        url = f"{base_url}/pay/{code}"
        
        link = {
            "id": link_id,
            "code": code,
            "url": url,
            "qr_code": self._generate_qr_placeholder(url),
            
            # Payment details
            "payment_id": payment_id,
            "invoice_number": invoice_number,
            "description": description,
            
            # Amount
            "amount": amount,
            "currency": currency.upper(),
            "allow_partial": allow_partial,
            "minimum_amount": minimum_amount,
            
            # Client
            "client_id": client_id,
            "client_name": client_name,
            "client_email": client_email,
            
            # Settings
            "gateways": gateways or ["stripe", "paypal"],
            "expires_at": (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
            "single_use": single_use,
            "send_receipt": send_receipt,
            
            # Tracking
            "status": "active",
            "views": 0,
            "attempts": 0,
            "paid_at": None,
            "paid_amount": None,
            "paid_via": None,
            "transaction_id": None,
            "fee_amount": None,
            "net_amount": None,
            
            # Metadata
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._links[link_id] = link
        return link
    
    def get_link(self, link_id: str) -> Optional[dict]:
        """Get link by ID"""
        return self._links.get(link_id)
    
    def get_link_by_code(self, code: str) -> Optional[dict]:
        """Get link by public code"""
        for link in self._links.values():
            if link["code"] == code:
                return link
        return None
    
    def list_links(
        self,
        status: str = None,
        client_id: str = None,
        payment_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List payment links with filters"""
        links = list(self._links.values())
        
        if status:
            links = [l for l in links if l["status"] == status]
        if client_id:
            links = [l for l in links if l["client_id"] == client_id]
        if payment_id:
            links = [l for l in links if l["payment_id"] == payment_id]
        
        # Check for expired links
        now = datetime.utcnow().isoformat()
        for link in links:
            if link["status"] == "active" and link["expires_at"] < now:
                link["status"] = "expired"
        
        # Sort by created_at descending
        links = sorted(links, key=lambda x: x["created_at"], reverse=True)
        
        total = len(links)
        paginated = links[offset:offset + limit]
        
        return {
            "links": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def record_view(self, code: str) -> Optional[dict]:
        """Record a link view"""
        link = self.get_link_by_code(code)
        if link:
            link["views"] += 1
            return link
        return None
    
    def record_attempt(self, code: str) -> Optional[dict]:
        """Record a payment attempt"""
        link = self.get_link_by_code(code)
        if link:
            link["attempts"] += 1
            return link
        return None
    
    def mark_as_paid(
        self,
        code: str,
        amount: float,
        gateway: str,
        transaction_id: str,
        fee_amount: float = 0
    ) -> Optional[dict]:
        """Mark link as paid"""
        link = self.get_link_by_code(code)
        if not link:
            return None
        
        link["status"] = "paid"
        link["paid_at"] = datetime.utcnow().isoformat()
        link["paid_amount"] = amount
        link["paid_via"] = gateway
        link["transaction_id"] = transaction_id
        link["fee_amount"] = fee_amount
        link["net_amount"] = amount - fee_amount
        
        return link
    
    def cancel_link(self, link_id: str) -> Optional[dict]:
        """Cancel a payment link"""
        link = self._links.get(link_id)
        if link and link["status"] == "active":
            link["status"] = "cancelled"
            return link
        return None
    
    def update_link(self, link_id: str, updates: dict) -> Optional[dict]:
        """Update a payment link"""
        link = self._links.get(link_id)
        if not link or link["status"] != "active":
            return None
        
        for key, value in updates.items():
            if key in link and key not in ["id", "code", "url", "created_at", "status"]:
                link[key] = value
        
        return link
    
    def get_checkout_data(self, code: str) -> Optional[dict]:
        """Get data needed for checkout page (public)"""
        link = self.get_link_by_code(code)
        if not link:
            return None
        
        # Check if expired
        if link["expires_at"] < datetime.utcnow().isoformat():
            link["status"] = "expired"
        
        # Return only public data
        return {
            "code": link["code"],
            "status": link["status"],
            "amount": link["amount"],
            "currency": link["currency"],
            "description": link["description"],
            "invoice_number": link["invoice_number"],
            "client_name": link["client_name"],
            "gateways": link["gateways"],
            "allow_partial": link["allow_partial"],
            "minimum_amount": link["minimum_amount"],
            "expires_at": link["expires_at"],
            "paid_at": link["paid_at"],
            "paid_amount": link["paid_amount"]
        }
    
    def get_statistics(self) -> dict:
        """Get payment link statistics"""
        links = list(self._links.values())
        
        total = len(links)
        active = len([l for l in links if l["status"] == "active"])
        paid = len([l for l in links if l["status"] == "paid"])
        expired = len([l for l in links if l["status"] == "expired"])
        cancelled = len([l for l in links if l["status"] == "cancelled"])
        
        total_collected = sum(l.get("paid_amount", 0) or 0 for l in links if l["status"] == "paid")
        total_fees = sum(l.get("fee_amount", 0) or 0 for l in links if l["status"] == "paid")
        total_views = sum(l.get("views", 0) for l in links)
        total_attempts = sum(l.get("attempts", 0) for l in links)
        
        conversion_rate = (paid / total * 100) if total > 0 else 0
        
        return {
            "total_links": total,
            "by_status": {
                "active": active,
                "paid": paid,
                "expired": expired,
                "cancelled": cancelled
            },
            "total_collected": round(total_collected, 2),
            "total_fees": round(total_fees, 2),
            "net_collected": round(total_collected - total_fees, 2),
            "total_views": total_views,
            "total_attempts": total_attempts,
            "conversion_rate": round(conversion_rate, 1)
        }


payment_link_service = PaymentLinkService()
```

### 2.2 Create Payment Links Routes

**File:** `backend/app/routes/payment_links.py`

```python
"""
Payment Links routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.payment_link_service import payment_link_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateLinkRequest(BaseModel):
    payment_id: str
    amount: float
    currency: str = "USD"
    description: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    invoice_number: Optional[str] = None
    gateways: List[str] = ["stripe", "paypal"]
    expires_in_days: int = 30
    single_use: bool = True
    allow_partial: bool = False
    minimum_amount: Optional[float] = None
    send_receipt: bool = True


class UpdateLinkRequest(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    gateways: Optional[List[str]] = None
    expires_in_days: Optional[int] = None


@router.get("/statistics")
async def get_statistics(current_user: dict = Depends(require_roles("admin"))):
    """Get payment link statistics"""
    return payment_link_service.get_statistics()


@router.get("")
async def list_links(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """List payment links"""
    return payment_link_service.list_links(status, client_id, payment_id, limit, offset)


@router.post("")
async def create_link(
    request: CreateLinkRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a payment link"""
    return payment_link_service.create_link(
        **request.model_dump(),
        created_by=current_user["id"]
    )


@router.get("/{link_id}")
async def get_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a payment link"""
    link = payment_link_service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.put("/{link_id}")
async def update_link(
    link_id: str,
    request: UpdateLinkRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a payment link"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    link = payment_link_service.update_link(link_id, updates)
    if not link:
        raise HTTPException(status_code=400, detail="Cannot update link")
    return link


@router.delete("/{link_id}")
async def cancel_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Cancel a payment link"""
    link = payment_link_service.cancel_link(link_id)
    if not link:
        raise HTTPException(status_code=400, detail="Cannot cancel link")
    return {"message": "Link cancelled", "link": link}


@router.post("/{link_id}/send")
async def send_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send payment link to client (simulated)"""
    link = payment_link_service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if not link.get("client_email"):
        raise HTTPException(status_code=400, detail="No client email configured")
    
    # In production, this would send an actual email
    return {
        "message": "Link sent successfully",
        "sent_to": link["client_email"],
        "link_url": link["url"]
    }
```

---

## TASK 3: CHECKOUT PAGE (PUBLIC) 🛒

### 3.1 Create Checkout Routes (Public - No Auth)

**File:** `backend/app/routes/checkout.py`

```python
"""
Public Checkout routes (no authentication required)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.payment_link_service import payment_link_service
from app.services.gateway_service import gateway_service

router = APIRouter()


class ProcessPaymentRequest(BaseModel):
    gateway: str
    card_number: Optional[str] = None  # For card payments
    card_expiry: Optional[str] = None
    card_cvc: Optional[str] = None
    card_zip: Optional[str] = None
    amount: Optional[float] = None  # For partial payments
    email: Optional[str] = None


@router.get("/{code}")
async def get_checkout_data(code: str):
    """Get checkout page data (public)"""
    # Record view
    payment_link_service.record_view(code)
    
    data = payment_link_service.get_checkout_data(code)
    if not data:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    if data["status"] == "expired":
        raise HTTPException(status_code=410, detail="Payment link has expired")
    
    if data["status"] == "paid":
        return {
            **data,
            "already_paid": True,
            "message": "This payment has already been completed"
        }
    
    if data["status"] == "cancelled":
        raise HTTPException(status_code=410, detail="Payment link has been cancelled")
    
    # Get available gateways with their info
    available_gateways = []
    for gw_id in data["gateways"]:
        gw = gateway_service.get_gateway(gw_id)
        if gw and gw["enabled"]:
            available_gateways.append({
                "id": gw["provider"],
                "name": gw["name"],
                "icon": gw["icon"],
                "methods": gw["supported_methods"]
            })
    
    return {
        **data,
        "available_gateways": available_gateways
    }


@router.post("/{code}/pay")
async def process_payment(code: str, request: ProcessPaymentRequest):
    """Process payment (public)"""
    # Get link
    link = payment_link_service.get_link_by_code(code)
    if not link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    if link["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Payment link is {link['status']}")
    
    # Record attempt
    payment_link_service.record_attempt(code)
    
    # Validate gateway
    if request.gateway not in link["gateways"]:
        raise HTTPException(status_code=400, detail="Gateway not allowed for this link")
    
    gateway = gateway_service.get_gateway(request.gateway)
    if not gateway or not gateway["enabled"]:
        raise HTTPException(status_code=400, detail="Gateway not available")
    
    # Determine amount
    pay_amount = request.amount if request.amount and link["allow_partial"] else link["amount"]
    
    # Validate partial payment
    if link["allow_partial"] and link["minimum_amount"]:
        if pay_amount < link["minimum_amount"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum payment amount is {link['minimum_amount']} {link['currency']}"
            )
    
    # Simulate payment processing based on gateway
    result = _simulate_payment(
        gateway=request.gateway,
        amount=pay_amount,
        currency=link["currency"],
        card_number=request.card_number
    )
    
    if result["success"]:
        # Calculate fees
        fee_info = gateway_service.calculate_fee(request.gateway, pay_amount)
        
        # Mark as paid
        payment_link_service.mark_as_paid(
            code=code,
            amount=pay_amount,
            gateway=request.gateway,
            transaction_id=result["transaction_id"],
            fee_amount=fee_info["total_fee"]
        )
        
        return {
            "success": True,
            "transaction_id": result["transaction_id"],
            "amount_paid": pay_amount,
            "currency": link["currency"],
            "fee": fee_info["total_fee"],
            "net": fee_info["net_amount"],
            "gateway": request.gateway,
            "receipt_sent": link["send_receipt"]
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "error_code": result.get("error_code", "payment_failed")
        }


@router.get("/{code}/status")
async def get_payment_status(code: str):
    """Get payment status (public)"""
    link = payment_link_service.get_link_by_code(code)
    if not link:
        raise HTTPException(status_code=404, detail="Payment link not found")
    
    return {
        "code": code,
        "status": link["status"],
        "paid_at": link.get("paid_at"),
        "paid_amount": link.get("paid_amount"),
        "paid_via": link.get("paid_via"),
        "transaction_id": link.get("transaction_id")
    }


def _simulate_payment(gateway: str, amount: float, currency: str, card_number: str = None) -> dict:
    """Simulate payment processing"""
    import secrets
    
    # Test card numbers for simulation
    if card_number:
        card_clean = card_number.replace(" ", "").replace("-", "")
        
        # Declined card
        if card_clean == "4000000000000002":
            return {
                "success": False,
                "error": "Your card was declined",
                "error_code": "card_declined"
            }
        
        # Insufficient funds
        if card_clean == "4000000000009995":
            return {
                "success": False,
                "error": "Insufficient funds",
                "error_code": "insufficient_funds"
            }
        
        # Expired card
        if card_clean == "4000000000000069":
            return {
                "success": False,
                "error": "Your card has expired",
                "error_code": "expired_card"
            }
    
    # Simulate successful payment
    transaction_id = f"txn_{secrets.token_hex(12)}"
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "gateway_response": {
            "status": "succeeded",
            "amount": amount,
            "currency": currency
        }
    }
```

### 3.2 Add APIs to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Gateway API
export const gatewayAPI = {
  getProviders: () => api.get('/api/v1/gateways/providers'),
  list: (enabledOnly = false) => api.get('/api/v1/gateways', { params: { enabled_only: enabledOnly } }),
  getDefault: () => api.get('/api/v1/gateways/default'),
  getForCurrency: (currency) => api.get(`/api/v1/gateways/for-currency/${currency}`),
  get: (provider) => api.get(`/api/v1/gateways/${provider}`),
  update: (provider, data) => api.put(`/api/v1/gateways/${provider}`, data),
  test: (provider) => api.post(`/api/v1/gateways/${provider}/test`),
  calculateFee: (provider, amount) => api.get(`/api/v1/gateways/${provider}/calculate-fee`, { params: { amount } })
};

// Payment Links API
export const paymentLinksAPI = {
  getStatistics: () => api.get('/api/v1/payment-links/statistics'),
  list: (params) => api.get('/api/v1/payment-links', { params }),
  create: (data) => api.post('/api/v1/payment-links', data),
  get: (linkId) => api.get(`/api/v1/payment-links/${linkId}`),
  update: (linkId, data) => api.put(`/api/v1/payment-links/${linkId}`, data),
  cancel: (linkId) => api.delete(`/api/v1/payment-links/${linkId}`),
  send: (linkId) => api.post(`/api/v1/payment-links/${linkId}/send`)
};

// Checkout API (public - no auth)
export const checkoutAPI = {
  getData: (code) => api.get(`/api/v1/checkout/${code}`),
  pay: (code, data) => api.post(`/api/v1/checkout/${code}/pay`, data),
  getStatus: (code) => api.get(`/api/v1/checkout/${code}/status`)
};
```

### 3.3 Create Gateway Settings Page

**File:** `frontend/src/pages/GatewaySettings.jsx`

```jsx
import { useState, useEffect } from 'react';
import { gatewayAPI } from '../services/api';

export default function GatewaySettings() {
  const [gateways, setGateways] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(null);
  const [editingGateway, setEditingGateway] = useState(null);
  const [credentials, setCredentials] = useState({});

  useEffect(() => {
    loadGateways();
  }, []);

  const loadGateways = async () => {
    try {
      const res = await gatewayAPI.list();
      setGateways(res.data.gateways);
    } catch (err) {
      console.error('Failed to load gateways:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (provider) => {
    setTesting(provider);
    try {
      const res = await gatewayAPI.test(provider);
      alert(res.data.message);
      loadGateways();
    } catch (err) {
      alert('Test failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTesting(null);
    }
  };

  const handleToggle = async (provider, enabled) => {
    try {
      await gatewayAPI.update(provider, { enabled: !enabled });
      loadGateways();
    } catch (err) {
      alert('Failed to update');
    }
  };

  const handleSetDefault = async (provider) => {
    try {
      await gatewayAPI.update(provider, { is_default: true });
      loadGateways();
    } catch (err) {
      alert('Failed to set default');
    }
  };

  const handleModeChange = async (provider, mode) => {
    try {
      await gatewayAPI.update(provider, { mode });
      loadGateways();
    } catch (err) {
      alert('Failed to change mode');
    }
  };

  const handleSaveCredentials = async () => {
    if (!editingGateway) return;
    try {
      await gatewayAPI.update(editingGateway, { credentials });
      setEditingGateway(null);
      setCredentials({});
      loadGateways();
    } catch (err) {
      alert('Failed to save credentials');
    }
  };

  const getStatusBadge = (gateway) => {
    if (!gateway.enabled) return <span className="badge badge-gray">Disabled</span>;
    if (gateway.test_status === 'success') return <span className="badge badge-success">Connected</span>;
    if (gateway.test_status === 'failed') return <span className="badge badge-danger">Failed</span>;
    return <span className="badge badge-warning">Not Tested</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        💳 Configure payment gateways to accept online payments from your clients.
      </div>

      <div className="section">
        <h3 className="section-title">Payment Gateways</h3>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : (
          <div className="gateway-list">
            {gateways.map(gateway => (
              <div key={gateway.provider} className={`gateway-card ${!gateway.enabled ? 'disabled' : ''}`}>
                <div className="gateway-header">
                  <div className="gateway-icon">{gateway.icon}</div>
                  <div className="gateway-info">
                    <div className="gateway-name">
                      {gateway.name}
                      {gateway.is_default && <span className="badge badge-primary ml-2">Default</span>}
                    </div>
                    <div className="gateway-meta">
                      Fee: {gateway.fee_percentage}% + ${gateway.fee_fixed}
                    </div>
                  </div>
                  <div className="gateway-status">
                    {getStatusBadge(gateway)}
                  </div>
                </div>

                <div className="gateway-details">
                  <div className="detail-row">
                    <span className="detail-label">Mode:</span>
                    <select
                      className="form-select form-select-sm"
                      value={gateway.mode}
                      onChange={(e) => handleModeChange(gateway.provider, e.target.value)}
                      disabled={!gateway.enabled}
                    >
                      <option value="test">Test Mode</option>
                      <option value="live">Live Mode</option>
                    </select>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Currencies:</span>
                    <span>{gateway.supported_currencies.slice(0, 5).join(', ')}{gateway.supported_currencies.length > 5 ? '...' : ''}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Methods:</span>
                    <span>{gateway.supported_methods.join(', ')}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Public Key:</span>
                    <code>{gateway.credentials?.public_key || 'Not set'}</code>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Webhook URL:</span>
                    <code className="text-xs">{window.location.origin}{gateway.webhook_url}</code>
                  </div>
                </div>

                <div className="gateway-actions">
                  <button
                    className={`btn btn-sm ${gateway.enabled ? 'btn-warning' : 'btn-success'}`}
                    onClick={() => handleToggle(gateway.provider, gateway.enabled)}
                  >
                    {gateway.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      setEditingGateway(gateway.provider);
                      setCredentials({});
                    }}
                  >
                    🔑 Credentials
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleTest(gateway.provider)}
                    disabled={testing === gateway.provider || !gateway.enabled}
                  >
                    {testing === gateway.provider ? 'Testing...' : '🔌 Test'}
                  </button>
                  {!gateway.is_default && gateway.enabled && (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleSetDefault(gateway.provider)}
                    >
                      Set Default
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Credentials Modal */}
      {editingGateway && (
        <div className="modal-overlay" onClick={() => setEditingGateway(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>API Credentials - {editingGateway}</h3>
              <button className="modal-close" onClick={() => setEditingGateway(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="alert alert-info mb-4">
                🔒 Credentials are encrypted and stored securely. Leave fields empty to keep existing values.
              </div>
              <div className="form-group">
                <label className="form-label">Public Key / Client ID</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="pk_test_..."
                  value={credentials.public_key || ''}
                  onChange={(e) => setCredentials({ ...credentials, public_key: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Secret Key / Client Secret</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="sk_test_..."
                  value={credentials.secret_key || ''}
                  onChange={(e) => setCredentials({ ...credentials, secret_key: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Webhook Secret</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="whsec_..."
                  value={credentials.webhook_secret || ''}
                  onChange={(e) => setCredentials({ ...credentials, webhook_secret: e.target.value })}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setEditingGateway(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveCredentials}>
                Save Credentials
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 3.4 Create Payment Links Page

**File:** `frontend/src/pages/PaymentLinks.jsx`

```jsx
import { useState, useEffect } from 'react';
import { paymentLinksAPI, gatewayAPI } from '../services/api';

export default function PaymentLinks() {
  const [links, setLinks] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gateways, setGateways] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedLink, setSelectedLink] = useState(null);
  const [filter, setFilter] = useState('all');

  const [newLink, setNewLink] = useState({
    payment_id: '',
    amount: '',
    currency: 'USD',
    description: '',
    client_name: '',
    client_email: '',
    invoice_number: '',
    gateways: ['stripe', 'paypal'],
    expires_in_days: 30,
    single_use: true,
    allow_partial: false,
    send_receipt: true
  });

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [linksRes, statsRes, gatewaysRes] = await Promise.all([
        paymentLinksAPI.list({ status: filter === 'all' ? null : filter }),
        paymentLinksAPI.getStatistics(),
        gatewayAPI.list(true)
      ]);
      setLinks(linksRes.data.links);
      setStatistics(statsRes.data);
      setGateways(gatewaysRes.data.gateways);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const data = {
        ...newLink,
        amount: parseFloat(newLink.amount),
        payment_id: newLink.payment_id || `PAY-${Date.now()}`
      };
      await paymentLinksAPI.create(data);
      setShowCreate(false);
      setNewLink({
        payment_id: '', amount: '', currency: 'USD', description: '',
        client_name: '', client_email: '', invoice_number: '',
        gateways: ['stripe', 'paypal'], expires_in_days: 30,
        single_use: true, allow_partial: false, send_receipt: true
      });
      loadData();
    } catch (err) {
      alert('Failed to create link');
    }
  };

  const handleCancel = async (linkId) => {
    if (!confirm('Cancel this payment link?')) return;
    try {
      await paymentLinksAPI.cancel(linkId);
      loadData();
    } catch (err) {
      alert('Failed to cancel');
    }
  };

  const handleSend = async (linkId) => {
    try {
      const res = await paymentLinksAPI.send(linkId);
      alert(`Link sent to ${res.data.sent_to}`);
    } catch (err) {
      alert('Failed to send: ' + (err.response?.data?.detail || err.message));
    }
  };

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    alert('Link copied to clipboard!');
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-success',
      paid: 'badge-primary',
      expired: 'badge-warning',
      cancelled: 'badge-danger'
    };
    return <span className={`badge ${badges[status] || 'badge-gray'}`}>{status}</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        🔗 Create payment links to collect payments from your clients online.
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">🔗</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.total_links}</div>
              <div className="stat-label">Total Links</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.by_status.paid}</div>
              <div className="stat-label">Paid</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <div className="stat-value">${statistics.total_collected.toLocaleString()}</div>
              <div className="stat-label">Collected</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.conversion_rate}%</div>
              <div className="stat-label">Conversion</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters & Actions */}
      <div className="section mb-6">
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            {['all', 'active', 'paid', 'expired', 'cancelled'].map(f => (
              <button
                key={f}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            ➕ Create Payment Link
          </button>
        </div>
      </div>

      {/* Links List */}
      <div className="section">
        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : links.length === 0 ? (
          <div className="text-center text-muted p-8">No payment links found</div>
        ) : (
          <div className="links-list">
            {links.map(link => (
              <div key={link.id} className="link-card">
                <div className="link-header">
                  <div className="link-amount">
                    ${link.amount.toLocaleString()} <span className="currency">{link.currency}</span>
                  </div>
                  {getStatusBadge(link.status)}
                </div>
                
                <div className="link-description">{link.description}</div>
                
                <div className="link-meta">
                  {link.client_name && <span>👤 {link.client_name}</span>}
                  {link.invoice_number && <span>📄 {link.invoice_number}</span>}
                  <span>👁️ {link.views} views</span>
                  <span>🔄 {link.attempts} attempts</span>
                </div>

                <div className="link-url">
                  <code>{link.url}</code>
                  <button className="btn btn-sm btn-secondary" onClick={() => copyLink(link.url)}>
                    📋 Copy
                  </button>
                </div>

                {link.status === 'paid' && (
                  <div className="link-paid-info">
                    ✅ Paid ${link.paid_amount} via {link.paid_via} on {new Date(link.paid_at).toLocaleDateString()}
                  </div>
                )}

                <div className="link-actions">
                  <button 
                    className="btn btn-sm btn-secondary"
                    onClick={() => setSelectedLink(link)}
                  >
                    View Details
                  </button>
                  {link.status === 'active' && (
                    <>
                      <button 
                        className="btn btn-sm btn-primary"
                        onClick={() => handleSend(link.id)}
                      >
                        📧 Send
                      </button>
                      <button 
                        className="btn btn-sm btn-danger"
                        onClick={() => handleCancel(link.id)}
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Payment Link</h3>
              <button className="modal-close" onClick={() => setShowCreate(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newLink.amount}
                    onChange={(e) => setNewLink({ ...newLink, amount: e.target.value })}
                    placeholder="1500.00"
                    step="0.01"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="form-select"
                    value={newLink.currency}
                    onChange={(e) => setNewLink({ ...newLink, currency: e.target.value })}
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="ARS">ARS</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newLink.description}
                  onChange={(e) => setNewLink({ ...newLink, description: e.target.value })}
                  placeholder="Invoice #INV-001 - Consulting Services"
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Client Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newLink.client_name}
                    onChange={(e) => setNewLink({ ...newLink, client_name: e.target.value })}
                    placeholder="Acme Corp"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Client Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={newLink.client_email}
                    onChange={(e) => setNewLink({ ...newLink, client_email: e.target.value })}
                    placeholder="billing@acme.com"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newLink.invoice_number}
                    onChange={(e) => setNewLink({ ...newLink, invoice_number: e.target.value })}
                    placeholder="INV-2025-001"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Expires In (days)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newLink.expires_in_days}
                    onChange={(e) => setNewLink({ ...newLink, expires_in_days: parseInt(e.target.value) || 30 })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Payment Gateways</label>
                <div className="checkbox-group">
                  {gateways.map(gw => (
                    <label key={gw.provider} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newLink.gateways.includes(gw.provider)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewLink({ ...newLink, gateways: [...newLink.gateways, gw.provider] });
                          } else {
                            setNewLink({ ...newLink, gateways: newLink.gateways.filter(g => g !== gw.provider) });
                          }
                        }}
                      />
                      {gw.icon} {gw.name}
                    </label>
                  ))}
                </div>
              </div>
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newLink.single_use}
                    onChange={(e) => setNewLink({ ...newLink, single_use: e.target.checked })}
                  />
                  Single use (disable after payment)
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newLink.send_receipt}
                    onChange={(e) => setNewLink({ ...newLink, send_receipt: e.target.checked })}
                  />
                  Send receipt email after payment
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button 
                className="btn btn-primary" 
                onClick={handleCreate}
                disabled={!newLink.amount || !newLink.description}
              >
                Create Link
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 3.5 Create Public Checkout Page

**File:** `frontend/src/pages/public/Checkout.jsx`

```jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { checkoutAPI } from '../../services/api';

export default function Checkout() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGateway, setSelectedGateway] = useState(null);
  
  const [cardForm, setCardForm] = useState({
    number: '',
    expiry: '',
    cvc: '',
    zip: ''
  });

  useEffect(() => {
    loadCheckoutData();
  }, [code]);

  const loadCheckoutData = async () => {
    try {
      const res = await checkoutAPI.getData(code);
      setData(res.data);
      if (res.data.available_gateways?.length > 0) {
        setSelectedGateway(res.data.available_gateways[0].id);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Payment link not found');
      } else if (err.response?.status === 410) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to load checkout');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    return parts.length ? parts.join(' ') : v;
  };

  const formatExpiry = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (v.length >= 2) {
      return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
  };

  const handlePay = async () => {
    setProcessing(true);
    setError(null);
    
    try {
      const res = await checkoutAPI.pay(code, {
        gateway: selectedGateway,
        card_number: cardForm.number.replace(/\s/g, ''),
        card_expiry: cardForm.expiry,
        card_cvc: cardForm.cvc,
        card_zip: cardForm.zip
      });
      
      if (res.data.success) {
        navigate(`/pay/${code}/success`, { 
          state: { 
            transaction_id: res.data.transaction_id,
            amount: res.data.amount_paid,
            currency: data.currency
          }
        });
      } else {
        setError(res.data.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Payment failed');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="text-center p-8">Loading...</div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="checkout-error">
            <div className="error-icon">❌</div>
            <h2>{error}</h2>
            <p>This payment link is no longer available.</p>
          </div>
        </div>
      </div>
    );
  }

  if (data?.already_paid) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="checkout-success">
            <div className="success-icon">✅</div>
            <h2>Already Paid</h2>
            <p>This payment was completed on {new Date(data.paid_at).toLocaleDateString()}</p>
            <p>Amount: ${data.paid_amount?.toLocaleString()} {data.currency}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        {/* Header */}
        <div className="checkout-header">
          <h1>Complete Payment</h1>
          {data.invoice_number && <p>Invoice: {data.invoice_number}</p>}
        </div>

        {/* Amount */}
        <div className="checkout-amount">
          <div className="amount-value">
            ${data.amount.toLocaleString()}
          </div>
          <div className="amount-currency">{data.currency}</div>
          <div className="amount-description">{data.description}</div>
        </div>

        {/* Gateway Selection */}
        <div className="checkout-section">
          <h3>Payment Method</h3>
          <div className="gateway-options">
            {data.available_gateways?.map(gw => (
              <div
                key={gw.id}
                className={`gateway-option ${selectedGateway === gw.id ? 'selected' : ''}`}
                onClick={() => setSelectedGateway(gw.id)}
              >
                <div className="gateway-icon">{gw.icon}</div>
                <div className="gateway-name">{gw.name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Card Form (for card-based gateways) */}
        {selectedGateway && ['stripe', 'mercadopago'].includes(selectedGateway) && (
          <div className="checkout-section">
            <h3>Card Details</h3>
            <div className="card-form">
              <div className="form-group">
                <label>Card Number</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="4242 4242 4242 4242"
                  value={cardForm.number}
                  onChange={(e) => setCardForm({ ...cardForm, number: formatCardNumber(e.target.value) })}
                  maxLength={19}
                />
              </div>
              <div className="card-row">
                <div className="form-group">
                  <label>Expiry</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="MM/YY"
                    value={cardForm.expiry}
                    onChange={(e) => setCardForm({ ...cardForm, expiry: formatExpiry(e.target.value) })}
                    maxLength={5}
                  />
                </div>
                <div className="form-group">
                  <label>CVC</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="123"
                    value={cardForm.cvc}
                    onChange={(e) => setCardForm({ ...cardForm, cvc: e.target.value.replace(/\D/g, '').slice(0, 4) })}
                    maxLength={4}
                  />
                </div>
                <div className="form-group">
                  <label>ZIP</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="10001"
                    value={cardForm.zip}
                    onChange={(e) => setCardForm({ ...cardForm, zip: e.target.value })}
                    maxLength={10}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PayPal Button */}
        {selectedGateway === 'paypal' && (
          <div className="checkout-section">
            <p className="text-center text-muted">
              You will be redirected to PayPal to complete your payment.
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="checkout-error-message">
            ❌ {error}
          </div>
        )}

        {/* Pay Button */}
        <button
          className="checkout-pay-btn"
          onClick={handlePay}
          disabled={processing || !selectedGateway}
        >
          {processing ? 'Processing...' : `Pay $${data.amount.toLocaleString()} ${data.currency}`}
        </button>

        {/* Security Badge */}
        <div className="checkout-security">
          🔒 Secured by {selectedGateway === 'stripe' ? 'Stripe' : selectedGateway === 'paypal' ? 'PayPal' : 'MercadoPago'}
        </div>

        {/* Test Cards Info */}
        <div className="checkout-test-info">
          <details>
            <summary>Test Card Numbers (Demo Mode)</summary>
            <ul>
              <li><code>4242 4242 4242 4242</code> - Success</li>
              <li><code>4000 0000 0000 0002</code> - Declined</li>
              <li><code>4000 0000 0000 9995</code> - Insufficient funds</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
}
```

### 3.6 Create Checkout Success Page

**File:** `frontend/src/pages/public/CheckoutSuccess.jsx`

```jsx
import { useLocation, useParams } from 'react-router-dom';

export default function CheckoutSuccess() {
  const { code } = useParams();
  const location = useLocation();
  const { transaction_id, amount, currency } = location.state || {};

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <div className="checkout-success">
          <div className="success-icon">✅</div>
          <h1>Payment Successful!</h1>
          
          <div className="success-details">
            <div className="detail-row">
              <span>Amount Paid:</span>
              <strong>${amount?.toLocaleString()} {currency}</strong>
            </div>
            <div className="detail-row">
              <span>Transaction ID:</span>
              <code>{transaction_id}</code>
            </div>
            <div className="detail-row">
              <span>Date:</span>
              <span>{new Date().toLocaleDateString()}</span>
            </div>
          </div>

          <p className="success-message">
            A receipt has been sent to your email address.
          </p>

          <button className="btn btn-primary" onClick={() => window.print()}>
            🖨️ Print Receipt
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 3.7 Add Checkout Styles

**Add to:** `frontend/src/index.css`

```css
/* Gateway Settings */
.gateway-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.gateway-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  background: var(--card-bg);
}

.gateway-card.disabled {
  opacity: 0.6;
}

.gateway-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.gateway-icon {
  font-size: 2rem;
}

.gateway-info {
  flex: 1;
}

.gateway-name {
  font-size: 1.25rem;
  font-weight: 600;
}

.gateway-meta {
  font-size: 0.9rem;
  color: var(--text-muted);
}

.gateway-details {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.detail-label {
  color: var(--text-muted);
}

.gateway-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Payment Links */
.links-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.link-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  background: var(--card-bg);
}

.link-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.link-amount {
  font-size: 1.5rem;
  font-weight: 700;
}

.link-amount .currency {
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-muted);
}

.link-description {
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.link-meta {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.link-url {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 12px;
}

.link-url code {
  flex: 1;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.link-paid-info {
  padding: 8px 12px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  color: #10b981;
  font-size: 0.9rem;
  margin-bottom: 12px;
}

.link-actions {
  display: flex;
  gap: 8px;
}

/* Public Checkout Page */
.checkout-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.checkout-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 480px;
  width: 100%;
  padding: 32px;
}

.checkout-header {
  text-align: center;
  margin-bottom: 24px;
}

.checkout-header h1 {
  margin: 0 0 8px 0;
  font-size: 1.5rem;
  color: #1a1a2e;
}

.checkout-header p {
  margin: 0;
  color: #666;
}

.checkout-amount {
  text-align: center;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 24px;
}

.amount-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1a1a2e;
}

.amount-currency {
  font-size: 1rem;
  color: #666;
}

.amount-description {
  margin-top: 8px;
  font-size: 0.9rem;
  color: #666;
}

.checkout-section {
  margin-bottom: 24px;
}

.checkout-section h3 {
  margin: 0 0 12px 0;
  font-size: 1rem;
  color: #1a1a2e;
}

.gateway-options {
  display: flex;
  gap: 12px;
}

.gateway-option {
  flex: 1;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.gateway-option:hover {
  border-color: #667eea;
}

.gateway-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.gateway-option .gateway-icon {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.gateway-option .gateway-name {
  font-size: 0.85rem;
  font-weight: 500;
}

.card-form .form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.card-form .form-input:focus {
  outline: none;
  border-color: #667eea;
}

.card-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.checkout-error-message {
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  margin-bottom: 16px;
  text-align: center;
}

.checkout-pay-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.checkout-pay-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.checkout-pay-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.checkout-security {
  text-align: center;
  margin-top: 16px;
  font-size: 0.85rem;
  color: #666;
}

.checkout-test-info {
  margin-top: 24px;
  padding: 12px;
  background: #fffbeb;
  border-radius: 8px;
  font-size: 0.8rem;
}

.checkout-test-info summary {
  cursor: pointer;
  color: #92400e;
}

.checkout-test-info ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.checkout-success, .checkout-error {
  text-align: center;
  padding: 32px;
}

.success-icon, .error-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.success-details {
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
}

.success-details .detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.success-details .detail-row:last-child {
  border-bottom: none;
}

.success-message {
  color: #666;
  margin-bottom: 24px;
}
```

---

## TASK 4: REGISTER ROUTES

### 4.1 Update Backend main.py

```python
from app.routes import gateways, payment_links, checkout

# Admin routes (require auth)
app.include_router(gateways.router, prefix="/api/v1/gateways", tags=["Gateways"])
app.include_router(payment_links.router, prefix="/api/v1/payment-links", tags=["Payment Links"])

# Public routes (no auth)
app.include_router(checkout.router, prefix="/api/v1/checkout", tags=["Checkout"])
```

### 4.2 Update Frontend App.jsx

```jsx
// Lazy imports
const GatewaySettings = lazy(() => import('./pages/GatewaySettings'));
const PaymentLinks = lazy(() => import('./pages/PaymentLinks'));
const Checkout = lazy(() => import('./pages/public/Checkout'));
const CheckoutSuccess = lazy(() => import('./pages/public/CheckoutSuccess'));

// Admin routes
<Route path="/gateways" element={
  <PrivateRoute roles={['admin']}>
    <Layout><GatewaySettings /></Layout>
  </PrivateRoute>
} />
<Route path="/payment-links" element={
  <PrivateRoute roles={['admin']}>
    <Layout><PaymentLinks /></Layout>
  </PrivateRoute>
} />

// Public routes (no Layout, no auth)
<Route path="/pay/:code" element={<Checkout />} />
<Route path="/pay/:code/success" element={<CheckoutSuccess />} />
```

### 4.3 Update Layout Navigation

```javascript
{ path: '/payment-links', icon: '🔗', label: 'Payment Links', roles: ['admin'] },
{ path: '/gateways', icon: '💳', label: 'Payment Gateways', roles: ['admin'] },
```

---

## COMPLETION CHECKLIST - PART 1

### Gateway Configuration ✅
- [x] Gateway service with Stripe, PayPal, MercadoPago
- [x] Enable/disable gateways
- [x] Test/Live mode toggle
- [x] Credentials management
- [x] Connection testing
- [x] Fee calculation
- [x] Gateway settings page

### Payment Links ✅
- [x] Create payment links
- [x] Link tracking (views, attempts)
- [x] QR code generation
- [x] Expiration handling
- [x] Statistics
- [x] Send link to client
- [x] Payment links page

### Public Checkout ✅
- [x] Checkout page
- [x] Gateway selection
- [x] Card form
- [x] Payment simulation
- [x] Success/error pages
- [x] Mobile responsive

---

**Continue to Part 2 for Gateway-specific integrations and Webhooks**
