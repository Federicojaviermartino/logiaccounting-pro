"""
Data Actions
CRUD operations and data manipulation actions
"""

from typing import Dict, Any, List
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now
from app.workflows.actions.base import (
    BaseAction, ActionCategory, ActionInput, ActionOutput, register_action
)

logger = logging.getLogger(__name__)


@register_action
class QueryRecordsAction(BaseAction):
    """Query records from database."""

    ACTION_ID = "query_records"
    ACTION_NAME = "Query Records"
    DESCRIPTION = "Query records from a data entity"
    CATEGORY = ActionCategory.DATA
    ICON = "🔍"

    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoices", "label": "Invoices"},
            {"value": "customers", "label": "Customers"},
            {"value": "projects", "label": "Projects"},
            {"value": "payments", "label": "Payments"},
            {"value": "tickets", "label": "Tickets"},
            {"value": "products", "label": "Products"},
        ]),
        ActionInput("filter", "Filter", "string", required=False, description="JSON filter criteria"),
        ActionInput("sort_by", "Sort By", "string", required=False),
        ActionInput("sort_order", "Sort Order", "select", required=False, default="desc", options=[
            {"value": "asc", "label": "Ascending"},
            {"value": "desc", "label": "Descending"},
        ]),
        ActionInput("limit", "Limit", "number", required=False, default=100),
    ]

    OUTPUTS = [
        ActionOutput("records", "Records", "array", "List of matching records"),
        ActionOutput("count", "Count", "number", "Total count of records"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Query records."""
        entity = config.get("entity")
        filter_criteria = config.get("filter", {})
        limit = config.get("limit", 100)

        # In production: query actual database
        # records = await db.query(entity, filter=filter_criteria, limit=limit)

        logger.info(f"[QueryRecords] Querying {entity}")

        # Demo response
        return {
            "records": [],
            "count": 0,
            "entity": entity,
        }


@register_action
class CreateRecordAction(BaseAction):
    """Create a new record."""

    ACTION_ID = "create_record"
    ACTION_NAME = "Create Record"
    DESCRIPTION = "Create a new record in a data entity"
    CATEGORY = ActionCategory.DATA
    ICON = "➕"

    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
            {"value": "note", "label": "Note"},
        ]),
        ActionInput("data", "Data", "string", required=True, description="JSON data for the record"),
    ]

    OUTPUTS = [
        ActionOutput("record_id", "Record ID", "string"),
        ActionOutput("record", "Record", "object", "Created record data"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Create record."""
        entity = config.get("entity")
        data = config.get("data", {})

        if isinstance(data, str):
            import json
            data = json.loads(data)

        record_id = f"{entity}_{uuid4().hex[:12]}"

        logger.info(f"[CreateRecord] Creating {entity}")

        return {
            "record_id": record_id,
            "record": {**data, "id": record_id, "created_at": utc_now().isoformat()},
        }


@register_action
class UpdateRecordAction(BaseAction):
    """Update an existing record."""

    ACTION_ID = "update_record"
    ACTION_NAME = "Update Record"
    DESCRIPTION = "Update an existing record"
    CATEGORY = ActionCategory.DATA
    ICON = "✏️"

    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("data", "Data", "string", required=True, description="JSON data to update"),
    ]

    OUTPUTS = [
        ActionOutput("success", "Success", "boolean"),
        ActionOutput("record", "Record", "object", "Updated record data"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Update record."""
        entity = config.get("entity")
        record_id = config.get("record_id")
        data = config.get("data", {})

        if isinstance(data, str):
            import json
            data = json.loads(data)

        logger.info(f"[UpdateRecord] Updating {entity} {record_id}")

        return {
            "success": True,
            "record": {**data, "id": record_id, "updated_at": utc_now().isoformat()},
        }


@register_action
class DeleteRecordAction(BaseAction):
    """Delete a record."""

    ACTION_ID = "delete_record"
    ACTION_NAME = "Delete Record"
    DESCRIPTION = "Delete a record (soft delete)"
    CATEGORY = ActionCategory.DATA
    ICON = "🗑️"

    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("hard_delete", "Hard Delete", "boolean", required=False, default=False),
    ]

    OUTPUTS = [
        ActionOutput("success", "Success", "boolean"),
        ActionOutput("deleted_at", "Deleted At", "datetime"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Delete record."""
        entity = config.get("entity")
        record_id = config.get("record_id")

        logger.info(f"[DeleteRecord] Deleting {entity} {record_id}")

        return {
            "success": True,
            "deleted_at": utc_now().isoformat(),
        }


@register_action
class CalculateAction(BaseAction):
    """Perform calculations."""

    ACTION_ID = "calculate"
    ACTION_NAME = "Calculate"
    DESCRIPTION = "Perform mathematical calculations"
    CATEGORY = ActionCategory.DATA
    ICON = "🔢"

    INPUTS = [
        ActionInput("operation", "Operation", "select", required=True, options=[
            {"value": "sum", "label": "Sum"},
            {"value": "average", "label": "Average"},
            {"value": "min", "label": "Minimum"},
            {"value": "max", "label": "Maximum"},
            {"value": "count", "label": "Count"},
            {"value": "add", "label": "Add (a + b)"},
            {"value": "subtract", "label": "Subtract (a - b)"},
            {"value": "multiply", "label": "Multiply (a * b)"},
            {"value": "divide", "label": "Divide (a / b)"},
            {"value": "percentage", "label": "Percentage (a% of b)"},
        ]),
        ActionInput("values", "Values", "string", required=False, description="Array of values for aggregate operations"),
        ActionInput("a", "Value A", "number", required=False),
        ActionInput("b", "Value B", "number", required=False),
    ]

    OUTPUTS = [
        ActionOutput("result", "Result", "number"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Perform calculation."""
        operation = config.get("operation")
        values = config.get("values", [])
        a = config.get("a", 0)
        b = config.get("b", 0)

        if isinstance(values, str):
            import json
            values = json.loads(values)

        result = 0

        if operation == "sum":
            result = sum(values)
        elif operation == "average":
            result = sum(values) / len(values) if values else 0
        elif operation == "min":
            result = min(values) if values else 0
        elif operation == "max":
            result = max(values) if values else 0
        elif operation == "count":
            result = len(values)
        elif operation == "add":
            result = float(a) + float(b)
        elif operation == "subtract":
            result = float(a) - float(b)
        elif operation == "multiply":
            result = float(a) * float(b)
        elif operation == "divide":
            result = float(a) / float(b) if b != 0 else 0
        elif operation == "percentage":
            result = (float(a) / 100) * float(b)

        return {"result": result}


@register_action
class TransformDataAction(BaseAction):
    """Transform data structure."""

    ACTION_ID = "transform_data"
    ACTION_NAME = "Transform Data"
    DESCRIPTION = "Transform data from one format to another"
    CATEGORY = ActionCategory.DATA
    ICON = "🔄"

    INPUTS = [
        ActionInput("input", "Input Data", "string", required=True, description="Input data (JSON)"),
        ActionInput("mapping", "Field Mapping", "string", required=True, description="Field mapping (JSON)"),
    ]

    OUTPUTS = [
        ActionOutput("output", "Output Data", "object"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Transform data."""
        import json

        input_data = config.get("input", {})
        mapping = config.get("mapping", {})

        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        if isinstance(mapping, str):
            mapping = json.loads(mapping)

        output = {}
        for target_key, source_key in mapping.items():
            if source_key in input_data:
                output[target_key] = input_data[source_key]

        return {"output": output}
