"""Compliance management service."""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from app.audit.models.compliance import (
    RetentionPolicy, ComplianceRule, ComplianceViolation, AccessLog,
    ComplianceStandard
)
from app.audit.models.audit_log import AuditLog, AuditSeverity
from app.audit.schemas.compliance import (
    RetentionPolicyCreate, RetentionPolicyResponse,
    ComplianceRuleCreate, ComplianceRuleResponse,
    ComplianceViolationResponse, ComplianceDashboard, AccessReport
)


class ComplianceService:
    """Service for compliance management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==========================================
    # RETENTION POLICIES
    # ==========================================
    
    async def create_retention_policy(
        self,
        customer_id: UUID,
        data: RetentionPolicyCreate
    ) -> RetentionPolicy:
        """Create a new retention policy."""
        policy = RetentionPolicy(
            id=uuid4(),
            customer_id=customer_id,
            name=data.name,
            description=data.description,
            resource_type=data.resource_type,
            retention_days=data.retention_days,
            archive_after_days=data.archive_after_days,
            compliance_standard=ComplianceStandard(data.compliance_standard) if data.compliance_standard else None,
            regulation_reference=data.regulation_reference,
            action_on_expiry=data.action_on_expiry
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    async def get_retention_policies(
        self,
        customer_id: UUID,
        include_system: bool = True
    ) -> List[RetentionPolicy]:
        """Get all retention policies."""
        query = select(RetentionPolicy).where(
            RetentionPolicy.customer_id == customer_id
        )
        if not include_system:
            query = query.where(RetentionPolicy.is_system == False)
        
        query = query.order_by(RetentionPolicy.resource_type)
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_policy_for_resource(
        self,
        customer_id: UUID,
        resource_type: str
    ) -> Optional[RetentionPolicy]:
        """Get retention policy for a specific resource type."""
        query = select(RetentionPolicy).where(
            RetentionPolicy.customer_id == customer_id,
            RetentionPolicy.resource_type == resource_type,
            RetentionPolicy.is_active == True
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    # ==========================================
    # COMPLIANCE RULES
    # ==========================================
    
    async def create_compliance_rule(
        self,
        customer_id: UUID,
        data: ComplianceRuleCreate
    ) -> ComplianceRule:
        """Create a new compliance rule."""
        rule = ComplianceRule(
            id=uuid4(),
            customer_id=customer_id,
            code=data.code,
            name=data.name,
            description=data.description,
            compliance_standard=ComplianceStandard(data.compliance_standard),
            category=data.category,
            rule_type=data.rule_type,
            rule_config=data.rule_config,
            severity=data.severity,
            alert_on_violation=data.alert_on_violation,
            block_on_violation=data.block_on_violation,
            notify_users=data.notify_users
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    async def get_compliance_rules(
        self,
        customer_id: UUID,
        standard: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[ComplianceRule]:
        """Get compliance rules."""
        query = select(ComplianceRule).where(
            ComplianceRule.customer_id == customer_id
        )
        
        if standard:
            query = query.where(ComplianceRule.compliance_standard == standard)
        if category:
            query = query.where(ComplianceRule.category == category)
        if active_only:
            query = query.where(ComplianceRule.is_active == True)
        
        query = query.order_by(ComplianceRule.compliance_standard, ComplianceRule.code)
        result = self.db.execute(query)
        return result.scalars().all()
    
    # ==========================================
    # VIOLATIONS
    # ==========================================
    
    async def record_violation(
        self,
        customer_id: UUID,
        rule_id: UUID,
        violation_type: str,
        severity: str,
        description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        audit_log_id: Optional[UUID] = None,
        details: Optional[dict] = None
    ) -> ComplianceViolation:
        """Record a compliance violation."""
        violation = ComplianceViolation(
            id=uuid4(),
            customer_id=customer_id,
            rule_id=rule_id,
            violation_type=violation_type,
            severity=severity,
            description=description,
            details=details,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            audit_log_id=audit_log_id
        )
        
        self.db.add(violation)
        self.db.commit()
        self.db.refresh(violation)
        
        return violation
    
    async def get_violations(
        self,
        customer_id: UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        rule_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[ComplianceViolation], int]:
        """Get compliance violations."""
        query = select(ComplianceViolation).where(
            ComplianceViolation.customer_id == customer_id
        )
        
        if status:
            query = query.where(ComplianceViolation.status == status)
        if severity:
            query = query.where(ComplianceViolation.severity == severity)
        if rule_id:
            query = query.where(ComplianceViolation.rule_id == rule_id)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()
        
        query = query.order_by(desc(ComplianceViolation.detected_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = self.db.execute(query)
        violations = result.scalars().all()
        
        return violations, total
    
    async def resolve_violation(
        self,
        customer_id: UUID,
        violation_id: UUID,
        resolved_by: UUID,
        status: str,
        resolution_notes: str
    ) -> Optional[ComplianceViolation]:
        """Resolve a compliance violation."""
        query = select(ComplianceViolation).where(
            ComplianceViolation.id == violation_id,
            ComplianceViolation.customer_id == customer_id
        )
        result = self.db.execute(query)
        violation = result.scalar_one_or_none()
        
        if violation:
            violation.status = status
            violation.resolved_by = resolved_by
            violation.resolved_at = datetime.utcnow()
            violation.resolution_notes = resolution_notes
            self.db.commit()
            self.db.refresh(violation)
        
        return violation
    
    # ==========================================
    # ACCESS LOGGING
    # ==========================================
    
    async def log_access(
        self,
        customer_id: UUID,
        user_id: UUID,
        user_email: str,
        resource_type: str,
        resource_id: str,
        access_type: str,
        resource_name: Optional[str] = None,
        data_classification: str = "internal",
        contains_pii: bool = False,
        contains_financial: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        access_reason: Optional[str] = None
    ) -> AccessLog:
        """Log access to sensitive data."""
        access_log = AccessLog(
            id=uuid4(),
            customer_id=customer_id,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            access_type=access_type,
            data_classification=data_classification,
            contains_pii=contains_pii,
            contains_financial=contains_financial,
            ip_address=ip_address,
            user_agent=user_agent,
            access_reason=access_reason
        )
        
        self.db.add(access_log)
        self.db.commit()
        self.db.refresh(access_log)
        
        return access_log
    
    async def get_access_report(
        self,
        customer_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> AccessReport:
        """Generate access report for a period."""
        base_query = select(AccessLog).where(
            AccessLog.customer_id == customer_id,
            AccessLog.accessed_at >= start_date,
            AccessLog.accessed_at <= end_date
        )
        
        total = self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        ).scalar()
        
        type_counts = self.db.execute(
            select(AccessLog.access_type, func.count()).where(
                AccessLog.customer_id == customer_id,
                AccessLog.accessed_at >= start_date,
                AccessLog.accessed_at <= end_date
            ).group_by(AccessLog.access_type)
        ).all()
        accesses_by_type = {row[0]: row[1] for row in type_counts}
        
        class_counts = self.db.execute(
            select(AccessLog.data_classification, func.count()).where(
                AccessLog.customer_id == customer_id,
                AccessLog.accessed_at >= start_date,
                AccessLog.accessed_at <= end_date
            ).group_by(AccessLog.data_classification)
        ).all()
        accesses_by_classification = {row[0]: row[1] for row in class_counts}
        
        pii_count = self.db.execute(
            select(func.count()).where(
                AccessLog.customer_id == customer_id,
                AccessLog.accessed_at >= start_date,
                AccessLog.accessed_at <= end_date,
                AccessLog.contains_pii == True
            )
        ).scalar()
        
        financial_count = self.db.execute(
            select(func.count()).where(
                AccessLog.customer_id == customer_id,
                AccessLog.accessed_at >= start_date,
                AccessLog.accessed_at <= end_date,
                AccessLog.contains_financial == True
            )
        ).scalar()
        
        top_accessors = self.db.execute(
            select(AccessLog.user_email, func.count().label('count')).where(
                AccessLog.customer_id == customer_id,
                AccessLog.accessed_at >= start_date,
                AccessLog.accessed_at <= end_date
            ).group_by(AccessLog.user_email).order_by(desc('count')).limit(10)
        ).all()
        
        return AccessReport(
            period_start=start_date,
            period_end=end_date,
            total_accesses=total,
            accesses_by_type=accesses_by_type,
            accesses_by_classification=accesses_by_classification,
            pii_accesses=pii_count,
            financial_accesses=financial_count,
            top_accessors=[{"email": row[0], "count": row[1]} for row in top_accessors]
        )
    
    # ==========================================
    # DASHBOARD
    # ==========================================
    
    async def get_compliance_dashboard(
        self,
        customer_id: UUID
    ) -> ComplianceDashboard:
        """Get compliance dashboard summary."""
        total_rules = self.db.execute(
            select(func.count()).where(
                ComplianceRule.customer_id == customer_id
            )
        ).scalar()
        
        active_rules = self.db.execute(
            select(func.count()).where(
                ComplianceRule.customer_id == customer_id,
                ComplianceRule.is_active == True
            )
        ).scalar()
        
        open_violations = self.db.execute(
            select(func.count()).where(
                ComplianceViolation.customer_id == customer_id,
                ComplianceViolation.status == "open"
            )
        ).scalar()
        
        severity_counts = self.db.execute(
            select(ComplianceViolation.severity, func.count()).where(
                ComplianceViolation.customer_id == customer_id,
                ComplianceViolation.status == "open"
            ).group_by(ComplianceViolation.severity)
        ).all()
        violations_by_severity = {row[0]: row[1] for row in severity_counts}
        
        standard_counts = self.db.execute(
            select(ComplianceRule.compliance_standard, func.count(ComplianceViolation.id)).join(
                ComplianceViolation, ComplianceViolation.rule_id == ComplianceRule.id
            ).where(
                ComplianceViolation.customer_id == customer_id,
                ComplianceViolation.status == "open"
            ).group_by(ComplianceRule.compliance_standard)
        ).all()
        violations_by_standard = {str(row[0].value): row[1] for row in standard_counts}
        
        retention_count = self.db.execute(
            select(func.count()).where(
                RetentionPolicy.customer_id == customer_id,
                RetentionPolicy.is_active == True
            )
        ).scalar()
        
        recent = self.db.execute(
            select(ComplianceViolation).where(
                ComplianceViolation.customer_id == customer_id
            ).order_by(desc(ComplianceViolation.detected_at)).limit(5)
        ).scalars().all()
        
        total_possible = max(active_rules * 10, 1)
        violations_weight = sum(
            3 if v == "critical" else 2 if v == "high" else 1
            for v in violations_by_severity.keys()
            for _ in range(violations_by_severity[v])
        )
        score = max(0, min(100, 100 - (violations_weight / total_possible * 100)))
        
        return ComplianceDashboard(
            total_rules=total_rules,
            active_rules=active_rules,
            open_violations=open_violations,
            violations_by_severity=violations_by_severity,
            violations_by_standard=violations_by_standard,
            retention_policies=retention_count,
            recent_violations=[ComplianceViolationResponse.model_validate(v) for v in recent],
            compliance_score=round(score, 1)
        )
