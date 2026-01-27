"""
Payment Recommendation Model
Store AI-generated payment suggestions
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


# In-memory storage
payment_recommendations_db: Dict[str, 'PaymentRecommendation'] = {}


@dataclass
class PaymentRecommendation:
    """Payment optimization recommendation"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    recommendation_type: str = ''
    invoice_ids: List[str] = field(default_factory=list)
    title: str = ''
    description: Optional[str] = None
    potential_savings: Optional[float] = None
    cash_flow_impact: Optional[float] = None
    suggested_payment_date: Optional[date] = None
    original_due_date: Optional[date] = None
    deadline: Optional[date] = None
    priority: str = 'medium'
    confidence_score: Optional[float] = None
    reasoning: Optional[Dict] = None
    status: str = 'pending'
    actioned_at: Optional[datetime] = None
    actioned_by: Optional[str] = None
    action_result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def save(self):
        payment_recommendations_db[self.id] = self

    @classmethod
    def get_by_id(cls, rec_id: str, tenant_id: str) -> Optional['PaymentRecommendation']:
        """Get recommendation by ID"""
        rec = payment_recommendations_db.get(rec_id)
        if rec and rec.tenant_id == tenant_id:
            return rec
        return None

    @classmethod
    def get_by_tenant(
        cls,
        tenant_id: str,
        status: str = 'pending',
        limit: int = 20
    ) -> List['PaymentRecommendation']:
        """Get recommendations for tenant"""
        recs = [r for r in payment_recommendations_db.values() if r.tenant_id == tenant_id]
        if status != 'all':
            recs = [r for r in recs if r.status == status]
        recs.sort(key=lambda x: x.created_at, reverse=True)
        return recs[:limit]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'recommendation_type': self.recommendation_type,
            'invoice_ids': self.invoice_ids,
            'title': self.title,
            'description': self.description,
            'potential_savings': self.potential_savings,
            'cash_flow_impact': self.cash_flow_impact,
            'suggested_payment_date': self.suggested_payment_date.isoformat() if self.suggested_payment_date else None,
            'original_due_date': self.original_due_date.isoformat() if self.original_due_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
