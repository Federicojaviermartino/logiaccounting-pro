"""
CRM Services Module
"""

from .lead_service import lead_service
from .contact_service import contact_service
from .company_service import company_service
from .opportunity_service import opportunity_service
from .pipeline_service import pipeline_service
from .activity_service import activity_service
from .email_template_service import email_template_service
from .quote_service import quote_service

__all__ = [
    "lead_service",
    "contact_service",
    "company_service",
    "opportunity_service",
    "pipeline_service",
    "activity_service",
    "email_template_service",
    "quote_service",
]
