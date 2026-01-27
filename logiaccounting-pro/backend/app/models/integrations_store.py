"""
Phase 14: External Integrations Hub - Data Store
In-memory data store for integrations
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum
import secrets
import hashlib
import json


class IntegrationStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"


class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING_OUTBOUND = "pending_outbound"
    PENDING_INBOUND = "pending_inbound"
    CONFLICT = "conflict"
    ERROR = "error"


class SyncLogStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConflictResolution(str, Enum):
    LAST_WRITE_WINS = "last_write_wins"
    SOURCE_PRIORITY = "source_priority"
    MANUAL_REVIEW = "manual_review"
    MERGE = "merge"


class TransformType(str, Enum):
    DIRECT = "direct"
    FORMAT = "format"
    LOOKUP = "lookup"
    COMPUTE = "compute"
    CONSTANT = "constant"
    CONCAT = "concat"
    SPLIT = "split"
    CAST = "cast"


# Provider configurations
PROVIDER_CONFIGS = {
    "quickbooks": {
        "name": "quickbooks",
        "label": "QuickBooks Online",
        "category": "accounting",
        "description": "Sync invoices, customers, and payments with QuickBooks",
        "auth_type": "oauth2",
        "logo": "/static/integrations/quickbooks.svg",
        "oauth_config": {
            "authorization_url": "https://appcenter.intuit.com/connect/oauth2",
            "token_url": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            "scopes": ["com.intuit.quickbooks.accounting"],
        },
        "supported_entities": ["customer", "supplier", "product", "invoice", "bill", "payment", "account"],
    },
    "xero": {
        "name": "xero",
        "label": "Xero",
        "category": "accounting",
        "description": "Connect with Xero for accounting synchronization",
        "auth_type": "oauth2",
        "logo": "/static/integrations/xero.svg",
        "oauth_config": {
            "authorization_url": "https://login.xero.com/identity/connect/authorize",
            "token_url": "https://identity.xero.com/connect/token",
            "scopes": ["openid", "profile", "email", "offline_access", "accounting.transactions", "accounting.contacts"],
        },
        "supported_entities": ["customer", "supplier", "invoice", "bill", "payment", "product", "account"],
    },
    "salesforce": {
        "name": "salesforce",
        "label": "Salesforce",
        "category": "crm",
        "description": "Sync customers and opportunities with Salesforce CRM",
        "auth_type": "oauth2",
        "logo": "/static/integrations/salesforce.svg",
        "oauth_config": {
            "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
            "token_url": "https://login.salesforce.com/services/oauth2/token",
            "scopes": ["api", "refresh_token", "offline_access"],
        },
        "supported_entities": ["customer", "contact", "lead", "opportunity", "product", "order", "task"],
    },
    "hubspot": {
        "name": "hubspot",
        "label": "HubSpot",
        "category": "crm",
        "description": "Connect with HubSpot CRM for contact management",
        "auth_type": "oauth2",
        "logo": "/static/integrations/hubspot.svg",
        "oauth_config": {
            "authorization_url": "https://app.hubspot.com/oauth/authorize",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read"],
        },
        "supported_entities": ["customer", "contact", "company", "opportunity", "deal", "product", "ticket"],
    },
    "shopify": {
        "name": "shopify",
        "label": "Shopify",
        "category": "ecommerce",
        "description": "Sync products, orders, and inventory with Shopify",
        "auth_type": "oauth2",
        "logo": "/static/integrations/shopify.svg",
        "oauth_config": {
            "authorization_url": "https://{shop}.myshopify.com/admin/oauth/authorize",
            "token_url": "https://{shop}.myshopify.com/admin/oauth/access_token",
            "scopes": ["read_products", "write_products", "read_orders", "write_orders", "read_customers"],
        },
        "supported_entities": ["product", "order", "customer", "inventory", "fulfillment", "collection"],
    },
    "stripe": {
        "name": "stripe",
        "label": "Stripe",
        "category": "payments",
        "description": "Process payments and sync transactions",
        "auth_type": "api_key",
        "logo": "/static/integrations/stripe.svg",
        "supported_entities": ["customer", "payment", "invoice", "subscription", "product", "price", "charge", "payout"],
    },
    "plaid": {
        "name": "plaid",
        "label": "Plaid",
        "category": "banking",
        "description": "Connect bank accounts for transaction import",
        "auth_type": "link",
        "logo": "/static/integrations/plaid.svg",
        "supported_entities": ["account", "transaction", "balance"],
    },
}


class IntegrationStore:
    """Store for integration connections"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, organization_id: Optional[str] = None,
                 category: Optional[str] = None,
                 status: Optional[str] = None) -> List[Dict]:
        results = self._data.copy()
        if organization_id:
            results = [i for i in results if i.get("organization_id") == organization_id]
        if category:
            results = [i for i in results if i.get("category") == category]
        if status:
            results = [i for i in results if i.get("status") == status]
        return results

    def find_by_id(self, integration_id: str) -> Optional[Dict]:
        return next((i for i in self._data if i["id"] == integration_id), None)

    def find_by_provider(self, organization_id: str, provider: str) -> Optional[Dict]:
        return next(
            (i for i in self._data
             if i["organization_id"] == organization_id and i["provider"] == provider),
            None
        )

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        integration = {
            "id": str(uuid4()),
            "organization_id": data["organization_id"],
            "provider": data["provider"],
            "category": data.get("category") or PROVIDER_CONFIGS.get(data["provider"], {}).get("category", "generic"),
            "name": data.get("name") or PROVIDER_CONFIGS.get(data["provider"], {}).get("label", data["provider"]),
            "description": data.get("description"),
            "icon_url": data.get("icon_url") or PROVIDER_CONFIGS.get(data["provider"], {}).get("logo"),
            "status": data.get("status", IntegrationStatus.DISCONNECTED),

            # OAuth tokens (encrypted in production)
            "oauth_access_token": data.get("oauth_access_token"),
            "oauth_refresh_token": data.get("oauth_refresh_token"),
            "oauth_token_expires_at": data.get("oauth_token_expires_at"),
            "oauth_scope": data.get("oauth_scope"),

            # API credentials
            "api_key": data.get("api_key"),
            "api_secret": data.get("api_secret"),

            # Provider-specific config
            "config": data.get("config", {}),

            # Sync settings
            "sync_enabled": data.get("sync_enabled", False),
            "sync_direction": data.get("sync_direction", SyncDirection.BIDIRECTIONAL),
            "sync_frequency_minutes": data.get("sync_frequency_minutes", 60),
            "last_sync_at": None,
            "next_sync_at": None,

            # Error tracking
            "last_error": None,
            "last_error_at": None,
            "error_count": 0,

            # Metadata
            "connected_by": data.get("connected_by"),
            "connected_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self._data.append(integration)
        return integration

    def update(self, integration_id: str, data: Dict) -> Optional[Dict]:
        for i, integration in enumerate(self._data):
            if integration["id"] == integration_id:
                self._data[i] = {
                    **integration,
                    **{k: v for k, v in data.items() if v is not None},
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, integration_id: str) -> bool:
        for i, integration in enumerate(self._data):
            if integration["id"] == integration_id:
                self._data.pop(i)
                return True
        return False

    def update_tokens(self, integration_id: str,
                      access_token: str,
                      refresh_token: str = None,
                      expires_in: int = None,
                      scope: str = None) -> Optional[Dict]:
        """Update OAuth tokens"""
        integration = self.find_by_id(integration_id)
        if not integration:
            return None

        update_data = {
            "oauth_access_token": access_token,
            "status": IntegrationStatus.CONNECTED,
            "last_error": None,
            "error_count": 0,
        }

        if refresh_token:
            update_data["oauth_refresh_token"] = refresh_token

        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            update_data["oauth_token_expires_at"] = expires_at.isoformat()

        if scope:
            update_data["oauth_scope"] = scope

        return self.update(integration_id, update_data)

    def mark_connected(self, integration_id: str, user_id: str = None) -> Optional[Dict]:
        """Mark integration as connected"""
        return self.update(integration_id, {
            "status": IntegrationStatus.CONNECTED,
            "connected_at": datetime.utcnow().isoformat(),
            "connected_by": user_id,
            "last_error": None,
            "error_count": 0,
        })

    def mark_error(self, integration_id: str, error: str) -> Optional[Dict]:
        """Mark integration with error"""
        integration = self.find_by_id(integration_id)
        if not integration:
            return None

        return self.update(integration_id, {
            "status": IntegrationStatus.ERROR,
            "last_error": error,
            "last_error_at": datetime.utcnow().isoformat(),
            "error_count": integration.get("error_count", 0) + 1,
        })

    def disconnect(self, integration_id: str) -> Optional[Dict]:
        """Disconnect integration"""
        return self.update(integration_id, {
            "status": IntegrationStatus.DISCONNECTED,
            "oauth_access_token": None,
            "oauth_refresh_token": None,
            "oauth_token_expires_at": None,
            "api_key": None,
            "api_secret": None,
            "connected_at": None,
            "connected_by": None,
            "sync_enabled": False,
        })

    def record_sync(self, integration_id: str) -> Optional[Dict]:
        """Record that a sync occurred"""
        integration = self.find_by_id(integration_id)
        if not integration:
            return None

        now = datetime.utcnow()
        next_sync = None
        if integration.get("sync_enabled") and integration.get("sync_frequency_minutes"):
            next_sync = (now + timedelta(minutes=integration["sync_frequency_minutes"])).isoformat()

        return self.update(integration_id, {
            "last_sync_at": now.isoformat(),
            "next_sync_at": next_sync,
        })

    def is_token_expired(self, integration_id: str) -> bool:
        """Check if OAuth token is expired"""
        integration = self.find_by_id(integration_id)
        if not integration or not integration.get("oauth_token_expires_at"):
            return False

        expires_at = datetime.fromisoformat(integration["oauth_token_expires_at"])
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (expires_at - buffer)


class SyncConfigStore:
    """Store for sync configurations"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, integration_id: Optional[str] = None) -> List[Dict]:
        results = self._data.copy()
        if integration_id:
            results = [s for s in results if s.get("integration_id") == integration_id]
        return results

    def find_by_id(self, config_id: str) -> Optional[Dict]:
        return next((s for s in self._data if s["id"] == config_id), None)

    def find_by_entities(self, integration_id: str,
                         local_entity: str,
                         remote_entity: str) -> Optional[Dict]:
        return next(
            (s for s in self._data
             if s["integration_id"] == integration_id
             and s["local_entity"] == local_entity
             and s["remote_entity"] == remote_entity),
            None
        )

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        config = {
            "id": str(uuid4()),
            "integration_id": data["integration_id"],
            "local_entity": data["local_entity"],
            "remote_entity": data["remote_entity"],
            "sync_enabled": data.get("sync_enabled", True),
            "sync_direction": data.get("sync_direction", SyncDirection.BIDIRECTIONAL),
            "sync_filter": data.get("sync_filter", {}),
            "conflict_resolution": data.get("conflict_resolution", ConflictResolution.LAST_WRITE_WINS),
            "priority_source": data.get("priority_source", "local"),
            "last_sync_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self._data.append(config)
        return config

    def update(self, config_id: str, data: Dict) -> Optional[Dict]:
        for i, config in enumerate(self._data):
            if config["id"] == config_id:
                self._data[i] = {
                    **config,
                    **{k: v for k, v in data.items() if v is not None},
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, config_id: str) -> bool:
        for i, config in enumerate(self._data):
            if config["id"] == config_id:
                self._data.pop(i)
                return True
        return False

    def delete_by_integration(self, integration_id: str) -> int:
        """Delete all configs for an integration"""
        count = 0
        self._data = [s for s in self._data if s["integration_id"] != integration_id or (count := count + 1) == -1]
        return count


class FieldMappingStore:
    """Store for field mappings"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, sync_config_id: Optional[str] = None) -> List[Dict]:
        results = self._data.copy()
        if sync_config_id:
            results = [m for m in results if m.get("sync_config_id") == sync_config_id]
        return results

    def find_by_id(self, mapping_id: str) -> Optional[Dict]:
        return next((m for m in self._data if m["id"] == mapping_id), None)

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        mapping = {
            "id": str(uuid4()),
            "sync_config_id": data["sync_config_id"],
            "local_field": data["local_field"],
            "remote_field": data["remote_field"],
            "transform_type": data.get("transform_type", TransformType.DIRECT),
            "transform_config": data.get("transform_config", {}),
            "direction": data.get("direction", SyncDirection.BIDIRECTIONAL),
            "is_required": data.get("is_required", False),
            "default_value": data.get("default_value"),
            "created_at": now,
        }
        self._data.append(mapping)
        return mapping

    def update(self, mapping_id: str, data: Dict) -> Optional[Dict]:
        for i, mapping in enumerate(self._data):
            if mapping["id"] == mapping_id:
                self._data[i] = {
                    **mapping,
                    **{k: v for k, v in data.items() if v is not None},
                }
                return self._data[i]
        return None

    def delete(self, mapping_id: str) -> bool:
        for i, mapping in enumerate(self._data):
            if mapping["id"] == mapping_id:
                self._data.pop(i)
                return True
        return False

    def delete_by_sync_config(self, sync_config_id: str) -> int:
        """Delete all mappings for a sync config"""
        original_len = len(self._data)
        self._data = [m for m in self._data if m["sync_config_id"] != sync_config_id]
        return original_len - len(self._data)


class SyncLogStore:
    """Store for sync operation logs"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, integration_id: Optional[str] = None,
                 limit: int = 100,
                 offset: int = 0) -> List[Dict]:
        results = self._data.copy()
        if integration_id:
            results = [l for l in results if l.get("integration_id") == integration_id]
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[offset:offset + limit]

    def find_by_id(self, log_id: str) -> Optional[Dict]:
        return next((l for l in self._data if l["id"] == log_id), None)

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        log = {
            "id": str(uuid4()),
            "integration_id": data["integration_id"],
            "sync_config_id": data.get("sync_config_id"),
            "sync_type": data["sync_type"],  # 'full', 'incremental', 'manual', 'webhook'
            "direction": data["direction"],  # 'inbound', 'outbound'
            "entity_type": data.get("entity_type"),
            "status": data.get("status", SyncLogStatus.PENDING),
            "records_processed": 0,
            "records_created": 0,
            "records_updated": 0,
            "records_failed": 0,
            "records_skipped": 0,
            "errors": [],
            "started_at": None,
            "completed_at": None,
            "duration_ms": None,
            "triggered_by": data.get("triggered_by", "manual"),
            "triggered_by_user_id": data.get("triggered_by_user_id"),
            "created_at": now,
        }
        self._data.append(log)
        return log

    def update(self, log_id: str, data: Dict) -> Optional[Dict]:
        for i, log in enumerate(self._data):
            if log["id"] == log_id:
                self._data[i] = {**log, **{k: v for k, v in data.items() if v is not None}}
                return self._data[i]
        return None

    def start(self, log_id: str) -> Optional[Dict]:
        """Mark sync as started"""
        return self.update(log_id, {
            "status": SyncLogStatus.RUNNING,
            "started_at": datetime.utcnow().isoformat(),
        })

    def complete(self, log_id: str, status: str = SyncLogStatus.COMPLETED) -> Optional[Dict]:
        """Mark sync as completed"""
        log = self.find_by_id(log_id)
        if not log:
            return None

        now = datetime.utcnow()
        duration_ms = None
        if log.get("started_at"):
            started = datetime.fromisoformat(log["started_at"])
            duration_ms = int((now - started).total_seconds() * 1000)

        return self.update(log_id, {
            "status": status,
            "completed_at": now.isoformat(),
            "duration_ms": duration_ms,
        })

    def add_error(self, log_id: str, error: Dict) -> Optional[Dict]:
        """Add an error to the log"""
        log = self.find_by_id(log_id)
        if not log:
            return None

        errors = log.get("errors", [])
        errors.append({
            **error,
            "timestamp": datetime.utcnow().isoformat()
        })

        return self.update(log_id, {
            "errors": errors,
            "records_failed": log.get("records_failed", 0) + 1,
        })

    def increment_stats(self, log_id: str,
                        created: int = 0,
                        updated: int = 0,
                        skipped: int = 0) -> Optional[Dict]:
        """Increment statistics"""
        log = self.find_by_id(log_id)
        if not log:
            return None

        return self.update(log_id, {
            "records_created": log.get("records_created", 0) + created,
            "records_updated": log.get("records_updated", 0) + updated,
            "records_skipped": log.get("records_skipped", 0) + skipped,
            "records_processed": log.get("records_processed", 0) + created + updated + skipped,
        })


class SyncRecordStore:
    """Store for tracking individual synced records"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_by_local_id(self, sync_config_id: str, local_id: str) -> Optional[Dict]:
        return next(
            (r for r in self._data
             if r["sync_config_id"] == sync_config_id and r["local_id"] == local_id),
            None
        )

    def find_by_remote_id(self, sync_config_id: str, remote_id: str) -> Optional[Dict]:
        return next(
            (r for r in self._data
             if r["sync_config_id"] == sync_config_id and r["remote_id"] == remote_id),
            None
        )

    def find_by_status(self, integration_id: str,
                       status: str,
                       limit: int = 100) -> List[Dict]:
        results = [
            r for r in self._data
            if r["integration_id"] == integration_id and r["sync_status"] == status
        ]
        return results[:limit]

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        record = {
            "id": str(uuid4()),
            "integration_id": data["integration_id"],
            "sync_config_id": data["sync_config_id"],
            "local_id": data["local_id"],
            "remote_id": data["remote_id"],
            "local_hash": data.get("local_hash"),
            "remote_hash": data.get("remote_hash"),
            "local_updated_at": data.get("local_updated_at"),
            "remote_updated_at": data.get("remote_updated_at"),
            "last_synced_at": now,
            "sync_status": data.get("sync_status", SyncStatus.SYNCED),
            "created_at": now,
            "updated_at": now,
        }
        self._data.append(record)
        return record

    def update(self, record_id: str, data: Dict) -> Optional[Dict]:
        for i, record in enumerate(self._data):
            if record["id"] == record_id:
                self._data[i] = {
                    **record,
                    **{k: v for k, v in data.items() if v is not None},
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def upsert(self, sync_config_id: str, local_id: str, remote_id: str,
               data: Dict) -> Dict:
        """Create or update a sync record"""
        existing = self.find_by_local_id(sync_config_id, local_id)
        if existing:
            return self.update(existing["id"], {**data, "remote_id": remote_id})

        return self.create({
            **data,
            "sync_config_id": sync_config_id,
            "local_id": local_id,
            "remote_id": remote_id,
        })


class WebhookStore:
    """Store for webhook registrations"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, integration_id: Optional[str] = None) -> List[Dict]:
        results = self._data.copy()
        if integration_id:
            results = [w for w in results if w.get("integration_id") == integration_id]
        return results

    def find_by_id(self, webhook_id: str) -> Optional[Dict]:
        return next((w for w in self._data if w["id"] == webhook_id), None)

    def find_by_event(self, integration_id: str, event_type: str) -> Optional[Dict]:
        return next(
            (w for w in self._data
             if w["integration_id"] == integration_id and w["event_type"] == event_type),
            None
        )

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        webhook = {
            "id": str(uuid4()),
            "integration_id": data["integration_id"],
            "event_type": data["event_type"],
            "endpoint_url": data["endpoint_url"],
            "secret_hash": secrets.token_hex(32),
            "is_active": data.get("is_active", True),
            "provider_webhook_id": data.get("provider_webhook_id"),
            "total_received": 0,
            "total_processed": 0,
            "total_failed": 0,
            "last_received_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self._data.append(webhook)
        return webhook

    def update(self, webhook_id: str, data: Dict) -> Optional[Dict]:
        for i, webhook in enumerate(self._data):
            if webhook["id"] == webhook_id:
                self._data[i] = {
                    **webhook,
                    **{k: v for k, v in data.items() if v is not None},
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, webhook_id: str) -> bool:
        for i, webhook in enumerate(self._data):
            if webhook["id"] == webhook_id:
                self._data.pop(i)
                return True
        return False

    def record_received(self, webhook_id: str, processed: bool = True) -> Optional[Dict]:
        """Record webhook received"""
        webhook = self.find_by_id(webhook_id)
        if not webhook:
            return None

        update_data = {
            "total_received": webhook.get("total_received", 0) + 1,
            "last_received_at": datetime.utcnow().isoformat(),
        }

        if processed:
            update_data["total_processed"] = webhook.get("total_processed", 0) + 1
        else:
            update_data["total_failed"] = webhook.get("total_failed", 0) + 1

        return self.update(webhook_id, update_data)


class WebhookEventStore:
    """Store for received webhook events"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def find_all(self, webhook_id: Optional[str] = None,
                 status: Optional[str] = None,
                 limit: int = 100) -> List[Dict]:
        results = self._data.copy()
        if webhook_id:
            results = [e for e in results if e.get("webhook_id") == webhook_id]
        if status:
            results = [e for e in results if e.get("status") == status]
        results.sort(key=lambda x: x.get("received_at", ""), reverse=True)
        return results[:limit]

    def find_by_id(self, event_id: str) -> Optional[Dict]:
        return next((e for e in self._data if e["id"] == event_id), None)

    def create(self, data: Dict) -> Dict:
        now = datetime.utcnow().isoformat()
        event = {
            "id": str(uuid4()),
            "webhook_id": data["webhook_id"],
            "event_type": data["event_type"],
            "payload": data["payload"],
            "headers": data.get("headers", {}),
            "status": data.get("status", "pending"),
            "processed_at": None,
            "error_message": None,
            "retry_count": 0,
            "received_at": now,
        }
        self._data.append(event)
        return event

    def update(self, event_id: str, data: Dict) -> Optional[Dict]:
        for i, event in enumerate(self._data):
            if event["id"] == event_id:
                self._data[i] = {**event, **{k: v for k, v in data.items() if v is not None}}
                return self._data[i]
        return None

    def mark_processed(self, event_id: str) -> Optional[Dict]:
        return self.update(event_id, {
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat(),
        })

    def mark_failed(self, event_id: str, error: str) -> Optional[Dict]:
        event = self.find_by_id(event_id)
        if not event:
            return None

        return self.update(event_id, {
            "status": "failed",
            "error_message": error,
            "retry_count": event.get("retry_count", 0) + 1,
        })


class OAuthStateStore:
    """Store for OAuth state tokens"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, organization_id: str, provider: str, user_id: str,
               redirect_uri: str = None, additional_data: Dict = None,
               expires_in_minutes: int = 10) -> Dict:
        """Create a new OAuth state"""
        now = datetime.utcnow()
        state = {
            "id": str(uuid4()),
            "state": secrets.token_urlsafe(32),
            "organization_id": organization_id,
            "provider": provider,
            "user_id": user_id,
            "redirect_uri": redirect_uri,
            "additional_data": additional_data or {},
            "expires_at": (now + timedelta(minutes=expires_in_minutes)).isoformat(),
            "created_at": now.isoformat(),
        }
        self._data.append(state)
        return state

    def validate_and_consume(self, state: str, provider: str) -> Optional[Dict]:
        """Validate state and remove it (one-time use)"""
        now = datetime.utcnow()

        for i, oauth_state in enumerate(self._data):
            if (oauth_state["state"] == state
                and oauth_state["provider"] == provider
                and datetime.fromisoformat(oauth_state["expires_at"]) > now):
                return self._data.pop(i)

        return None

    def cleanup_expired(self) -> int:
        """Remove expired states"""
        now = datetime.utcnow()
        original_len = len(self._data)
        self._data = [
            s for s in self._data
            if datetime.fromisoformat(s["expires_at"]) > now
        ]
        return original_len - len(self._data)


# Global stores
integrations_store = IntegrationStore()
sync_configs_store = SyncConfigStore()
field_mappings_store = FieldMappingStore()
sync_logs_store = SyncLogStore()
sync_records_store = SyncRecordStore()
webhooks_store = WebhookStore()
webhook_events_store = WebhookEventStore()
oauth_states_store = OAuthStateStore()


def init_integrations_database():
    """Initialize integrations database with demo data"""
    # Demo integration (disconnected)
    integrations_store.create({
        "organization_id": "demo-org",
        "provider": "quickbooks",
        "name": "QuickBooks Online",
        "status": IntegrationStatus.DISCONNECTED,
    })

    print("Integrations database initialized")
