"""
Portal Services Module
Customer Portal v2 - Self-Service Hub
"""

from .auth_service import portal_auth_service, PortalAuthService
from .dashboard_service import portal_dashboard_service, PortalDashboardService
from .ticket_service import ticket_service, TicketService
from .knowledge_service import knowledge_service, KnowledgeService
from .payment_service import portal_payment_service, PortalPaymentService
from .project_service import portal_project_service, PortalProjectService
from .quote_service import portal_quote_service, PortalQuoteService
from .message_service import message_service, MessageService

__all__ = [
    "portal_auth_service",
    "PortalAuthService",
    "portal_dashboard_service",
    "PortalDashboardService",
    "ticket_service",
    "TicketService",
    "knowledge_service",
    "KnowledgeService",
    "portal_payment_service",
    "PortalPaymentService",
    "portal_project_service",
    "PortalProjectService",
    "portal_quote_service",
    "PortalQuoteService",
    "message_service",
    "MessageService",
]
