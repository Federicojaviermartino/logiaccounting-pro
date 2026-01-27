"""
Phase 14: Data Transformer
Transforms data between local and remote formats using field mappings
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import re
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms data between systems using field mappings"""

    def __init__(self, field_mappings: List[Dict]):
        """
        Initialize transformer with field mappings

        Args:
            field_mappings: List of field mapping dictionaries
        """
        self.field_mappings = field_mappings
        self._lookup_tables = {}

    def transform_to_remote(self, local_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform local data to remote format

        Args:
            local_data: Local record data

        Returns:
            Transformed data for remote system
        """
        remote_data = {}

        for mapping in self.field_mappings:
            direction = mapping.get("direction", "bidirectional")
            if direction == 'inbound':
                continue  # Skip inbound-only mappings

            local_value = self._get_nested_value(local_data, mapping["local_field"])

            # Apply transformation
            transformed_value = self._apply_transform(
                value=local_value,
                transform_type=mapping.get("transform_type", "direct"),
                transform_config=mapping.get("transform_config", {}),
                direction='outbound'
            )

            # Handle default value
            if transformed_value is None and mapping.get("default_value") is not None:
                transformed_value = mapping["default_value"]

            # Skip if required field is missing
            if mapping.get("is_required") and transformed_value is None:
                raise ValueError(f"Required field missing: {mapping['local_field']}")

            # Set value in remote data
            if transformed_value is not None:
                self._set_nested_value(remote_data, mapping["remote_field"], transformed_value)

        return remote_data

    def transform_to_local(self, remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform remote data to local format

        Args:
            remote_data: Remote record data

        Returns:
            Transformed data for local system
        """
        local_data = {}

        for mapping in self.field_mappings:
            direction = mapping.get("direction", "bidirectional")
            if direction == 'outbound':
                continue  # Skip outbound-only mappings

            remote_value = self._get_nested_value(remote_data, mapping["remote_field"])

            # Apply transformation (reverse direction)
            transformed_value = self._apply_transform(
                value=remote_value,
                transform_type=mapping.get("transform_type", "direct"),
                transform_config=mapping.get("transform_config", {}),
                direction='inbound'
            )

            # Handle default value
            if transformed_value is None and mapping.get("default_value") is not None:
                transformed_value = mapping["default_value"]

            # Set value in local data
            if transformed_value is not None:
                self._set_nested_value(local_data, mapping["local_field"], transformed_value)

        return local_data

    def _apply_transform(
        self,
        value: Any,
        transform_type: str,
        transform_config: Dict[str, Any],
        direction: str
    ) -> Any:
        """
        Apply transformation to a value

        Args:
            value: Value to transform
            transform_type: Type of transformation
            transform_config: Transformation configuration
            direction: 'inbound' or 'outbound'

        Returns:
            Transformed value
        """
        if value is None:
            return None

        transform_config = transform_config or {}

        if transform_type == 'direct':
            return value

        elif transform_type == 'format':
            return self._transform_format(value, transform_config, direction)

        elif transform_type == 'lookup':
            return self._transform_lookup(value, transform_config, direction)

        elif transform_type == 'compute':
            return self._transform_compute(value, transform_config, direction)

        elif transform_type == 'constant':
            return transform_config.get('value')

        elif transform_type == 'concat':
            return self._transform_concat(value, transform_config)

        elif transform_type == 'split':
            return self._transform_split(value, transform_config)

        elif transform_type == 'cast':
            return self._transform_cast(value, transform_config)

        else:
            logger.warning(f"Unknown transform type: {transform_type}")
            return value

    def _transform_format(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Format transformation (dates, numbers, etc.)"""
        format_type = config.get('type', 'string')

        if format_type == 'date':
            input_format = config.get('input_format', '%Y-%m-%d')
            output_format = config.get('output_format', '%Y-%m-%d')

            if direction == 'inbound':
                input_format, output_format = output_format, input_format

            if isinstance(value, str):
                try:
                    dt = datetime.strptime(value, input_format)
                    return dt.strftime(output_format)
                except ValueError:
                    return value
            elif isinstance(value, (datetime, date)):
                return value.strftime(output_format)

        elif format_type == 'datetime':
            input_format = config.get('input_format', '%Y-%m-%dT%H:%M:%S')
            output_format = config.get('output_format', '%Y-%m-%dT%H:%M:%S')

            if direction == 'inbound':
                input_format, output_format = output_format, input_format

            if isinstance(value, str):
                try:
                    # Handle ISO format with Z
                    value = value.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(value)
                    return dt.strftime(output_format)
                except ValueError:
                    try:
                        dt = datetime.strptime(value, input_format)
                        return dt.strftime(output_format)
                    except ValueError:
                        return value
            elif isinstance(value, datetime):
                return value.strftime(output_format)

        elif format_type == 'number':
            decimals = config.get('decimals', 2)
            if isinstance(value, (int, float, Decimal)):
                return round(float(value), decimals)
            elif isinstance(value, str):
                try:
                    return round(float(value.replace(',', '')), decimals)
                except ValueError:
                    return None

        elif format_type == 'currency':
            # Remove currency symbols, convert to cents/pence if needed
            if isinstance(value, str):
                clean = re.sub(r'[^\d.-]', '', value)
                try:
                    return float(clean)
                except ValueError:
                    return None
            elif isinstance(value, (int, float, Decimal)):
                return float(value)

        elif format_type == 'phone':
            # Normalize phone number format
            if isinstance(value, str):
                digits = re.sub(r'\D', '', value)
                return digits

        elif format_type == 'email':
            # Lowercase email
            if isinstance(value, str):
                return value.lower().strip()

        return value

    def _transform_lookup(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Lookup table transformation"""
        lookup_table = config.get('table', {})
        default = config.get('default')

        if direction == 'inbound':
            # Reverse lookup
            lookup_table = {v: k for k, v in lookup_table.items()}

        return lookup_table.get(str(value), default)

    def _transform_compute(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Computed transformation using expression"""
        expression = config.get('expression', 'value')

        # Simple expression evaluation (for security, only allow basic operations)
        allowed_operations = {
            'value': value,
            'upper': str(value).upper() if value else None,
            'lower': str(value).lower() if value else None,
            'trim': str(value).strip() if value else None,
            'bool': bool(value),
            'int': int(value) if value else None,
            'float': float(value) if value else None,
            'str': str(value) if value else None,
        }

        if expression in allowed_operations:
            return allowed_operations[expression]

        # Handle simple math
        if isinstance(value, (int, float)):
            if expression.startswith('multiply:'):
                factor = float(expression.split(':')[1])
                return value * factor
            elif expression.startswith('divide:'):
                divisor = float(expression.split(':')[1])
                return value / divisor if divisor != 0 else None
            elif expression.startswith('add:'):
                addend = float(expression.split(':')[1])
                return value + addend
            elif expression.startswith('subtract:'):
                subtrahend = float(expression.split(':')[1])
                return value - subtrahend
            elif expression.startswith('round:'):
                decimals = int(expression.split(':')[1])
                return round(value, decimals)

        # Handle string operations
        if isinstance(value, str):
            if expression.startswith('prefix:'):
                prefix = expression.split(':', 1)[1]
                return prefix + value
            elif expression.startswith('suffix:'):
                suffix = expression.split(':', 1)[1]
                return value + suffix
            elif expression.startswith('replace:'):
                parts = expression.split(':')[1:]
                if len(parts) >= 2:
                    return value.replace(parts[0], parts[1])

        return value

    def _transform_concat(self, value: Any, config: Dict[str, Any]) -> str:
        """Concatenate multiple fields"""
        separator = config.get('separator', ' ')
        fields = config.get('fields', [])

        if isinstance(value, dict):
            parts = []
            for field in fields:
                part = self._get_nested_value(value, field)
                if part:
                    parts.append(str(part))
            return separator.join(parts)

        return str(value) if value else ''

    def _transform_split(self, value: Any, config: Dict[str, Any]) -> Any:
        """Split string and extract part"""
        separator = config.get('separator', ' ')
        index = config.get('index', 0)

        if isinstance(value, str):
            parts = value.split(separator)
            if 0 <= index < len(parts):
                return parts[index]
            elif index == -1 and len(parts) > 0:
                return parts[-1]

        return value

    def _transform_cast(self, value: Any, config: Dict[str, Any]) -> Any:
        """Cast value to specified type"""
        target_type = config.get('to', 'string')

        try:
            if target_type == 'string':
                return str(value) if value is not None else None
            elif target_type == 'integer':
                return int(float(value)) if value else None
            elif target_type == 'float':
                return float(value) if value else None
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 'on')
                return bool(value)
            elif target_type == 'array':
                if isinstance(value, list):
                    return value
                return [value] if value else []
            elif target_type == 'json':
                import json
                if isinstance(value, str):
                    return json.loads(value)
                return value
        except (ValueError, TypeError):
            return None

        return value

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        if not data or not path:
            return None

        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None

            if current is None:
                return None

        return current

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set value in nested dict using dot notation"""
        keys = path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def add_lookup_table(self, name: str, table: Dict[str, str]):
        """Add a lookup table for use in transformations"""
        self._lookup_tables[name] = table

    def get_lookup_table(self, name: str) -> Optional[Dict[str, str]]:
        """Get a lookup table by name"""
        return self._lookup_tables.get(name)


class TransformationBuilder:
    """Builder for creating field mappings with transformations"""

    @staticmethod
    def direct(local_field: str, remote_field: str, **kwargs) -> Dict:
        """Create a direct mapping"""
        return {
            "local_field": local_field,
            "remote_field": remote_field,
            "transform_type": "direct",
            **kwargs
        }

    @staticmethod
    def format_date(local_field: str, remote_field: str,
                    input_format: str = '%Y-%m-%d',
                    output_format: str = '%Y-%m-%d', **kwargs) -> Dict:
        """Create a date format mapping"""
        return {
            "local_field": local_field,
            "remote_field": remote_field,
            "transform_type": "format",
            "transform_config": {
                "type": "date",
                "input_format": input_format,
                "output_format": output_format,
            },
            **kwargs
        }

    @staticmethod
    def format_number(local_field: str, remote_field: str,
                      decimals: int = 2, **kwargs) -> Dict:
        """Create a number format mapping"""
        return {
            "local_field": local_field,
            "remote_field": remote_field,
            "transform_type": "format",
            "transform_config": {
                "type": "number",
                "decimals": decimals,
            },
            **kwargs
        }

    @staticmethod
    def lookup(local_field: str, remote_field: str,
               table: Dict[str, str], default: Any = None, **kwargs) -> Dict:
        """Create a lookup mapping"""
        return {
            "local_field": local_field,
            "remote_field": remote_field,
            "transform_type": "lookup",
            "transform_config": {
                "table": table,
                "default": default,
            },
            **kwargs
        }

    @staticmethod
    def constant(remote_field: str, value: Any, **kwargs) -> Dict:
        """Create a constant value mapping"""
        return {
            "local_field": "",
            "remote_field": remote_field,
            "transform_type": "constant",
            "transform_config": {"value": value},
            **kwargs
        }

    @staticmethod
    def cast(local_field: str, remote_field: str,
             target_type: str, **kwargs) -> Dict:
        """Create a type cast mapping"""
        return {
            "local_field": local_field,
            "remote_field": remote_field,
            "transform_type": "cast",
            "transform_config": {"to": target_type},
            **kwargs
        }
