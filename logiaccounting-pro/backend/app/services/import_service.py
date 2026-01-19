"""
Data Import Service
CSV/Excel import with validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import csv
import io
from app.models.store import db


class ImportService:
    """Handles data import with validation"""

    _instance = None
    _imports: Dict[str, dict] = {}
    _templates: Dict[str, dict] = {}
    _counter = 0

    ENTITY_CONFIGS = {
        "materials": {
            "collection": "materials",
            "required_fields": ["name"],
            "field_mappings": {
                "name": {"type": "string", "required": True},
                "sku": {"type": "string", "required": False},
                "description": {"type": "string", "required": False},
                "quantity": {"type": "number", "required": False, "default": 0},
                "unit_cost": {"type": "number", "required": False, "default": 0},
                "category_id": {"type": "string", "required": False},
                "location_id": {"type": "string", "required": False},
                "min_stock": {"type": "number", "required": False, "default": 0},
                "max_stock": {"type": "number", "required": False}
            }
        },
        "transactions": {
            "collection": "transactions",
            "required_fields": ["description", "amount", "type"],
            "field_mappings": {
                "description": {"type": "string", "required": True},
                "amount": {"type": "number", "required": True},
                "type": {"type": "enum", "values": ["income", "expense"], "required": True},
                "date": {"type": "date", "required": False},
                "category_id": {"type": "string", "required": False},
                "project_id": {"type": "string", "required": False},
                "invoice_number": {"type": "string", "required": False}
            }
        },
        "payments": {
            "collection": "payments",
            "required_fields": ["amount", "type"],
            "field_mappings": {
                "amount": {"type": "number", "required": True},
                "type": {"type": "enum", "values": ["receivable", "payable"], "required": True},
                "status": {"type": "enum", "values": ["pending", "paid", "overdue"], "default": "pending"},
                "due_date": {"type": "date", "required": False},
                "description": {"type": "string", "required": False},
                "project_id": {"type": "string", "required": False}
            }
        },
        "categories": {
            "collection": "categories",
            "required_fields": ["name"],
            "field_mappings": {
                "name": {"type": "string", "required": True},
                "type": {"type": "enum", "values": ["income", "expense", "inventory"], "required": False},
                "description": {"type": "string", "required": False},
                "color": {"type": "string", "required": False}
            }
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._imports = {}
            cls._templates = {}
            cls._counter = 0
        return cls._instance

    def get_entity_config(self, entity: str) -> Optional[dict]:
        """Get configuration for an entity type"""
        return self.ENTITY_CONFIGS.get(entity)

    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        return list(self.ENTITY_CONFIGS.keys())

    def parse_csv(self, content: str, delimiter: str = ",") -> Tuple[List[str], List[dict]]:
        """Parse CSV content"""
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        headers = reader.fieldnames or []
        rows = list(reader)
        return headers, rows

    def suggest_mappings(self, headers: List[str], entity: str) -> Dict[str, str]:
        """Suggest column mappings based on header names"""
        config = self.ENTITY_CONFIGS.get(entity, {})
        field_mappings = config.get("field_mappings", {})

        suggestions = {}

        for header in headers:
            header_lower = header.lower().strip()

            # Direct match
            if header_lower in field_mappings:
                suggestions[header] = header_lower
                continue

            # Common variations
            variations = {
                "product": "name",
                "product_name": "name",
                "item": "name",
                "item_name": "name",
                "material": "name",
                "price": "unit_cost",
                "cost": "unit_cost",
                "unit_price": "unit_cost",
                "qty": "quantity",
                "stock": "quantity",
                "on_hand": "quantity",
                "category": "category_id",
                "location": "location_id",
                "desc": "description",
                "notes": "description",
                "min": "min_stock",
                "minimum": "min_stock",
                "max": "max_stock",
                "maximum": "max_stock",
                "invoice": "invoice_number",
                "inv_no": "invoice_number",
                "due": "due_date",
                "payment_date": "due_date"
            }

            if header_lower in variations and variations[header_lower] in field_mappings:
                suggestions[header] = variations[header_lower]

        return suggestions

    def validate_row(self, row: dict, mapping: dict, entity: str, row_index: int) -> Tuple[dict, List[dict]]:
        """Validate and transform a single row"""
        config = self.ENTITY_CONFIGS.get(entity, {})
        field_mappings = config.get("field_mappings", {})
        required_fields = config.get("required_fields", [])

        errors = []
        validated = {}

        for source_col, target_field in mapping.items():
            if target_field not in field_mappings:
                continue

            field_config = field_mappings[target_field]
            value = row.get(source_col, "").strip()

            # Handle empty values
            if not value:
                if field_config.get("required"):
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Required field '{target_field}' is empty"
                    })
                elif "default" in field_config:
                    validated[target_field] = field_config["default"]
                continue

            # Type validation
            field_type = field_config.get("type")

            if field_type == "number":
                try:
                    validated[target_field] = float(value.replace(",", ""))
                except ValueError:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid number: {value}"
                    })

            elif field_type == "date":
                # Try common date formats
                parsed = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        parsed = datetime.strptime(value, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

                if parsed:
                    validated[target_field] = parsed
                else:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid date format: {value}"
                    })

            elif field_type == "enum":
                allowed = field_config.get("values", [])
                if value.lower() in [v.lower() for v in allowed]:
                    validated[target_field] = value.lower()
                else:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid value: {value}. Allowed: {', '.join(allowed)}"
                    })

            else:  # string
                validated[target_field] = value

        # Check required fields
        for req in required_fields:
            if req not in validated:
                errors.append({
                    "row": row_index,
                    "field": req,
                    "error": f"Required field '{req}' not mapped or empty"
                })

        return validated, errors

    def create_import(
        self,
        entity: str,
        headers: List[str],
        rows: List[dict],
        mapping: Dict[str, str],
        created_by: str
    ) -> dict:
        """Create an import job with validation"""
        self._counter += 1
        import_id = f"IMP-{self._counter:04d}"

        # Validate all rows
        valid_rows = []
        all_errors = []

        for i, row in enumerate(rows):
            validated, errors = self.validate_row(row, mapping, entity, i + 1)
            if errors:
                all_errors.extend(errors)
            else:
                valid_rows.append(validated)

        import_job = {
            "id": import_id,
            "entity": entity,
            "headers": headers,
            "mapping": mapping,
            "total_rows": len(rows),
            "valid_rows": len(valid_rows),
            "error_rows": len(all_errors),
            "errors": all_errors[:100],  # Limit errors returned
            "preview": valid_rows[:10],
            "status": "pending",
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat()
        }

        # Store validated data for execution
        import_job["_valid_data"] = valid_rows

        self._imports[import_id] = import_job

        return {
            k: v for k, v in import_job.items() if not k.startswith("_")
        }

    def execute_import(self, import_id: str) -> dict:
        """Execute the import and create records"""
        import_job = self._imports.get(import_id)
        if not import_job:
            return {"error": "Import not found"}

        if import_job["status"] != "pending":
            return {"error": f"Import already {import_job['status']}"}

        entity = import_job["entity"]
        config = self.ENTITY_CONFIGS.get(entity)
        collection_name = config["collection"]

        # Get the collection
        collection = getattr(db, collection_name, None)
        if not collection:
            return {"error": f"Collection {collection_name} not found"}

        # Insert records
        created = 0
        valid_data = import_job.get("_valid_data", [])
        created_ids = []

        for data in valid_data:
            try:
                record = collection.create(data)
                created += 1
                created_ids.append(record.get("id"))
            except Exception as e:
                pass  # Continue on individual failures

        import_job["status"] = "completed"
        import_job["completed_at"] = datetime.utcnow().isoformat()
        import_job["created_count"] = created
        import_job["created_ids"] = created_ids

        return {
            "success": True,
            "import_id": import_id,
            "created_count": created,
            "total_rows": import_job["total_rows"]
        }

    def rollback_import(self, import_id: str) -> dict:
        """Rollback an executed import"""
        import_job = self._imports.get(import_id)
        if not import_job:
            return {"error": "Import not found"}

        if import_job["status"] != "completed":
            return {"error": "Can only rollback completed imports"}

        entity = import_job["entity"]
        config = self.ENTITY_CONFIGS.get(entity)
        collection_name = config["collection"]
        collection = getattr(db, collection_name, None)

        if not collection:
            return {"error": f"Collection {collection_name} not found"}

        # Delete created records
        deleted = 0
        for record_id in import_job.get("created_ids", []):
            try:
                if collection.delete(record_id):
                    deleted += 1
            except:
                pass

        import_job["status"] = "rolled_back"
        import_job["rolled_back_at"] = datetime.utcnow().isoformat()
        import_job["deleted_count"] = deleted

        return {
            "success": True,
            "deleted_count": deleted
        }

    def get_import(self, import_id: str) -> Optional[dict]:
        """Get import job details"""
        job = self._imports.get(import_id)
        if job:
            return {k: v for k, v in job.items() if not k.startswith("_")}
        return None

    def list_imports(self, limit: int = 20) -> List[dict]:
        """List recent imports"""
        imports = list(self._imports.values())
        imports = sorted(imports, key=lambda x: x["created_at"], reverse=True)[:limit]
        return [{k: v for k, v in i.items() if not k.startswith("_")} for i in imports]


import_service = ImportService()
