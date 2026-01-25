"""
IP filtering implementation for LogiAccounting Pro.
"""

from typing import Optional, Dict, List, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address, IPv4Network, IPv6Network
from enum import Enum
import threading
import re


class IPFilterAction(str, Enum):
    """Action to take for filtered IPs."""

    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    LOG_ONLY = "log_only"


class IPFilterReason(str, Enum):
    """Reason for IP filtering."""

    ALLOWLIST = "allowlist"
    BLOCKLIST = "blocklist"
    GEOGRAPHIC = "geographic"
    REPUTATION = "reputation"
    RATE_LIMIT = "rate_limit"
    MANUAL_BLOCK = "manual_block"
    TEMPORARY_BLOCK = "temporary_block"
    BOT_DETECTION = "bot_detection"


@dataclass
class IPFilterRule:
    """IP filter rule definition."""

    id: str
    name: str
    network: str
    action: IPFilterAction
    reason: IPFilterReason
    priority: int = 0
    enabled: bool = True
    expires_at: Optional[datetime] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if rule has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def matches(self, ip: str) -> bool:
        """Check if IP matches this rule."""
        if not self.enabled or self.is_expired():
            return False

        try:
            check_ip = ip_address(ip)
            rule_network = ip_network(self.network, strict=False)
            return check_ip in rule_network
        except ValueError:
            return False


@dataclass
class IPFilterResult:
    """Result of IP filter check."""

    allowed: bool
    action: IPFilterAction
    reason: Optional[IPFilterReason] = None
    matched_rule: Optional[str] = None
    message: str = ""
    challenge_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class IPFilter:
    """IP address filtering service."""

    def __init__(self):
        self._rules: Dict[str, IPFilterRule] = {}
        self._allowlist: Set[str] = set()
        self._blocklist: Set[str] = set()
        self._temporary_blocks: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._default_action = IPFilterAction.ALLOW
        self._allow_private = True
        self._allow_loopback = True
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize default rules."""
        self.add_rule(IPFilterRule(
            id="allow-loopback-v4",
            name="Allow IPv4 Loopback",
            network="127.0.0.0/8",
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=1000,
        ))

        self.add_rule(IPFilterRule(
            id="allow-loopback-v6",
            name="Allow IPv6 Loopback",
            network="::1/128",
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=1000,
        ))

        self.add_rule(IPFilterRule(
            id="allow-private-10",
            name="Allow Private 10.x.x.x",
            network="10.0.0.0/8",
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=900,
        ))

        self.add_rule(IPFilterRule(
            id="allow-private-172",
            name="Allow Private 172.16.x.x",
            network="172.16.0.0/12",
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=900,
        ))

        self.add_rule(IPFilterRule(
            id="allow-private-192",
            name="Allow Private 192.168.x.x",
            network="192.168.0.0/16",
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=900,
        ))

    def add_rule(self, rule: IPFilterRule) -> None:
        """Add an IP filter rule."""
        with self._lock:
            self._rules[rule.id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an IP filter rule."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False

    def get_rule(self, rule_id: str) -> Optional[IPFilterRule]:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(
        self,
        organization_id: Optional[str] = None,
        action: Optional[IPFilterAction] = None,
        include_expired: bool = False,
    ) -> List[IPFilterRule]:
        """List all rules with optional filtering."""
        rules = list(self._rules.values())

        if organization_id:
            rules = [r for r in rules if r.organization_id == organization_id or r.organization_id is None]

        if action:
            rules = [r for r in rules if r.action == action]

        if not include_expired:
            rules = [r for r in rules if not r.is_expired()]

        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def add_to_allowlist(
        self,
        ip_or_network: str,
        name: Optional[str] = None,
        organization_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> IPFilterRule:
        """Add IP or network to allowlist."""
        rule_id = f"allowlist-{ip_or_network.replace('/', '-')}"
        rule = IPFilterRule(
            id=rule_id,
            name=name or f"Allowlist: {ip_or_network}",
            network=ip_or_network,
            action=IPFilterAction.ALLOW,
            reason=IPFilterReason.ALLOWLIST,
            priority=800,
            organization_id=organization_id,
            created_by=created_by,
        )
        self.add_rule(rule)
        return rule

    def add_to_blocklist(
        self,
        ip_or_network: str,
        name: Optional[str] = None,
        reason: IPFilterReason = IPFilterReason.BLOCKLIST,
        expires_in_hours: Optional[int] = None,
        organization_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> IPFilterRule:
        """Add IP or network to blocklist."""
        rule_id = f"blocklist-{ip_or_network.replace('/', '-')}"
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        rule = IPFilterRule(
            id=rule_id,
            name=name or f"Blocklist: {ip_or_network}",
            network=ip_or_network,
            action=IPFilterAction.DENY,
            reason=reason,
            priority=850,
            expires_at=expires_at,
            organization_id=organization_id,
            created_by=created_by,
        )
        self.add_rule(rule)
        return rule

    def block_temporarily(
        self,
        ip: str,
        duration_minutes: int = 30,
        reason: IPFilterReason = IPFilterReason.TEMPORARY_BLOCK,
    ) -> None:
        """Temporarily block an IP address."""
        with self._lock:
            self._temporary_blocks[ip] = datetime.utcnow() + timedelta(minutes=duration_minutes)

    def unblock(self, ip: str) -> bool:
        """Remove temporary block from an IP."""
        with self._lock:
            if ip in self._temporary_blocks:
                del self._temporary_blocks[ip]
                return True

            for rule_id, rule in list(self._rules.items()):
                if rule.network == ip or rule.network == f"{ip}/32":
                    if rule.action == IPFilterAction.DENY:
                        del self._rules[rule_id]
                        return True
        return False

    def _check_temporary_block(self, ip: str) -> Optional[datetime]:
        """Check if IP is temporarily blocked."""
        with self._lock:
            if ip in self._temporary_blocks:
                if datetime.utcnow() < self._temporary_blocks[ip]:
                    return self._temporary_blocks[ip]
                del self._temporary_blocks[ip]
        return None

    def check(
        self,
        ip: str,
        organization_id: Optional[str] = None,
    ) -> IPFilterResult:
        """Check if an IP address is allowed."""
        try:
            parsed_ip = ip_address(ip)
        except ValueError:
            return IPFilterResult(
                allowed=False,
                action=IPFilterAction.DENY,
                reason=IPFilterReason.BLOCKLIST,
                message="Invalid IP address format",
            )

        temp_block_expires = self._check_temporary_block(ip)
        if temp_block_expires:
            return IPFilterResult(
                allowed=False,
                action=IPFilterAction.DENY,
                reason=IPFilterReason.TEMPORARY_BLOCK,
                message=f"IP temporarily blocked until {temp_block_expires.isoformat()}",
                metadata={"expires_at": temp_block_expires.isoformat()},
            )

        if self._allow_loopback and parsed_ip.is_loopback:
            return IPFilterResult(
                allowed=True,
                action=IPFilterAction.ALLOW,
                reason=IPFilterReason.ALLOWLIST,
                message="Loopback address allowed",
            )

        if self._allow_private and parsed_ip.is_private:
            return IPFilterResult(
                allowed=True,
                action=IPFilterAction.ALLOW,
                reason=IPFilterReason.ALLOWLIST,
                message="Private network address allowed",
            )

        rules = self.list_rules(organization_id=organization_id)
        for rule in rules:
            if rule.matches(ip):
                if rule.action == IPFilterAction.DENY:
                    return IPFilterResult(
                        allowed=False,
                        action=rule.action,
                        reason=rule.reason,
                        matched_rule=rule.id,
                        message=f"Blocked by rule: {rule.name}",
                    )
                elif rule.action == IPFilterAction.ALLOW:
                    return IPFilterResult(
                        allowed=True,
                        action=rule.action,
                        reason=rule.reason,
                        matched_rule=rule.id,
                        message=f"Allowed by rule: {rule.name}",
                    )
                elif rule.action == IPFilterAction.CHALLENGE:
                    return IPFilterResult(
                        allowed=False,
                        action=rule.action,
                        reason=rule.reason,
                        matched_rule=rule.id,
                        message="Challenge required",
                        challenge_required=True,
                    )
                elif rule.action == IPFilterAction.LOG_ONLY:
                    continue

        return IPFilterResult(
            allowed=self._default_action == IPFilterAction.ALLOW,
            action=self._default_action,
            message="Default action applied",
        )

    def is_allowed(self, ip: str, organization_id: Optional[str] = None) -> bool:
        """Simple check if IP is allowed."""
        return self.check(ip, organization_id).allowed

    def get_blocked_ips(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of all blocked IPs."""
        blocked = []

        with self._lock:
            for ip, expires in self._temporary_blocks.items():
                if datetime.utcnow() < expires:
                    blocked.append({
                        "ip": ip,
                        "type": "temporary",
                        "reason": IPFilterReason.TEMPORARY_BLOCK.value,
                        "expires_at": expires.isoformat(),
                    })

        for rule in self.list_rules(organization_id=organization_id, action=IPFilterAction.DENY):
            blocked.append({
                "ip": rule.network,
                "type": "rule",
                "reason": rule.reason.value,
                "rule_id": rule.id,
                "rule_name": rule.name,
                "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
            })

        return blocked

    def cleanup_expired(self) -> int:
        """Remove expired temporary blocks and rules."""
        count = 0

        with self._lock:
            current_time = datetime.utcnow()

            expired_temps = [ip for ip, exp in self._temporary_blocks.items() if exp < current_time]
            for ip in expired_temps:
                del self._temporary_blocks[ip]
                count += 1

            expired_rules = [rule_id for rule_id, rule in self._rules.items() if rule.is_expired()]
            for rule_id in expired_rules:
                del self._rules[rule_id]
                count += 1

        return count

    def set_default_action(self, action: IPFilterAction) -> None:
        """Set the default action for unmatched IPs."""
        self._default_action = action

    def set_allow_private(self, allow: bool) -> None:
        """Set whether to allow private network addresses."""
        self._allow_private = allow

    def set_allow_loopback(self, allow: bool) -> None:
        """Set whether to allow loopback addresses."""
        self._allow_loopback = allow

    def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules for backup."""
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "network": rule.network,
                "action": rule.action.value,
                "reason": rule.reason.value,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
                "organization_id": rule.organization_id,
                "metadata": rule.metadata,
                "created_at": rule.created_at.isoformat(),
                "created_by": rule.created_by,
            }
            for rule in self._rules.values()
        ]

    def import_rules(self, rules_data: List[Dict[str, Any]], merge: bool = True) -> int:
        """Import rules from backup."""
        if not merge:
            self._rules.clear()

        count = 0
        for data in rules_data:
            rule = IPFilterRule(
                id=data["id"],
                name=data["name"],
                network=data["network"],
                action=IPFilterAction(data["action"]),
                reason=IPFilterReason(data["reason"]),
                priority=data.get("priority", 0),
                enabled=data.get("enabled", True),
                expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                organization_id=data.get("organization_id"),
                metadata=data.get("metadata", {}),
                created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
                created_by=data.get("created_by"),
            )
            self.add_rule(rule)
            count += 1

        return count


_ip_filter: Optional[IPFilter] = None


def get_ip_filter() -> IPFilter:
    """Get the global IP filter instance."""
    global _ip_filter
    if _ip_filter is None:
        _ip_filter = IPFilter()
    return _ip_filter


def set_ip_filter(filter: IPFilter) -> None:
    """Set the global IP filter instance."""
    global _ip_filter
    _ip_filter = filter


def is_ip_allowed(ip: str, organization_id: Optional[str] = None) -> bool:
    """Check if IP is allowed using the global filter."""
    return get_ip_filter().is_allowed(ip, organization_id)
