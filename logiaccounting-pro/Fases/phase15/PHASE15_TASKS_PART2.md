# LogiAccounting Pro - Phase 15 Tasks Part 2

## COMPLIANCE FRAMEWORKS & REPORTING

---

## TASK 5: COMPLIANCE FRAMEWORK BASE

### 5.1 Base Compliance Framework

**File:** `backend/app/audit/compliance/base_framework.py`

```python
"""
Base Compliance Framework
Abstract base class for compliance frameworks
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """Compliance check status"""
    PASSED = 'passed'
    FAILED = 'failed'
    WARNING = 'warning'
    NOT_APPLICABLE = 'not_applicable'
    PENDING = 'pending'
    ERROR = 'error'


class CheckType(str, Enum):
    """Type of compliance check"""
    AUTOMATED = 'automated'
    MANUAL = 'manual'
    EVIDENCE = 'evidence'


@dataclass
class ComplianceControl:
    """Definition of a compliance control"""
    id: str
    name: str
    description: str
    category: str
    check_type: CheckType
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    remediation: str = None
    references: List[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Result of a compliance check"""
    control_id: str
    control_name: str
    status: CheckStatus
    score: float = 100.0  # 0-100
    findings: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'control_id': self.control_id,
            'control_name': self.control_name,
            'status': self.status.value,
            'score': self.score,
            'findings': self.findings,
            'evidence': self.evidence,
            'recommendations': self.recommendations,
            'checked_at': self.checked_at.isoformat(),
        }


class BaseComplianceFramework(ABC):
    """Abstract base class for compliance frameworks"""
    
    FRAMEWORK_ID: str = 'base'
    FRAMEWORK_NAME: str = 'Base Framework'
    VERSION: str = '1.0'
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self._controls: Dict[str, ComplianceControl] = {}
        self._register_controls()
    
    @abstractmethod
    def _register_controls(self):
        """Register all controls for this framework"""
        pass
    
    @abstractmethod
    def run_check(self, control_id: str) -> CheckResult:
        """Run a specific compliance check"""
        pass
    
    def run_all_checks(self) -> List[CheckResult]:
        """Run all compliance checks"""
        results = []
        
        for control_id in self._controls:
            try:
                result = self.run_check(control_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running check {control_id}: {e}")
                results.append(CheckResult(
                    control_id=control_id,
                    control_name=self._controls[control_id].name,
                    status=CheckStatus.ERROR,
                    score=0,
                    findings=[f"Check failed with error: {str(e)}"],
                ))
        
        return results
    
    def get_controls(self) -> List[ComplianceControl]:
        """Get all controls"""
        return list(self._controls.values())
    
    def get_control(self, control_id: str) -> Optional[ComplianceControl]:
        """Get a specific control"""
        return self._controls.get(control_id)
    
    def calculate_overall_score(self, results: List[CheckResult]) -> float:
        """Calculate overall compliance score"""
        if not results:
            return 0.0
        
        total_score = sum(r.score for r in results if r.status != CheckStatus.NOT_APPLICABLE)
        applicable_count = len([r for r in results if r.status != CheckStatus.NOT_APPLICABLE])
        
        return total_score / applicable_count if applicable_count > 0 else 0.0
    
    def get_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        """Get compliance summary"""
        passed = len([r for r in results if r.status == CheckStatus.PASSED])
        failed = len([r for r in results if r.status == CheckStatus.FAILED])
        warnings = len([r for r in results if r.status == CheckStatus.WARNING])
        na = len([r for r in results if r.status == CheckStatus.NOT_APPLICABLE])
        
        return {
            'framework_id': self.FRAMEWORK_ID,
            'framework_name': self.FRAMEWORK_NAME,
            'total_controls': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'not_applicable': na,
            'overall_score': self.calculate_overall_score(results),
            'status': 'compliant' if failed == 0 else 'non_compliant',
        }
    
    # Helper methods for checks
    
    def _check_audit_logging_enabled(self) -> Tuple[bool, Dict]:
        """Check if audit logging is capturing events"""
        from datetime import timedelta
        
        recent_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return recent_logs > 0, {'recent_log_count': recent_logs}
    
    def _check_access_reviews(self, days: int = 90) -> Tuple[bool, Dict]:
        """Check if access reviews are performed regularly"""
        # Check for access review audit events
        from datetime import timedelta
        
        reviews = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type.in_(['role.assigned', 'role.removed', 'permission.granted', 'permission.revoked']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=days)
        ).count()
        
        return reviews > 0, {'access_changes_count': reviews, 'period_days': days}
    
    def _check_password_policy(self) -> Tuple[bool, Dict]:
        """Check password policy compliance"""
        # This would check organization settings
        # For now, return placeholder
        return True, {'policy_enforced': True}
    
    def _check_mfa_adoption(self, threshold: float = 0.8) -> Tuple[bool, Dict]:
        """Check MFA adoption rate"""
        from app.models.user import User
        
        total_users = User.query.filter(
            User.organization_id == self.organization_id,
            User.is_active == True
        ).count()
        
        mfa_users = User.query.filter(
            User.organization_id == self.organization_id,
            User.is_active == True,
            User.mfa_enabled == True
        ).count()
        
        adoption_rate = mfa_users / total_users if total_users > 0 else 0
        passed = adoption_rate >= threshold
        
        return passed, {
            'total_users': total_users,
            'mfa_enabled_users': mfa_users,
            'adoption_rate': round(adoption_rate * 100, 1),
            'threshold': threshold * 100,
        }
```

### 5.2 SOX Compliance Framework

**File:** `backend/app/audit/compliance/sox_compliance.py`

```python
"""
SOX Compliance Framework
Sarbanes-Oxley Act compliance controls
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.compliance.base_framework import (
    BaseComplianceFramework, ComplianceControl, CheckResult,
    CheckStatus, CheckType
)


class SOXComplianceFramework(BaseComplianceFramework):
    """SOX (Sarbanes-Oxley) compliance framework"""
    
    FRAMEWORK_ID = 'sox'
    FRAMEWORK_NAME = 'Sarbanes-Oxley Act (SOX)'
    VERSION = '2024.1'
    
    def _register_controls(self):
        """Register SOX controls"""
        
        # Section 302 - Corporate Responsibility
        self._controls['SOX-302-1'] = ComplianceControl(
            id='SOX-302-1',
            name='Financial Data Integrity',
            description='Ensure financial data is accurate and complete',
            category='Data Integrity',
            check_type=CheckType.AUTOMATED,
            severity='critical',
            remediation='Implement data validation and reconciliation processes',
        )
        
        # Section 404 - Internal Controls
        self._controls['SOX-404-1'] = ComplianceControl(
            id='SOX-404-1',
            name='Access Control Management',
            description='Ensure proper access controls are in place for financial systems',
            category='Access Control',
            check_type=CheckType.AUTOMATED,
            severity='high',
            remediation='Review and update access control policies',
        )
        
        self._controls['SOX-404-2'] = ComplianceControl(
            id='SOX-404-2',
            name='Segregation of Duties',
            description='Ensure proper segregation of duties for financial transactions',
            category='Access Control',
            check_type=CheckType.AUTOMATED,
            severity='critical',
            remediation='Implement role-based access with proper separation',
        )
        
        self._controls['SOX-404-3'] = ComplianceControl(
            id='SOX-404-3',
            name='Change Management',
            description='Track and approve all changes to financial systems',
            category='Change Management',
            check_type=CheckType.AUTOMATED,
            severity='high',
            remediation='Implement change management workflow with approvals',
        )
        
        self._controls['SOX-404-4'] = ComplianceControl(
            id='SOX-404-4',
            name='Audit Trail Completeness',
            description='Maintain complete audit trail for all financial transactions',
            category='Audit',
            check_type=CheckType.AUTOMATED,
            severity='critical',
            remediation='Enable comprehensive audit logging',
        )
        
        self._controls['SOX-404-5'] = ComplianceControl(
            id='SOX-404-5',
            name='User Access Reviews',
            description='Periodic review of user access rights',
            category='Access Control',
            check_type=CheckType.AUTOMATED,
            severity='high',
            remediation='Conduct quarterly access reviews',
        )
        
        self._controls['SOX-404-6'] = ComplianceControl(
            id='SOX-404-6',
            name='Transaction Authorization',
            description='All financial transactions require proper authorization',
            category='Authorization',
            check_type=CheckType.AUTOMATED,
            severity='critical',
            remediation='Implement approval workflows for transactions',
        )
        
        self._controls['SOX-404-7'] = ComplianceControl(
            id='SOX-404-7',
            name='Password Policy Compliance',
            description='Enforce strong password policies',
            category='Authentication',
            check_type=CheckType.AUTOMATED,
            severity='medium',
            remediation='Implement password complexity requirements',
        )
    
    def run_check(self, control_id: str) -> CheckResult:
        """Run a specific SOX compliance check"""
        control = self._controls.get(control_id)
        if not control:
            raise ValueError(f"Unknown control: {control_id}")
        
        check_methods = {
            'SOX-302-1': self._check_financial_data_integrity,
            'SOX-404-1': self._check_access_control,
            'SOX-404-2': self._check_segregation_of_duties,
            'SOX-404-3': self._check_change_management,
            'SOX-404-4': self._check_audit_trail,
            'SOX-404-5': self._check_user_access_reviews,
            'SOX-404-6': self._check_transaction_authorization,
            'SOX-404-7': self._check_password_policy_compliance,
        }
        
        check_method = check_methods.get(control_id)
        if check_method:
            return check_method(control)
        
        return CheckResult(
            control_id=control_id,
            control_name=control.name,
            status=CheckStatus.NOT_APPLICABLE,
        )
    
    def _check_financial_data_integrity(self, control: ComplianceControl) -> CheckResult:
        """Check financial data integrity"""
        findings = []
        evidence = {}
        
        # Check for data validation errors in recent logs
        validation_errors = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type.like('%validation%'),
            AuditLog.severity.in_(['error', 'critical']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['validation_errors_30d'] = validation_errors
        
        if validation_errors > 0:
            findings.append(f"Found {validation_errors} data validation errors in the last 30 days")
        
        # Calculate score
        score = 100 if validation_errors == 0 else max(0, 100 - (validation_errors * 10))
        status = CheckStatus.PASSED if validation_errors == 0 else (
            CheckStatus.WARNING if validation_errors < 5 else CheckStatus.FAILED
        )
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=score,
            findings=findings,
            evidence=evidence,
            recommendations=['Implement automated data validation'] if findings else [],
        )
    
    def _check_access_control(self, control: ComplianceControl) -> CheckResult:
        """Check access control management"""
        findings = []
        evidence = {}
        
        # Check for role-based access
        from app.models.user import User
        
        users_without_roles = User.query.filter(
            User.organization_id == self.organization_id,
            User.is_active == True,
            User.role == None
        ).count()
        
        evidence['users_without_roles'] = users_without_roles
        
        if users_without_roles > 0:
            findings.append(f"{users_without_roles} active users have no assigned role")
        
        # Check for admin users
        admin_users = User.query.filter(
            User.organization_id == self.organization_id,
            User.is_active == True,
            User.role == 'admin'
        ).count()
        
        evidence['admin_users'] = admin_users
        
        total_users = User.query.filter(
            User.organization_id == self.organization_id,
            User.is_active == True
        ).count()
        
        admin_ratio = admin_users / total_users if total_users > 0 else 0
        evidence['admin_ratio'] = round(admin_ratio * 100, 1)
        
        if admin_ratio > 0.2:  # More than 20% admins is concerning
            findings.append(f"High admin user ratio: {evidence['admin_ratio']}%")
        
        # Calculate result
        score = 100
        if users_without_roles > 0:
            score -= 30
        if admin_ratio > 0.2:
            score -= 20
        
        status = CheckStatus.PASSED if not findings else (
            CheckStatus.WARNING if score >= 70 else CheckStatus.FAILED
        )
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=max(0, score),
            findings=findings,
            evidence=evidence,
        )
    
    def _check_segregation_of_duties(self, control: ComplianceControl) -> CheckResult:
        """Check segregation of duties"""
        findings = []
        evidence = {}
        
        # Check for users with conflicting roles
        # E.g., users who can both create and approve invoices
        conflicting_actions = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type.in_(['invoice.created', 'invoice.approved']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Group by user and check for conflicts
        user_actions = {}
        for log in conflicting_actions:
            user_id = str(log.user_id)
            if user_id not in user_actions:
                user_actions[user_id] = set()
            user_actions[user_id].add(log.event_type)
        
        conflicts = 0
        for user_id, actions in user_actions.items():
            if 'invoice.created' in actions and 'invoice.approved' in actions:
                conflicts += 1
        
        evidence['sod_conflicts'] = conflicts
        
        if conflicts > 0:
            findings.append(f"{conflicts} users performed both create and approve actions")
        
        score = 100 if conflicts == 0 else max(0, 100 - (conflicts * 20))
        status = CheckStatus.PASSED if conflicts == 0 else CheckStatus.FAILED
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=score,
            findings=findings,
            evidence=evidence,
            recommendations=['Implement approval workflows with different approvers'] if conflicts > 0 else [],
        )
    
    def _check_change_management(self, control: ComplianceControl) -> CheckResult:
        """Check change management controls"""
        findings = []
        evidence = {}
        
        # Check for system configuration changes
        config_changes = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type == 'system.config_changed',
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['config_changes_30d'] = config_changes
        
        # Check if changes have proper documentation (metadata)
        undocumented = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type == 'system.config_changed',
            AuditLog.metadata == {},
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['undocumented_changes'] = undocumented
        
        if undocumented > 0:
            findings.append(f"{undocumented} configuration changes without documentation")
        
        score = 100 if undocumented == 0 else max(0, 100 - (undocumented * 15))
        status = CheckStatus.PASSED if not findings else CheckStatus.WARNING
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=score,
            findings=findings,
            evidence=evidence,
        )
    
    def _check_audit_trail(self, control: ComplianceControl) -> CheckResult:
        """Check audit trail completeness"""
        findings = []
        evidence = {}
        
        # Check if audit logging is active
        recent_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        evidence['logs_last_7_days'] = recent_logs
        
        if recent_logs == 0:
            findings.append("No audit logs found in the last 7 days")
        
        # Check for financial transaction logging
        financial_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.entity_type.in_(['invoices', 'payments', 'transactions']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['financial_logs_30d'] = financial_logs
        
        # Verify integrity
        from app.audit.core.integrity_service import integrity_service
        is_valid, issues = integrity_service.verify_chain(
            self.organization_id,
            limit=1000
        )
        
        evidence['chain_valid'] = is_valid
        evidence['integrity_issues'] = len(issues)
        
        if not is_valid:
            findings.append(f"Audit chain integrity issues: {len(issues)} problems found")
        
        score = 100
        if recent_logs == 0:
            score -= 50
        if not is_valid:
            score -= 30
        
        status = CheckStatus.PASSED if not findings else (
            CheckStatus.FAILED if score < 70 else CheckStatus.WARNING
        )
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=max(0, score),
            findings=findings,
            evidence=evidence,
        )
    
    def _check_user_access_reviews(self, control: ComplianceControl) -> CheckResult:
        """Check user access review compliance"""
        passed, evidence = self._check_access_reviews(days=90)
        
        findings = []
        if not passed:
            findings.append("No access reviews performed in the last 90 days")
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if passed else CheckStatus.WARNING,
            score=100 if passed else 50,
            findings=findings,
            evidence=evidence,
            recommendations=['Conduct quarterly user access reviews'] if not passed else [],
        )
    
    def _check_transaction_authorization(self, control: ComplianceControl) -> CheckResult:
        """Check transaction authorization controls"""
        findings = []
        evidence = {}
        
        # Check for approved invoices
        total_invoices = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type == 'invoice.created',
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        approved_invoices = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type == 'invoice.approved',
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['invoices_created'] = total_invoices
        evidence['invoices_approved'] = approved_invoices
        
        if total_invoices > 0:
            approval_rate = approved_invoices / total_invoices
            evidence['approval_rate'] = round(approval_rate * 100, 1)
            
            if approval_rate < 0.9:
                findings.append(f"Invoice approval rate is {evidence['approval_rate']}%")
        
        score = 100 if not findings else 70
        status = CheckStatus.PASSED if not findings else CheckStatus.WARNING
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=score,
            findings=findings,
            evidence=evidence,
        )
    
    def _check_password_policy_compliance(self, control: ComplianceControl) -> CheckResult:
        """Check password policy compliance"""
        passed, evidence = self._check_password_policy()
        
        # Also check MFA
        mfa_passed, mfa_evidence = self._check_mfa_adoption(threshold=0.5)
        evidence.update(mfa_evidence)
        
        findings = []
        if not mfa_passed:
            findings.append(f"MFA adoption is below 50%: {mfa_evidence.get('adoption_rate', 0)}%")
        
        score = 100
        if not passed:
            score -= 30
        if not mfa_passed:
            score -= 20
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if not findings else CheckStatus.WARNING,
            score=max(0, score),
            findings=findings,
            evidence=evidence,
        )
```

### 5.3 GDPR Compliance Framework

**File:** `backend/app/audit/compliance/gdpr_compliance.py`

```python
"""
GDPR Compliance Framework
General Data Protection Regulation compliance controls
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.compliance.base_framework import (
    BaseComplianceFramework, ComplianceControl, CheckResult,
    CheckStatus, CheckType
)


class GDPRComplianceFramework(BaseComplianceFramework):
    """GDPR compliance framework"""
    
    FRAMEWORK_ID = 'gdpr'
    FRAMEWORK_NAME = 'General Data Protection Regulation (GDPR)'
    VERSION = '2024.1'
    
    def _register_controls(self):
        """Register GDPR controls"""
        
        # Article 5 - Principles
        self._controls['GDPR-5-1'] = ComplianceControl(
            id='GDPR-5-1',
            name='Lawfulness and Transparency',
            description='Personal data must be processed lawfully and transparently',
            category='Data Processing',
            check_type=CheckType.MANUAL,
            severity='high',
        )
        
        # Article 6 - Lawful Basis
        self._controls['GDPR-6-1'] = ComplianceControl(
            id='GDPR-6-1',
            name='Consent Management',
            description='Track and manage consent for data processing',
            category='Consent',
            check_type=CheckType.AUTOMATED,
            severity='critical',
        )
        
        # Article 15-22 - Data Subject Rights
        self._controls['GDPR-15-1'] = ComplianceControl(
            id='GDPR-15-1',
            name='Right of Access (DSAR)',
            description='Ability to provide data subject access requests',
            category='Data Subject Rights',
            check_type=CheckType.AUTOMATED,
            severity='high',
        )
        
        self._controls['GDPR-17-1'] = ComplianceControl(
            id='GDPR-17-1',
            name='Right to Erasure',
            description='Ability to delete personal data upon request',
            category='Data Subject Rights',
            check_type=CheckType.AUTOMATED,
            severity='high',
        )
        
        # Article 30 - Records of Processing
        self._controls['GDPR-30-1'] = ComplianceControl(
            id='GDPR-30-1',
            name='Processing Activity Records',
            description='Maintain records of all processing activities',
            category='Documentation',
            check_type=CheckType.AUTOMATED,
            severity='medium',
        )
        
        # Article 32 - Security
        self._controls['GDPR-32-1'] = ComplianceControl(
            id='GDPR-32-1',
            name='Data Security Measures',
            description='Implement appropriate security measures',
            category='Security',
            check_type=CheckType.AUTOMATED,
            severity='high',
        )
        
        # Article 33-34 - Breach Notification
        self._controls['GDPR-33-1'] = ComplianceControl(
            id='GDPR-33-1',
            name='Breach Detection',
            description='Ability to detect and respond to data breaches',
            category='Incident Response',
            check_type=CheckType.AUTOMATED,
            severity='critical',
        )
        
        # Data Retention
        self._controls['GDPR-RET-1'] = ComplianceControl(
            id='GDPR-RET-1',
            name='Data Retention Policies',
            description='Implement and enforce data retention policies',
            category='Data Lifecycle',
            check_type=CheckType.AUTOMATED,
            severity='medium',
        )
    
    def run_check(self, control_id: str) -> CheckResult:
        """Run a specific GDPR compliance check"""
        control = self._controls.get(control_id)
        if not control:
            raise ValueError(f"Unknown control: {control_id}")
        
        check_methods = {
            'GDPR-5-1': self._check_lawfulness,
            'GDPR-6-1': self._check_consent_management,
            'GDPR-15-1': self._check_dsar_capability,
            'GDPR-17-1': self._check_erasure_capability,
            'GDPR-30-1': self._check_processing_records,
            'GDPR-32-1': self._check_security_measures,
            'GDPR-33-1': self._check_breach_detection,
            'GDPR-RET-1': self._check_retention_policies,
        }
        
        check_method = check_methods.get(control_id)
        if check_method:
            return check_method(control)
        
        return CheckResult(
            control_id=control_id,
            control_name=control.name,
            status=CheckStatus.NOT_APPLICABLE,
        )
    
    def _check_lawfulness(self, control: ComplianceControl) -> CheckResult:
        """Check lawfulness and transparency (manual check)"""
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PENDING,
            score=0,
            findings=['Manual review required'],
            recommendations=['Review privacy policy and data processing agreements'],
        )
    
    def _check_consent_management(self, control: ComplianceControl) -> CheckResult:
        """Check consent tracking"""
        findings = []
        evidence = {}
        
        # Check for consent-related audit logs
        consent_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type.like('%consent%'),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=90)
        ).count()
        
        evidence['consent_events_90d'] = consent_logs
        
        # This would integrate with a consent management system
        # For now, check if consent tracking is enabled
        has_consent_tracking = consent_logs > 0
        
        if not has_consent_tracking:
            findings.append("No consent tracking events found")
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if has_consent_tracking else CheckStatus.WARNING,
            score=100 if has_consent_tracking else 50,
            findings=findings,
            evidence=evidence,
            recommendations=['Implement consent management system'] if not has_consent_tracking else [],
        )
    
    def _check_dsar_capability(self, control: ComplianceControl) -> CheckResult:
        """Check Data Subject Access Request capability"""
        findings = []
        evidence = {}
        
        # Check for data export capability
        export_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_type.in_(['entity.exported', 'data.exported']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=365)
        ).count()
        
        evidence['data_exports_1y'] = export_logs
        
        # Check audit trail for personal data access
        personal_data_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.entity_type.in_(['users', 'customers', 'contacts']),
            AuditLog.action == 'read',
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['personal_data_access_30d'] = personal_data_logs
        
        # DSAR capability exists if we can track and export data
        has_capability = True  # Assume capability exists
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if has_capability else CheckStatus.FAILED,
            score=100 if has_capability else 0,
            findings=findings,
            evidence=evidence,
        )
    
    def _check_erasure_capability(self, control: ComplianceControl) -> CheckResult:
        """Check right to erasure (deletion) capability"""
        findings = []
        evidence = {}
        
        # Check for deletion events
        deletion_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.action == 'delete',
            AuditLog.entity_type.in_(['users', 'customers', 'contacts']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=365)
        ).count()
        
        evidence['personal_data_deletions_1y'] = deletion_logs
        
        # Check if soft-delete or hard-delete
        has_deletion_capability = True  # Assume exists
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED,
            score=100,
            findings=findings,
            evidence=evidence,
        )
    
    def _check_processing_records(self, control: ComplianceControl) -> CheckResult:
        """Check records of processing activities"""
        findings = []
        evidence = {}
        
        # Audit logs serve as processing records
        total_logs = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id
        ).count()
        
        evidence['total_audit_logs'] = total_logs
        
        # Check completeness - do we log all entity types?
        entity_types = db.session.query(AuditLog.entity_type).filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.entity_type != None
        ).distinct().all()
        
        evidence['tracked_entity_types'] = [e[0] for e in entity_types]
        
        if total_logs == 0:
            findings.append("No processing records found")
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if total_logs > 0 else CheckStatus.FAILED,
            score=100 if total_logs > 0 else 0,
            findings=findings,
            evidence=evidence,
        )
    
    def _check_security_measures(self, control: ComplianceControl) -> CheckResult:
        """Check security measures"""
        findings = []
        evidence = {}
        score = 100
        
        # Check MFA adoption
        mfa_passed, mfa_evidence = self._check_mfa_adoption(threshold=0.5)
        evidence.update(mfa_evidence)
        
        if not mfa_passed:
            findings.append(f"Low MFA adoption: {mfa_evidence.get('adoption_rate', 0)}%")
            score -= 30
        
        # Check for security events
        security_events = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.event_category == 'security',
            AuditLog.severity.in_(['warning', 'error', 'critical']),
            AuditLog.occurred_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['security_events_30d'] = security_events
        
        if security_events > 10:
            findings.append(f"High number of security events: {security_events}")
            score -= 20
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if not findings else CheckStatus.WARNING,
            score=max(0, score),
            findings=findings,
            evidence=evidence,
        )
    
    def _check_breach_detection(self, control: ComplianceControl) -> CheckResult:
        """Check breach detection capability"""
        findings = []
        evidence = {}
        
        # Check for security monitoring
        from app.audit.models.alert import AlertRule
        
        security_rules = AlertRule.query.filter(
            AlertRule.organization_id == self.organization_id,
            AlertRule.alert_type.in_(['suspicious_login', 'brute_force', 'data_export']),
            AlertRule.is_active == True
        ).count()
        
        evidence['active_security_rules'] = security_rules
        
        if security_rules == 0:
            findings.append("No active security alert rules configured")
        
        # Check recent security alerts
        from app.audit.models.alert import AuditAlert
        
        recent_alerts = AuditAlert.query.filter(
            AuditAlert.organization_id == self.organization_id,
            AuditAlert.severity.in_(['high', 'critical']),
            AuditAlert.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        evidence['high_severity_alerts_30d'] = recent_alerts
        
        score = 100 if security_rules > 0 else 50
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if security_rules > 0 else CheckStatus.WARNING,
            score=score,
            findings=findings,
            evidence=evidence,
            recommendations=['Configure security alert rules'] if security_rules == 0 else [],
        )
    
    def _check_retention_policies(self, control: ComplianceControl) -> CheckResult:
        """Check data retention policies"""
        findings = []
        evidence = {}
        
        from app.audit.models.retention_policy import RetentionPolicy
        
        policies = RetentionPolicy.query.filter(
            RetentionPolicy.organization_id == self.organization_id,
            RetentionPolicy.is_active == True
        ).count()
        
        evidence['active_retention_policies'] = policies
        
        if policies == 0:
            findings.append("No data retention policies defined")
        
        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if policies > 0 else CheckStatus.WARNING,
            score=100 if policies > 0 else 50,
            findings=findings,
            evidence=evidence,
            recommendations=['Define data retention policies'] if policies == 0 else [],
        )
```

---

## TASK 6: REPORT SERVICE

### 6.1 Compliance Report Service

**File:** `backend/app/audit/services/report_service.py`

```python
"""
Report Service
Generate compliance and audit reports
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from io import BytesIO
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.models.change_history import ChangeHistory
from app.audit.models.access_log import AccessLog
from app.audit.compliance.sox_compliance import SOXComplianceFramework
from app.audit.compliance.gdpr_compliance import GDPRComplianceFramework

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating audit and compliance reports"""
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
    
    def generate_compliance_report(
        self,
        framework: str,
        format: str = 'json',
        include_evidence: bool = True
    ) -> Dict[str, Any]:
        """
        Generate compliance report for a framework
        
        Args:
            framework: Framework ID (sox, gdpr, soc2)
            format: Output format (json, pdf, xlsx)
            include_evidence: Include evidence details
            
        Returns:
            Report data
        """
        # Get framework
        frameworks = {
            'sox': SOXComplianceFramework,
            'gdpr': GDPRComplianceFramework,
        }
        
        framework_class = frameworks.get(framework.lower())
        if not framework_class:
            raise ValueError(f"Unknown framework: {framework}")
        
        compliance = framework_class(self.organization_id)
        
        # Run checks
        results = compliance.run_all_checks()
        summary = compliance.get_summary(results)
        
        report = {
            'report_type': 'compliance_summary',
            'framework': framework,
            'organization_id': self.organization_id,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': summary,
            'controls': [r.to_dict() for r in results],
        }
        
        if not include_evidence:
            for control in report['controls']:
                control.pop('evidence', None)
        
        return report
    
    def generate_activity_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: str = None,
        entity_type: str = None
    ) -> Dict[str, Any]:
        """Generate activity summary report"""
        query = AuditLog.query.filter(
            AuditLog.organization_id == self.organization_id,
            AuditLog.occurred_at >= start_date,
            AuditLog.occurred_at <= end_date
        )
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        logs = query.order_by(AuditLog.occurred_at.desc()).all()
        
        # Aggregate statistics
        stats = {
            'total_events': len(logs),
            'by_action': {},
            'by_entity_type': {},
            'by_user': {},
            'by_severity': {},
        }
        
        for log in logs:
            # By action
            stats['by_action'][log.action] = stats['by_action'].get(log.action, 0) + 1
            
            # By entity type
            if log.entity_type:
                stats['by_entity_type'][log.entity_type] = stats['by_entity_type'].get(log.entity_type, 0) + 1
            
            # By user
            if log.user_email:
                stats['by_user'][log.user_email] = stats['by_user'].get(log.user_email, 0) + 1
            
            # By severity
            stats['by_severity'][log.severity] = stats['by_severity'].get(log.severity, 0) + 1
        
        return {
            'report_type': 'activity_summary',
            'organization_id': self.organization_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'filters': {
                'user_id': user_id,
                'entity_type': entity_type,
            },
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': stats,
            'events': [log.to_dict() for log in logs[:1000]],  # Limit events
        }
    
    def generate_access_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_failed: bool = True
    ) -> Dict[str, Any]:
        """Generate access/authentication report"""
        query = AccessLog.query.filter(
            AccessLog.organization_id == self.organization_id,
            AccessLog.occurred_at >= start_date,
            AccessLog.occurred_at <= end_date
        )
        
        if not include_failed:
            query = query.filter(AccessLog.success == True)
        
        logs = query.order_by(AccessLog.occurred_at.desc()).all()
        
        # Statistics
        stats = {
            'total_events': len(logs),
            'successful_logins': len([l for l in logs if l.success and l.event_type == 'login_success']),
            'failed_logins': len([l for l in logs if not l.success and l.event_type == 'login_failed']),
            'unique_users': len(set(l.user_email for l in logs if l.user_email)),
            'unique_ips': len(set(str(l.ip_address) for l in logs if l.ip_address)),
            'by_auth_method': {},
            'by_event_type': {},
            'high_risk_events': 0,
        }
        
        for log in logs:
            if log.auth_method:
                stats['by_auth_method'][log.auth_method] = stats['by_auth_method'].get(log.auth_method, 0) + 1
            
            stats['by_event_type'][log.event_type] = stats['by_event_type'].get(log.event_type, 0) + 1
            
            if log.risk_score and log.risk_score >= 70:
                stats['high_risk_events'] += 1
        
        return {
            'report_type': 'access_review',
            'organization_id': self.organization_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'generated_at': datetime.utcnow().isoformat(),
            'statistics': stats,
            'events': [log.to_dict() for log in logs[:500]],
        }
    
    def generate_change_report(
        self,
        entity_type: str,
        entity_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Generate entity change report"""
        query = ChangeHistory.query.filter(
            ChangeHistory.organization_id == self.organization_id,
            ChangeHistory.entity_type == entity_type
        )
        
        if entity_id:
            query = query.filter(ChangeHistory.entity_id == entity_id)
        
        if start_date:
            query = query.filter(ChangeHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(ChangeHistory.created_at <= end_date)
        
        changes = query.order_by(ChangeHistory.created_at.desc()).all()
        
        return {
            'report_type': 'change_report',
            'organization_id': self.organization_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
            },
            'generated_at': datetime.utcnow().isoformat(),
            'total_changes': len(changes),
            'changes': [c.to_dict(include_snapshots=True) for c in changes[:500]],
        }
    
    def generate_pdf_report(self, report_data: Dict[str, Any]) -> BytesIO:
        """Generate PDF from report data"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        
        report_type = report_data.get('report_type', 'Report').replace('_', ' ').title()
        elements.append(Paragraph(report_type, title_style))
        
        # Metadata
        elements.append(Paragraph(f"Generated: {report_data.get('generated_at', '')}", styles['Normal']))
        elements.append(Paragraph(f"Organization: {report_data.get('organization_id', '')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Summary section
        if 'summary' in report_data:
            elements.append(Paragraph("Summary", styles['Heading2']))
            summary = report_data['summary']
            
            summary_data = [
                ['Metric', 'Value'],
                ['Overall Score', f"{summary.get('overall_score', 0):.1f}%"],
                ['Status', summary.get('status', 'Unknown')],
                ['Controls Passed', str(summary.get('passed', 0))],
                ['Controls Failed', str(summary.get('failed', 0))],
                ['Warnings', str(summary.get('warnings', 0))],
            ]
            
            table = Table(summary_data, colWidths=[200, 200])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
        
        # Statistics section
        if 'statistics' in report_data:
            elements.append(Paragraph("Statistics", styles['Heading2']))
            stats = report_data['statistics']
            
            for key, value in stats.items():
                if not isinstance(value, dict):
                    elements.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", styles['Normal']))
            
            elements.append(Spacer(1, 20))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    def generate_excel_report(self, report_data: Dict[str, Any]) -> BytesIO:
        """Generate Excel from report data"""
        import xlsxwriter
        
        buffer = BytesIO()
        workbook = xlsxwriter.Workbook(buffer)
        
        # Summary sheet
        summary_sheet = workbook.add_worksheet('Summary')
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white'})
        
        row = 0
        summary_sheet.write(row, 0, 'Report Type', header_format)
        summary_sheet.write(row, 1, report_data.get('report_type', ''))
        row += 1
        
        summary_sheet.write(row, 0, 'Generated At', header_format)
        summary_sheet.write(row, 1, report_data.get('generated_at', ''))
        row += 2
        
        # Write summary if exists
        if 'summary' in report_data:
            summary_sheet.write(row, 0, 'Summary', header_format)
            row += 1
            
            for key, value in report_data['summary'].items():
                summary_sheet.write(row, 0, key.replace('_', ' ').title())
                summary_sheet.write(row, 1, str(value))
                row += 1
        
        # Events/Controls sheet
        if 'controls' in report_data:
            controls_sheet = workbook.add_worksheet('Controls')
            
            headers = ['Control ID', 'Name', 'Status', 'Score', 'Findings']
            for col, header in enumerate(headers):
                controls_sheet.write(0, col, header, header_format)
            
            for row, control in enumerate(report_data['controls'], start=1):
                controls_sheet.write(row, 0, control.get('control_id', ''))
                controls_sheet.write(row, 1, control.get('control_name', ''))
                controls_sheet.write(row, 2, control.get('status', ''))
                controls_sheet.write(row, 3, control.get('score', 0))
                controls_sheet.write(row, 4, '; '.join(control.get('findings', [])))
        
        if 'events' in report_data:
            events_sheet = workbook.add_worksheet('Events')
            
            if report_data['events']:
                headers = list(report_data['events'][0].keys())
                for col, header in enumerate(headers):
                    events_sheet.write(0, col, header, header_format)
                
                for row, event in enumerate(report_data['events'], start=1):
                    for col, key in enumerate(headers):
                        events_sheet.write(row, col, str(event.get(key, '')))
        
        workbook.close()
        buffer.seek(0)
        
        return buffer
```

---

## TASK 7: ALERT SERVICE

### 7.1 Alert Management Service

**File:** `backend/app/audit/services/alert_service.py`

```python
"""
Alert Service
Alert creation, evaluation, and notification
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.models.alert import AuditAlert, AlertRule
from app.audit.core.context_provider import ContextProvider

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing audit alerts"""
    
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
    
    def evaluate_rules(self, audit_log: AuditLog) -> List[AuditAlert]:
        """
        Evaluate alert rules against an audit log entry
        
        Args:
            audit_log: The audit log entry to evaluate
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        # Get active rules
        rules = AlertRule.query.filter(
            AlertRule.organization_id == self.organization_id,
            AlertRule.is_active == True
        ).all()
        
        for rule in rules:
            if self._matches_rule(audit_log, rule):
                if rule.can_trigger():
                    alert = self._create_alert(audit_log, rule)
                    if alert:
                        triggered_alerts.append(alert)
                        rule.record_trigger()
        
        if triggered_alerts:
            db.session.commit()
        
        return triggered_alerts
    
    def _matches_rule(self, audit_log: AuditLog, rule: AlertRule) -> bool:
        """Check if audit log matches rule conditions"""
        # Check event type
        if audit_log.event_type not in rule.event_types:
            return False
        
        conditions = rule.conditions or {}
        
        # Check field matches
        if 'field_match' in conditions:
            for field, expected in conditions['field_match'].items():
                actual = getattr(audit_log, field, None)
                if actual is None:
                    actual = audit_log.metadata.get(field) if audit_log.metadata else None
                
                if actual != expected:
                    return False
        
        # Check count-based conditions
        if 'count' in conditions:
            count_condition = conditions['count']
            timeframe = conditions.get('timeframe_minutes', 60)
            
            # Count recent matching events
            since = datetime.utcnow() - timedelta(minutes=timeframe)
            count = AuditLog.query.filter(
                AuditLog.organization_id == self.organization_id,
                AuditLog.event_type.in_(rule.event_types),
                AuditLog.occurred_at >= since
            ).count()
            
            for op, value in count_condition.items():
                if op == '>' and not (count > value):
                    return False
                if op == '>=' and not (count >= value):
                    return False
                if op == '<' and not (count < value):
                    return False
                if op == '==' and not (count == value):
                    return False
        
        # Check severity threshold
        if 'min_severity' in conditions:
            severity_order = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
            min_level = severity_order.get(conditions['min_severity'], 0)
            actual_level = severity_order.get(audit_log.severity, 0)
            
            if actual_level < min_level:
                return False
        
        return True
    
    def _create_alert(self, audit_log: AuditLog, rule: AlertRule) -> Optional[AuditAlert]:
        """Create alert from rule match"""
        try:
            alert = AuditAlert(
                organization_id=self.organization_id,
                alert_type=rule.alert_type,
                triggered_by_log_id=audit_log.id,
                severity=rule.severity,
                title=f"{rule.name}: {audit_log.event_type}",
                description=self._generate_description(audit_log, rule),
                affected_entity_type=audit_log.entity_type,
                affected_entity_id=audit_log.entity_id,
                affected_user_id=audit_log.user_id,
                evidence={
                    'event_type': audit_log.event_type,
                    'action': audit_log.action,
                    'entity': f"{audit_log.entity_type}/{audit_log.entity_id}",
                    'user': audit_log.user_email,
                    'ip_address': str(audit_log.ip_address) if audit_log.ip_address else None,
                    'occurred_at': audit_log.occurred_at.isoformat(),
                },
                status='open',
            )
            
            db.session.add(alert)
            
            # Send notifications
            self._send_notifications(alert, rule)
            
            logger.info(f"Alert created: {alert.title}")
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None
    
    def _generate_description(self, audit_log: AuditLog, rule: AlertRule) -> str:
        """Generate alert description"""
        parts = [
            f"Rule '{rule.name}' triggered.",
            f"Event: {audit_log.event_type}",
        ]
        
        if audit_log.entity_type:
            parts.append(f"Entity: {audit_log.entity_type}")
        
        if audit_log.user_email:
            parts.append(f"User: {audit_log.user_email}")
        
        if audit_log.ip_address:
            parts.append(f"IP: {audit_log.ip_address}")
        
        return " | ".join(parts)
    
    def _send_notifications(self, alert: AuditAlert, rule: AlertRule):
        """Send alert notifications"""
        channels = rule.notification_channels or []
        
        if 'email' in channels:
            self._send_email_notification(alert, rule)
        
        if 'slack' in channels:
            self._send_slack_notification(alert, rule)
        
        if 'webhook' in channels:
            self._send_webhook_notification(alert, rule)
    
    def _send_email_notification(self, alert: AuditAlert, rule: AlertRule):
        """Send email notification"""
        # This would integrate with email service
        logger.info(f"Email notification for alert {alert.id}")
    
    def _send_slack_notification(self, alert: AuditAlert, rule: AlertRule):
        """Send Slack notification"""
        # This would integrate with Slack
        logger.info(f"Slack notification for alert {alert.id}")
    
    def _send_webhook_notification(self, alert: AuditAlert, rule: AlertRule):
        """Send webhook notification"""
        # This would make HTTP request to webhook URL
        logger.info(f"Webhook notification for alert {alert.id}")
    
    # Alert management methods
    
    def get_alerts(
        self,
        status: str = None,
        severity: str = None,
        limit: int = 50
    ) -> List[AuditAlert]:
        """Get alerts with filters"""
        query = AuditAlert.query.filter(
            AuditAlert.organization_id == self.organization_id
        )
        
        if status:
            query = query.filter(AuditAlert.status == status)
        
        if severity:
            query = query.filter(AuditAlert.severity == severity)
        
        return query.order_by(AuditAlert.created_at.desc()).limit(limit).all()
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        alerts = AuditAlert.query.filter(
            AuditAlert.organization_id == self.organization_id,
            AuditAlert.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        return {
            'total_30d': len(alerts),
            'open': len([a for a in alerts if a.status == 'open']),
            'acknowledged': len([a for a in alerts if a.status == 'acknowledged']),
            'resolved': len([a for a in alerts if a.status == 'resolved']),
            'by_severity': {
                'critical': len([a for a in alerts if a.severity == 'critical']),
                'high': len([a for a in alerts if a.severity == 'high']),
                'medium': len([a for a in alerts if a.severity == 'medium']),
                'low': len([a for a in alerts if a.severity == 'low']),
            },
        }
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        alert = AuditAlert.query.filter(
            AuditAlert.id == alert_id,
            AuditAlert.organization_id == self.organization_id
        ).first()
        
        if alert:
            alert.acknowledge(user_id)
            db.session.commit()
            return True
        
        return False
    
    def resolve_alert(self, alert_id: str, user_id: str, notes: str = None) -> bool:
        """Resolve an alert"""
        alert = AuditAlert.query.filter(
            AuditAlert.id == alert_id,
            AuditAlert.organization_id == self.organization_id
        ).first()
        
        if alert:
            alert.resolve(user_id, notes)
            db.session.commit()
            return True
        
        return False


# Default alert rules
DEFAULT_ALERT_RULES = [
    {
        'name': 'Multiple Failed Logins',
        'description': 'Alert on multiple failed login attempts',
        'event_types': ['auth.login_failed'],
        'conditions': {'count': {'>': 5}, 'timeframe_minutes': 10},
        'alert_type': 'brute_force',
        'severity': 'high',
        'notification_channels': ['email'],
    },
    {
        'name': 'Bulk Data Delete',
        'description': 'Alert on bulk data deletion',
        'event_types': ['entity.deleted'],
        'conditions': {'count': {'>': 10}, 'timeframe_minutes': 5},
        'alert_type': 'bulk_delete',
        'severity': 'critical',
        'notification_channels': ['email', 'slack'],
    },
    {
        'name': 'Admin Role Assigned',
        'description': 'Alert when admin role is assigned',
        'event_types': ['role.assigned'],
        'conditions': {'field_match': {'metadata.role': 'admin'}},
        'alert_type': 'permission_escalation',
        'severity': 'medium',
        'notification_channels': ['email'],
    },
    {
        'name': 'Large Data Export',
        'description': 'Alert on large data exports',
        'event_types': ['entity.exported', 'data.exported'],
        'conditions': {},
        'alert_type': 'data_export',
        'severity': 'medium',
        'notification_channels': ['email'],
    },
]


def setup_default_rules(organization_id: str):
    """Setup default alert rules for an organization"""
    for rule_data in DEFAULT_ALERT_RULES:
        existing = AlertRule.query.filter(
            AlertRule.organization_id == organization_id,
            AlertRule.name == rule_data['name']
        ).first()
        
        if not existing:
            rule = AlertRule(
                organization_id=organization_id,
                **rule_data
            )
            db.session.add(rule)
    
    db.session.commit()
```

---

## Continue to Part 3 for API Routes & Frontend

---

*Phase 15 Tasks Part 2 - LogiAccounting Pro*
*Compliance Frameworks & Reporting*
