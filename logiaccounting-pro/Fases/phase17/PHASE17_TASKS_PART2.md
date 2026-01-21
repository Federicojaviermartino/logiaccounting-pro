# LogiAccounting Pro - Phase 17 Tasks Part 2

## WEBHOOKS SYSTEM

---

## TASK 6: WEBHOOK MODELS

### 6.1 Webhook Endpoint Model

**File:** `backend/app/webhooks/models/webhook_endpoint.py`

```python
"""
Webhook Endpoint Model
Webhook subscriptions and configuration
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import secrets


class WebhookEndpoint(db.Model):
    """Webhook endpoint subscription"""
    
    __tablename__ = 'webhook_endpoints'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Endpoint Info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(2048), nullable=False)
    
    # Authentication
    secret = Column(String(255), nullable=False)  # For HMAC signature
    
    # Events (subscribed event types)
    events = Column(ARRAY(Text), nullable=False)
    # ['invoice.created', 'invoice.paid', 'payment.received', '*']
    
    # Headers (custom headers to include)
    custom_headers = Column(JSONB, default=dict)
    
    # Settings
    content_type = Column(String(50), default='application/json')
    timeout_seconds = Column(Integer, default=30)
    
    # Retry Policy
    max_retries = Column(Integer, default=5)
    retry_delay_seconds = Column(Integer, default=60)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Health
    last_success_at = Column(db.DateTime)
    last_failure_at = Column(db.DateTime)
    consecutive_failures = Column(Integer, default=0)
    
    # Auto-disable after N failures
    failure_threshold = Column(Integer, default=10)
    disabled_at = Column(db.DateTime)
    disabled_reason = Column(Text)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', backref='webhook_endpoints')
    deliveries = relationship('WebhookDelivery', back_populates='endpoint', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        if 'secret' not in kwargs:
            kwargs['secret'] = self.generate_secret()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_secret() -> str:
        """Generate webhook signing secret"""
        return f"whsec_{secrets.token_urlsafe(32)}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if webhook is in healthy state"""
        if not self.is_active:
            return False
        if self.disabled_at:
            return False
        return self.consecutive_failures < self.failure_threshold
    
    def matches_event(self, event_type: str) -> bool:
        """Check if endpoint subscribes to event type"""
        if '*' in self.events:
            return True
        
        if event_type in self.events:
            return True
        
        # Check for category wildcard (e.g., 'invoice.*')
        category = event_type.split('.')[0]
        if f'{category}.*' in self.events:
            return True
        
        return False
    
    def record_success(self):
        """Record successful delivery"""
        self.last_success_at = datetime.utcnow()
        self.consecutive_failures = 0
    
    def record_failure(self, reason: str = None):
        """Record failed delivery"""
        self.last_failure_at = datetime.utcnow()
        self.consecutive_failures = (self.consecutive_failures or 0) + 1
        
        # Auto-disable if threshold reached
        if self.consecutive_failures >= self.failure_threshold:
            self.is_active = False
            self.disabled_at = datetime.utcnow()
            self.disabled_reason = f"Auto-disabled after {self.consecutive_failures} consecutive failures"
    
    def reactivate(self):
        """Reactivate a disabled webhook"""
        self.is_active = True
        self.disabled_at = None
        self.disabled_reason = None
        self.consecutive_failures = 0
    
    def regenerate_secret(self) -> str:
        """Generate a new signing secret"""
        self.secret = self.generate_secret()
        return self.secret
    
    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'events': self.events,
            'custom_headers': self.custom_headers or {},
            'content_type': self.content_type,
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'is_active': self.is_active,
            'is_healthy': self.is_healthy,
            'last_success_at': self.last_success_at.isoformat() if self.last_success_at else None,
            'last_failure_at': self.last_failure_at.isoformat() if self.last_failure_at else None,
            'consecutive_failures': self.consecutive_failures,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_secret:
            data['secret'] = self.secret
        
        return data


class WebhookEventType(db.Model):
    """Webhook event type definition"""
    
    __tablename__ = 'webhook_event_types'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event Info
    event_type = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Payload Schema (JSON Schema)
    payload_schema = Column(JSONB, nullable=False)
    
    # Sample Payload
    sample_payload = Column(JSONB)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # API Version introduced
    api_version = Column(String(10), default='v1')
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_type': self.event_type,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'payload_schema': self.payload_schema,
            'sample_payload': self.sample_payload,
            'api_version': self.api_version,
        }
```

### 6.2 Webhook Delivery Model

**File:** `backend/app/webhooks/models/webhook_delivery.py`

```python
"""
Webhook Delivery Model
Track webhook delivery attempts and status
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class WebhookDelivery(db.Model):
    """Webhook delivery tracking"""
    
    __tablename__ = 'webhook_deliveries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(UUID(as_uuid=True), db.ForeignKey('webhook_endpoints.id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event
    event_type = Column(String(100), nullable=False)
    event_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to source event
    
    # Payload
    payload = Column(JSONB, nullable=False)
    
    # Delivery Status
    status = Column(String(20), default='pending', index=True)
    # 'pending', 'delivering', 'delivered', 'failed', 'cancelled'
    
    # Attempts
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    next_retry_at = Column(db.DateTime, index=True)
    
    # Response
    response_status = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSONB)
    response_time_ms = Column(Integer)
    
    # Error
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow, index=True)
    delivered_at = Column(db.DateTime)
    
    # Relationships
    endpoint = relationship('WebhookEndpoint', back_populates='deliveries')
    attempts = relationship('WebhookDeliveryAttempt', back_populates='delivery', cascade='all, delete-orphan')
    
    # Retry delays (exponential backoff)
    RETRY_DELAYS = [60, 300, 1800, 7200, 86400]  # 1m, 5m, 30m, 2h, 24h
    
    @property
    def can_retry(self) -> bool:
        """Check if delivery can be retried"""
        if self.status == 'delivered':
            return False
        if self.status == 'cancelled':
            return False
        return self.attempt_count < self.max_attempts
    
    def get_next_retry_delay(self) -> int:
        """Get delay for next retry attempt"""
        idx = min(self.attempt_count, len(self.RETRY_DELAYS) - 1)
        return self.RETRY_DELAYS[idx]
    
    def schedule_retry(self):
        """Schedule next retry attempt"""
        from datetime import timedelta
        
        if not self.can_retry:
            self.status = 'failed'
            return
        
        delay = self.get_next_retry_delay()
        self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        self.status = 'pending'
    
    def mark_delivered(self, response_status: int, response_time_ms: int, response_body: str = None):
        """Mark delivery as successful"""
        self.status = 'delivered'
        self.delivered_at = datetime.utcnow()
        self.response_status = response_status
        self.response_time_ms = response_time_ms
        self.response_body = response_body
        
        # Update endpoint health
        self.endpoint.record_success()
    
    def mark_failed(self, error_message: str, response_status: int = None):
        """Mark delivery attempt as failed"""
        self.error_message = error_message
        self.response_status = response_status
        
        # Update endpoint health
        self.endpoint.record_failure(error_message)
        
        # Schedule retry or mark as final failure
        self.schedule_retry()
    
    def cancel(self):
        """Cancel pending delivery"""
        if self.status == 'delivered':
            return False
        
        self.status = 'cancelled'
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'endpoint_id': str(self.endpoint_id),
            'event_type': self.event_type,
            'event_id': str(self.event_id),
            'status': self.status,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
        }


class WebhookDeliveryAttempt(db.Model):
    """Individual delivery attempt details"""
    
    __tablename__ = 'webhook_delivery_attempts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id = Column(UUID(as_uuid=True), db.ForeignKey('webhook_deliveries.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Attempt
    attempt_number = Column(Integer, nullable=False)
    
    # Request
    request_url = Column(String(2048), nullable=False)
    request_headers = Column(JSONB, nullable=False)
    request_body = Column(Text, nullable=False)
    
    # Response
    response_status = Column(Integer)
    response_headers = Column(JSONB)
    response_body = Column(Text)
    response_time_ms = Column(Integer)
    
    # Error
    error_type = Column(String(50))  # 'timeout', 'connection_error', 'ssl_error'
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(db.DateTime, nullable=False)
    completed_at = Column(db.DateTime)
    
    # Relationships
    delivery = relationship('WebhookDelivery', back_populates='attempts')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'attempt_number': self.attempt_number,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
```

---

## TASK 7: EVENT EMITTER & TYPES

### 7.1 Event Type Definitions

**File:** `backend/app/webhooks/core/event_types.py`

```python
"""
Webhook Event Types
Definition of all available webhook events
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class EventCategory(str, Enum):
    """Event categories"""
    INVOICES = 'invoices'
    PAYMENTS = 'payments'
    INVENTORY = 'inventory'
    PROJECTS = 'projects'
    CUSTOMERS = 'customers'
    SUPPLIERS = 'suppliers'
    DOCUMENTS = 'documents'
    USERS = 'users'
    SYSTEM = 'system'


@dataclass
class EventDefinition:
    """Event type definition"""
    event_type: str
    category: EventCategory
    name: str
    description: str
    payload_fields: List[str]


# All available events
EVENT_DEFINITIONS: Dict[str, EventDefinition] = {
    # Invoice Events
    'invoice.created': EventDefinition(
        event_type='invoice.created',
        category=EventCategory.INVOICES,
        name='Invoice Created',
        description='Triggered when a new invoice is created',
        payload_fields=['id', 'number', 'customer_id', 'total', 'status', 'created_at']
    ),
    'invoice.updated': EventDefinition(
        event_type='invoice.updated',
        category=EventCategory.INVOICES,
        name='Invoice Updated',
        description='Triggered when an invoice is modified',
        payload_fields=['id', 'number', 'changes', 'updated_at']
    ),
    'invoice.sent': EventDefinition(
        event_type='invoice.sent',
        category=EventCategory.INVOICES,
        name='Invoice Sent',
        description='Triggered when an invoice is sent to customer',
        payload_fields=['id', 'number', 'sent_to', 'sent_at']
    ),
    'invoice.paid': EventDefinition(
        event_type='invoice.paid',
        category=EventCategory.INVOICES,
        name='Invoice Paid',
        description='Triggered when an invoice is marked as paid',
        payload_fields=['id', 'number', 'paid_amount', 'paid_at', 'payment_method']
    ),
    'invoice.overdue': EventDefinition(
        event_type='invoice.overdue',
        category=EventCategory.INVOICES,
        name='Invoice Overdue',
        description='Triggered when an invoice becomes overdue',
        payload_fields=['id', 'number', 'days_overdue', 'amount_due']
    ),
    'invoice.voided': EventDefinition(
        event_type='invoice.voided',
        category=EventCategory.INVOICES,
        name='Invoice Voided',
        description='Triggered when an invoice is voided/cancelled',
        payload_fields=['id', 'number', 'voided_at', 'reason']
    ),
    'invoice.deleted': EventDefinition(
        event_type='invoice.deleted',
        category=EventCategory.INVOICES,
        name='Invoice Deleted',
        description='Triggered when an invoice is deleted',
        payload_fields=['id', 'number', 'deleted_at']
    ),
    
    # Payment Events
    'payment.received': EventDefinition(
        event_type='payment.received',
        category=EventCategory.PAYMENTS,
        name='Payment Received',
        description='Triggered when a payment is received',
        payload_fields=['id', 'amount', 'currency', 'invoice_id', 'method', 'received_at']
    ),
    'payment.refunded': EventDefinition(
        event_type='payment.refunded',
        category=EventCategory.PAYMENTS,
        name='Payment Refunded',
        description='Triggered when a payment is refunded',
        payload_fields=['id', 'refund_amount', 'reason', 'refunded_at']
    ),
    'payment.failed': EventDefinition(
        event_type='payment.failed',
        category=EventCategory.PAYMENTS,
        name='Payment Failed',
        description='Triggered when a payment attempt fails',
        payload_fields=['id', 'amount', 'error_code', 'error_message', 'failed_at']
    ),
    
    # Inventory Events
    'product.created': EventDefinition(
        event_type='product.created',
        category=EventCategory.INVENTORY,
        name='Product Created',
        description='Triggered when a new product is created',
        payload_fields=['id', 'sku', 'name', 'price', 'stock_quantity']
    ),
    'product.updated': EventDefinition(
        event_type='product.updated',
        category=EventCategory.INVENTORY,
        name='Product Updated',
        description='Triggered when a product is modified',
        payload_fields=['id', 'sku', 'changes', 'updated_at']
    ),
    'product.deleted': EventDefinition(
        event_type='product.deleted',
        category=EventCategory.INVENTORY,
        name='Product Deleted',
        description='Triggered when a product is deleted',
        payload_fields=['id', 'sku', 'deleted_at']
    ),
    'stock.low': EventDefinition(
        event_type='stock.low',
        category=EventCategory.INVENTORY,
        name='Low Stock Alert',
        description='Triggered when stock falls below threshold',
        payload_fields=['product_id', 'sku', 'current_stock', 'threshold']
    ),
    'stock.out': EventDefinition(
        event_type='stock.out',
        category=EventCategory.INVENTORY,
        name='Out of Stock',
        description='Triggered when a product is out of stock',
        payload_fields=['product_id', 'sku', 'last_stock_at']
    ),
    'stock.adjusted': EventDefinition(
        event_type='stock.adjusted',
        category=EventCategory.INVENTORY,
        name='Stock Adjusted',
        description='Triggered when stock quantity is adjusted',
        payload_fields=['product_id', 'sku', 'previous_quantity', 'new_quantity', 'reason']
    ),
    
    # Project Events
    'project.created': EventDefinition(
        event_type='project.created',
        category=EventCategory.PROJECTS,
        name='Project Created',
        description='Triggered when a new project is created',
        payload_fields=['id', 'name', 'client_id', 'budget', 'start_date']
    ),
    'project.updated': EventDefinition(
        event_type='project.updated',
        category=EventCategory.PROJECTS,
        name='Project Updated',
        description='Triggered when a project is modified',
        payload_fields=['id', 'name', 'changes', 'updated_at']
    ),
    'project.status_changed': EventDefinition(
        event_type='project.status_changed',
        category=EventCategory.PROJECTS,
        name='Project Status Changed',
        description='Triggered when project status changes',
        payload_fields=['id', 'name', 'old_status', 'new_status', 'changed_at']
    ),
    'project.completed': EventDefinition(
        event_type='project.completed',
        category=EventCategory.PROJECTS,
        name='Project Completed',
        description='Triggered when a project is marked complete',
        payload_fields=['id', 'name', 'completed_at', 'final_budget']
    ),
    'project.milestone_completed': EventDefinition(
        event_type='project.milestone_completed',
        category=EventCategory.PROJECTS,
        name='Milestone Completed',
        description='Triggered when a project milestone is completed',
        payload_fields=['project_id', 'milestone_id', 'name', 'completed_at']
    ),
    
    # Customer Events
    'customer.created': EventDefinition(
        event_type='customer.created',
        category=EventCategory.CUSTOMERS,
        name='Customer Created',
        description='Triggered when a new customer is created',
        payload_fields=['id', 'email', 'name', 'company', 'created_at']
    ),
    'customer.updated': EventDefinition(
        event_type='customer.updated',
        category=EventCategory.CUSTOMERS,
        name='Customer Updated',
        description='Triggered when customer info is modified',
        payload_fields=['id', 'changes', 'updated_at']
    ),
    'customer.deleted': EventDefinition(
        event_type='customer.deleted',
        category=EventCategory.CUSTOMERS,
        name='Customer Deleted',
        description='Triggered when a customer is deleted',
        payload_fields=['id', 'deleted_at']
    ),
    
    # Document Events
    'document.uploaded': EventDefinition(
        event_type='document.uploaded',
        category=EventCategory.DOCUMENTS,
        name='Document Uploaded',
        description='Triggered when a document is uploaded',
        payload_fields=['id', 'filename', 'size_bytes', 'mime_type', 'uploaded_at']
    ),
    'document.processed': EventDefinition(
        event_type='document.processed',
        category=EventCategory.DOCUMENTS,
        name='Document Processed',
        description='Triggered when OCR/processing completes',
        payload_fields=['id', 'filename', 'extracted_data', 'processed_at']
    ),
    'document.signed': EventDefinition(
        event_type='document.signed',
        category=EventCategory.DOCUMENTS,
        name='Document Signed',
        description='Triggered when a document is digitally signed',
        payload_fields=['id', 'signed_by', 'signed_at']
    ),
    
    # User Events
    'user.invited': EventDefinition(
        event_type='user.invited',
        category=EventCategory.USERS,
        name='User Invited',
        description='Triggered when a user is invited to the organization',
        payload_fields=['email', 'role', 'invited_by', 'invited_at']
    ),
    'user.joined': EventDefinition(
        event_type='user.joined',
        category=EventCategory.USERS,
        name='User Joined',
        description='Triggered when a user accepts an invitation',
        payload_fields=['id', 'email', 'role', 'joined_at']
    ),
    'user.removed': EventDefinition(
        event_type='user.removed',
        category=EventCategory.USERS,
        name='User Removed',
        description='Triggered when a user is removed from the organization',
        payload_fields=['id', 'email', 'removed_by', 'removed_at']
    ),
}


def get_event_definition(event_type: str) -> EventDefinition:
    """Get event definition by type"""
    return EVENT_DEFINITIONS.get(event_type)


def get_events_by_category(category: EventCategory) -> List[EventDefinition]:
    """Get all events in a category"""
    return [
        event for event in EVENT_DEFINITIONS.values()
        if event.category == category
    ]


def get_all_event_types() -> List[str]:
    """Get all available event types"""
    return list(EVENT_DEFINITIONS.keys())


def get_all_categories() -> List[str]:
    """Get all event categories"""
    return [c.value for c in EventCategory]
```

### 7.2 Event Emitter

**File:** `backend/app/webhooks/core/event_emitter.py`

```python
"""
Event Emitter
Emit events for webhook delivery
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import logging

from app.extensions import db
from app.webhooks.models.webhook_endpoint import WebhookEndpoint
from app.webhooks.models.webhook_delivery import WebhookDelivery
from app.webhooks.core.event_types import get_event_definition
from app.tenancy.core.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class EventEmitter:
    """Emit webhook events"""
    
    @staticmethod
    def emit(
        event_type: str,
        payload: Dict[str, Any],
        tenant=None,
        entity_id: str = None,
        async_delivery: bool = True
    ) -> Optional[str]:
        """
        Emit a webhook event
        
        Args:
            event_type: Type of event (e.g., 'invoice.created')
            payload: Event payload data
            tenant: Tenant context (uses current if not provided)
            entity_id: ID of the related entity
            async_delivery: If True, queue for async delivery
            
        Returns:
            Event ID if emitted successfully
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            logger.warning(f"Cannot emit event {event_type}: No tenant context")
            return None
        
        # Validate event type
        event_def = get_event_definition(event_type)
        if not event_def:
            logger.warning(f"Unknown event type: {event_type}")
            return None
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Build full payload
        full_payload = EventEmitter._build_payload(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            tenant=tenant
        )
        
        # Find matching webhook endpoints
        endpoints = WebhookEndpoint.query.filter(
            WebhookEndpoint.tenant_id == tenant.id,
            WebhookEndpoint.is_active == True,
            WebhookEndpoint.disabled_at == None
        ).all()
        
        # Filter endpoints that subscribe to this event
        matching_endpoints = [
            ep for ep in endpoints
            if ep.matches_event(event_type)
        ]
        
        if not matching_endpoints:
            logger.debug(f"No webhooks subscribed to {event_type} for tenant {tenant.slug}")
            return event_id
        
        # Create delivery records
        deliveries = []
        for endpoint in matching_endpoints:
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                tenant_id=tenant.id,
                event_type=event_type,
                event_id=event_id,
                payload=full_payload,
                max_attempts=endpoint.max_retries,
            )
            db.session.add(delivery)
            deliveries.append(delivery)
        
        db.session.commit()
        
        logger.info(f"Emitted event {event_type} ({event_id}) to {len(deliveries)} endpoints")
        
        # Queue for delivery
        if async_delivery and deliveries:
            from app.webhooks.tasks.delivery_tasks import deliver_webhook
            
            for delivery in deliveries:
                deliver_webhook.delay(str(delivery.id))
        
        return event_id
    
    @staticmethod
    def _build_payload(
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        tenant
    ) -> Dict[str, Any]:
        """Build the full webhook payload"""
        return {
            'id': event_id,
            'type': event_type,
            'api_version': 'v1',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'tenant_id': str(tenant.id),
            'data': payload,
        }


# Convenience functions for common events
def emit_invoice_created(invoice_data: Dict[str, Any]):
    """Emit invoice.created event"""
    return EventEmitter.emit('invoice.created', invoice_data)


def emit_invoice_paid(invoice_id: str, payment_data: Dict[str, Any]):
    """Emit invoice.paid event"""
    return EventEmitter.emit('invoice.paid', {
        'invoice_id': invoice_id,
        **payment_data
    })


def emit_payment_received(payment_data: Dict[str, Any]):
    """Emit payment.received event"""
    return EventEmitter.emit('payment.received', payment_data)


def emit_product_created(product_data: Dict[str, Any]):
    """Emit product.created event"""
    return EventEmitter.emit('product.created', product_data)


def emit_stock_low(product_id: str, current_stock: int, threshold: int):
    """Emit stock.low event"""
    return EventEmitter.emit('stock.low', {
        'product_id': product_id,
        'current_stock': current_stock,
        'threshold': threshold,
    })


def emit_customer_created(customer_data: Dict[str, Any]):
    """Emit customer.created event"""
    return EventEmitter.emit('customer.created', customer_data)
```

---

## TASK 8: SIGNATURE & DELIVERY

### 8.1 HMAC Signature

**File:** `backend/app/webhooks/core/signature.py`

```python
"""
Webhook Signature
HMAC signature generation and verification
"""

import hmac
import hashlib
import time
from typing import Tuple


class WebhookSignature:
    """Webhook signature handling"""
    
    SIGNATURE_VERSION = 'v1'
    TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    @classmethod
    def sign(cls, payload: str, secret: str, timestamp: int = None) -> Tuple[str, int]:
        """
        Sign a webhook payload
        
        Args:
            payload: JSON payload string
            secret: Webhook signing secret
            timestamp: Unix timestamp (current time if not provided)
            
        Returns:
            Tuple of (signature, timestamp)
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Create signed payload (timestamp.payload)
        signed_payload = f"{timestamp}.{payload}"
        
        # Generate HMAC-SHA256
        signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"{cls.SIGNATURE_VERSION}={signature}", timestamp
    
    @classmethod
    def verify(cls, payload: str, signature: str, timestamp: str, secret: str) -> bool:
        """
        Verify a webhook signature
        
        Args:
            payload: JSON payload string
            signature: Signature header value
            timestamp: Timestamp header value
            secret: Webhook signing secret
            
        Returns:
            True if signature is valid
        """
        try:
            # Check timestamp tolerance
            ts = int(timestamp)
            now = int(time.time())
            
            if abs(now - ts) > cls.TIMESTAMP_TOLERANCE:
                return False
            
            # Parse signature
            if not signature.startswith(f"{cls.SIGNATURE_VERSION}="):
                return False
            
            expected_sig = signature.split('=', 1)[1]
            
            # Generate expected signature
            signed_payload = f"{ts}.{payload}"
            computed_sig = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(expected_sig, computed_sig)
            
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def get_headers(cls, payload: str, secret: str) -> dict:
        """
        Get webhook signature headers
        
        Args:
            payload: JSON payload string
            secret: Webhook signing secret
            
        Returns:
            Dict of headers to include
        """
        signature, timestamp = cls.sign(payload, secret)
        
        return {
            'X-Webhook-Signature': signature,
            'X-Webhook-Timestamp': str(timestamp),
        }
```

### 8.2 Delivery Manager

**File:** `backend/app/webhooks/core/delivery_manager.py`

```python
"""
Webhook Delivery Manager
Handle webhook delivery with retries
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging
import httpx

from app.extensions import db
from app.webhooks.models.webhook_delivery import WebhookDelivery, WebhookDeliveryAttempt
from app.webhooks.core.signature import WebhookSignature

logger = logging.getLogger(__name__)


class DeliveryManager:
    """Manage webhook delivery"""
    
    DEFAULT_TIMEOUT = 30  # seconds
    
    @classmethod
    def deliver(cls, delivery_id: str) -> bool:
        """
        Attempt to deliver a webhook
        
        Args:
            delivery_id: Delivery record ID
            
        Returns:
            True if delivery successful
        """
        delivery = WebhookDelivery.query.get(delivery_id)
        
        if not delivery:
            logger.error(f"Delivery not found: {delivery_id}")
            return False
        
        if delivery.status == 'delivered':
            logger.info(f"Delivery {delivery_id} already delivered")
            return True
        
        if delivery.status == 'cancelled':
            logger.info(f"Delivery {delivery_id} was cancelled")
            return False
        
        # Update status
        delivery.status = 'delivering'
        delivery.attempt_count += 1
        db.session.commit()
        
        # Get endpoint
        endpoint = delivery.endpoint
        
        if not endpoint or not endpoint.is_active:
            delivery.status = 'failed'
            delivery.error_message = 'Endpoint inactive'
            db.session.commit()
            return False
        
        # Prepare payload
        payload_json = json.dumps(delivery.payload, separators=(',', ':'))
        
        # Generate signature
        signature_headers = WebhookSignature.get_headers(payload_json, endpoint.secret)
        
        # Build headers
        headers = {
            'Content-Type': endpoint.content_type or 'application/json',
            'User-Agent': 'LogiAccounting-Webhook/1.0',
            **signature_headers,
            **(endpoint.custom_headers or {})
        }
        
        # Create attempt record
        attempt = WebhookDeliveryAttempt(
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count,
            request_url=endpoint.url,
            request_headers=headers,
            request_body=payload_json,
            started_at=datetime.utcnow(),
        )
        db.session.add(attempt)
        
        # Make request
        try:
            timeout = endpoint.timeout_seconds or cls.DEFAULT_TIMEOUT
            
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    endpoint.url,
                    content=payload_json,
                    headers=headers,
                )
            
            # Record response
            attempt.response_status = response.status_code
            attempt.response_body = response.text[:5000]  # Limit size
            attempt.response_headers = dict(response.headers)
            attempt.response_time_ms = int(response.elapsed.total_seconds() * 1000)
            attempt.completed_at = datetime.utcnow()
            
            # Check success (2xx status)
            if 200 <= response.status_code < 300:
                delivery.mark_delivered(
                    response_status=response.status_code,
                    response_time_ms=attempt.response_time_ms,
                    response_body=attempt.response_body
                )
                db.session.commit()
                
                logger.info(f"Webhook delivered: {delivery_id} to {endpoint.url}")
                return True
            else:
                # Non-2xx response
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                delivery.mark_failed(error_msg, response.status_code)
                db.session.commit()
                
                logger.warning(f"Webhook failed: {delivery_id} - {error_msg}")
                return False
                
        except httpx.TimeoutException:
            attempt.error_type = 'timeout'
            attempt.error_message = f"Request timed out after {timeout}s"
            attempt.completed_at = datetime.utcnow()
            
            delivery.mark_failed(attempt.error_message)
            db.session.commit()
            
            logger.warning(f"Webhook timeout: {delivery_id} to {endpoint.url}")
            return False
            
        except httpx.ConnectError as e:
            attempt.error_type = 'connection_error'
            attempt.error_message = str(e)
            attempt.completed_at = datetime.utcnow()
            
            delivery.mark_failed(attempt.error_message)
            db.session.commit()
            
            logger.warning(f"Webhook connection error: {delivery_id} - {e}")
            return False
            
        except Exception as e:
            attempt.error_type = 'unknown'
            attempt.error_message = str(e)
            attempt.completed_at = datetime.utcnow()
            
            delivery.mark_failed(str(e))
            db.session.commit()
            
            logger.error(f"Webhook error: {delivery_id} - {e}")
            return False
    
    @classmethod
    def retry_failed(cls, max_retries: int = 100) -> int:
        """
        Retry failed deliveries that are due
        
        Returns:
            Number of deliveries queued
        """
        from app.webhooks.tasks.delivery_tasks import deliver_webhook
        
        # Find deliveries due for retry
        deliveries = WebhookDelivery.query.filter(
            WebhookDelivery.status == 'pending',
            WebhookDelivery.next_retry_at <= datetime.utcnow(),
            WebhookDelivery.attempt_count < WebhookDelivery.max_attempts
        ).limit(max_retries).all()
        
        count = 0
        for delivery in deliveries:
            deliver_webhook.delay(str(delivery.id))
            count += 1
        
        if count > 0:
            logger.info(f"Queued {count} webhook retries")
        
        return count
    
    @classmethod
    def send_test(cls, endpoint_id: str) -> Dict[str, Any]:
        """
        Send a test webhook to an endpoint
        
        Args:
            endpoint_id: Webhook endpoint ID
            
        Returns:
            Test result
        """
        from app.webhooks.models.webhook_endpoint import WebhookEndpoint
        
        endpoint = WebhookEndpoint.query.get(endpoint_id)
        
        if not endpoint:
            return {
                'success': False,
                'error': 'Endpoint not found'
            }
        
        # Build test payload
        test_payload = {
            'id': 'test_' + str(datetime.utcnow().timestamp()),
            'type': 'test.ping',
            'api_version': 'v1',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'data': {
                'message': 'This is a test webhook from LogiAccounting Pro',
                'endpoint_id': str(endpoint.id),
            }
        }
        
        payload_json = json.dumps(test_payload, separators=(',', ':'))
        signature_headers = WebhookSignature.get_headers(payload_json, endpoint.secret)
        
        headers = {
            'Content-Type': endpoint.content_type or 'application/json',
            'User-Agent': 'LogiAccounting-Webhook/1.0',
            **signature_headers,
            **(endpoint.custom_headers or {})
        }
        
        try:
            timeout = endpoint.timeout_seconds or cls.DEFAULT_TIMEOUT
            
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    endpoint.url,
                    content=payload_json,
                    headers=headers,
                )
            
            return {
                'success': 200 <= response.status_code < 300,
                'status_code': response.status_code,
                'response_time_ms': int(response.elapsed.total_seconds() * 1000),
                'response_body': response.text[:1000],
            }
            
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'timeout',
                'error_message': f"Request timed out after {timeout}s"
            }
            
        except httpx.ConnectError as e:
            return {
                'success': False,
                'error': 'connection_error',
                'error_message': str(e)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown',
                'error_message': str(e)
            }
```

---

## TASK 9: CELERY TASKS

### 9.1 Delivery Tasks

**File:** `backend/app/webhooks/tasks/delivery_tasks.py`

```python
"""
Webhook Delivery Tasks
Celery tasks for async webhook delivery
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def deliver_webhook(self, delivery_id: str):
    """
    Deliver a webhook asynchronously
    
    Args:
        delivery_id: WebhookDelivery ID
    """
    from app.webhooks.core.delivery_manager import DeliveryManager
    
    try:
        success = DeliveryManager.deliver(delivery_id)
        return {'success': success, 'delivery_id': delivery_id}
        
    except Exception as e:
        logger.error(f"Webhook delivery task failed: {e}")
        raise


@shared_task
def process_retry_queue():
    """Process pending webhook retries"""
    from app.webhooks.core.delivery_manager import DeliveryManager
    
    count = DeliveryManager.retry_failed(max_retries=100)
    return {'retries_queued': count}


@shared_task
def cleanup_old_deliveries(days: int = 30):
    """Clean up old delivery records"""
    from datetime import datetime, timedelta
    from app.extensions import db
    from app.webhooks.models.webhook_delivery import WebhookDelivery, WebhookDeliveryAttempt
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Delete old attempts first (due to foreign key)
    old_deliveries = WebhookDelivery.query.filter(
        WebhookDelivery.created_at < cutoff,
        WebhookDelivery.status.in_(['delivered', 'failed', 'cancelled'])
    ).all()
    
    delivery_ids = [d.id for d in old_deliveries]
    
    if delivery_ids:
        # Delete attempts
        WebhookDeliveryAttempt.query.filter(
            WebhookDeliveryAttempt.delivery_id.in_(delivery_ids)
        ).delete(synchronize_session=False)
        
        # Delete deliveries
        WebhookDelivery.query.filter(
            WebhookDelivery.id.in_(delivery_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        logger.info(f"Cleaned up {len(delivery_ids)} old webhook deliveries")
    
    return {'deleted': len(delivery_ids)}


@shared_task
def check_endpoint_health():
    """Check health of webhook endpoints and disable unhealthy ones"""
    from app.webhooks.models.webhook_endpoint import WebhookEndpoint
    from app.extensions import db
    
    # Find endpoints that have exceeded failure threshold
    unhealthy = WebhookEndpoint.query.filter(
        WebhookEndpoint.is_active == True,
        WebhookEndpoint.disabled_at == None,
        WebhookEndpoint.consecutive_failures >= WebhookEndpoint.failure_threshold
    ).all()
    
    for endpoint in unhealthy:
        endpoint.is_active = False
        endpoint.disabled_at = datetime.utcnow()
        endpoint.disabled_reason = f"Auto-disabled: {endpoint.consecutive_failures} consecutive failures"
        
        logger.warning(f"Auto-disabled webhook endpoint: {endpoint.id}")
    
    if unhealthy:
        db.session.commit()
    
    return {'disabled': len(unhealthy)}
```

---

## Continue to Part 3 for API Routes & Frontend

---

*Phase 17 Tasks Part 2 - LogiAccounting Pro*
*Webhooks System*
