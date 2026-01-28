"""
Approval Workflow Service
Multi-level approval system for transactions and payments
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models.store import db
from app.utils.activity_logger import activity_logger
from app.utils.datetime_utils import utc_now


class ApprovalService:
    """Manages approval workflows"""

    _instance = None
    _approvals: Dict[str, dict] = {}
    _rules: List[dict] = []
    _counter = 0

    DEFAULT_RULES = [
        {"min_amount": 1000, "max_amount": 5000, "levels": 1, "approvers": ["manager"]},
        {"min_amount": 5000, "max_amount": 10000, "levels": 2, "approvers": ["manager", "director"]},
        {"min_amount": 10000, "max_amount": None, "levels": 3, "approvers": ["manager", "director", "cfo"]}
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._approvals = {}
            cls._rules = cls.DEFAULT_RULES.copy()
            cls._counter = 0
        return cls._instance

    def get_rules(self) -> List[dict]:
        """Get all approval rules"""
        return self._rules

    def update_rules(self, rules: List[dict]):
        """Update approval rules"""
        self._rules = rules

    def requires_approval(self, amount: float) -> Optional[dict]:
        """Check if amount requires approval and return matching rule"""
        for rule in sorted(self._rules, key=lambda r: r["min_amount"]):
            if amount >= rule["min_amount"]:
                if rule["max_amount"] is None or amount < rule["max_amount"]:
                    return rule
        return None

    def create_approval_request(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: dict,
        amount: float,
        requested_by: str,
        requested_by_email: str
    ) -> Optional[dict]:
        """Create an approval request if needed"""
        rule = self.requires_approval(amount)
        if not rule:
            return None

        self._counter += 1
        approval_id = f"APR-{self._counter:06d}"

        approval = {
            "id": approval_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_data": entity_data,
            "amount": amount,
            "status": "pending",
            "current_level": 1,
            "required_levels": rule["levels"],
            "approver_roles": rule["approvers"],
            "approvals": [],
            "requested_by": requested_by,
            "requested_by_email": requested_by_email,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat()
        }

        self._approvals[approval_id] = approval

        activity_logger.log(
            user_id=requested_by,
            user_email=requested_by_email,
            user_role="user",
            action="CREATE",
            entity_type="approval",
            entity_id=approval_id,
            details={"amount": amount, "entity_type": entity_type}
        )

        return approval

    def approve(
        self,
        approval_id: str,
        approver_id: str,
        approver_email: str,
        approver_role: str,
        comment: str = ""
    ) -> dict:
        """Approve an approval request"""
        if approval_id not in self._approvals:
            return {"error": "Approval not found"}

        approval = self._approvals[approval_id]

        if approval["status"] != "pending":
            return {"error": "Approval is not pending"}

        if any(a["approver_id"] == approver_id for a in approval["approvals"]):
            return {"error": "Already approved by this user"}

        approval["approvals"].append({
            "approver_id": approver_id,
            "approver_email": approver_email,
            "approver_role": approver_role,
            "action": "approved",
            "comment": comment,
            "timestamp": utc_now().isoformat()
        })

        if len(approval["approvals"]) >= approval["required_levels"]:
            approval["status"] = "approved"
            approval["completed_at"] = utc_now().isoformat()
        else:
            approval["current_level"] = len(approval["approvals"]) + 1

        approval["updated_at"] = utc_now().isoformat()

        activity_logger.log(
            user_id=approver_id,
            user_email=approver_email,
            user_role=approver_role,
            action="APPROVE",
            entity_type="approval",
            entity_id=approval_id
        )

        return approval

    def reject(
        self,
        approval_id: str,
        rejector_id: str,
        rejector_email: str,
        rejector_role: str,
        reason: str = ""
    ) -> dict:
        """Reject an approval request"""
        if approval_id not in self._approvals:
            return {"error": "Approval not found"}

        approval = self._approvals[approval_id]

        if approval["status"] != "pending":
            return {"error": "Approval is not pending"}

        approval["status"] = "rejected"
        approval["rejected_by"] = rejector_id
        approval["rejection_reason"] = reason
        approval["completed_at"] = utc_now().isoformat()
        approval["updated_at"] = utc_now().isoformat()

        approval["approvals"].append({
            "approver_id": rejector_id,
            "approver_email": rejector_email,
            "approver_role": rejector_role,
            "action": "rejected",
            "comment": reason,
            "timestamp": utc_now().isoformat()
        })

        activity_logger.log(
            user_id=rejector_id,
            user_email=rejector_email,
            user_role=rejector_role,
            action="REJECT",
            entity_type="approval",
            entity_id=approval_id
        )

        return approval

    def get_pending_approvals(self, role: Optional[str] = None) -> List[dict]:
        """Get all pending approvals, optionally filtered by approver role"""
        pending = [a for a in self._approvals.values() if a["status"] == "pending"]

        if role:
            filtered = []
            for approval in pending:
                level_idx = approval["current_level"] - 1
                if level_idx < len(approval["approver_roles"]):
                    required_role = approval["approver_roles"][level_idx]
                    if role == required_role or role == "admin":
                        filtered.append(approval)
            return filtered

        return pending

    def get_approval(self, approval_id: str) -> Optional[dict]:
        """Get a specific approval"""
        return self._approvals.get(approval_id)

    def get_all_approvals(self, status: Optional[str] = None) -> List[dict]:
        """Get all approvals"""
        approvals = list(self._approvals.values())
        if status:
            approvals = [a for a in approvals if a["status"] == status]
        return sorted(approvals, key=lambda a: a["created_at"], reverse=True)


approval_service = ApprovalService()
