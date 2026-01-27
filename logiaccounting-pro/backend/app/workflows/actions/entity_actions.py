"""
Entity CRUD action executors.
Create, update, and delete entities in the system.
"""
from typing import Dict, Any
from datetime import datetime
import logging
import re
import uuid

from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


class UpdateEntityExecutor(ActionExecutor):
    """Updates an existing entity."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an entity.

        Config:
            entity: Entity type (invoice, payment, project, etc.)
            id: Entity ID (or variable reference)
            updates: Dictionary of field updates
        """
        entity_type = config.get("entity")
        entity_id = self._interpolate(config.get("id", ""), variables)
        updates = self._interpolate_dict(config.get("updates", {}), variables)

        if not entity_type or not entity_id:
            return {"updated": False, "error": "Missing entity or id"}

        store = self._get_store(entity_type)
        if not store:
            return {"updated": False, "error": f"Unknown entity type: {entity_type}"}

        entity = store.get(entity_id) if hasattr(store, 'get') else None
        if not entity:
            return {"updated": False, "error": f"Entity not found: {entity_id}"}

        for key, value in updates.items():
            entity[key] = value

        entity["updated_at"] = datetime.utcnow().isoformat()

        if hasattr(store, 'save'):
            store.save(entity)

        logger.info(f"Updated {entity_type} {entity_id}")

        return {
            "updated": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "updates": updates
        }

    def _get_store(self, entity_type: str):
        """Get the store for an entity type."""
        try:
            from app.models import store as app_store

            stores = {
                "invoice": getattr(app_store, 'invoices', None),
                "payment": getattr(app_store, 'payments', None),
                "project": getattr(app_store, 'projects', None),
                "transaction": getattr(app_store, 'transactions', None),
                "inventory": getattr(app_store, 'inventory', None),
            }

            return stores.get(entity_type)
        except ImportError:
            return None

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in text."""
        def replace(match):
            key = match.group(1).strip()
            value = self._get_nested(variables, key)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)

    def _interpolate_dict(
        self,
        obj: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpolate variables in dictionary."""
        result = {}

        for key, value in obj.items():
            if isinstance(value, str):
                result[key] = self._interpolate(value, variables)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict(value, variables)
            else:
                result[key] = value

        return result

    def _get_nested(self, obj: Dict, path: str) -> Any:
        """Get nested value from dict."""
        keys = path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value


class CreateEntityExecutor(ActionExecutor):
    """Creates a new entity."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an entity.

        Config:
            entity: Entity type
            data: Entity data
        """
        entity_type = config.get("entity")
        data = self._interpolate_dict(config.get("data", {}), variables)

        if not entity_type:
            return {"created": False, "error": "Missing entity type"}

        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        data["created_at"] = datetime.utcnow().isoformat()

        store = self._get_store(entity_type)
        if not store:
            return {"created": False, "error": f"Unknown entity type: {entity_type}"}

        if hasattr(store, 'save'):
            store.save(data)

        logger.info(f"Created {entity_type} {data['id']}")

        return {
            "created": True,
            "entity_type": entity_type,
            "entity_id": data["id"],
            "entity": data
        }

    def _get_store(self, entity_type: str):
        """Get the store for an entity type."""
        try:
            from app.models import store as app_store

            stores = {
                "invoice": getattr(app_store, 'invoices', None),
                "payment": getattr(app_store, 'payments', None),
                "project": getattr(app_store, 'projects', None),
                "transaction": getattr(app_store, 'transactions', None),
                "inventory": getattr(app_store, 'inventory', None),
            }

            return stores.get(entity_type)
        except ImportError:
            return None

    def _interpolate_dict(
        self,
        obj: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpolate variables in dictionary."""
        result = {}

        for key, value in obj.items():
            if isinstance(value, str):
                result[key] = self._interpolate(value, variables)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict(value, variables)
            else:
                result[key] = value

        return result

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables."""
        def replace(match):
            key = match.group(1).strip()
            parts = key.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)


class DeleteEntityExecutor(ActionExecutor):
    """Deletes an entity."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delete an entity.

        Config:
            entity: Entity type
            id: Entity ID
            soft_delete: Whether to soft delete (default: True)
        """
        entity_type = config.get("entity")
        entity_id = self._interpolate(config.get("id", ""), variables)
        soft_delete = config.get("soft_delete", True)

        if not entity_type or not entity_id:
            return {"deleted": False, "error": "Missing entity or id"}

        store = self._get_store(entity_type)
        if not store:
            return {"deleted": False, "error": f"Unknown entity type: {entity_type}"}

        if soft_delete:
            entity = store.get(entity_id) if hasattr(store, 'get') else None
            if entity:
                entity["deleted"] = True
                entity["deleted_at"] = datetime.utcnow().isoformat()
                if hasattr(store, 'save'):
                    store.save(entity)
        else:
            if hasattr(store, 'delete'):
                store.delete(entity_id)

        logger.info(f"Deleted {entity_type} {entity_id} (soft={soft_delete})")

        return {
            "deleted": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "soft_delete": soft_delete
        }

    def _get_store(self, entity_type: str):
        """Get the store for an entity type."""
        try:
            from app.models import store as app_store

            stores = {
                "invoice": getattr(app_store, 'invoices', None),
                "payment": getattr(app_store, 'payments', None),
                "project": getattr(app_store, 'projects', None),
                "transaction": getattr(app_store, 'transactions', None),
                "inventory": getattr(app_store, 'inventory', None),
            }

            return stores.get(entity_type)
        except ImportError:
            return None

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables."""
        def replace(match):
            key = match.group(1).strip()
            parts = key.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)
