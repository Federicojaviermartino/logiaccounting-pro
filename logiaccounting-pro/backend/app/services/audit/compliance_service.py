"""
Compliance Service
SOX, GDPR, SOC 2 compliance frameworks and checks
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

from app.models.audit_store import audit_db
from app.models.store import db

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
    severity: str = 'medium'
    remediation: str = None
    references: List[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Result of a compliance check"""
    control_id: str
    control_name: str
    status: CheckStatus
    score: float = 100.0
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

        applicable = [r for r in results if r.status != CheckStatus.NOT_APPLICABLE]
        if not applicable:
            return 100.0

        return sum(r.score for r in applicable) / len(applicable)

    def get_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        """Get compliance summary"""
        passed = len([r for r in results if r.status == CheckStatus.PASSED])
        failed = len([r for r in results if r.status == CheckStatus.FAILED])
        warnings = len([r for r in results if r.status == CheckStatus.WARNING])
        na = len([r for r in results if r.status == CheckStatus.NOT_APPLICABLE])
        errors = len([r for r in results if r.status == CheckStatus.ERROR])

        return {
            'framework_id': self.FRAMEWORK_ID,
            'framework_name': self.FRAMEWORK_NAME,
            'version': self.VERSION,
            'total_controls': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'not_applicable': na,
            'errors': errors,
            'overall_score': self.calculate_overall_score(results),
            'status': 'compliant' if failed == 0 and errors == 0 else 'non_compliant',
            'checked_at': datetime.utcnow().isoformat(),
        }

    # Helper methods for common checks

    def _check_audit_logging_enabled(self) -> Tuple[bool, Dict]:
        """Check if audit logging is capturing events"""
        since = (datetime.utcnow() - timedelta(days=7)).isoformat()
        recent_logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=1000)

        return len(recent_logs) > 0, {'recent_log_count': len(recent_logs)}

    def _check_access_reviews(self, days: int = 90) -> Tuple[bool, Dict]:
        """Check if access reviews are performed regularly"""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        reviews = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        access_events = [
            l for l in reviews
            if l.get("event_type") in ['role.assigned', 'role.removed', 'permission.granted', 'permission.revoked']
        ]

        return len(access_events) > 0, {'access_changes_count': len(access_events), 'period_days': days}

    def _check_mfa_adoption(self, threshold: float = 0.8) -> Tuple[bool, Dict]:
        """Check MFA adoption rate"""
        users = db.users.find_all()
        org_users = [u for u in users if u.get("organization_id") == self.organization_id and u.get("status") == "active"]

        total = len(org_users)
        mfa_enabled = len([u for u in org_users if u.get("mfa_enabled")])

        adoption_rate = mfa_enabled / total if total > 0 else 0
        passed = adoption_rate >= threshold

        return passed, {
            'total_users': total,
            'mfa_enabled_users': mfa_enabled,
            'adoption_rate': round(adoption_rate * 100, 1),
            'threshold': threshold * 100,
        }


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

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        # Check for error-level events
        error_events = [l for l in logs if l.get("severity") in ['error', 'critical']]
        evidence['error_events_30d'] = len(error_events)

        if len(error_events) > 0:
            findings.append(f"Found {len(error_events)} error/critical events in the last 30 days")

        score = 100 if len(error_events) == 0 else max(0, 100 - (len(error_events) * 5))
        status = CheckStatus.PASSED if len(error_events) == 0 else (
            CheckStatus.WARNING if len(error_events) < 10 else CheckStatus.FAILED
        )

        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=status,
            score=score,
            findings=findings,
            evidence=evidence,
            recommendations=['Review and address error events'] if findings else [],
        )

    def _check_access_control(self, control: ComplianceControl) -> CheckResult:
        """Check access control management"""
        findings = []
        evidence = {}

        users = db.users.find_all()
        org_users = [u for u in users if u.get("organization_id") == self.organization_id and u.get("status") == "active"]

        # Users without roles
        users_without_roles = [u for u in org_users if not u.get("role")]
        evidence['users_without_roles'] = len(users_without_roles)

        if users_without_roles:
            findings.append(f"{len(users_without_roles)} active users have no assigned role")

        # Admin ratio
        admin_users = [u for u in org_users if u.get("role") == "admin"]
        evidence['admin_users'] = len(admin_users)
        evidence['total_users'] = len(org_users)

        admin_ratio = len(admin_users) / len(org_users) if org_users else 0
        evidence['admin_ratio'] = round(admin_ratio * 100, 1)

        if admin_ratio > 0.2:
            findings.append(f"High admin user ratio: {evidence['admin_ratio']}%")

        score = 100
        if users_without_roles:
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

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        # Check for users who both create and approve
        create_events = [l for l in logs if l.get("event_type") in ['invoice.created', 'entity.created']]
        approve_events = [l for l in logs if l.get("event_type") in ['invoice.approved']]

        user_actions = {}
        for log in create_events + approve_events:
            user_id = log.get("user_id")
            if user_id:
                if user_id not in user_actions:
                    user_actions[user_id] = set()
                user_actions[user_id].add(log.get("event_type"))

        conflicts = 0
        for user_id, actions in user_actions.items():
            if any('created' in a for a in actions) and any('approved' in a for a in actions):
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

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        config_changes = [l for l in logs if l.get("event_type") == 'system.config_changed']
        evidence['config_changes_30d'] = len(config_changes)

        # Check for undocumented changes (no metadata)
        undocumented = [l for l in config_changes if not l.get("metadata")]
        evidence['undocumented_changes'] = len(undocumented)

        if undocumented:
            findings.append(f"{len(undocumented)} configuration changes without documentation")

        score = 100 if not undocumented else max(0, 100 - (len(undocumented) * 15))
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

        # Check recent logs
        passed, log_evidence = self._check_audit_logging_enabled()
        evidence.update(log_evidence)

        if not passed:
            findings.append("No audit logs found in the last 7 days")

        # Check financial transaction logging
        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        financial_logs = [l for l in logs if l.get("entity_type") in ['invoices', 'payments', 'transactions']]
        evidence['financial_logs_30d'] = len(financial_logs)

        # Verify integrity
        is_valid, issues = audit_db.audit_logs.verify_chain(self.organization_id)
        evidence['chain_valid'] = is_valid
        evidence['integrity_issues'] = len(issues)

        if not is_valid:
            findings.append(f"Audit chain integrity issues: {len(issues)} problems found")

        score = 100
        if not passed:
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

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        created = [l for l in logs if l.get("event_type") == 'invoice.created']
        approved = [l for l in logs if l.get("event_type") == 'invoice.approved']

        evidence['invoices_created'] = len(created)
        evidence['invoices_approved'] = len(approved)

        if created:
            approval_rate = len(approved) / len(created)
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
        findings = []
        evidence = {'policy_enforced': True}

        # Check MFA adoption
        mfa_passed, mfa_evidence = self._check_mfa_adoption(threshold=0.5)
        evidence.update(mfa_evidence)

        if not mfa_passed:
            findings.append(f"MFA adoption is below 50%: {mfa_evidence.get('adoption_rate', 0)}%")

        score = 100
        if not mfa_passed:
            score -= 30

        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if not findings else CheckStatus.WARNING,
            score=max(0, score),
            findings=findings,
            evidence=evidence,
        )


class GDPRComplianceFramework(BaseComplianceFramework):
    """GDPR compliance framework"""

    FRAMEWORK_ID = 'gdpr'
    FRAMEWORK_NAME = 'General Data Protection Regulation (GDPR)'
    VERSION = '2024.1'

    def _register_controls(self):
        """Register GDPR controls"""

        self._controls['GDPR-5-1'] = ComplianceControl(
            id='GDPR-5-1',
            name='Lawfulness and Transparency',
            description='Personal data must be processed lawfully and transparently',
            category='Data Processing',
            check_type=CheckType.MANUAL,
            severity='high',
        )

        self._controls['GDPR-6-1'] = ComplianceControl(
            id='GDPR-6-1',
            name='Consent Management',
            description='Track and manage consent for data processing',
            category='Consent',
            check_type=CheckType.AUTOMATED,
            severity='critical',
        )

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

        self._controls['GDPR-30-1'] = ComplianceControl(
            id='GDPR-30-1',
            name='Processing Activity Records',
            description='Maintain records of all processing activities',
            category='Documentation',
            check_type=CheckType.AUTOMATED,
            severity='medium',
        )

        self._controls['GDPR-32-1'] = ComplianceControl(
            id='GDPR-32-1',
            name='Data Security Measures',
            description='Implement appropriate security measures',
            category='Security',
            check_type=CheckType.AUTOMATED,
            severity='high',
        )

        self._controls['GDPR-33-1'] = ComplianceControl(
            id='GDPR-33-1',
            name='Breach Detection',
            description='Ability to detect and respond to data breaches',
            category='Incident Response',
            check_type=CheckType.AUTOMATED,
            severity='critical',
        )

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

        since = (datetime.utcnow() - timedelta(days=90)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        consent_logs = [l for l in logs if 'consent' in l.get("event_type", "").lower()]
        evidence['consent_events_90d'] = len(consent_logs)

        has_consent_tracking = len(consent_logs) > 0

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

        since = (datetime.utcnow() - timedelta(days=365)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        export_logs = [l for l in logs if l.get("event_type") in ['entity.exported', 'data.exported']]
        evidence['data_exports_1y'] = len(export_logs)

        personal_data_logs = [l for l in logs if l.get("entity_type") in ['users', 'customers', 'contacts'] and l.get("action") == 'read']
        evidence['personal_data_access_30d'] = len(personal_data_logs)

        has_capability = True

        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if has_capability else CheckStatus.FAILED,
            score=100 if has_capability else 0,
            findings=findings,
            evidence=evidence,
        )

    def _check_erasure_capability(self, control: ComplianceControl) -> CheckResult:
        """Check right to erasure capability"""
        findings = []
        evidence = {}

        since = (datetime.utcnow() - timedelta(days=365)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        deletion_logs = [l for l in logs if l.get("action") == 'delete' and l.get("entity_type") in ['users', 'customers', 'contacts']]
        evidence['personal_data_deletions_1y'] = len(deletion_logs)

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

        total_logs = audit_db.audit_logs.count({"organization_id": self.organization_id})
        evidence['total_audit_logs'] = total_logs

        logs = audit_db.audit_logs.find_all({"organization_id": self.organization_id}, limit=10000)
        entity_types = list(set(l.get("entity_type") for l in logs if l.get("entity_type")))
        evidence['tracked_entity_types'] = entity_types

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

        mfa_passed, mfa_evidence = self._check_mfa_adoption(threshold=0.5)
        evidence.update(mfa_evidence)

        if not mfa_passed:
            findings.append(f"Low MFA adoption: {mfa_evidence.get('adoption_rate', 0)}%")
            score -= 30

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        logs = audit_db.audit_logs.find_all({
            "organization_id": self.organization_id,
            "from_date": since
        }, limit=10000)

        security_events = [l for l in logs if l.get("event_category") == 'security' and l.get("severity") in ['warning', 'error', 'critical']]
        evidence['security_events_30d'] = len(security_events)

        if len(security_events) > 10:
            findings.append(f"High number of security events: {len(security_events)}")
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

        rules = audit_db.alert_rules.find_all({
            "organization_id": self.organization_id,
            "is_active": True
        })

        security_rules = [r for r in rules if r.get("alert_type") in ['suspicious_login', 'brute_force', 'data_export']]
        evidence['active_security_rules'] = len(security_rules)

        if len(security_rules) == 0:
            findings.append("No active security alert rules configured")

        alerts = audit_db.alerts.find_all({
            "organization_id": self.organization_id
        }, limit=1000)

        since = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_alerts = [a for a in alerts if a.get("created_at", "") >= since and a.get("severity") in ['high', 'critical']]
        evidence['high_severity_alerts_30d'] = len(recent_alerts)

        score = 100 if len(security_rules) > 0 else 50

        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if len(security_rules) > 0 else CheckStatus.WARNING,
            score=score,
            findings=findings,
            evidence=evidence,
            recommendations=['Configure security alert rules'] if len(security_rules) == 0 else [],
        )

    def _check_retention_policies(self, control: ComplianceControl) -> CheckResult:
        """Check data retention policies"""
        findings = []
        evidence = {}

        policies = audit_db.retention_policies.find_all({
            "organization_id": self.organization_id,
            "is_active": True
        })

        evidence['active_retention_policies'] = len(policies)

        if len(policies) == 0:
            findings.append("No data retention policies defined")

        return CheckResult(
            control_id=control.id,
            control_name=control.name,
            status=CheckStatus.PASSED if len(policies) > 0 else CheckStatus.WARNING,
            score=100 if len(policies) > 0 else 50,
            findings=findings,
            evidence=evidence,
            recommendations=['Define data retention policies'] if len(policies) == 0 else [],
        )


class ComplianceService:
    """Service for managing compliance checks"""

    FRAMEWORKS = {
        'sox': SOXComplianceFramework,
        'gdpr': GDPRComplianceFramework,
    }

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def get_available_frameworks(self) -> List[Dict]:
        """Get list of available frameworks"""
        return [
            {
                'id': 'sox',
                'name': 'Sarbanes-Oxley (SOX)',
                'description': 'US financial reporting and internal controls',
                'region': 'US',
            },
            {
                'id': 'gdpr',
                'name': 'General Data Protection Regulation (GDPR)',
                'description': 'EU data privacy and protection',
                'region': 'EU',
            },
            {
                'id': 'soc2',
                'name': 'SOC 2',
                'description': 'Service organization controls',
                'region': 'Global',
                'status': 'coming_soon',
            },
            {
                'id': 'hipaa',
                'name': 'HIPAA',
                'description': 'US healthcare data protection',
                'region': 'US',
                'status': 'coming_soon',
            },
            {
                'id': 'pci_dss',
                'name': 'PCI-DSS',
                'description': 'Payment card data security',
                'region': 'Global',
                'status': 'coming_soon',
            },
        ]

    def get_framework(self, framework_id: str) -> Optional[BaseComplianceFramework]:
        """Get framework instance"""
        framework_class = self.FRAMEWORKS.get(framework_id)
        if framework_class:
            return framework_class(self.organization_id)
        return None

    def run_framework_checks(self, framework_id: str) -> Dict:
        """Run all checks for a framework"""
        framework = self.get_framework(framework_id)
        if not framework:
            raise ValueError(f"Unknown framework: {framework_id}")

        results = framework.run_all_checks()
        summary = framework.get_summary(results)

        # Store results
        for result in results:
            audit_db.compliance_checks.create({
                "organization_id": self.organization_id,
                "framework": framework_id,
                "control_id": result.control_id,
                "control_name": result.control_name,
                "status": result.status.value,
                "score": result.score,
                "findings": result.findings,
                "evidence": result.evidence,
                "recommendations": result.recommendations,
            })

        return {
            'framework': framework_id,
            'summary': summary,
            'controls': [r.to_dict() for r in results]
        }

    def get_dashboard(self) -> Dict:
        """Get compliance dashboard data"""
        frameworks_status = {}

        for framework_id in self.FRAMEWORKS:
            framework = self.get_framework(framework_id)
            results = framework.run_all_checks()
            summary = framework.get_summary(results)
            frameworks_status[framework_id] = summary

        # Calculate overall score
        scores = [f['overall_score'] for f in frameworks_status.values()]
        overall_score = sum(scores) / len(scores) if scores else 0

        # Get alert stats
        alert_stats = audit_db.alerts.get_stats(self.organization_id)

        return {
            'overall_score': round(overall_score, 1),
            'frameworks': frameworks_status,
            'alerts': alert_stats,
        }
