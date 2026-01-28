"""
Variable System
Handles variable resolution and template rendering in workflows
"""

from typing import Dict, Any, List, Optional, Union
import re
import json
from datetime import datetime
import logging

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class VariableResolver:
    """Resolves variables in workflow configurations."""

    # Pattern to match {{variable}} or {{object.property}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    # Built-in functions
    FUNCTIONS = {
        "now": lambda: utc_now().isoformat(),
        "today": lambda: utc_now().strftime("%Y-%m-%d"),
        "timestamp": lambda: int(utc_now().timestamp()),
        "uuid": lambda: __import__('uuid').uuid4().hex,
    }

    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or {}

    def set_context(self, context: Dict[str, Any]):
        """Set the variable context."""
        self.context = context

    def update_context(self, key: str, value: Any):
        """Update a single context variable."""
        self.context[key] = value

    def merge_context(self, data: Dict[str, Any]):
        """Merge data into context."""
        self.context.update(data)

    def resolve(self, template: Union[str, Dict, List, Any]) -> Any:
        """Resolve variables in a template."""
        if isinstance(template, str):
            return self._resolve_string(template)
        elif isinstance(template, dict):
            return self._resolve_dict(template)
        elif isinstance(template, list):
            return self._resolve_list(template)
        else:
            return template

    def _resolve_string(self, template: str) -> Any:
        """Resolve variables in a string template."""
        # Check if entire string is a single variable
        match = re.fullmatch(r'\{\{([^}]+)\}\}', template.strip())
        if match:
            # Return the actual value (not stringified)
            return self._get_value(match.group(1).strip())

        # Replace all variables in string
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self._get_value(var_name)
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value)

        return self.VARIABLE_PATTERN.sub(replace_var, template)

    def _resolve_dict(self, template: Dict) -> Dict:
        """Resolve variables in a dictionary."""
        result = {}
        for key, value in template.items():
            resolved_key = self._resolve_string(key) if isinstance(key, str) else key
            result[resolved_key] = self.resolve(value)
        return result

    def _resolve_list(self, template: List) -> List:
        """Resolve variables in a list."""
        return [self.resolve(item) for item in template]

    def _get_value(self, var_path: str) -> Any:
        """Get value from context using dot notation."""
        # Check for function call
        if var_path.endswith("()"):
            func_name = var_path[:-2]
            if func_name in self.FUNCTIONS:
                return self.FUNCTIONS[func_name]()
            return None

        # Check for pipe functions (e.g., {{name|upper}})
        if "|" in var_path:
            var_name, pipe_func = var_path.split("|", 1)
            value = self._get_value(var_name.strip())
            return self._apply_pipe(value, pipe_func.strip())

        # Navigate nested path
        parts = var_path.split(".")
        value = self.context

        for part in parts:
            if value is None:
                return None

            # Handle array indexing: items[0]
            array_match = re.match(r'(\w+)\[(\d+)\]', part)
            if array_match:
                key, index = array_match.groups()
                if isinstance(value, dict):
                    value = value.get(key)
                if isinstance(value, list) and len(value) > int(index):
                    value = value[int(index)]
                else:
                    return None
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _apply_pipe(self, value: Any, pipe_func: str) -> Any:
        """Apply a pipe function to a value."""
        if value is None:
            return None

        pipe_functions = {
            "upper": lambda v: str(v).upper(),
            "lower": lambda v: str(v).lower(),
            "title": lambda v: str(v).title(),
            "trim": lambda v: str(v).strip(),
            "length": lambda v: len(v) if hasattr(v, '__len__') else 0,
            "first": lambda v: v[0] if v else None,
            "last": lambda v: v[-1] if v else None,
            "sum": lambda v: sum(v) if isinstance(v, list) else v,
            "min": lambda v: min(v) if isinstance(v, list) else v,
            "max": lambda v: max(v) if isinstance(v, list) else v,
            "join": lambda v: ", ".join(str(x) for x in v) if isinstance(v, list) else str(v),
            "json": lambda v: json.dumps(v),
            "keys": lambda v: list(v.keys()) if isinstance(v, dict) else [],
            "values": lambda v: list(v.values()) if isinstance(v, dict) else [],
            "default": lambda v: v if v else "",
            "currency": lambda v: f"${float(v):,.2f}" if v else "$0.00",
            "date": lambda v: datetime.fromisoformat(str(v)).strftime("%Y-%m-%d") if v else "",
            "datetime": lambda v: datetime.fromisoformat(str(v)).strftime("%Y-%m-%d %H:%M") if v else "",
        }

        if pipe_func in pipe_functions:
            try:
                return pipe_functions[pipe_func](value)
            except Exception as e:
                logger.warning(f"Pipe function {pipe_func} failed: {e}")
                return value

        return value

    def extract_variables(self, template: Union[str, Dict, List]) -> List[str]:
        """Extract all variable names from a template."""
        variables = set()

        def extract(value):
            if isinstance(value, str):
                matches = self.VARIABLE_PATTERN.findall(value)
                for match in matches:
                    # Remove pipe functions
                    var_name = match.split("|")[0].strip()
                    # Remove function calls
                    if not var_name.endswith("()"):
                        variables.add(var_name)
            elif isinstance(value, dict):
                for v in value.values():
                    extract(v)
            elif isinstance(value, list):
                for item in value:
                    extract(item)

        extract(template)
        return list(variables)

    def validate_variables(self, template: Union[str, Dict, List]) -> List[str]:
        """Check which variables are missing from context."""
        required = self.extract_variables(template)
        missing = []

        for var in required:
            if self._get_value(var) is None:
                missing.append(var)

        return missing


class ExpressionEvaluator:
    """Evaluates expressions for conditions."""

    OPERATORS = {
        "equals": lambda a, b: a == b,
        "not_equals": lambda a, b: a != b,
        "greater_than": lambda a, b: float(a) > float(b) if a and b else False,
        "greater_than_or_equals": lambda a, b: float(a) >= float(b) if a and b else False,
        "less_than": lambda a, b: float(a) < float(b) if a and b else False,
        "less_than_or_equals": lambda a, b: float(a) <= float(b) if a and b else False,
        "contains": lambda a, b: str(b) in str(a) if a else False,
        "not_contains": lambda a, b: str(b) not in str(a) if a else True,
        "starts_with": lambda a, b: str(a).startswith(str(b)) if a else False,
        "ends_with": lambda a, b: str(a).endswith(str(b)) if a else False,
        "is_empty": lambda a, _: not a or (isinstance(a, (list, dict, str)) and len(a) == 0),
        "is_not_empty": lambda a, _: bool(a) and (not isinstance(a, (list, dict, str)) or len(a) > 0),
        "in": lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple)) else True,
        "matches": lambda a, b: bool(re.match(str(b), str(a))) if a and b else False,
    }

    def __init__(self, resolver: VariableResolver):
        self.resolver = resolver

    def evaluate(self, condition: Dict) -> bool:
        """Evaluate a condition."""
        condition_type = condition.get("type", "simple")

        if condition_type == "and":
            conditions = condition.get("conditions", [])
            return all(self.evaluate(c) for c in conditions)

        elif condition_type == "or":
            conditions = condition.get("conditions", [])
            return any(self.evaluate(c) for c in conditions)

        elif condition_type == "not":
            inner = condition.get("condition", {})
            return not self.evaluate(inner)

        else:
            # Simple condition
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")

            # Resolve variables
            field_value = self.resolver.resolve(field) if isinstance(field, str) and "{{" in field else self.resolver._get_value(field) if field else None
            compare_value = self.resolver.resolve(value) if isinstance(value, str) and "{{" in value else value

            # Get operator function
            op_func = self.OPERATORS.get(operator)
            if not op_func:
                logger.warning(f"Unknown operator: {operator}")
                return False

            try:
                return op_func(field_value, compare_value)
            except Exception as e:
                logger.warning(f"Condition evaluation failed: {e}")
                return False
