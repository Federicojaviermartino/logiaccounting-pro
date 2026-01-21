"""
Tenant Management Routes - Phase 16
Multi-tenancy API endpoints
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Request

from app.utils.auth import require_roles
from app.models.tenant_store import tenant_db, TenantTier, TIER_QUOTAS, TIER_FEATURES
from app.middleware.tenant_context import (
    get_current_tenant,
    get_current_tenant_id,
    require_tenant,
    require_feature,
    check_quota
)
from app.services.tenant import (
    TenantService,
    ProvisioningService,
    QuotaService,
    FeatureService
)
from app.schemas.tenant_schemas import (
    TenantCreate, TenantUpdate, TenantResponse,
    TenantListResponse, TenantDetailResponse,
    DomainCreate, DomainListResponse, DomainVerifyResponse,
    TenantSettingsUpdate, SecuritySettingsUpdate, SettingsDetailResponse,
    SubscriptionDetailResponse, SubscriptionUpgradeRequest, SubscriptionCancelRequest,
    PlanListResponse, PricingPlan,
    QuotaDetailResponse, UsageSummaryResponse,
    FeatureListResponse, FeatureEnableRequest,
    InvitationCreate, InvitationListResponse, InvitationAcceptRequest,
    MemberListResponse, MemberUpdateRequest,
    TenantStatsResponse
)


router = APIRouter()


# ==================== Tenant Management ====================

@router.get("/current", response_model=TenantDetailResponse)
async def get_current_tenant_info(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get current tenant information"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # Try to get from user's memberships
        user_id = current_user.get("id")
        memberships = tenant_db.members.find_by_user(user_id)
        if memberships:
            tenant_id = memberships[0].get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=404, detail="No tenant context found")

    service = TenantService(tenant_id)
    tenant = service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"success": True, "tenant": tenant}


@router.put("/current", response_model=TenantDetailResponse)
async def update_current_tenant(
    data: TenantUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update current tenant information"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    tenant = service.update_tenant(tenant_id, data.model_dump(exclude_none=True))

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"success": True, "tenant": tenant}


@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get tenant statistics"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    stats = service.get_tenant_stats(tenant_id)

    return {"success": True, **stats}


# ==================== Admin Tenant Management ====================

@router.get("/admin/list", response_model=TenantListResponse)
async def list_all_tenants(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """List all tenants (superadmin only)"""
    service = TenantService()
    result = service.list_tenants(
        status=status,
        tier=tier,
        search=search,
        limit=limit,
        offset=offset
    )
    return {"success": True, **result}


@router.post("/admin/create", response_model=TenantDetailResponse)
async def create_new_tenant(
    data: TenantCreate,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Create a new tenant (superadmin only)"""
    service = ProvisioningService()

    try:
        result = service.provision_tenant(
            name=data.name,
            owner_email=data.owner_email,
            tier=data.tier.value if data.tier else TenantTier.FREE.value,
            country=data.country,
            timezone=data.timezone,
            locale=data.locale,
            metadata=data.metadata
        )

        return {"success": True, "tenant": result.get("tenant")}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant_by_id(
    tenant_id: str,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Get tenant by ID (superadmin only)"""
    service = TenantService(tenant_id)
    tenant = service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"success": True, "tenant": tenant}


@router.put("/admin/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Activate a tenant (superadmin only)"""
    service = TenantService()

    try:
        tenant = service.activate_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {"success": True, "tenant": tenant}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/admin/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Suspend a tenant (superadmin only)"""
    service = TenantService()

    try:
        tenant = service.suspend_tenant(tenant_id, reason)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {"success": True, "tenant": tenant}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/admin/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    hard_delete: bool = False,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Delete a tenant (superadmin only)"""
    service = TenantService()
    result = service.delete_tenant(tenant_id, hard_delete=hard_delete)

    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"success": True, "message": "Tenant deleted"}


# ==================== Domains ====================

@router.get("/domains", response_model=DomainListResponse)
async def list_domains(
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """List all domains for current tenant"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    domains = tenant_db.domains.find_by_tenant(tenant_id)
    return {"success": True, "domains": domains}


@router.post("/domains")
async def add_domain(
    data: DomainCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Add a custom domain"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        domain = service.add_domain(
            tenant_id,
            data.domain,
            data.domain_type,
            data.is_primary
        )
        return {"success": True, "domain": domain}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/domains/{domain_id}/verify", response_model=DomainVerifyResponse)
async def verify_domain(
    domain_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Verify domain ownership"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        domain = service.verify_domain(domain_id)
        return {
            "success": True,
            "is_verified": True,
            "message": "Domain verified successfully",
            "domain": domain
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/domains/{domain_id}")
async def remove_domain(
    domain_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Remove a custom domain"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        service.remove_domain(domain_id)
        return {"success": True, "message": "Domain removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Settings ====================

@router.get("/settings", response_model=SettingsDetailResponse)
async def get_settings(
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get tenant settings"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    settings = service.get_settings(tenant_id)

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return {"success": True, "settings": settings}


@router.put("/settings")
async def update_settings(
    data: TenantSettingsUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update tenant settings"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    settings = service.update_settings(tenant_id, data.model_dump(exclude_none=True))

    return {"success": True, "settings": settings}


@router.put("/settings/security")
async def update_security_settings(
    data: SecuritySettingsUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update security settings"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    settings = service.update_settings(tenant_id, data.model_dump(exclude_none=True))

    return {"success": True, "settings": settings}


# ==================== Subscription ====================

@router.get("/subscription", response_model=SubscriptionDetailResponse)
async def get_subscription(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get current subscription"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    subscription = tenant_db.subscriptions.find_by_tenant(tenant_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {"success": True, "subscription": subscription}


@router.post("/subscription/upgrade")
async def upgrade_subscription(
    data: SubscriptionUpgradeRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Upgrade subscription tier"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        tenant = service.change_tier(tenant_id, data.tier.value)
        return {"success": True, "tenant": tenant}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription/downgrade")
async def downgrade_subscription(
    data: SubscriptionUpgradeRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Downgrade subscription tier"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Check current usage vs new tier limits
    service = TenantService(tenant_id)
    quota_service = QuotaService(tenant_id)

    new_limits = TIER_QUOTAS.get(TenantTier(data.tier.value), {})
    current_usage = quota_service.get_usage_summary()

    # Validate downgrade is possible
    for usage in current_usage.get("usage", []):
        resource = usage["resource"]
        current = usage["current"]
        new_limit = new_limits.get(f"max_{resource}s", new_limits.get(f"max_{resource}", -1))

        if new_limit != -1 and current > new_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot downgrade: {resource} usage ({current}) exceeds new tier limit ({new_limit})"
            )

    try:
        tenant = service.change_tier(tenant_id, data.tier.value)
        return {"success": True, "tenant": tenant}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription/cancel")
async def cancel_subscription(
    data: SubscriptionCancelRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Cancel subscription"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    tenant = service.cancel_tenant(tenant_id, data.reason)

    return {"success": True, "tenant": tenant}


@router.get("/plans", response_model=PlanListResponse)
async def list_plans():
    """List available subscription plans"""
    plans = [
        PricingPlan(
            tier=TenantTier.FREE,
            name="Free",
            description="Perfect for getting started",
            price_monthly=0,
            price_yearly=0,
            currency="USD",
            features=TIER_FEATURES.get(TenantTier.FREE, []),
            limits=TIER_QUOTAS.get(TenantTier.FREE, {}),
            is_popular=False
        ),
        PricingPlan(
            tier=TenantTier.STANDARD,
            name="Standard",
            description="For growing businesses",
            price_monthly=29,
            price_yearly=290,
            currency="USD",
            features=TIER_FEATURES.get(TenantTier.STANDARD, []),
            limits=TIER_QUOTAS.get(TenantTier.STANDARD, {}),
            is_popular=False
        ),
        PricingPlan(
            tier=TenantTier.PROFESSIONAL,
            name="Professional",
            description="For established businesses",
            price_monthly=79,
            price_yearly=790,
            currency="USD",
            features=TIER_FEATURES.get(TenantTier.PROFESSIONAL, []),
            limits=TIER_QUOTAS.get(TenantTier.PROFESSIONAL, {}),
            is_popular=True
        ),
        PricingPlan(
            tier=TenantTier.BUSINESS,
            name="Business",
            description="For large organizations",
            price_monthly=199,
            price_yearly=1990,
            currency="USD",
            features=TIER_FEATURES.get(TenantTier.BUSINESS, []),
            limits=TIER_QUOTAS.get(TenantTier.BUSINESS, {}),
            is_popular=False
        ),
        PricingPlan(
            tier=TenantTier.ENTERPRISE,
            name="Enterprise",
            description="Custom solution for enterprises",
            price_monthly=0,
            price_yearly=0,
            currency="USD",
            features=TIER_FEATURES.get(TenantTier.ENTERPRISE, []),
            limits=TIER_QUOTAS.get(TenantTier.ENTERPRISE, {}),
            is_popular=False
        )
    ]

    return {"success": True, "plans": plans}


# ==================== Quota & Usage ====================

@router.get("/quota", response_model=QuotaDetailResponse)
async def get_quota(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get tenant quota information"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = QuotaService(tenant_id)
    quota = service.get_quota()

    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")

    return {"success": True, "quota": quota}


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get usage summary with percentages"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = QuotaService(tenant_id)
    summary = service.get_usage_summary()

    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    return {"success": True, **summary}


@router.get("/usage/alerts")
async def get_usage_alerts(
    threshold: int = Query(default=80, ge=50, le=100),
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get alerts for resources approaching limits"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = QuotaService(tenant_id)
    alerts = service.get_quota_alerts(threshold)

    return {"success": True, "alerts": alerts, "threshold": threshold}


# ==================== Features ====================

@router.get("/features", response_model=FeatureListResponse)
async def list_features(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """List all features with their status"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = FeatureService(tenant_id)
    features = service.get_all_features()

    return {"success": True, "features": features}


@router.get("/features/{feature_name}")
async def get_feature(
    feature_name: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Get specific feature details"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = FeatureService(tenant_id)
    feature = service.get_feature(feature_name)

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    return {"success": True, "feature": feature}


@router.post("/features/enable")
async def enable_feature(
    data: FeatureEnableRequest,
    request: Request,
    current_user: dict = Depends(require_roles("superadmin"))
):
    """Enable a feature (superadmin only for non-tier features)"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = FeatureService(tenant_id)

    try:
        feature = service.enable_feature(
            data.feature_name,
            config=data.config,
            expires_at=data.expires_at
        )
        return {"success": True, "feature": feature}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/features/upgrade-suggestions")
async def get_upgrade_suggestions(
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get suggestions for tier upgrade"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = FeatureService(tenant_id)
    suggestions = service.get_upgrade_suggestions()

    return {"success": True, **suggestions}


# ==================== Team & Invitations ====================

@router.get("/team", response_model=MemberListResponse)
async def list_team_members(
    request: Request,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """List all team members"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    members = service.get_members(tenant_id)

    # Enrich with user info (in production would join with users table)
    enriched = []
    for member in members:
        enriched.append({
            **member,
            "user_email": f"user_{member.get('user_id')}@example.com",
            "user_name": f"User {member.get('user_id')[:8]}"
        })

    return {"success": True, "members": enriched, "total": len(enriched)}


@router.put("/team/{user_id}/role")
async def update_member_role(
    user_id: str,
    data: MemberUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a team member's role"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        member = service.update_member_role(tenant_id, user_id, data.role.value)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/team/{user_id}")
async def remove_team_member(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Remove a team member"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    # Prevent removing yourself
    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    service = TenantService(tenant_id)

    try:
        result = service.remove_member(tenant_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Member not found")
        return {"success": True, "message": "Member removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    status: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """List pending invitations"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    invitations = service.get_invitations(tenant_id, status)

    return {"success": True, "invitations": invitations}


@router.post("/invitations")
async def create_invitation(
    data: InvitationCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send a team invitation"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)

    try:
        invitation = service.create_invitation(
            tenant_id,
            data.email,
            data.role.value,
            current_user.get("id")
        )
        return {"success": True, "invitation": invitation}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/accept")
async def accept_invitation(
    data: InvitationAcceptRequest,
    current_user: dict = Depends(require_roles("admin", "member"))
):
    """Accept a team invitation"""
    service = TenantService()

    try:
        member = service.accept_invitation(data.token, current_user.get("id"))
        return {"success": True, "member": member}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/invitations/{invitation_id}")
async def revoke_invitation(
    invitation_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Revoke an invitation"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    service = TenantService(tenant_id)
    result = service.revoke_invitation(invitation_id)

    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return {"success": True, "message": "Invitation revoked"}
