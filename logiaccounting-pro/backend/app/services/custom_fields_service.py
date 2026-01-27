"""
Custom Fields Service
Extend entities with user-defined fields
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


class CustomFieldsService:
    """Manages custom field definitions and values"""

    _instance = None
    _fields: Dict[str, dict] = {}
    _values: Dict[str, Dict[str, Any]] = {}  # entity_key -> field_values
    _counter = 0

    FIELD_TYPES = [
        "text", "textarea", "number", "currency", "date", "datetime",
        "dropdown", "multiselect", "checkbox", "url", "email", "phone", "formula"
    ]

    SUPPORTED_ENTITIES = ["materials", "transactions", "payments", "projects", "categories"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._fields = {}
            cls._values = {}
            cls._counter = 0
        return cls._instance

    def create_field(
        self,
        entity: str,
        name: str,
        label: str,
        field_type: str,
        required: bool = False,
        default_value: Any = None,
        options: List[str] = None,
        validation: dict = None,
        placeholder: str = "",
        help_text: str = "",
        position: int = 0,
        group: str = "Custom Fields",
        searchable: bool = False,
        show_in_list: bool = False
    ) -> dict:
        """Create a custom field definition"""
        if entity not in self.SUPPORTED_ENTITIES:
            return {"error": f"Entity {entity} not supported"}
        if field_type not in self.FIELD_TYPES:
            return {"error": f"Field type {field_type} not supported"}

        self._counter += 1
        field_id = f"CF-{self._counter:04d}"

        field = {
            "id": field_id,
            "entity": entity,
            "name": name,
            "label": label,
            "type": field_type,
            "required": required,
            "default_value": default_value,
            "options": options or [],
            "validation": validation or {},
            "placeholder": placeholder,
            "help_text": help_text,
            "position": position,
            "group": group,
            "searchable": searchable,
            "show_in_list": show_in_list,
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }

        self._fields[field_id] = field
        return field

    def update_field(self, field_id: str, updates: dict) -> Optional[dict]:
        """Update a custom field definition"""
        if field_id not in self._fields:
            return None

        field = self._fields[field_id]

        for key, value in updates.items():
            if key in field and key not in ["id", "entity", "created_at"]:
                field[key] = value

        return field

    def delete_field(self, field_id: str) -> bool:
        """Delete a custom field"""
        if field_id not in self._fields:
            return False

        # Remove all values for this field
        field = self._fields[field_id]
        for entity_key in list(self._values.keys()):
            if entity_key.startswith(f"{field['entity']}:"):
                if field_id in self._values[entity_key]:
                    del self._values[entity_key][field_id]

        del self._fields[field_id]
        return True

    def get_field(self, field_id: str) -> Optional[dict]:
        """Get a custom field"""
        return self._fields.get(field_id)

    def get_entity_fields(self, entity: str, active_only: bool = True) -> List[dict]:
        """Get all custom fields for an entity"""
        fields = [f for f in self._fields.values() if f["entity"] == entity]
        if active_only:
            fields = [f for f in fields if f["active"]]
        return sorted(fields, key=lambda x: x["position"])

    def set_value(self, entity: str, entity_id: str, field_id: str, value: Any) -> dict:
        """Set a custom field value for an entity instance"""
        field = self._fields.get(field_id)
        if not field:
            return {"error": "Field not found"}
        if field["entity"] != entity:
            return {"error": "Field does not belong to this entity"}

        # Validate value
        validation_error = self._validate_value(field, value)
        if validation_error:
            return {"error": validation_error}

        entity_key = f"{entity}:{entity_id}"
        if entity_key not in self._values:
            self._values[entity_key] = {}

        self._values[entity_key][field_id] = value

        return {
            "entity": entity,
            "entity_id": entity_id,
            "field_id": field_id,
            "value": value
        }

    def _validate_value(self, field: dict, value: Any) -> Optional[str]:
        """Validate a value against field rules"""
        if field["required"] and (value is None or value == ""):
            return f"Field {field['label']} is required"

        if value is None or value == "":
            return None

        validation = field.get("validation", {})

        if field["type"] == "number" or field["type"] == "currency":
            try:
                num_value = float(value)
                if "min" in validation and num_value < validation["min"]:
                    return f"Value must be at least {validation['min']}"
                if "max" in validation and num_value > validation["max"]:
                    return f"Value must be at most {validation['max']}"
            except (ValueError, TypeError):
                return "Invalid number value"

        if field["type"] == "text" or field["type"] == "textarea":
            if "max_length" in validation and len(str(value)) > validation["max_length"]:
                return f"Value must be at most {validation['max_length']} characters"

        if field["type"] == "dropdown" and field.get("options"):
            if value not in field["options"]:
                return f"Value must be one of: {', '.join(field['options'])}"

        if field["type"] == "multiselect" and field.get("options"):
            if not isinstance(value, list):
                return "Value must be a list"
            for v in value:
                if v not in field["options"]:
                    return f"Invalid option: {v}"

        if field["type"] == "email" and value:
            if "@" not in str(value):
                return "Invalid email format"

        if field["type"] == "url" and value:
            if not str(value).startswith(("http://", "https://")):
                return "URL must start with http:// or https://"

        return None

    def get_value(self, entity: str, entity_id: str, field_id: str) -> Any:
        """Get a custom field value"""
        entity_key = f"{entity}:{entity_id}"
        if entity_key not in self._values:
            field = self._fields.get(field_id)
            return field.get("default_value") if field else None

        return self._values[entity_key].get(field_id)

    def get_entity_values(self, entity: str, entity_id: str) -> Dict[str, Any]:
        """Get all custom field values for an entity instance"""
        entity_key = f"{entity}:{entity_id}"
        values = self._values.get(entity_key, {})

        # Include defaults for missing fields
        fields = self.get_entity_fields(entity)
        result = {}

        for field in fields:
            if field["id"] in values:
                result[field["id"]] = {
                    "field": field,
                    "value": values[field["id"]]
                }
            elif field.get("default_value") is not None:
                result[field["id"]] = {
                    "field": field,
                    "value": field["default_value"]
                }

        return result

    def set_bulk_values(self, entity: str, entity_id: str, values: Dict[str, Any]) -> dict:
        """Set multiple custom field values at once"""
        results = {"success": [], "errors": []}

        for field_id, value in values.items():
            result = self.set_value(entity, entity_id, field_id, value)
            if "error" in result:
                results["errors"].append({"field_id": field_id, "error": result["error"]})
            else:
                results["success"].append(field_id)

        return results

    def search_by_field(self, entity: str, field_id: str, value: Any) -> List[str]:
        """Search entities by custom field value"""
        field = self._fields.get(field_id)
        if not field or not field.get("searchable"):
            return []

        results = []
        prefix = f"{entity}:"

        for entity_key, values in self._values.items():
            if entity_key.startswith(prefix):
                if field_id in values and values[field_id] == value:
                    results.append(entity_key.split(":")[1])

        return results


custom_fields_service = CustomFieldsService()
