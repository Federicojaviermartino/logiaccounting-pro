# LogiAccounting Pro - Phase 15 Tasks Part 3

## API ROUTES & FRONTEND COMPONENTS

---

## TASK 8: AUDIT API ROUTES

### 8.1 Audit Log Routes

**File:** `backend/app/audit/routes/audit.py`

```python
"""
Audit Routes
API endpoints for audit log access and management
"""

from flask import Blueprint, request, jsonify, g, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from io import BytesIO
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.models.change_history import ChangeHistory
from app.audit.services.audit_service import AuditService
from app.audit.core.integrity_service import integrity_service

logger = logging.getLogger(__name__)

audit_bp = Blueprint('audit', __name__, url_prefix='/api/v1/audit')


# ==================== Audit Logs ====================

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
def list_audit_logs():
    """List audit logs with filters"""
    organization_id = g.current_user.organization_id
    
    # Parse filters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    # Build query
    query = AuditLog.query.filter(
        AuditLog.organization_id == organization_id
    )
    
    # Apply filters
    if request.args.get('event_type'):
        query = query.filter(AuditLog.event_type == request.args.get('event_type'))
    
    if request.args.get('category'):
        query = query.filter(AuditLog.event_category == request.args.get('category'))
    
    if request.args.get('severity'):
        query = query.filter(AuditLog.severity == request.args.get('severity'))
    
    if request.args.get('user_id'):
        query = query.filter(AuditLog.user_id == request.args.get('user_id'))
    
    if request.args.get('entity_type'):
        query = query.filter(AuditLog.entity_type == request.args.get('entity_type'))
    
    if request.args.get('entity_id'):
        query = query.filter(AuditLog.entity_id == request.args.get('entity_id'))
    
    if request.args.get('action'):
        query = query.filter(AuditLog.action == request.args.get('action'))
    
    # Date range
    if request.args.get('from_date'):
        from_date = datetime.fromisoformat(request.args.get('from_date'))
        query = query.filter(AuditLog.occurred_at >= from_date)
    
    if request.args.get('to_date'):
        to_date = datetime.fromisoformat(request.args.get('to_date'))
        query = query.filter(AuditLog.occurred_at <= to_date)
    
    # Search
    if request.args.get('search'):
        search = f"%{request.args.get('search')}%"
        query = query.filter(
            db.or_(
                AuditLog.entity_name.ilike(search),
                AuditLog.user_email.ilike(search),
                AuditLog.event_type.ilike(search),
            )
        )
    
    # Order and paginate
    query = query.order_by(AuditLog.occurred_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })


@audit_bp.route('/logs/<log_id>', methods=['GET'])
@jwt_required()
def get_audit_log(log_id):
    """Get audit log details"""
    organization_id = g.current_user.organization_id
    
    log = AuditLog.query.filter(
        AuditLog.id == log_id,
        AuditLog.organization_id == organization_id
    ).first()
    
    if not log:
        return jsonify({'success': False, 'error': 'Log not found'}), 404
    
    # Include change history if available
    data = log.to_dict(include_changes=True)
    
    if log.change_history:
        data['change_history'] = log.change_history.to_dict(include_snapshots=True)
    
    return jsonify({
        'success': True,
        'log': data
    })


@audit_bp.route('/logs/entity/<entity_type>/<entity_id>', methods=['GET'])
@jwt_required()
def get_entity_audit_trail(entity_type, entity_id):
    """Get complete audit trail for an entity"""
    organization_id = g.current_user.organization_id
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    query = AuditLog.query.filter(
        AuditLog.organization_id == organization_id,
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.occurred_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'logs': [log.to_dict(include_changes=True) for log in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })


@audit_bp.route('/logs/user/<user_id>', methods=['GET'])
@jwt_required()
def get_user_activity(user_id):
    """Get activity for a specific user"""
    organization_id = g.current_user.organization_id
    
    # Verify user is in same organization
    from app.models.user import User
    user = User.query.filter(
        User.id == user_id,
        User.organization_id == organization_id
    ).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    query = AuditLog.query.filter(
        AuditLog.organization_id == organization_id,
        AuditLog.user_id == user_id
    ).order_by(AuditLog.occurred_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'user': {
            'id': str(user.id),
            'email': user.email,
            'name': user.full_name,
        },
        'logs': [log.to_dict() for log in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
        }
    })


@audit_bp.route('/logs/statistics', methods=['GET'])
@jwt_required()
def get_audit_statistics():
    """Get audit log statistics"""
    organization_id = g.current_user.organization_id
    
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    service = AuditService(organization_id)
    stats = service.get_statistics(since)
    
    return jsonify({
        'success': True,
        'period_days': days,
        'statistics': stats
    })


@audit_bp.route('/logs/export', methods=['POST'])
@jwt_required()
def export_audit_logs():
    """Export audit logs to file"""
    organization_id = g.current_user.organization_id
    user_id = get_jwt_identity()
    
    data = request.get_json()
    format = data.get('format', 'csv')  # csv, excel, json
    filters = data.get('filters', {})
    
    # Log the export action
    from app.audit.core.audit_logger import log_audit
    log_audit(
        event_type='entity.exported',
        action='export',
        entity_type='audit_logs',
        metadata={'format': format, 'filters': filters}
    )
    
    service = AuditService(organization_id)
    
    try:
        if format == 'csv':
            output = service.export_to_csv(filters)
            mimetype = 'text/csv'
            filename = f'audit_logs_{datetime.now().strftime("%Y%m%d")}.csv'
        elif format == 'excel':
            output = service.export_to_excel(filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'audit_logs_{datetime.now().strftime("%Y%m%d")}.xlsx'
        else:
            output = service.export_to_json(filters)
            mimetype = 'application/json'
            filename = f'audit_logs_{datetime.now().strftime("%Y%m%d")}.json'
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Change History ====================

@audit_bp.route('/changes/<entity_type>/<entity_id>', methods=['GET'])
@jwt_required()
def get_change_history(entity_type, entity_id):
    """Get change history for an entity"""
    organization_id = g.current_user.organization_id
    
    history = ChangeHistory.get_entity_history(entity_type, entity_id)
    
    # Filter by organization
    history = [h for h in history if str(h.organization_id) == str(organization_id)]
    
    return jsonify({
        'success': True,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'versions': [h.to_dict(include_snapshots=True) for h in history]
    })


@audit_bp.route('/changes/<entity_type>/<entity_id>/version/<int:version>', methods=['GET'])
@jwt_required()
def get_entity_version(entity_type, entity_id, version):
    """Get specific version of an entity"""
    organization_id = g.current_user.organization_id
    
    history = ChangeHistory.get_version(entity_type, entity_id, version)
    
    if not history or str(history.organization_id) != str(organization_id):
        return jsonify({'success': False, 'error': 'Version not found'}), 404
    
    return jsonify({
        'success': True,
        'version': history.to_dict(include_snapshots=True)
    })


@audit_bp.route('/changes/<entity_type>/<entity_id>/diff', methods=['GET'])
@jwt_required()
def get_version_diff(entity_type, entity_id):
    """Compare two versions"""
    organization_id = g.current_user.organization_id
    
    v1 = request.args.get('v1', type=int)
    v2 = request.args.get('v2', type=int)
    
    if not v1 or not v2:
        return jsonify({'success': False, 'error': 'v1 and v2 required'}), 400
    
    version1 = ChangeHistory.get_version(entity_type, entity_id, v1)
    version2 = ChangeHistory.get_version(entity_type, entity_id, v2)
    
    if not version1 or not version2:
        return jsonify({'success': False, 'error': 'Version not found'}), 404
    
    # Calculate diff
    diff = {}
    snapshot1 = version1.after_snapshot or {}
    snapshot2 = version2.after_snapshot or {}
    
    all_keys = set(snapshot1.keys()) | set(snapshot2.keys())
    for key in all_keys:
        val1 = snapshot1.get(key)
        val2 = snapshot2.get(key)
        if val1 != val2:
            diff[key] = {'v1': val1, 'v2': val2}
    
    return jsonify({
        'success': True,
        'v1': v1,
        'v2': v2,
        'diff': diff
    })


# ==================== Integrity ====================

@audit_bp.route('/integrity/status', methods=['GET'])
@jwt_required()
def get_integrity_status():
    """Get hash chain integrity status"""
    organization_id = g.current_user.organization_id
    
    status = integrity_service.get_chain_status(organization_id)
    
    return jsonify({
        'success': True,
        'status': status
    })


@audit_bp.route('/integrity/verify', methods=['POST'])
@jwt_required()
def verify_integrity():
    """Verify audit log integrity"""
    organization_id = g.current_user.organization_id
    
    data = request.get_json() or {}
    start_sequence = data.get('start_sequence')
    end_sequence = data.get('end_sequence')
    
    is_valid, issues = integrity_service.verify_chain(
        organization_id,
        start_sequence=start_sequence,
        end_sequence=end_sequence
    )
    
    return jsonify({
        'success': True,
        'is_valid': is_valid,
        'issues_count': len(issues),
        'issues': issues[:100] if issues else []  # Limit issues returned
    })
```

### 8.2 Compliance Routes

**File:** `backend/app/audit/routes/compliance.py`

```python
"""
Compliance Routes
API endpoints for compliance management
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from app.extensions import db
from app.audit.models.alert import AuditAlert, AlertRule
from app.audit.compliance.sox_compliance import SOXComplianceFramework
from app.audit.compliance.gdpr_compliance import GDPRComplianceFramework
from app.audit.services.report_service import ReportService
from app.audit.services.alert_service import AlertService

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/v1/compliance')


# ==================== Dashboard ====================

@compliance_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_compliance_dashboard():
    """Get compliance dashboard data"""
    organization_id = g.current_user.organization_id
    
    # Get compliance status for each framework
    frameworks_status = {}
    
    for framework_id, framework_class in [
        ('sox', SOXComplianceFramework),
        ('gdpr', GDPRComplianceFramework),
    ]:
        framework = framework_class(str(organization_id))
        results = framework.run_all_checks()
        summary = framework.get_summary(results)
        frameworks_status[framework_id] = summary
    
    # Get alert stats
    alert_service = AlertService(str(organization_id))
    alert_stats = alert_service.get_alert_stats()
    
    # Calculate overall compliance score
    scores = [f['overall_score'] for f in frameworks_status.values() if f.get('overall_score')]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    return jsonify({
        'success': True,
        'dashboard': {
            'overall_score': round(overall_score, 1),
            'frameworks': frameworks_status,
            'alerts': alert_stats,
        }
    })


# ==================== Frameworks ====================

@compliance_bp.route('/frameworks', methods=['GET'])
@jwt_required()
def list_frameworks():
    """List available compliance frameworks"""
    frameworks = [
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
            'id': 'hipaa',
            'name': 'Health Insurance Portability and Accountability Act',
            'description': 'US healthcare data protection',
            'region': 'US',
            'status': 'coming_soon',
        },
        {
            'id': 'pci_dss',
            'name': 'Payment Card Industry Data Security Standard',
            'description': 'Payment card data security',
            'region': 'Global',
            'status': 'coming_soon',
        },
    ]
    
    return jsonify({
        'success': True,
        'frameworks': frameworks
    })


@compliance_bp.route('/frameworks/<framework_id>', methods=['GET'])
@jwt_required()
def get_framework_status(framework_id):
    """Get compliance status for a framework"""
    organization_id = g.current_user.organization_id
    
    framework_classes = {
        'sox': SOXComplianceFramework,
        'gdpr': GDPRComplianceFramework,
    }
    
    framework_class = framework_classes.get(framework_id)
    if not framework_class:
        return jsonify({'success': False, 'error': 'Framework not found'}), 404
    
    framework = framework_class(str(organization_id))
    results = framework.run_all_checks()
    summary = framework.get_summary(results)
    
    return jsonify({
        'success': True,
        'framework': framework_id,
        'summary': summary,
        'controls': [r.to_dict() for r in results]
    })


@compliance_bp.route('/frameworks/<framework_id>/run', methods=['POST'])
@jwt_required()
def run_compliance_checks(framework_id):
    """Run compliance checks for a framework"""
    organization_id = g.current_user.organization_id
    user_id = get_jwt_identity()
    
    framework_classes = {
        'sox': SOXComplianceFramework,
        'gdpr': GDPRComplianceFramework,
    }
    
    framework_class = framework_classes.get(framework_id)
    if not framework_class:
        return jsonify({'success': False, 'error': 'Framework not found'}), 404
    
    framework = framework_class(str(organization_id))
    
    # Log the compliance check
    from app.audit.core.audit_logger import log_audit
    log_audit(
        event_type='compliance.check_run',
        action='execute',
        entity_type='compliance_framework',
        entity_name=framework_id,
        metadata={'framework': framework_id}
    )
    
    results = framework.run_all_checks()
    summary = framework.get_summary(results)
    
    return jsonify({
        'success': True,
        'framework': framework_id,
        'run_at': datetime.utcnow().isoformat(),
        'run_by': user_id,
        'summary': summary,
        'controls': [r.to_dict() for r in results]
    })


# ==================== Reports ====================

@compliance_bp.route('/reports', methods=['GET'])
@jwt_required()
def list_reports():
    """List available report types"""
    reports = [
        {
            'id': 'compliance_summary',
            'name': 'Compliance Summary',
            'description': 'Overview of compliance status across frameworks',
        },
        {
            'id': 'activity_summary',
            'name': 'Activity Summary',
            'description': 'Summary of system activity',
        },
        {
            'id': 'access_review',
            'name': 'Access Review',
            'description': 'Authentication and access events',
        },
        {
            'id': 'change_report',
            'name': 'Change Report',
            'description': 'Entity changes over time',
        },
    ]
    
    return jsonify({
        'success': True,
        'reports': reports
    })


@compliance_bp.route('/reports/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """Generate a compliance report"""
    organization_id = g.current_user.organization_id
    
    data = request.get_json()
    report_type = data.get('report_type')
    parameters = data.get('parameters', {})
    output_format = data.get('format', 'json')
    
    if not report_type:
        return jsonify({'success': False, 'error': 'report_type required'}), 400
    
    service = ReportService(str(organization_id))
    
    try:
        if report_type == 'compliance_summary':
            framework = parameters.get('framework', 'sox')
            report_data = service.generate_compliance_report(
                framework=framework,
                include_evidence=parameters.get('include_evidence', True)
            )
        
        elif report_type == 'activity_summary':
            start_date = datetime.fromisoformat(parameters.get('start_date', (datetime.utcnow() - timedelta(days=30)).isoformat()))
            end_date = datetime.fromisoformat(parameters.get('end_date', datetime.utcnow().isoformat()))
            report_data = service.generate_activity_report(
                start_date=start_date,
                end_date=end_date,
                user_id=parameters.get('user_id'),
                entity_type=parameters.get('entity_type')
            )
        
        elif report_type == 'access_review':
            start_date = datetime.fromisoformat(parameters.get('start_date', (datetime.utcnow() - timedelta(days=30)).isoformat()))
            end_date = datetime.fromisoformat(parameters.get('end_date', datetime.utcnow().isoformat()))
            report_data = service.generate_access_report(
                start_date=start_date,
                end_date=end_date,
                include_failed=parameters.get('include_failed', True)
            )
        
        else:
            return jsonify({'success': False, 'error': 'Unknown report type'}), 400
        
        # Generate file if requested
        if output_format == 'pdf':
            output = service.generate_pdf_report(report_data)
            from flask import send_file
            return send_file(
                output,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{report_type}_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
        
        elif output_format == 'excel':
            output = service.generate_excel_report(report_data)
            from flask import send_file
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{report_type}_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
        
        return jsonify({
            'success': True,
            'report': report_data
        })
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Alerts ====================

@compliance_bp.route('/alerts', methods=['GET'])
@jwt_required()
def list_alerts():
    """List compliance alerts"""
    organization_id = g.current_user.organization_id
    
    status = request.args.get('status')
    severity = request.args.get('severity')
    limit = request.args.get('limit', 50, type=int)
    
    service = AlertService(str(organization_id))
    alerts = service.get_alerts(status=status, severity=severity, limit=limit)
    
    return jsonify({
        'success': True,
        'alerts': [a.to_dict() for a in alerts]
    })


@compliance_bp.route('/alerts/<alert_id>', methods=['GET'])
@jwt_required()
def get_alert(alert_id):
    """Get alert details"""
    organization_id = g.current_user.organization_id
    
    alert = AuditAlert.query.filter(
        AuditAlert.id == alert_id,
        AuditAlert.organization_id == organization_id
    ).first()
    
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    return jsonify({
        'success': True,
        'alert': alert.to_dict()
    })


@compliance_bp.route('/alerts/<alert_id>/acknowledge', methods=['PUT'])
@jwt_required()
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    organization_id = g.current_user.organization_id
    user_id = get_jwt_identity()
    
    service = AlertService(str(organization_id))
    success = service.acknowledge_alert(alert_id, user_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    return jsonify({'success': True, 'message': 'Alert acknowledged'})


@compliance_bp.route('/alerts/<alert_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alert(alert_id):
    """Resolve an alert"""
    organization_id = g.current_user.organization_id
    user_id = get_jwt_identity()
    
    data = request.get_json() or {}
    notes = data.get('notes')
    
    service = AlertService(str(organization_id))
    success = service.resolve_alert(alert_id, user_id, notes)
    
    if not success:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    return jsonify({'success': True, 'message': 'Alert resolved'})


# ==================== Alert Rules ====================

@compliance_bp.route('/alert-rules', methods=['GET'])
@jwt_required()
def list_alert_rules():
    """List alert rules"""
    organization_id = g.current_user.organization_id
    
    rules = AlertRule.query.filter(
        AlertRule.organization_id == organization_id
    ).all()
    
    return jsonify({
        'success': True,
        'rules': [r.to_dict() for r in rules]
    })


@compliance_bp.route('/alert-rules', methods=['POST'])
@jwt_required()
def create_alert_rule():
    """Create alert rule"""
    organization_id = g.current_user.organization_id
    
    data = request.get_json()
    
    rule = AlertRule(
        organization_id=organization_id,
        name=data.get('name'),
        description=data.get('description'),
        event_types=data.get('event_types', []),
        conditions=data.get('conditions', {}),
        alert_type=data.get('alert_type'),
        severity=data.get('severity', 'medium'),
        notify_roles=data.get('notify_roles'),
        notification_channels=data.get('notification_channels', ['email']),
        cooldown_minutes=data.get('cooldown_minutes', 60),
        is_active=data.get('is_active', True),
    )
    
    db.session.add(rule)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rule': rule.to_dict()
    }), 201


@compliance_bp.route('/alert-rules/<rule_id>', methods=['PUT'])
@jwt_required()
def update_alert_rule(rule_id):
    """Update alert rule"""
    organization_id = g.current_user.organization_id
    
    rule = AlertRule.query.filter(
        AlertRule.id == rule_id,
        AlertRule.organization_id == organization_id
    ).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        rule.name = data['name']
    if 'description' in data:
        rule.description = data['description']
    if 'event_types' in data:
        rule.event_types = data['event_types']
    if 'conditions' in data:
        rule.conditions = data['conditions']
    if 'severity' in data:
        rule.severity = data['severity']
    if 'is_active' in data:
        rule.is_active = data['is_active']
    if 'cooldown_minutes' in data:
        rule.cooldown_minutes = data['cooldown_minutes']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rule': rule.to_dict()
    })


@compliance_bp.route('/alert-rules/<rule_id>', methods=['DELETE'])
@jwt_required()
def delete_alert_rule(rule_id):
    """Delete alert rule"""
    organization_id = g.current_user.organization_id
    
    rule = AlertRule.query.filter(
        AlertRule.id == rule_id,
        AlertRule.organization_id == organization_id
    ).first()
    
    if not rule:
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    
    db.session.delete(rule)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Rule deleted'})
```

---

## TASK 9: FRONTEND COMPONENTS

### 9.1 Audit Logs Page

**File:** `frontend/src/features/audit/pages/AuditLogsPage.jsx`

```jsx
/**
 * Audit Logs Page
 * Browse and search audit trail
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuditLogs } from '../hooks/useAuditLogs';
import AuditLogTable from '../components/AuditLogTable';
import AuditFilters from '../components/AuditFilters';
import AuditLogDetail from '../components/AuditLogDetail';

const AuditLogsPage = () => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState({});
  const [selectedLog, setSelectedLog] = useState(null);
  
  const {
    logs,
    pagination,
    isLoading,
    page,
    setPage,
    exportLogs,
    isExporting,
  } = useAuditLogs(filters);
  
  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };
  
  const handleExport = async (format) => {
    await exportLogs(format);
  };
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('audit.title', 'Audit Logs')}
          </h1>
          <p className="text-gray-600 mt-1">
            {t('audit.description', 'View and search system activity history')}
          </p>
        </div>
        
        {/* Export Button */}
        <div className="relative group">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {t('common.export', 'Export')}
          </button>
          
          <div className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg border border-gray-200 hidden group-hover:block z-10">
            <button
              onClick={() => handleExport('csv')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
            >
              Export as CSV
            </button>
            <button
              onClick={() => handleExport('excel')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
            >
              Export as Excel
            </button>
            <button
              onClick={() => handleExport('json')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
            >
              Export as JSON
            </button>
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <AuditFilters
        filters={filters}
        onChange={handleFilterChange}
      />
      
      {/* Results */}
      <div className="bg-white rounded-lg border border-gray-200">
        <AuditLogTable
          logs={logs}
          isLoading={isLoading}
          onSelect={setSelectedLog}
        />
        
        {/* Pagination */}
        {pagination && pagination.pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {((page - 1) * pagination.per_page) + 1} to {Math.min(page * pagination.per_page, pagination.total)} of {pagination.total}
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              
              <span className="px-3 py-1">
                Page {page} of {pagination.pages}
              </span>
              
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= pagination.pages}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Detail Modal */}
      {selectedLog && (
        <AuditLogDetail
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
};

export default AuditLogsPage;
```

### 9.2 Audit Log Table Component

**File:** `frontend/src/features/audit/components/AuditLogTable.jsx`

```jsx
/**
 * Audit Log Table Component
 */

import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const SEVERITY_COLORS = {
  debug: 'bg-gray-100 text-gray-700',
  info: 'bg-blue-100 text-blue-700',
  warning: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
  critical: 'bg-red-200 text-red-800',
};

const ACTION_COLORS = {
  create: 'text-green-600',
  read: 'text-blue-600',
  update: 'text-yellow-600',
  delete: 'text-red-600',
  export: 'text-purple-600',
};

const AuditLogTable = ({ logs, isLoading, onSelect }) => {
  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mx-auto" />
      </div>
    );
  }
  
  if (!logs || logs.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No audit logs found
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Event
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Action
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Entity
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              User
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Severity
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              IP
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {logs.map((log) => (
            <tr
              key={log.id}
              onClick={() => onSelect(log)}
              className="hover:bg-gray-50 cursor-pointer"
            >
              <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                <div>{new Date(log.occurred_at).toLocaleString()}</div>
                <div className="text-xs text-gray-400">
                  {formatDistanceToNow(new Date(log.occurred_at), { addSuffix: true })}
                </div>
              </td>
              
              <td className="px-4 py-3 text-sm">
                <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                  {log.event_type}
                </code>
              </td>
              
              <td className="px-4 py-3 text-sm">
                <span className={`font-medium ${ACTION_COLORS[log.action] || 'text-gray-600'}`}>
                  {log.action}
                </span>
              </td>
              
              <td className="px-4 py-3 text-sm">
                {log.entity_type && (
                  <div>
                    <div className="text-gray-900">{log.entity_name || log.entity_type}</div>
                    <div className="text-xs text-gray-400">{log.entity_type}</div>
                  </div>
                )}
              </td>
              
              <td className="px-4 py-3 text-sm">
                <div className="text-gray-900">{log.user_email || 'System'}</div>
                {log.user_role && (
                  <div className="text-xs text-gray-400">{log.user_role}</div>
                )}
              </td>
              
              <td className="px-4 py-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${SEVERITY_COLORS[log.severity]}`}>
                  {log.severity}
                </span>
              </td>
              
              <td className="px-4 py-3 text-sm text-gray-600">
                {log.ip_address}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AuditLogTable;
```

### 9.3 Compliance Dashboard Page

**File:** `frontend/src/features/audit/pages/CompliancePage.jsx`

```jsx
/**
 * Compliance Dashboard Page
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useCompliance } from '../hooks/useCompliance';
import ComplianceStatus from '../components/ComplianceStatus';
import ControlStatus from '../components/ControlStatus';
import AlertList from '../components/AlertList';

const CompliancePage = () => {
  const { t } = useTranslation();
  const [selectedFramework, setSelectedFramework] = useState('sox');
  
  const {
    dashboard,
    frameworks,
    frameworkDetails,
    alerts,
    isLoading,
    runChecks,
    isRunningChecks,
  } = useCompliance(selectedFramework);
  
  const handleRunChecks = async () => {
    await runChecks(selectedFramework);
  };
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('compliance.title', 'Compliance Dashboard')}
          </h1>
          <p className="text-gray-600 mt-1">
            {t('compliance.description', 'Monitor compliance status across frameworks')}
          </p>
        </div>
        
        <button
          onClick={handleRunChecks}
          disabled={isRunningChecks}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isRunningChecks ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              Running...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Run Checks
            </>
          )}
        </button>
      </div>
      
      {/* Overall Score */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500 mb-1">Overall Score</div>
            <div className="text-3xl font-bold text-blue-600">
              {dashboard.overall_score?.toFixed(1)}%
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500 mb-1">Open Alerts</div>
            <div className="text-3xl font-bold text-red-600">
              {dashboard.alerts?.open || 0}
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500 mb-1">Critical Alerts</div>
            <div className="text-3xl font-bold text-red-800">
              {dashboard.alerts?.by_severity?.critical || 0}
            </div>
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500 mb-1">Resolved (30d)</div>
            <div className="text-3xl font-bold text-green-600">
              {dashboard.alerts?.resolved || 0}
            </div>
          </div>
        </div>
      )}
      
      {/* Framework Tabs */}
      <div className="flex gap-2 mb-6">
        {frameworks?.map((fw) => (
          <button
            key={fw.id}
            onClick={() => setSelectedFramework(fw.id)}
            disabled={fw.status === 'coming_soon'}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${selectedFramework === fw.id
                ? 'bg-blue-600 text-white'
                : fw.status === 'coming_soon'
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {fw.name}
            {fw.status === 'coming_soon' && ' (Coming Soon)'}
          </button>
        ))}
      </div>
      
      {/* Framework Status */}
      {frameworkDetails && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Summary Card */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Framework Summary</h2>
            <ComplianceStatus summary={frameworkDetails.summary} />
          </div>
          
          {/* Controls */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Controls</h2>
            <ControlStatus controls={frameworkDetails.controls} />
          </div>
        </div>
      )}
      
      {/* Alerts */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Alerts</h2>
        <AlertList alerts={alerts} />
      </div>
    </div>
  );
};

export default CompliancePage;
```

### 9.4 Compliance Status Component

**File:** `frontend/src/features/audit/components/ComplianceStatus.jsx`

```jsx
/**
 * Compliance Status Component
 */

import React from 'react';

const ComplianceStatus = ({ summary }) => {
  if (!summary) return null;
  
  const getStatusColor = (status) => {
    if (status === 'compliant') return 'text-green-600';
    if (status === 'non_compliant') return 'text-red-600';
    return 'text-yellow-600';
  };
  
  const getScoreColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  return (
    <div className="space-y-4">
      {/* Score */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Compliance Score</span>
          <span className="text-lg font-bold">{summary.overall_score?.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${getScoreColor(summary.overall_score)}`}
            style={{ width: `${summary.overall_score}%` }}
          />
        </div>
      </div>
      
      {/* Status */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">Status</span>
        <span className={`font-medium capitalize ${getStatusColor(summary.status)}`}>
          {summary.status?.replace('_', ' ')}
        </span>
      </div>
      
      {/* Control Counts */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{summary.passed || 0}</div>
          <div className="text-xs text-gray-500">Passed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{summary.failed || 0}</div>
          <div className="text-xs text-gray-500">Failed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{summary.warnings || 0}</div>
          <div className="text-xs text-gray-500">Warnings</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">{summary.not_applicable || 0}</div>
          <div className="text-xs text-gray-500">N/A</div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceStatus;
```

### 9.5 Audit Hooks

**File:** `frontend/src/features/audit/hooks/useAuditLogs.js`

```javascript
/**
 * useAuditLogs Hook
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { auditApi } from '../api/auditApi';
import { toast } from 'react-hot-toast';

export const useAuditLogs = (filters = {}) => {
  const [page, setPage] = useState(1);
  const perPage = 50;
  
  const {
    data,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['audit-logs', filters, page],
    queryFn: () => auditApi.getLogs({ ...filters, page, per_page: perPage }),
  });
  
  const exportMutation = useMutation({
    mutationFn: ({ format }) => auditApi.exportLogs(format, filters),
    onSuccess: () => {
      toast.success('Export started');
    },
    onError: (error) => {
      toast.error(error.message || 'Export failed');
    },
  });
  
  const exportLogs = useCallback((format) => {
    return exportMutation.mutateAsync({ format });
  }, [exportMutation]);
  
  return {
    logs: data?.logs || [],
    pagination: data?.pagination,
    isLoading,
    page,
    setPage,
    refetch,
    exportLogs,
    isExporting: exportMutation.isPending,
  };
};

export default useAuditLogs;
```

**File:** `frontend/src/features/audit/hooks/useCompliance.js`

```javascript
/**
 * useCompliance Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { auditApi } from '../api/auditApi';
import { toast } from 'react-hot-toast';

export const useCompliance = (frameworkId = 'sox') => {
  const queryClient = useQueryClient();
  
  // Dashboard
  const {
    data: dashboard,
    isLoading: isLoadingDashboard,
  } = useQuery({
    queryKey: ['compliance-dashboard'],
    queryFn: () => auditApi.getComplianceDashboard(),
  });
  
  // Frameworks list
  const {
    data: frameworksData,
  } = useQuery({
    queryKey: ['compliance-frameworks'],
    queryFn: () => auditApi.getFrameworks(),
  });
  
  // Framework details
  const {
    data: frameworkDetails,
    isLoading: isLoadingDetails,
  } = useQuery({
    queryKey: ['compliance-framework', frameworkId],
    queryFn: () => auditApi.getFrameworkStatus(frameworkId),
    enabled: !!frameworkId,
  });
  
  // Alerts
  const {
    data: alertsData,
  } = useQuery({
    queryKey: ['compliance-alerts'],
    queryFn: () => auditApi.getAlerts({ status: 'open', limit: 10 }),
  });
  
  // Run checks mutation
  const runChecksMutation = useMutation({
    mutationFn: (framework) => auditApi.runComplianceChecks(framework),
    onSuccess: () => {
      queryClient.invalidateQueries(['compliance-dashboard']);
      queryClient.invalidateQueries(['compliance-framework']);
      toast.success('Compliance checks completed');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to run checks');
    },
  });
  
  return {
    dashboard: dashboard?.dashboard,
    frameworks: frameworksData?.frameworks || [],
    frameworkDetails,
    alerts: alertsData?.alerts || [],
    isLoading: isLoadingDashboard || isLoadingDetails,
    runChecks: runChecksMutation.mutateAsync,
    isRunningChecks: runChecksMutation.isPending,
  };
};

export default useCompliance;
```

### 9.6 Audit API Service

**File:** `frontend/src/features/audit/api/auditApi.js`

```javascript
/**
 * Audit API Service
 */

import api from '../../../services/api';

export const auditApi = {
  // Audit Logs
  async getLogs(params = {}) {
    const response = await api.get('/audit/logs', { params });
    return response.data;
  },
  
  async getLog(id) {
    const response = await api.get(`/audit/logs/${id}`);
    return response.data.log;
  },
  
  async getEntityAuditTrail(entityType, entityId, params = {}) {
    const response = await api.get(`/audit/logs/entity/${entityType}/${entityId}`, { params });
    return response.data;
  },
  
  async getUserActivity(userId, params = {}) {
    const response = await api.get(`/audit/logs/user/${userId}`, { params });
    return response.data;
  },
  
  async getStatistics(days = 30) {
    const response = await api.get('/audit/logs/statistics', { params: { days } });
    return response.data;
  },
  
  async exportLogs(format, filters = {}) {
    const response = await api.post('/audit/logs/export', { format, filters }, {
      responseType: 'blob',
    });
    
    // Trigger download
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
  },
  
  // Change History
  async getChangeHistory(entityType, entityId) {
    const response = await api.get(`/audit/changes/${entityType}/${entityId}`);
    return response.data;
  },
  
  async getVersionDiff(entityType, entityId, v1, v2) {
    const response = await api.get(`/audit/changes/${entityType}/${entityId}/diff`, {
      params: { v1, v2 },
    });
    return response.data;
  },
  
  // Integrity
  async getIntegrityStatus() {
    const response = await api.get('/audit/integrity/status');
    return response.data;
  },
  
  async verifyIntegrity(params = {}) {
    const response = await api.post('/audit/integrity/verify', params);
    return response.data;
  },
  
  // Compliance
  async getComplianceDashboard() {
    const response = await api.get('/compliance/dashboard');
    return response.data;
  },
  
  async getFrameworks() {
    const response = await api.get('/compliance/frameworks');
    return response.data;
  },
  
  async getFrameworkStatus(frameworkId) {
    const response = await api.get(`/compliance/frameworks/${frameworkId}`);
    return response.data;
  },
  
  async runComplianceChecks(frameworkId) {
    const response = await api.post(`/compliance/frameworks/${frameworkId}/run`);
    return response.data;
  },
  
  // Alerts
  async getAlerts(params = {}) {
    const response = await api.get('/compliance/alerts', { params });
    return response.data;
  },
  
  async acknowledgeAlert(alertId) {
    const response = await api.put(`/compliance/alerts/${alertId}/acknowledge`);
    return response.data;
  },
  
  async resolveAlert(alertId, notes) {
    const response = await api.put(`/compliance/alerts/${alertId}/resolve`, { notes });
    return response.data;
  },
  
  // Reports
  async generateReport(reportType, parameters = {}, format = 'json') {
    const response = await api.post('/compliance/reports/generate', {
      report_type: reportType,
      parameters,
      format,
    }, format !== 'json' ? { responseType: 'blob' } : {});
    
    if (format !== 'json') {
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}_report.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    }
    
    return response.data;
  },
};

export default auditApi;
```

---

## SUMMARY

### Phase 15 Complete Implementation

| Part | Content |
|------|---------|
| **Part 1** | Database models, Audit logger, Change tracker, Integrity service |
| **Part 2** | SOX framework, GDPR framework, Report service, Alert service |
| **Part 3** | API routes, Frontend pages, Components, Hooks, API service |

### Key Features

| Feature | Implementation |
|---------|----------------|
| **Audit Logging** | Automatic tracking via SQLAlchemy events |
| **Change History** | Before/after snapshots with versioning |
| **Hash Chain** | Cryptographic integrity verification |
| **SOX Compliance** | 8 automated controls |
| **GDPR Compliance** | 8 automated controls |
| **Alert System** | Configurable rules with notifications |
| **Reporting** | PDF/Excel/CSV export |
| **Frontend** | Audit log viewer, Compliance dashboard |

### API Endpoints Summary

| Category | Endpoints |
|----------|-----------|
| **Audit Logs** | GET/logs, GET/logs/:id, GET/logs/entity, GET/logs/user |
| **Changes** | GET/changes/:entity/:id, GET/changes/diff |
| **Integrity** | GET/integrity/status, POST/integrity/verify |
| **Compliance** | GET/dashboard, GET/frameworks, POST/frameworks/:id/run |
| **Alerts** | GET/alerts, PUT/acknowledge, PUT/resolve |
| **Reports** | POST/reports/generate |

---

*Phase 15 Tasks Part 3 - LogiAccounting Pro*
*API Routes & Frontend Components*
