"""
Anomaly Model
Store detected anomalies
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


# In-memory storage
anomalies_db: Dict[str, 'Anomaly'] = {}


@dataclass
class Anomaly:
    """Detected anomaly record"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    anomaly_type: str = ''
    severity: str = 'medium'
    risk_score: Optional[float] = None
    entity_type: str = ''
    entity_id: str = ''
    title: str = ''
    description: Optional[str] = None
    detection_method: Optional[str] = None
    detection_rule: Optional[str] = None
    evidence: Optional[Dict] = None
    related_entities: Optional[List[Dict]] = None
    status: str = 'open'
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    SEVERITY_CRITICAL = 'critical'
    SEVERITY_HIGH = 'high'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_LOW = 'low'

    def save(self):
        anomalies_db[self.id] = self

    @classmethod
    def get_by_id(cls, anomaly_id: str, tenant_id: str) -> Optional['Anomaly']:
        """Get anomaly by ID"""
        anomaly = anomalies_db.get(anomaly_id)
        if anomaly and anomaly.tenant_id == tenant_id:
            return anomaly
        return None

    @classmethod
    def get_by_tenant(
        cls,
        tenant_id: str,
        status: str = 'open',
        severity: str = None,
        anomaly_type: str = None,
        limit: int = 50
    ) -> List['Anomaly']:
        """Get anomalies for tenant"""
        anomalies = [a for a in anomalies_db.values() if a.tenant_id == tenant_id]

        if status != 'all':
            anomalies = [a for a in anomalies if a.status == status]
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]

        anomalies.sort(key=lambda x: x.created_at, reverse=True)
        return anomalies[:limit]

    @classmethod
    def exists(
        cls,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        anomaly_type: str
    ) -> bool:
        """Check if similar anomaly already exists"""
        for a in anomalies_db.values():
            if (a.tenant_id == tenant_id and
                a.entity_type == entity_type and
                a.entity_id == entity_id and
                a.anomaly_type == anomaly_type and
                a.status in ['open', 'investigating']):
                return True
        return False

    @classmethod
    def get_stats(cls, tenant_id: str) -> Dict[str, Any]:
        """Get anomaly statistics"""
        anomalies = [a for a in anomalies_db.values() if a.tenant_id == tenant_id]

        stats = {
            'total': len(anomalies),
            'by_status': {},
            'by_severity': {},
        }

        for a in anomalies:
            stats['by_status'][a.status] = stats['by_status'].get(a.status, 0) + 1
            stats['by_severity'][a.severity] = stats['by_severity'].get(a.severity, 0) + 1

        return stats

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'risk_score': self.risk_score,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'title': self.title,
            'description': self.description,
            'detection_method': self.detection_method,
            'evidence': self.evidence,
            'related_entities': self.related_entities,
            'status': self.status,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
