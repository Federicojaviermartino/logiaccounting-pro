"""
Policy engine for conditional access control in LogiAccounting Pro.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Callable, Union
from datetime import datetime, time
from ipaddress import ip_address, ip_network
import re


class PolicyEffect(str, Enum):
    """Policy evaluation result."""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"


class PolicyPriority(int, Enum):
    """Policy evaluation priority."""

    CRITICAL = 1000
    HIGH = 750
    NORMAL = 500
    LOW = 250
    FALLBACK = 0


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""

    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"


@dataclass
class PolicyCondition:
    """Single condition for policy evaluation."""

    field: str
    operator: ConditionOperator
    value: Any
    negate: bool = False

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        field_value = self._get_field_value(context, self.field)
        result = self._evaluate_operator(field_value)
        return not result if self.negate else result

    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get value from context using dot notation."""
        parts = field_path.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _evaluate_operator(self, field_value: Any) -> bool:
        """Evaluate the operator against field value."""
        if self.operator == ConditionOperator.EXISTS:
            return field_value is not None

        if self.operator == ConditionOperator.NOT_EXISTS:
            return field_value is None

        if field_value is None:
            return False

        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value

        if self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value

        if self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value

        if self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value

        if self.operator == ConditionOperator.GREATER_EQUAL:
            return field_value >= self.value

        if self.operator == ConditionOperator.LESS_EQUAL:
            return field_value <= self.value

        if self.operator == ConditionOperator.IN:
            return field_value in self.value

        if self.operator == ConditionOperator.NOT_IN:
            return field_value not in self.value

        if self.operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, (list, tuple, set)):
                return self.value in field_value
            if isinstance(field_value, str):
                return self.value in field_value
            return False

        if self.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, (list, tuple, set)):
                return self.value not in field_value
            if isinstance(field_value, str):
                return self.value not in field_value
            return True

        if self.operator == ConditionOperator.MATCHES:
            if isinstance(field_value, str):
                return bool(re.match(self.value, field_value))
            return False

        if self.operator == ConditionOperator.BETWEEN:
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                return self.value[0] <= field_value <= self.value[1]
            return False

        return False


@dataclass
class TimeBasedCondition:
    """Time-based access restriction."""

    start_time: time
    end_time: time
    days_of_week: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    timezone: str = "UTC"

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if current time is within allowed window."""
        now = context.get("current_time", datetime.utcnow())
        if isinstance(now, str):
            now = datetime.fromisoformat(now)

        current_time = now.time()
        current_day = now.weekday()

        if current_day not in self.days_of_week:
            return False

        if self.start_time <= self.end_time:
            return self.start_time <= current_time <= self.end_time
        else:
            return current_time >= self.start_time or current_time <= self.end_time


@dataclass
class IPBasedCondition:
    """IP-based access restriction."""

    allowed_networks: List[str] = field(default_factory=list)
    blocked_networks: List[str] = field(default_factory=list)
    allow_private: bool = True

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if IP address is allowed."""
        ip_str = context.get("ip_address") or context.get("client_ip")
        if not ip_str:
            return False

        try:
            ip = ip_address(ip_str)
        except ValueError:
            return False

        for blocked in self.blocked_networks:
            try:
                if ip in ip_network(blocked, strict=False):
                    return False
            except ValueError:
                continue

        if self.allow_private and ip.is_private:
            return True

        if not self.allowed_networks:
            return True

        for allowed in self.allowed_networks:
            try:
                if ip in ip_network(allowed, strict=False):
                    return True
            except ValueError:
                continue

        return False


@dataclass
class ResourceOwnershipCondition:
    """Resource ownership verification."""

    resource_user_field: str = "user_id"
    resource_org_field: str = "organization_id"
    allow_organization_access: bool = True

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if user owns or has access to resource."""
        user_id = context.get("user_id")
        resource = context.get("resource", {})

        resource_owner = resource.get(self.resource_user_field)
        if resource_owner and resource_owner == user_id:
            return True

        if self.allow_organization_access:
            user_org = context.get("organization_id")
            resource_org = resource.get(self.resource_org_field)
            if user_org and resource_org and user_org == resource_org:
                return True

        return False


@dataclass
class Policy:
    """Access control policy definition."""

    id: str
    name: str
    description: str
    effect: PolicyEffect
    priority: int = PolicyPriority.NORMAL.value
    resources: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    conditions: List[PolicyCondition] = field(default_factory=list)
    time_condition: Optional[TimeBasedCondition] = None
    ip_condition: Optional[IPBasedCondition] = None
    ownership_condition: Optional[ResourceOwnershipCondition] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def matches_request(
        self,
        resource: str,
        action: str,
        role: Optional[str] = None,
    ) -> bool:
        """Check if policy applies to the request."""
        if not self.is_active:
            return False

        if self.resources and resource not in self.resources:
            if not any(self._matches_pattern(resource, r) for r in self.resources):
                return False

        if self.actions and action not in self.actions:
            if not any(self._matches_pattern(action, a) for a in self.actions):
                return False

        if self.roles and role and role not in self.roles:
            return False

        return True

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern with wildcards."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        return value == pattern

    def evaluate(self, context: Dict[str, Any]) -> PolicyEffect:
        """Evaluate policy against context."""
        if not self.is_active:
            return PolicyEffect.ABSTAIN

        for condition in self.conditions:
            if not condition.evaluate(context):
                return PolicyEffect.ABSTAIN

        if self.time_condition and not self.time_condition.evaluate(context):
            return PolicyEffect.DENY if self.effect == PolicyEffect.ALLOW else PolicyEffect.ABSTAIN

        if self.ip_condition and not self.ip_condition.evaluate(context):
            return PolicyEffect.DENY if self.effect == PolicyEffect.ALLOW else PolicyEffect.ABSTAIN

        if self.ownership_condition and not self.ownership_condition.evaluate(context):
            return PolicyEffect.ABSTAIN

        return self.effect


class PolicyEngine:
    """Engine for evaluating access control policies."""

    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._policy_cache: Dict[str, PolicyEffect] = {}
        self._cache_ttl: int = 300

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies[policy.id] = policy
        self._invalidate_cache()

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the engine."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            self._invalidate_cache()
            return True
        return False

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self._policies.get(policy_id)

    def get_all_policies(self, active_only: bool = True) -> List[Policy]:
        """Get all policies, optionally filtered by active status."""
        policies = list(self._policies.values())
        if active_only:
            policies = [p for p in policies if p.is_active]
        return sorted(policies, key=lambda p: p.priority, reverse=True)

    def evaluate(
        self,
        resource: str,
        action: str,
        context: Dict[str, Any],
        role: Optional[str] = None,
    ) -> PolicyEffect:
        """Evaluate all applicable policies and determine access."""
        applicable_policies = [
            p for p in self._policies.values()
            if p.matches_request(resource, action, role)
        ]

        applicable_policies.sort(key=lambda p: p.priority, reverse=True)

        for policy in applicable_policies:
            result = policy.evaluate(context)
            if result == PolicyEffect.DENY:
                return PolicyEffect.DENY
            if result == PolicyEffect.ALLOW:
                return PolicyEffect.ALLOW

        return PolicyEffect.ABSTAIN

    def evaluate_with_details(
        self,
        resource: str,
        action: str,
        context: Dict[str, Any],
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate policies and return detailed results."""
        applicable_policies = [
            p for p in self._policies.values()
            if p.matches_request(resource, action, role)
        ]

        applicable_policies.sort(key=lambda p: p.priority, reverse=True)

        evaluation_results = []
        final_effect = PolicyEffect.ABSTAIN
        deciding_policy = None

        for policy in applicable_policies:
            result = policy.evaluate(context)
            evaluation_results.append({
                "policy_id": policy.id,
                "policy_name": policy.name,
                "priority": policy.priority,
                "effect": result.value,
            })

            if final_effect == PolicyEffect.ABSTAIN:
                if result in (PolicyEffect.ALLOW, PolicyEffect.DENY):
                    final_effect = result
                    deciding_policy = policy.id

        return {
            "effect": final_effect.value,
            "deciding_policy": deciding_policy,
            "evaluated_policies": len(evaluation_results),
            "policy_results": evaluation_results,
        }

    def _invalidate_cache(self) -> None:
        """Invalidate the policy evaluation cache."""
        self._policy_cache.clear()

    def create_time_policy(
        self,
        policy_id: str,
        name: str,
        resources: List[str],
        actions: List[str],
        start_time: time,
        end_time: time,
        days_of_week: Optional[List[int]] = None,
        effect: PolicyEffect = PolicyEffect.ALLOW,
    ) -> Policy:
        """Create a time-based access policy."""
        time_condition = TimeBasedCondition(
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week or [0, 1, 2, 3, 4],
        )

        policy = Policy(
            id=policy_id,
            name=name,
            description=f"Time-based access: {start_time} - {end_time}",
            effect=effect,
            resources=resources,
            actions=actions,
            time_condition=time_condition,
        )

        self.add_policy(policy)
        return policy

    def create_ip_policy(
        self,
        policy_id: str,
        name: str,
        resources: List[str],
        actions: List[str],
        allowed_networks: Optional[List[str]] = None,
        blocked_networks: Optional[List[str]] = None,
        effect: PolicyEffect = PolicyEffect.ALLOW,
    ) -> Policy:
        """Create an IP-based access policy."""
        ip_condition = IPBasedCondition(
            allowed_networks=allowed_networks or [],
            blocked_networks=blocked_networks or [],
        )

        policy = Policy(
            id=policy_id,
            name=name,
            description="IP-based access restriction",
            effect=effect,
            resources=resources,
            actions=actions,
            ip_condition=ip_condition,
        )

        self.add_policy(policy)
        return policy

    def create_ownership_policy(
        self,
        policy_id: str,
        name: str,
        resources: List[str],
        actions: List[str],
        effect: PolicyEffect = PolicyEffect.ALLOW,
    ) -> Policy:
        """Create a resource ownership policy."""
        ownership_condition = ResourceOwnershipCondition()

        policy = Policy(
            id=policy_id,
            name=name,
            description="Resource ownership verification",
            effect=effect,
            resources=resources,
            actions=actions,
            ownership_condition=ownership_condition,
        )

        self.add_policy(policy)
        return policy

    def create_conditional_policy(
        self,
        policy_id: str,
        name: str,
        resources: List[str],
        actions: List[str],
        conditions: List[Dict[str, Any]],
        effect: PolicyEffect = PolicyEffect.ALLOW,
    ) -> Policy:
        """Create a policy with custom conditions."""
        parsed_conditions = []
        for cond in conditions:
            parsed_conditions.append(PolicyCondition(
                field=cond["field"],
                operator=ConditionOperator(cond["operator"]),
                value=cond["value"],
                negate=cond.get("negate", False),
            ))

        policy = Policy(
            id=policy_id,
            name=name,
            description="Conditional access policy",
            effect=effect,
            resources=resources,
            actions=actions,
            conditions=parsed_conditions,
        )

        self.add_policy(policy)
        return policy


policy_engine = PolicyEngine()
