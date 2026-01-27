"""
Integration with existing LogiAccounting Pro events.
Hooks into entity operations to trigger workflows.
"""
from typing import Dict, Any, Optional
import logging

from app.workflows.engine.core import workflow_engine


logger = logging.getLogger(__name__)


def emit_entity_event(
    entity: str,
    event: str,
    data: Dict[str, Any],
    tenant_id: str,
    user_id: Optional[str] = None
):
    """
    Emit an entity event to trigger workflows.

    Call this from existing routes after entity operations:
    - After creating an invoice
    - After updating a payment
    - After deleting a project
    - etc.

    Args:
        entity: Entity type (invoice, payment, project, etc.)
        event: Event type (created, updated, deleted, etc.)
        data: Entity data (the created/updated/deleted record)
        tenant_id: Tenant ID
        user_id: User who performed the action
    """
    workflow_engine.on_entity_event(
        entity=entity,
        event=event,
        data=data,
        tenant_id=tenant_id,
        user_id=user_id
    )


def on_invoice_created(invoice: Dict, tenant_id: str, user_id: str = None):
    """Called when an invoice is created."""
    emit_entity_event("invoice", "created", invoice, tenant_id, user_id)


def on_invoice_updated(invoice: Dict, tenant_id: str, user_id: str = None):
    """Called when an invoice is updated."""
    emit_entity_event("invoice", "updated", invoice, tenant_id, user_id)


def on_invoice_paid(invoice: Dict, tenant_id: str, user_id: str = None):
    """Called when an invoice is marked as paid."""
    emit_entity_event("invoice", "paid", invoice, tenant_id, user_id)


def on_invoice_overdue(invoice: Dict, tenant_id: str):
    """Called when an invoice becomes overdue."""
    emit_entity_event("invoice", "overdue", invoice, tenant_id)


def on_payment_created(payment: Dict, tenant_id: str, user_id: str = None):
    """Called when a payment is created."""
    emit_entity_event("payment", "created", payment, tenant_id, user_id)


def on_payment_confirmed(payment: Dict, tenant_id: str, user_id: str = None):
    """Called when a payment is confirmed."""
    emit_entity_event("payment", "confirmed", payment, tenant_id, user_id)


def on_project_created(project: Dict, tenant_id: str, user_id: str = None):
    """Called when a project is created."""
    emit_entity_event("project", "created", project, tenant_id, user_id)


def on_project_completed(project: Dict, tenant_id: str, user_id: str = None):
    """Called when a project is completed."""
    emit_entity_event("project", "completed", project, tenant_id, user_id)


def on_inventory_low_stock(item: Dict, tenant_id: str):
    """Called when inventory item falls below threshold."""
    emit_entity_event("inventory", "low_stock", item, tenant_id)


def on_approval_requested(approval: Dict, tenant_id: str, user_id: str = None):
    """Called when approval is requested."""
    emit_entity_event("approval", "requested", approval, tenant_id, user_id)


def on_approval_completed(approval: Dict, tenant_id: str, user_id: str = None):
    """Called when approval is completed (approved/rejected)."""
    emit_entity_event("approval", "completed", approval, tenant_id, user_id)
