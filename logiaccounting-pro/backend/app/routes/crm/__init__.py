"""
CRM Module Router
Aggregates all CRM sub-routers
"""

from fastapi import APIRouter

from .contacts import router as contacts_router
from .companies import router as companies_router
from .leads import router as leads_router
from .opportunities import router as opportunities_router
from .activities import router as activities_router
from .quotes import router as quotes_router


# Create main CRM router
router = APIRouter(prefix="/api/v1/crm", tags=["CRM"])

# Include sub-routers
router.include_router(contacts_router, prefix="/contacts", tags=["CRM - Contacts"])
router.include_router(companies_router, prefix="/companies", tags=["CRM - Companies"])
router.include_router(leads_router, prefix="/leads", tags=["CRM - Leads"])
router.include_router(opportunities_router, prefix="/opportunities", tags=["CRM - Opportunities"])
router.include_router(activities_router, prefix="/activities", tags=["CRM - Activities"])
router.include_router(quotes_router, prefix="/quotes", tags=["CRM - Quotes"])
