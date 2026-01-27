"""
Expression evaluator for workflow conditions and rules.
Supports variables, operators, and built-in functions.
"""
from typing import Dict, Any, Optional
import re
import operator
import logging
from datetime import datetime, timedelta

from app.workflows.rules.functions import BUILTIN_FUNCTIONS


logger = logging.getLogger(__name__)


class ExpressionEvaluator:
    """
    Evaluates expressions with variables and operators.

    Supports:
    - Variable interpolation: {{variable.path}}
    - Comparison operators: ==, !=, >, <, >=, <=
    - Logical operators: AND, OR, NOT
    - Arithmetic: +, -, *, /, %
    - Built-in functions: UPPER, LOWER, DATE_ADD, etc.
    """

    COMPARISON_OPS = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'equals': operator.eq,
        'not_equals': operator.ne,
        'greater_than': operator.gt,
        'greater_than_or_equals': operator.ge,
        'less_than': operator.lt,
        'less_than_or_equals': operator.le,
    }

    def evaluate(
        self,
        expression: str,
        variables: Dict[str, Any]
    ) -> Any:
        """
        Evaluate an expression.

        Args:
            expression: Expression string
            variables: Variable values

        Returns:
            Evaluation result
        """
        if not expression:
            return True

        try:
            interpolated = self.interpolate(expression, variables)

            if ' AND ' in interpolated.upper():
                parts = re.split(r'\s+AND\s+', interpolated, flags=re.IGNORECASE)
                return all(self.evaluate(part.strip(), variables) for part in parts)

            if ' OR ' in interpolated.upper():
                parts = re.split(r'\s+OR\s+', interpolated, flags=re.IGNORECASE)
                return any(self.evaluate(part.strip(), variables) for part in parts)

            if interpolated.upper().startswith('NOT '):
                return not self.evaluate(interpolated[4:].strip(), variables)

            for op_str, op_func in self.COMPARISON_OPS.items():
                if f' {op_str} ' in interpolated or f' {op_str.upper()} ' in interpolated.upper():
                    pattern = rf'\s+{re.escape(op_str)}\s+'
                    parts = re.split(pattern, interpolated, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2:
                        left = self._parse_value(parts[0].strip())
                        right = self._parse_value(parts[1].strip())
                        return op_func(left, right)

            if ' IN ' in interpolated.upper():
                match = re.match(r'(.+?)\s+IN\s+\[(.+)\]', interpolated, re.IGNORECASE)
                if match:
                    value = self._parse_value(match.group(1).strip())
                    items = [
                        self._parse_value(item.strip().strip('"\''))
                        for item in match.group(2).split(',')
                    ]
                    return value in items

            return self._parse_value(interpolated)

        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return False

    def interpolate(
        self,
        text: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Interpolate variables in text.

        Handles:
        - {{variable.path}}
        - {{FUNCTION(args)}}
        """
        def replace_var(match):
            content = match.group(1).strip()

            func_match = re.match(r'(\w+)\((.+)\)', content)
            if func_match:
                func_name = func_match.group(1).upper()
                args_str = func_match.group(2)

                if func_name in BUILTIN_FUNCTIONS:
                    args = self._parse_function_args(args_str, variables)
                    result = BUILTIN_FUNCTIONS[func_name](*args)
                    return str(result) if result is not None else ''

            value = self._get_nested(variables, content)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace_var, text)

    def _get_nested(
        self,
        obj: Dict[str, Any],
        path: str
    ) -> Any:
        """Get nested value from object using dot notation."""
        keys = path.split('.')
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None

        return value

    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value to appropriate type."""
        value_str = value_str.strip()

        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False

        if value_str.lower() in ('null', 'none'):
            return None

        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        return value_str

    def _parse_function_args(
        self,
        args_str: str,
        variables: Dict[str, Any]
    ) -> list:
        """Parse function arguments."""
        args = []
        current = ''
        depth = 0
        in_string = False
        string_char = None

        for char in args_str + ',':
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False

            if char == '(' and not in_string:
                depth += 1
            elif char == ')' and not in_string:
                depth -= 1

            if char == ',' and depth == 0 and not in_string:
                arg = current.strip()
                if arg:
                    if arg.startswith('{{') and arg.endswith('}}'):
                        arg = self.interpolate(arg, variables)
                    args.append(self._parse_value(arg))
                current = ''
            else:
                current += char

        return args


class RuleEvaluator:
    """
    Evaluates business rules against entity data.
    Supports complex conditions with nested AND/OR logic.
    """

    OPERATORS = {
        'equals': lambda a, b: a == b,
        'not_equals': lambda a, b: a != b,
        'greater_than': lambda a, b: float(a) > float(b) if a and b else False,
        'greater_than_or_equals': lambda a, b: float(a) >= float(b) if a and b else False,
        'less_than': lambda a, b: float(a) < float(b) if a and b else False,
        'less_than_or_equals': lambda a, b: float(a) <= float(b) if a and b else False,
        'contains': lambda a, b: b in str(a) if a else False,
        'not_contains': lambda a, b: b not in str(a) if a else True,
        'starts_with': lambda a, b: str(a).startswith(str(b)) if a else False,
        'ends_with': lambda a, b: str(a).endswith(str(b)) if a else False,
        'in': lambda a, b: a in b if b else False,
        'not_in': lambda a, b: a not in b if b else True,
        'is_empty': lambda a, _: not a,
        'is_not_empty': lambda a, _: bool(a),
        'matches_regex': lambda a, b: bool(re.match(b, str(a))) if a else False,
        'between': lambda a, b: b[0] <= float(a) <= b[1] if a and b else False,
    }

    def __init__(self):
        self.expression_evaluator = ExpressionEvaluator()

    def evaluate(
        self,
        rule: Dict[str, Any],
        entity: Dict[str, Any]
    ) -> bool:
        """Evaluate a rule against an entity."""
        conditions = rule.get('conditions', [])

        if not conditions:
            return True

        return self._evaluate_group(conditions[0], entity)

    def _evaluate_group(
        self,
        group: Dict[str, Any],
        entity: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition group."""
        group_type = group.get('type', 'all')
        rules = group.get('rules', [])

        results = []
        for rule in rules:
            if 'type' in rule and rule['type'] in ('all', 'any', 'none'):
                results.append(self._evaluate_group(rule, entity))
            else:
                results.append(self._evaluate_condition(rule, entity))

        if group_type == 'all':
            return all(results)
        elif group_type == 'any':
            return any(results)
        elif group_type == 'none':
            return not any(results)

        return False

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        entity: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition."""
        field = condition.get('field', '')
        op = condition.get('operator', 'equals')
        expected = condition.get('value')

        actual = self.expression_evaluator._get_nested(entity, field)

        op_func = self.OPERATORS.get(op)
        if not op_func:
            logger.warning(f"Unknown operator: {op}")
            return False

        try:
            return op_func(actual, expected)
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
