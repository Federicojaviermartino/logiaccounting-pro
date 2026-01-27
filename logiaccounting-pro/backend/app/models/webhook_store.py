"""
Webhook Data Store
Webhook endpoints, deliveries, and event types for Phase 17
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
import secrets
from enum import Enum


class EventCategory(str, Enum):
    """Webhook event categories"""
    INVOICES = "invoices"
    PAYMENTS = "payments"
    INVENTORY = "inventory"
    PROJECTS = "projects"
    CUSTOMERS = "customers"
    SUPPLIERS = "suppliers"
    DOCUMENTS = "documents"
    USERS = "users"
    SYSTEM = "system"


# Event definitions with categories and descriptions
EVENT_DEFINITIONS = {
    # Invoice Events
    "invoice.created": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Created",
        "description": "Triggered when a new invoice is created",
        "payload_fields": ["id", "number", "customer_id", "total", "status", "created_at"]
    },
    "invoice.updated": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Updated",
        "description": "Triggered when an invoice is modified",
        "payload_fields": ["id", "number", "changes", "updated_at"]
    },
    "invoice.sent": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Sent",
        "description": "Triggered when an invoice is sent to customer",
        "payload_fields": ["id", "number", "sent_to", "sent_at"]
    },
    "invoice.paid": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Paid",
        "description": "Triggered when an invoice is marked as paid",
        "payload_fields": ["id", "number", "paid_amount", "paid_at", "payment_method"]
    },
    "invoice.overdue": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Overdue",
        "description": "Triggered when an invoice becomes overdue",
        "payload_fields": ["id", "number", "days_overdue", "amount_due"]
    },
    "invoice.voided": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Voided",
        "description": "Triggered when an invoice is voided/cancelled",
        "payload_fields": ["id", "number", "voided_at", "reason"]
    },
    "invoice.deleted": {
        "category": EventCategory.INVOICES,
        "name": "Invoice Deleted",
        "description": "Triggered when an invoice is deleted",
        "payload_fields": ["id", "number", "deleted_at"]
    },

    # Payment Events
    "payment.received": {
        "category": EventCategory.PAYMENTS,
        "name": "Payment Received",
        "description": "Triggered when a payment is received",
        "payload_fields": ["id", "amount", "currency", "invoice_id", "method", "received_at"]
    },
    "payment.refunded": {
        "category": EventCategory.PAYMENTS,
        "name": "Payment Refunded",
        "description": "Triggered when a payment is refunded",
        "payload_fields": ["id", "refund_amount", "reason", "refunded_at"]
    },
    "payment.failed": {
        "category": EventCategory.PAYMENTS,
        "name": "Payment Failed",
        "description": "Triggered when a payment attempt fails",
        "payload_fields": ["id", "amount", "error_code", "error_message", "failed_at"]
    },
    "payment.due_soon": {
        "category": EventCategory.PAYMENTS,
        "name": "Payment Due Soon",
        "description": "Triggered when a payment is due within 7 days",
        "payload_fields": ["id", "amount", "due_date", "days_until_due"]
    },

    # Inventory Events
    "product.created": {
        "category": EventCategory.INVENTORY,
        "name": "Product Created",
        "description": "Triggered when a new product is created",
        "payload_fields": ["id", "sku", "name", "price", "stock_quantity"]
    },
    "product.updated": {
        "category": EventCategory.INVENTORY,
        "name": "Product Updated",
        "description": "Triggered when a product is modified",
        "payload_fields": ["id", "sku", "changes", "updated_at"]
    },
    "product.deleted": {
        "category": EventCategory.INVENTORY,
        "name": "Product Deleted",
        "description": "Triggered when a product is deleted",
        "payload_fields": ["id", "sku", "deleted_at"]
    },
    "stock.low": {
        "category": EventCategory.INVENTORY,
        "name": "Low Stock Alert",
        "description": "Triggered when stock falls below threshold",
        "payload_fields": ["product_id", "sku", "current_stock", "threshold"]
    },
    "stock.out": {
        "category": EventCategory.INVENTORY,
        "name": "Out of Stock",
        "description": "Triggered when a product is out of stock",
        "payload_fields": ["product_id", "sku", "last_stock_at"]
    },
    "stock.adjusted": {
        "category": EventCategory.INVENTORY,
        "name": "Stock Adjusted",
        "description": "Triggered when stock quantity is adjusted",
        "payload_fields": ["product_id", "sku", "previous_quantity", "new_quantity", "reason"]
    },

    # Project Events
    "project.created": {
        "category": EventCategory.PROJECTS,
        "name": "Project Created",
        "description": "Triggered when a new project is created",
        "payload_fields": ["id", "name", "client_id", "budget", "start_date"]
    },
    "project.updated": {
        "category": EventCategory.PROJECTS,
        "name": "Project Updated",
        "description": "Triggered when a project is modified",
        "payload_fields": ["id", "name", "changes", "updated_at"]
    },
    "project.status_changed": {
        "category": EventCategory.PROJECTS,
        "name": "Project Status Changed",
        "description": "Triggered when project status changes",
        "payload_fields": ["id", "name", "old_status", "new_status", "changed_at"]
    },
    "project.completed": {
        "category": EventCategory.PROJECTS,
        "name": "Project Completed",
        "description": "Triggered when a project is marked complete",
        "payload_fields": ["id", "name", "completed_at", "final_budget"]
    },
    "project.milestone_completed": {
        "category": EventCategory.PROJECTS,
        "name": "Milestone Completed",
        "description": "Triggered when a project milestone is completed",
        "payload_fields": ["project_id", "milestone_id", "name", "completed_at"]
    },

    # Customer Events
    "customer.created": {
        "category": EventCategory.CUSTOMERS,
        "name": "Customer Created",
        "description": "Triggered when a new customer is created",
        "payload_fields": ["id", "email", "name", "company", "created_at"]
    },
    "customer.updated": {
        "category": EventCategory.CUSTOMERS,
        "name": "Customer Updated",
        "description": "Triggered when customer info is modified",
        "payload_fields": ["id", "changes", "updated_at"]
    },
    "customer.deleted": {
        "category": EventCategory.CUSTOMERS,
        "name": "Customer Deleted",
        "description": "Triggered when a customer is deleted",
        "payload_fields": ["id", "deleted_at"]
    },

    # Document Events
    "document.uploaded": {
        "category": EventCategory.DOCUMENTS,
        "name": "Document Uploaded",
        "description": "Triggered when a document is uploaded",
        "payload_fields": ["id", "filename", "size_bytes", "mime_type", "uploaded_at"]
    },
    "document.processed": {
        "category": EventCategory.DOCUMENTS,
        "name": "Document Processed",
        "description": "Triggered when OCR/processing completes",
        "payload_fields": ["id", "filename", "extracted_data", "processed_at"]
    },
    "document.signed": {
        "category": EventCategory.DOCUMENTS,
        "name": "Document Signed",
        "description": "Triggered when a document is digitally signed",
        "payload_fields": ["id", "signed_by", "signed_at"]
    },

    # User Events
    "user.invited": {
        "category": EventCategory.USERS,
        "name": "User Invited",
        "description": "Triggered when a user is invited to the organization",
        "payload_fields": ["email", "role", "invited_by", "invited_at"]
    },
    "user.joined": {
        "category": EventCategory.USERS,
        "name": "User Joined",
        "description": "Triggered when a user accepts an invitation",
        "payload_fields": ["id", "email", "role", "joined_at"]
    },
    "user.removed": {
        "category": EventCategory.USERS,
        "name": "User Removed",
        "description": "Triggered when a user is removed from the organization",
        "payload_fields": ["id", "email", "removed_by", "removed_at"]
    },

    # System Events
    "anomaly.detected": {
        "category": EventCategory.SYSTEM,
        "name": "Anomaly Detected",
        "description": "Triggered when a potential anomaly is detected",
        "payload_fields": ["type", "severity", "description", "entity_id", "detected_at"]
    },
    "backup.completed": {
        "category": EventCategory.SYSTEM,
        "name": "Backup Completed",
        "description": "Triggered when a backup operation completes",
        "payload_fields": ["backup_id", "size_bytes", "completed_at"]
    },
    "test.ping": {
        "category": EventCategory.SYSTEM,
        "name": "Test Ping",
        "description": "Test event for webhook verification",
        "payload_fields": ["message", "timestamp"]
    }
}


class WebhookEndpointStore:
    """Store for webhook endpoint subscriptions"""

    def __init__(self):
        self._endpoints: Dict[str, dict] = {}

    def create(self, data: Dict) -> Dict:
        """Create a new webhook endpoint"""
        endpoint_id = str(uuid4())

        # Generate signing secret
        secret = f"whsec_{secrets.token_urlsafe(32)}"

        endpoint = {
            "id": endpoint_id,
            "tenant_id": data.get("tenant_id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "url": data.get("url"),
            "secret": secret,
            "events": data.get("events", []),
            "custom_headers": data.get("custom_headers", {}),
            "content_type": data.get("content_type", "application/json"),
            "timeout_seconds": data.get("timeout_seconds", 30),
            "max_retries": data.get("max_retries", 5),
            "retry_delay_seconds": data.get("retry_delay_seconds", 60),
            "is_active": True,
            "last_success_at": None,
            "last_failure_at": None,
            "consecutive_failures": 0,
            "failure_threshold": data.get("failure_threshold", 10),
            "disabled_at": None,
            "disabled_reason": None,
            "created_by": data.get("created_by"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        self._endpoints[endpoint_id] = endpoint
        return endpoint

    def find_by_id(self, endpoint_id: str) -> Optional[Dict]:
        """Find endpoint by ID"""
        return self._endpoints.get(endpoint_id)

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Find all endpoints for a tenant"""
        return [
            e for e in self._endpoints.values()
            if e.get("tenant_id") == tenant_id
        ]

    def find_active_for_event(self, tenant_id: str, event_type: str) -> List[Dict]:
        """Find active endpoints subscribed to an event"""
        endpoints = []

        for endpoint in self._endpoints.values():
            if endpoint.get("tenant_id") != tenant_id:
                continue
            if not endpoint.get("is_active"):
                continue
            if endpoint.get("disabled_at"):
                continue

            # Check if endpoint subscribes to this event
            if self._matches_event(endpoint, event_type):
                endpoints.append(endpoint)

        return endpoints

    def _matches_event(self, endpoint: dict, event_type: str) -> bool:
        """Check if endpoint subscribes to event type"""
        events = endpoint.get("events", [])

        if "*" in events:
            return True
        if event_type in events:
            return True

        # Check for category wildcard (e.g., 'invoice.*')
        category = event_type.split(".")[0]
        if f"{category}.*" in events:
            return True

        return False

    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Find all endpoints with optional filters"""
        results = list(self._endpoints.values())

        if filters:
            if filters.get("tenant_id"):
                results = [e for e in results if e.get("tenant_id") == filters["tenant_id"]]
            if filters.get("is_active") is not None:
                results = [e for e in results if e.get("is_active") == filters["is_active"]]

        return sorted(results, key=lambda x: x["created_at"], reverse=True)

    def update(self, endpoint_id: str, data: Dict) -> Optional[Dict]:
        """Update a webhook endpoint"""
        if endpoint_id not in self._endpoints:
            return None

        endpoint = self._endpoints[endpoint_id]

        for field in ["name", "description", "url", "events", "custom_headers",
                      "content_type", "timeout_seconds", "max_retries", "is_active"]:
            if field in data:
                endpoint[field] = data[field]

        # Handle reactivation
        if data.get("is_active") and endpoint.get("disabled_at"):
            endpoint["disabled_at"] = None
            endpoint["disabled_reason"] = None
            endpoint["consecutive_failures"] = 0

        endpoint["updated_at"] = datetime.utcnow().isoformat()
        return endpoint

    def record_success(self, endpoint_id: str):
        """Record successful delivery"""
        if endpoint_id in self._endpoints:
            self._endpoints[endpoint_id]["last_success_at"] = datetime.utcnow().isoformat()
            self._endpoints[endpoint_id]["consecutive_failures"] = 0

    def record_failure(self, endpoint_id: str, reason: str = None):
        """Record failed delivery"""
        if endpoint_id in self._endpoints:
            endpoint = self._endpoints[endpoint_id]
            endpoint["last_failure_at"] = datetime.utcnow().isoformat()
            endpoint["consecutive_failures"] = endpoint.get("consecutive_failures", 0) + 1

            # Auto-disable if threshold reached
            if endpoint["consecutive_failures"] >= endpoint.get("failure_threshold", 10):
                endpoint["is_active"] = False
                endpoint["disabled_at"] = datetime.utcnow().isoformat()
                endpoint["disabled_reason"] = f"Auto-disabled after {endpoint['consecutive_failures']} consecutive failures"

    def regenerate_secret(self, endpoint_id: str) -> Optional[str]:
        """Regenerate signing secret"""
        if endpoint_id not in self._endpoints:
            return None

        new_secret = f"whsec_{secrets.token_urlsafe(32)}"
        self._endpoints[endpoint_id]["secret"] = new_secret
        self._endpoints[endpoint_id]["updated_at"] = datetime.utcnow().isoformat()

        return new_secret

    def delete(self, endpoint_id: str) -> bool:
        """Delete a webhook endpoint"""
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            return True
        return False


class WebhookDeliveryStore:
    """Store for webhook delivery tracking"""

    RETRY_DELAYS = [60, 300, 1800, 7200, 86400]  # 1m, 5m, 30m, 2h, 24h

    def __init__(self):
        self._deliveries: Dict[str, dict] = {}
        self._attempts: List[dict] = []
        self._max_attempts = 10000

    def create(self, data: Dict) -> Dict:
        """Create a new delivery record"""
        delivery_id = str(uuid4())

        delivery = {
            "id": delivery_id,
            "endpoint_id": data.get("endpoint_id"),
            "tenant_id": data.get("tenant_id"),
            "event_type": data.get("event_type"),
            "event_id": data.get("event_id", str(uuid4())),
            "payload": data.get("payload"),
            "status": "pending",  # pending, delivering, delivered, failed, cancelled
            "attempt_count": 0,
            "max_attempts": data.get("max_attempts", 5),
            "next_retry_at": None,
            "response_status": None,
            "response_body": None,
            "response_headers": None,
            "response_time_ms": None,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "delivered_at": None
        }

        self._deliveries[delivery_id] = delivery
        return delivery

    def find_by_id(self, delivery_id: str) -> Optional[Dict]:
        """Find delivery by ID"""
        return self._deliveries.get(delivery_id)

    def find_by_endpoint(self, endpoint_id: str, limit: int = 50) -> List[Dict]:
        """Find deliveries for an endpoint"""
        deliveries = [
            d for d in self._deliveries.values()
            if d.get("endpoint_id") == endpoint_id
        ]
        return sorted(deliveries, key=lambda x: x["created_at"], reverse=True)[:limit]

    def find_pending_retries(self, limit: int = 100) -> List[Dict]:
        """Find deliveries pending retry"""
        now = datetime.utcnow().isoformat()

        deliveries = [
            d for d in self._deliveries.values()
            if d.get("status") == "pending" and
               d.get("next_retry_at") and
               d.get("next_retry_at") <= now and
               d.get("attempt_count", 0) < d.get("max_attempts", 5)
        ]

        return sorted(deliveries, key=lambda x: x.get("next_retry_at", ""))[:limit]

    def update_status(self, delivery_id: str, status: str, **kwargs) -> Optional[Dict]:
        """Update delivery status"""
        if delivery_id not in self._deliveries:
            return None

        delivery = self._deliveries[delivery_id]
        delivery["status"] = status

        for key, value in kwargs.items():
            delivery[key] = value

        return delivery

    def mark_delivered(self, delivery_id: str, response_status: int,
                      response_time_ms: int, response_body: str = None):
        """Mark delivery as successful"""
        if delivery_id in self._deliveries:
            delivery = self._deliveries[delivery_id]
            delivery["status"] = "delivered"
            delivery["delivered_at"] = datetime.utcnow().isoformat()
            delivery["response_status"] = response_status
            delivery["response_time_ms"] = response_time_ms
            delivery["response_body"] = response_body[:5000] if response_body else None

    def mark_failed(self, delivery_id: str, error_message: str,
                   response_status: int = None):
        """Mark delivery attempt as failed and schedule retry"""
        if delivery_id not in self._deliveries:
            return

        delivery = self._deliveries[delivery_id]
        delivery["error_message"] = error_message
        delivery["response_status"] = response_status

        # Check if can retry
        if delivery["attempt_count"] >= delivery["max_attempts"]:
            delivery["status"] = "failed"
        else:
            # Schedule retry
            idx = min(delivery["attempt_count"], len(self.RETRY_DELAYS) - 1)
            delay = self.RETRY_DELAYS[idx]
            delivery["next_retry_at"] = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
            delivery["status"] = "pending"

    def increment_attempt(self, delivery_id: str):
        """Increment attempt counter"""
        if delivery_id in self._deliveries:
            self._deliveries[delivery_id]["attempt_count"] = \
                self._deliveries[delivery_id].get("attempt_count", 0) + 1
            self._deliveries[delivery_id]["status"] = "delivering"

    def record_attempt(self, data: Dict) -> Dict:
        """Record a delivery attempt"""
        attempt = {
            "id": str(uuid4()),
            "delivery_id": data.get("delivery_id"),
            "attempt_number": data.get("attempt_number"),
            "request_url": data.get("request_url"),
            "request_headers": data.get("request_headers"),
            "request_body": data.get("request_body"),
            "response_status": data.get("response_status"),
            "response_headers": data.get("response_headers"),
            "response_body": data.get("response_body"),
            "response_time_ms": data.get("response_time_ms"),
            "error_type": data.get("error_type"),
            "error_message": data.get("error_message"),
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at", datetime.utcnow().isoformat())
        }

        self._attempts.insert(0, attempt)

        # Trim attempts
        if len(self._attempts) > self._max_attempts:
            self._attempts = self._attempts[:self._max_attempts]

        return attempt

    def get_attempts(self, delivery_id: str) -> List[Dict]:
        """Get attempts for a delivery"""
        return [
            a for a in self._attempts
            if a.get("delivery_id") == delivery_id
        ]

    def cancel(self, delivery_id: str) -> bool:
        """Cancel a pending delivery"""
        if delivery_id in self._deliveries:
            if self._deliveries[delivery_id]["status"] != "delivered":
                self._deliveries[delivery_id]["status"] = "cancelled"
                return True
        return False


class WebhookDatabase:
    """Webhook database container"""

    def __init__(self):
        self.endpoints = WebhookEndpointStore()
        self.deliveries = WebhookDeliveryStore()


# Global webhook database instance
webhook_db = WebhookDatabase()


def get_event_definitions() -> Dict:
    """Get all event definitions"""
    return EVENT_DEFINITIONS


def get_event_types() -> List[str]:
    """Get all event type names"""
    return list(EVENT_DEFINITIONS.keys())


def get_events_by_category(category: str) -> List[Dict]:
    """Get events by category"""
    return [
        {"event_type": k, **v}
        for k, v in EVENT_DEFINITIONS.items()
        if v["category"].value == category
    ]


def get_all_categories() -> List[str]:
    """Get all event categories"""
    return [c.value for c in EventCategory]


def init_webhook_database():
    """Initialize webhook database (called from main)"""
    print("Webhook database initialized")
