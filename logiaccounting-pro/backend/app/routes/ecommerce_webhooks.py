"""
E-commerce webhook handlers
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import hmac
import hashlib
import base64

from app.services.ecommerce.connection_service import ecommerce_service
from app.services.ecommerce.order_import_service import order_import_service
from app.services.ecommerce.inventory_sync_service import inventory_sync_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["ecommerce-webhooks"])


def verify_shopify_signature(
    body: bytes,
    signature: str,
    secret: str = "demo_webhook_secret"
) -> bool:
    """Verify Shopify webhook signature"""
    computed = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(computed, signature)


def verify_woocommerce_signature(
    body: bytes,
    signature: str,
    secret: str = "demo_webhook_secret"
) -> bool:
    """Verify WooCommerce webhook signature"""
    computed = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(computed, signature)


@router.post("/shopify")
async def shopify_webhook(
    request: Request,
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """Handle Shopify webhooks"""
    body = await request.body()

    # In production, verify signature
    # if not verify_shopify_signature(body, x_shopify_hmac_sha256):
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    topic = x_shopify_topic or "unknown"

    # Find store by domain
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "shopify":
            if s["credentials"].get("shop_domain") == x_shopify_shop_domain:
                store = s
                break

    if not store:
        # Demo mode - use first Shopify store
        for s in ecommerce_service.get_stores():
            if s["platform"] == "shopify":
                store = s
                break

    if store:
        await process_shopify_event(store["id"], topic, data)

    return {"received": True, "topic": topic}


async def process_shopify_event(store_id: str, topic: str, data: dict):
    """Process Shopify webhook event"""
    if topic == "orders/create" or topic == "orders/paid":
        # Import order
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)

    elif topic == "inventory_levels/update":
        # Sync inventory
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await inventory_sync_service.pull_inventory(store_id, adapter)

    elif topic == "products/update":
        # Could trigger product sync
        pass


@router.post("/woocommerce")
async def woocommerce_webhook(
    request: Request,
    x_wc_webhook_topic: Optional[str] = Header(None),
    x_wc_webhook_source: Optional[str] = Header(None),
    x_wc_webhook_signature: Optional[str] = Header(None)
):
    """Handle WooCommerce webhooks"""
    body = await request.body()
    data = await request.json()
    topic = x_wc_webhook_topic or "unknown"

    # Find store by URL
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "woocommerce":
            if x_wc_webhook_source and x_wc_webhook_source.startswith(
                s["credentials"].get("store_url", "")
            ):
                store = s
                break

    if not store:
        # Demo mode - use first WooCommerce store
        for s in ecommerce_service.get_stores():
            if s["platform"] == "woocommerce":
                store = s
                break

    if store:
        await process_woocommerce_event(store["id"], topic, data)

    return {"received": True, "topic": topic}


async def process_woocommerce_event(store_id: str, topic: str, data: dict):
    """Process WooCommerce webhook event"""
    if topic in ["order.created", "order.updated"]:
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)

    elif topic == "product.updated":
        pass


@router.post("/amazon")
async def amazon_webhook(request: Request):
    """Handle Amazon notifications (SNS)"""
    data = await request.json()
    notification_type = data.get("NotificationType", "unknown")

    # Find Amazon store
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "amazon":
            store = s
            break

    if store:
        await process_amazon_event(store["id"], notification_type, data)

    return {"received": True, "type": notification_type}


async def process_amazon_event(store_id: str, notification_type: str, data: dict):
    """Process Amazon notification"""
    if notification_type == "ORDER_CHANGE":
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)
