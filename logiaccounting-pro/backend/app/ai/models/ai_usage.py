"""
AI Usage Model
Track AI service usage for billing and analytics
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import uuid

from app.utils.datetime_utils import utc_now

# In-memory storage
ai_usage_db: Dict[str, 'AIUsage'] = {}


@dataclass
class AIUsage:
    """AI usage tracking per tenant per day"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    usage_date: date = field(default_factory=date.today)
    service: str = ''
    request_count: int = 0
    token_input: int = 0
    token_output: int = 0
    processing_time_ms: int = 0
    estimated_cost: float = 0.0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    COSTS = {
        'anthropic': {
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
        },
        'openai': {
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
        }
    }

    @classmethod
    def record_usage(
        cls,
        tenant_id: str,
        service: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        processing_time_ms: int = 0,
        model: str = None,
        provider: str = 'anthropic',
    ) -> 'AIUsage':
        """Record AI usage"""
        today = date.today()
        key = f"{tenant_id}:{today}:{service}"

        if key in ai_usage_db:
            usage = ai_usage_db[key]
        else:
            usage = cls(
                tenant_id=tenant_id,
                usage_date=today,
                service=service,
            )
            ai_usage_db[key] = usage

        usage.request_count += 1
        usage.token_input += input_tokens
        usage.token_output += output_tokens
        usage.processing_time_ms += processing_time_ms
        usage.updated_at = utc_now()

        if model and provider in cls.COSTS and model in cls.COSTS[provider]:
            costs = cls.COSTS[provider][model]
            cost = (input_tokens * costs['input'] / 1000) + \
                   (output_tokens * costs['output'] / 1000)
            usage.estimated_cost += cost

        return usage

    @classmethod
    def get_usage_summary(
        cls,
        tenant_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get usage summary for period"""
        summary = {
            'total_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_processing_time_ms': 0,
            'total_estimated_cost': 0,
            'by_service': {},
        }

        for key, usage in ai_usage_db.items():
            if usage.tenant_id != tenant_id:
                continue
            if not (start_date <= usage.usage_date <= end_date):
                continue

            summary['total_requests'] += usage.request_count
            summary['total_input_tokens'] += usage.token_input
            summary['total_output_tokens'] += usage.token_output
            summary['total_processing_time_ms'] += usage.processing_time_ms
            summary['total_estimated_cost'] += usage.estimated_cost

            if usage.service not in summary['by_service']:
                summary['by_service'][usage.service] = {
                    'requests': 0,
                    'tokens': 0,
                    'cost': 0,
                }

            summary['by_service'][usage.service]['requests'] += usage.request_count
            summary['by_service'][usage.service]['tokens'] += \
                usage.token_input + usage.token_output
            summary['by_service'][usage.service]['cost'] += usage.estimated_cost

        return summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'usage_date': self.usage_date.isoformat(),
            'service': self.service,
            'request_count': self.request_count,
            'token_input': self.token_input,
            'token_output': self.token_output,
            'processing_time_ms': self.processing_time_ms,
            'estimated_cost': self.estimated_cost,
        }
