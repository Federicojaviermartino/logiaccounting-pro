"""
Rule Engine
Custom rules for anomaly detection
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from ...models.anomaly import Anomaly

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """Anomaly detection rule"""
    id: str
    name: str
    description: str
    enabled: bool
    severity: str
    condition: Callable[[Dict[str, Any]], bool]
    message_template: str


class RuleEngine:
    """Custom rule-based anomaly detection"""

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default detection rules"""
        # Large transaction rule
        self.add_rule(Rule(
            id='large_transaction',
            name='Large Transaction Alert',
            description='Detect transactions over threshold amount',
            enabled=True,
            severity='high',
            condition=lambda t: abs(t.get('amount', 0)) > 50000,
            message_template='Large transaction detected: ${amount:,.2f}',
        ))

        # Round number rule
        self.add_rule(Rule(
            id='round_number',
            name='Round Number Alert',
            description='Detect suspiciously round transaction amounts',
            enabled=True,
            severity='low',
            condition=lambda t: self._is_suspicious_round(t.get('amount', 0)),
            message_template='Suspiciously round amount: ${amount:,.2f}',
        ))

        # Weekend transaction rule
        self.add_rule(Rule(
            id='weekend_transaction',
            name='Weekend Transaction',
            description='Detect transactions on weekends',
            enabled=True,
            severity='low',
            condition=lambda t: self._is_weekend(t.get('date')),
            message_template='Transaction on weekend: {date}',
        ))

        # New vendor high amount rule
        self.add_rule(Rule(
            id='new_vendor_high_amount',
            name='New Vendor High Amount',
            description='Detect high amounts to new vendors',
            enabled=True,
            severity='medium',
            condition=lambda t: t.get('is_new_vendor', False) and abs(t.get('amount', 0)) > 10000,
            message_template='High amount (${amount:,.2f}) to new vendor: {vendor}',
        ))

        # Sequential invoice numbers gap
        self.add_rule(Rule(
            id='invoice_number_gap',
            name='Invoice Number Gap',
            description='Detect gaps in sequential invoice numbers',
            enabled=True,
            severity='medium',
            condition=lambda t: t.get('invoice_gap', 0) > 5,
            message_template='Gap of {invoice_gap} in invoice sequence',
        ))

        # Same amount different vendor
        self.add_rule(Rule(
            id='same_amount_diff_vendor',
            name='Same Amount Different Vendor',
            description='Detect identical amounts to different vendors same day',
            enabled=True,
            severity='medium',
            condition=lambda t: t.get('same_amount_different_vendor', False),
            message_template='Same amount ${amount:,.2f} to multiple vendors',
        ))

    def _is_suspicious_round(self, amount: float) -> bool:
        """Check if amount is suspiciously round"""
        if amount == 0:
            return False
        abs_amount = abs(amount)
        # Check if amount is exact thousands with no cents
        return abs_amount >= 1000 and abs_amount % 1000 == 0

    def _is_weekend(self, date_value) -> bool:
        """Check if date is weekend"""
        if not date_value:
            return False
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value)
        return date_value.weekday() >= 5

    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        self._rules[rule.id] = rule

    def remove_rule(self, rule_id: str):
        """Remove a rule from the engine"""
        if rule_id in self._rules:
            del self._rules[rule_id]

    def enable_rule(self, rule_id: str):
        """Enable a rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str):
        """Disable a rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all rules"""
        return [
            {
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'enabled': r.enabled,
                'severity': r.severity,
            }
            for r in self._rules.values()
        ]

    def evaluate(
        self,
        tenant_id: str,
        transaction: Dict[str, Any],
    ) -> List[Anomaly]:
        """
        Evaluate transaction against all rules

        Args:
            tenant_id: Tenant ID
            transaction: Transaction data

        Returns:
            List of triggered anomalies
        """
        anomalies = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            try:
                if rule.condition(transaction):
                    # Format message
                    try:
                        message = rule.message_template.format(**transaction)
                    except KeyError:
                        message = rule.name

                    # Check if similar anomaly exists
                    txn_id = transaction.get('id', 'unknown')
                    if Anomaly.exists(tenant_id, 'transaction', txn_id, f'rule_{rule.id}'):
                        continue

                    anomaly = Anomaly(
                        tenant_id=tenant_id,
                        anomaly_type=f'rule_{rule.id}',
                        severity=rule.severity,
                        risk_score=self._severity_to_score(rule.severity),
                        entity_type='transaction',
                        entity_id=txn_id,
                        title=message,
                        description=rule.description,
                        detection_method='rule',
                        detection_rule=rule.id,
                        evidence={
                            'rule_id': rule.id,
                            'rule_name': rule.name,
                            'transaction': transaction,
                        },
                    )
                    anomalies.append(anomaly)

            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.id}: {e}")

        return anomalies

    def evaluate_batch(
        self,
        tenant_id: str,
        transactions: List[Dict[str, Any]],
    ) -> List[Anomaly]:
        """
        Evaluate multiple transactions against all rules

        Args:
            tenant_id: Tenant ID
            transactions: List of transaction data

        Returns:
            List of triggered anomalies
        """
        all_anomalies = []

        for transaction in transactions:
            anomalies = self.evaluate(tenant_id, transaction)
            all_anomalies.extend(anomalies)

        # Save all anomalies
        for anomaly in all_anomalies:
            anomaly.save()

        return all_anomalies

    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to risk score"""
        scores = {
            'critical': 0.95,
            'high': 0.75,
            'medium': 0.50,
            'low': 0.25,
        }
        return scores.get(severity, 0.5)


# Custom rule builder
class RuleBuilder:
    """Builder for creating custom rules"""

    def __init__(self, rule_id: str):
        self.rule_id = rule_id
        self._name = rule_id
        self._description = ''
        self._enabled = True
        self._severity = 'medium'
        self._conditions: List[Callable] = []
        self._message = rule_id

    def name(self, name: str) -> 'RuleBuilder':
        self._name = name
        return self

    def description(self, desc: str) -> 'RuleBuilder':
        self._description = desc
        return self

    def severity(self, severity: str) -> 'RuleBuilder':
        self._severity = severity
        return self

    def message(self, template: str) -> 'RuleBuilder':
        self._message = template
        return self

    def when_amount_greater_than(self, threshold: float) -> 'RuleBuilder':
        self._conditions.append(lambda t: abs(t.get('amount', 0)) > threshold)
        return self

    def when_amount_less_than(self, threshold: float) -> 'RuleBuilder':
        self._conditions.append(lambda t: abs(t.get('amount', 0)) < threshold)
        return self

    def when_vendor_is(self, vendor: str) -> 'RuleBuilder':
        self._conditions.append(lambda t: t.get('vendor', '').lower() == vendor.lower())
        return self

    def when_category_is(self, category: str) -> 'RuleBuilder':
        self._conditions.append(lambda t: t.get('category', '').lower() == category.lower())
        return self

    def build(self) -> Rule:
        """Build the rule"""
        def combined_condition(t: Dict) -> bool:
            return all(cond(t) for cond in self._conditions)

        return Rule(
            id=self.rule_id,
            name=self._name,
            description=self._description,
            enabled=self._enabled,
            severity=self._severity,
            condition=combined_condition,
            message_template=self._message,
        )
