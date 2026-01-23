"""
CRM Condition Evaluators
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class CRMConditionEvaluator:
    """Evaluates conditions on CRM entities."""

    OPERATORS = {
        "equals": lambda a, b: a == b,
        "not_equals": lambda a, b: a != b,
        "contains": lambda a, b: b in str(a) if a else False,
        "greater_than": lambda a, b: float(a or 0) > float(b),
        "less_than": lambda a, b: float(a or 0) < float(b),
        "greater_than_or_equal": lambda a, b: float(a or 0) >= float(b),
        "less_than_or_equal": lambda a, b: float(a or 0) <= float(b),
        "is_empty": lambda a, b: not a,
        "is_not_empty": lambda a, b: bool(a),
        "in_list": lambda a, b: a in b if isinstance(b, list) else False,
    }

    def evaluate(self, conditions: List[Dict], context: Dict) -> bool:
        if not conditions:
            return True

        for group in conditions:
            group_type = group.get("type", "all")
            rules = group.get("rules", [])

            if group_type == "all":
                if not self._evaluate_all(rules, context):
                    return False
            elif group_type == "any":
                if not self._evaluate_any(rules, context):
                    return False
            elif group_type == "none":
                if self._evaluate_any(rules, context):
                    return False
        return True

    def _evaluate_all(self, rules: List[Dict], context: Dict) -> bool:
        return all(self._evaluate_rule(rule, context) for rule in rules)

    def _evaluate_any(self, rules: List[Dict], context: Dict) -> bool:
        return any(self._evaluate_rule(rule, context) for rule in rules)

    def _evaluate_rule(self, rule: Dict, context: Dict) -> bool:
        if "type" in rule and "rules" in rule:
            return self.evaluate([rule], context)

        field = rule.get("field", "")
        operator = rule.get("operator", "equals")
        value = rule.get("value")

        actual_value = self._get_field_value(field, context)
        op_func = self.OPERATORS.get(operator)

        if not op_func:
            return False

        try:
            return op_func(actual_value, value)
        except Exception:
            return False

    def _get_field_value(self, field: str, context: Dict) -> Any:
        parts = field.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value


CRM_CONDITION_TEMPLATES = [
    {"id": "lead_is_hot", "name": "Lead is Hot", "entity": "lead", "conditions": [{"type": "any", "rules": [{"field": "entity.rating", "operator": "equals", "value": "hot"}, {"field": "entity.score", "operator": "greater_than_or_equal", "value": 70}]}]},
    {"id": "deal_high_value", "name": "High Value Deal", "entity": "opportunity", "conditions": [{"type": "all", "rules": [{"field": "entity.amount", "operator": "greater_than", "value": 10000}]}]},
    {"id": "company_at_risk", "name": "At-Risk Account", "entity": "company", "conditions": [{"type": "all", "rules": [{"field": "entity.type", "operator": "equals", "value": "customer"}, {"field": "entity.health_score", "operator": "less_than", "value": 40}]}]},
]

crm_condition_evaluator = CRMConditionEvaluator()
