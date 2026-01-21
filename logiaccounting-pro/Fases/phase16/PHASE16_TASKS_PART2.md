# LogiAccounting Pro - Phase 16 Tasks Part 2

## SERVICES & PROVISIONING

---

## TASK 5: TENANT SERVICE

### 5.1 Core Tenant Service

**File:** `backend/app/tenancy/services/tenant_service.py`

```python
"""
Tenant Service
Core operations for tenant management
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from app.extensions import db
from app.tenancy.models.tenant import Tenant, TenantDomain, TenantStatus, TenantTier, IsolationLevel
from app.tenancy.models.tenant_settings import TenantSettings
from app.tenancy.models.tenant_subscription import TenantSubscription, TenantQuota
from app.tenancy.models.tenant_feature import TenantFeature, get_features_for_tier
from app.tenancy.core.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant operations"""
    
    @staticmethod
    def create_tenant(
        name: str,
        email: str,
        slug: str = None,
        tier: str = 'standard',
        owner_id: str = None,
        **kwargs
    ) -> Tenant:
        """
        Create a new tenant with all related entities
        
        Args:
            name: Tenant/organization name
            email: Primary contact email
            slug: URL-safe identifier (auto-generated if not provided)
            tier: Subscription tier
            owner_id: Owner user ID
            **kwargs: Additional tenant fields
            
        Returns:
            Created Tenant
        """
        # Create tenant
        tenant = Tenant(
            name=name,
            email=email,
            slug=slug,
            tier=tier,
            owner_id=owner_id,
            status=TenantStatus.PENDING.value,
            **kwargs
        )
        
        db.session.add(tenant)
        db.session.flush()  # Get tenant ID
        
        # Create default subdomain
        domain = TenantDomain(
            tenant_id=tenant.id,
            domain=f"{tenant.slug}.logiaccounting.com",
            domain_type='subdomain',
            is_verified=True,
            is_primary=True,
        )
        db.session.add(domain)
        
        # Create settings
        settings = TenantSettings(tenant_id=tenant.id)
        db.session.add(settings)
        
        # Create subscription based on tier
        plan = TenantService._get_plan_for_tier(tier)
        subscription = TenantSubscription(
            tenant_id=tenant.id,
            plan_id=plan['id'],
            plan_name=plan['name'],
            price_amount=plan.get('price_monthly', 0),
            status='trial',
        )
        subscription.start_trial(days=14)
        db.session.add(subscription)
        
        # Create quotas based on tier
        quotas = TenantQuota(
            tenant_id=tenant.id,
            **TenantService._get_quotas_for_tier(tier)
        )
        db.session.add(quotas)
        
        # Create feature flags based on tier
        features = get_features_for_tier(tier)
        for feature_key in features:
            feature = TenantFeature(
                tenant_id=tenant.id,
                feature_key=feature_key,
                is_enabled=True,
                enabled_at=datetime.utcnow(),
            )
            db.session.add(feature)
        
        db.session.commit()
        
        logger.info(f"Created tenant: {tenant.slug} ({tenant.id})")
        
        return tenant
    
    @staticmethod
    def get_tenant(tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return Tenant.query.filter(
            Tenant.id == tenant_id,
            Tenant.deleted_at == None
        ).first()
    
    @staticmethod
    def get_tenant_by_slug(slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        return Tenant.query.filter(
            Tenant.slug == slug,
            Tenant.deleted_at == None
        ).first()
    
    @staticmethod
    def list_tenants(
        status: str = None,
        tier: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple:
        """List tenants with pagination"""
        query = Tenant.query.filter(Tenant.deleted_at == None)
        
        if status:
            query = query.filter(Tenant.status == status)
        
        if tier:
            query = query.filter(Tenant.tier == tier)
        
        query = query.order_by(Tenant.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.total
    
    @staticmethod
    def update_tenant(tenant_id: str, **data) -> Optional[Tenant]:
        """Update tenant fields"""
        tenant = TenantService.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # Fields that can be updated
        updatable_fields = [
            'name', 'legal_name', 'email', 'phone',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'tax_id', 'vat_number'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(tenant, field, data[field])
        
        tenant.updated_at = datetime.utcnow()
        db.session.commit()
        
        return tenant
    
    @staticmethod
    def activate_tenant(tenant_id: str) -> bool:
        """Activate a tenant"""
        tenant = TenantService.get_tenant(tenant_id)
        if not tenant:
            return False
        
        tenant.activate()
        db.session.commit()
        
        logger.info(f"Activated tenant: {tenant.slug}")
        return True
    
    @staticmethod
    def suspend_tenant(tenant_id: str, reason: str = None) -> bool:
        """Suspend a tenant"""
        tenant = TenantService.get_tenant(tenant_id)
        if not tenant:
            return False
        
        tenant.suspend(reason)
        db.session.commit()
        
        logger.warning(f"Suspended tenant: {tenant.slug} - {reason}")
        return True
    
    @staticmethod
    def delete_tenant(tenant_id: str, hard_delete: bool = False) -> bool:
        """Delete a tenant"""
        tenant = TenantService.get_tenant(tenant_id)
        if not tenant:
            return False
        
        if hard_delete:
            db.session.delete(tenant)
        else:
            tenant.soft_delete()
        
        db.session.commit()
        
        logger.warning(f"Deleted tenant: {tenant.slug} (hard={hard_delete})")
        return True
    
    @staticmethod
    def change_tier(tenant_id: str, new_tier: str) -> bool:
        """Change tenant tier"""
        tenant = TenantService.get_tenant(tenant_id)
        if not tenant:
            return False
        
        old_tier = tenant.tier
        tenant.tier = new_tier
        
        # Update quotas
        new_quotas = TenantService._get_quotas_for_tier(new_tier)
        if tenant.quotas:
            for key, value in new_quotas.items():
                setattr(tenant.quotas, key, value)
        
        # Update features
        TenantService._sync_features_for_tier(tenant, new_tier)
        
        # Update subscription
        plan = TenantService._get_plan_for_tier(new_tier)
        if tenant.subscription:
            tenant.subscription.plan_id = plan['id']
            tenant.subscription.plan_name = plan['name']
            tenant.subscription.price_amount = plan.get('price_monthly', 0)
        
        db.session.commit()
        
        logger.info(f"Changed tier for {tenant.slug}: {old_tier} -> {new_tier}")
        return True
    
    @staticmethod
    def _get_plan_for_tier(tier: str) -> Dict[str, Any]:
        """Get plan details for a tier"""
        plans = {
            'free': {'id': 'free', 'name': 'Free', 'price_monthly': 0},
            'standard': {'id': 'standard', 'name': 'Standard', 'price_monthly': 29},
            'professional': {'id': 'professional', 'name': 'Professional', 'price_monthly': 79},
            'business': {'id': 'business', 'name': 'Business', 'price_monthly': 199},
            'enterprise': {'id': 'enterprise', 'name': 'Enterprise', 'price_monthly': 0},
        }
        return plans.get(tier, plans['standard'])
    
    @staticmethod
    def _get_quotas_for_tier(tier: str) -> Dict[str, int]:
        """Get quota limits for a tier"""
        quotas = {
            'free': {
                'max_users': 2,
                'max_storage_mb': 100,
                'max_api_calls_per_month': 1000,
                'max_invoices_per_month': 10,
                'max_products': 50,
                'max_projects': 5,
                'max_integrations': 1,
            },
            'standard': {
                'max_users': 5,
                'max_storage_mb': 1024,
                'max_api_calls_per_month': 10000,
                'max_invoices_per_month': 100,
                'max_products': 500,
                'max_projects': 50,
                'max_integrations': 3,
            },
            'professional': {
                'max_users': 15,
                'max_storage_mb': 5120,
                'max_api_calls_per_month': 50000,
                'max_invoices_per_month': 500,
                'max_products': 2000,
                'max_projects': 200,
                'max_integrations': 10,
            },
            'business': {
                'max_users': 50,
                'max_storage_mb': 20480,
                'max_api_calls_per_month': 200000,
                'max_invoices_per_month': 2000,
                'max_products': 10000,
                'max_projects': 1000,
                'max_integrations': 25,
            },
            'enterprise': {
                'max_users': None,  # Unlimited
                'max_storage_mb': None,
                'max_api_calls_per_month': None,
                'max_invoices_per_month': None,
                'max_products': None,
                'max_projects': None,
                'max_integrations': None,
            },
        }
        return quotas.get(tier, quotas['standard'])
    
    @staticmethod
    def _sync_features_for_tier(tenant: Tenant, tier: str):
        """Sync feature flags for tier"""
        enabled_features = get_features_for_tier(tier)
        
        # Disable features not in tier
        for feature in tenant.features:
            if feature.feature_key not in enabled_features:
                feature.is_enabled = False
        
        # Enable features in tier
        existing_keys = {f.feature_key for f in tenant.features}
        for feature_key in enabled_features:
            if feature_key in existing_keys:
                # Enable existing
                for f in tenant.features:
                    if f.feature_key == feature_key:
                        f.is_enabled = True
                        f.enabled_at = datetime.utcnow()
            else:
                # Create new
                feature = TenantFeature(
                    tenant_id=tenant.id,
                    feature_key=feature_key,
                    is_enabled=True,
                    enabled_at=datetime.utcnow(),
                )
                db.session.add(feature)
```

---

## TASK 6: PROVISIONING SERVICE

### 6.1 Tenant Provisioning

**File:** `backend/app/tenancy/services/provisioning_service.py`

```python
"""
Provisioning Service
Tenant setup and teardown operations
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.extensions import db
from app.tenancy.models.tenant import Tenant, TenantStatus, IsolationLevel
from app.tenancy.services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class ProvisioningService:
    """Service for tenant provisioning"""
    
    @staticmethod
    def provision_tenant(
        name: str,
        email: str,
        owner_email: str,
        tier: str = 'standard',
        isolation_level: str = 'shared_database',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Full tenant provisioning workflow
        
        Args:
            name: Organization name
            email: Organization email
            owner_email: Owner user email
            tier: Subscription tier
            isolation_level: Data isolation level
            **kwargs: Additional tenant data
            
        Returns:
            Provisioning result with tenant and owner details
        """
        try:
            # 1. Create tenant
            tenant = TenantService.create_tenant(
                name=name,
                email=email,
                tier=tier,
                isolation_level=isolation_level,
                **kwargs
            )
            
            # 2. Set up isolation based on level
            if isolation_level == IsolationLevel.SCHEMA.value:
                ProvisioningService._create_tenant_schema(tenant)
            elif isolation_level == IsolationLevel.DATABASE.value:
                ProvisioningService._create_tenant_database(tenant)
            
            # 3. Create owner user
            owner = ProvisioningService._create_owner_user(tenant, owner_email)
            
            # 4. Initialize default data
            ProvisioningService._initialize_tenant_data(tenant)
            
            # 5. Activate tenant
            tenant.status = TenantStatus.ACTIVE.value
            db.session.commit()
            
            logger.info(f"Successfully provisioned tenant: {tenant.slug}")
            
            return {
                'success': True,
                'tenant': tenant.to_dict(),
                'owner': {
                    'id': str(owner.id),
                    'email': owner.email,
                },
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Provisioning failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def deprovision_tenant(tenant_id: str, retain_data_days: int = 30) -> Dict[str, Any]:
        """
        Tenant deprovisioning workflow
        
        Args:
            tenant_id: Tenant to deprovision
            retain_data_days: Days to retain data before purge
            
        Returns:
            Deprovisioning result
        """
        try:
            tenant = TenantService.get_tenant(tenant_id)
            if not tenant:
                return {'success': False, 'error': 'Tenant not found'}
            
            # 1. Suspend tenant
            tenant.status = TenantStatus.CANCELLED.value
            
            # 2. Cancel subscription
            if tenant.subscription:
                tenant.subscription.cancel(immediate=True)
            
            # 3. Schedule data cleanup
            from datetime import timedelta
            cleanup_date = datetime.utcnow() + timedelta(days=retain_data_days)
            
            # Store cleanup date in metadata or create cleanup task
            
            # 4. Soft delete tenant
            tenant.soft_delete()
            
            db.session.commit()
            
            logger.info(f"Deprovisioned tenant: {tenant.slug}")
            
            return {
                'success': True,
                'tenant_id': str(tenant.id),
                'cleanup_scheduled': cleanup_date.isoformat(),
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Deprovisioning failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def _create_tenant_schema(tenant: Tenant):
        """Create dedicated schema for tenant"""
        schema_name = f"tenant_{tenant.slug.replace('-', '_')}"
        
        # Create schema
        db.session.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        
        # Store schema name
        tenant.schema_name = schema_name
        
        logger.info(f"Created schema: {schema_name}")
    
    @staticmethod
    def _create_tenant_database(tenant: Tenant):
        """Create dedicated database for tenant"""
        db_name = f"logiaccounting_{tenant.slug.replace('-', '_')}"
        
        # This would typically be done via admin connection
        # or through cloud provider API (e.g., AWS RDS)
        
        # For now, store the intended database name
        tenant.database_name = db_name
        
        logger.info(f"Database requested: {db_name}")
    
    @staticmethod
    def _create_owner_user(tenant: Tenant, email: str):
        """Create owner user for tenant"""
        from app.models.user import User
        import secrets
        
        # Generate temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # Create user
        user = User(
            email=email,
            organization_id=tenant.id,
            role='admin',
            is_active=True,
        )
        user.set_password(temp_password)
        
        db.session.add(user)
        db.session.flush()
        
        # Update tenant owner
        tenant.owner_id = user.id
        
        # TODO: Send welcome email with temp password
        
        return user
    
    @staticmethod
    def _initialize_tenant_data(tenant: Tenant):
        """Initialize default data for tenant"""
        # This could include:
        # - Default categories
        # - Default payment terms
        # - Default tax rates
        # - Sample data (optional)
        
        logger.info(f"Initialized data for tenant: {tenant.slug}")


class TenantMigrationService:
    """Service for migrating tenant data between isolation levels"""
    
    @staticmethod
    def migrate_to_schema(tenant: Tenant) -> bool:
        """Migrate tenant from shared DB to dedicated schema"""
        if tenant.isolation_level == IsolationLevel.SCHEMA.value:
            return True  # Already using schema
        
        try:
            # 1. Create new schema
            schema_name = f"tenant_{tenant.slug.replace('-', '_')}"
            db.session.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            
            # 2. Copy tables to new schema
            # This would involve:
            # - Creating tables in new schema
            # - Copying data with tenant_id filter
            # - Updating foreign keys
            
            # 3. Update tenant configuration
            tenant.schema_name = schema_name
            tenant.isolation_level = IsolationLevel.SCHEMA.value
            
            # 4. Clean up old data (after verification)
            
            db.session.commit()
            
            logger.info(f"Migrated tenant {tenant.slug} to schema isolation")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Migration failed: {e}")
            return False
    
    @staticmethod
    def export_tenant_data(tenant: Tenant, format: str = 'json') -> Dict[str, Any]:
        """Export all tenant data for migration or backup"""
        # This would export all tenant data for:
        # - Migration to new system
        # - Backup purposes
        # - Data portability (GDPR)
        
        data = {
            'tenant': tenant.to_dict(include_settings=True),
            'users': [],
            'invoices': [],
            'products': [],
            'projects': [],
            # ... all tenant data
        }
        
        # Collect data from each tenant-aware model
        # ...
        
        return data
```

---

## TASK 7: QUOTA SERVICE

### 7.1 Quota Management Service

**File:** `backend/app/tenancy/services/quota_service.py`

```python
"""
Quota Service
Resource quota management and enforcement
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from app.extensions import db
from app.tenancy.models.tenant import Tenant
from app.tenancy.models.tenant_subscription import TenantQuota
from app.tenancy.core.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class QuotaService:
    """Service for quota management"""
    
    RESOURCES = [
        'users', 'storage_mb', 'api_calls', 'invoices',
        'products', 'projects', 'integrations'
    ]
    
    @staticmethod
    def check_quota(resource: str, amount: int = 1, tenant: Tenant = None) -> Dict[str, Any]:
        """
        Check if resource usage is within quota
        
        Args:
            resource: Resource type
            amount: Amount to check
            tenant: Tenant (uses context if not provided)
            
        Returns:
            Check result with quota details
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant or not tenant.quotas:
            return {
                'allowed': True,
                'reason': 'No quota restrictions',
            }
        
        quota = tenant.quotas
        max_key = f'max_{resource}'
        current_key = f'current_{resource}'
        
        max_value = getattr(quota, max_key, None)
        current_value = getattr(quota, current_key, 0) or 0
        
        # Unlimited
        if max_value is None:
            return {
                'allowed': True,
                'limit': None,
                'used': current_value,
                'available': None,
            }
        
        available = max_value - current_value
        allowed = (current_value + amount) <= max_value
        
        return {
            'allowed': allowed,
            'limit': max_value,
            'used': current_value,
            'available': available,
            'requested': amount,
            'would_exceed': not allowed,
        }
    
    @staticmethod
    def increment_usage(resource: str, amount: int = 1, tenant: Tenant = None) -> bool:
        """
        Increment resource usage
        
        Args:
            resource: Resource type
            amount: Amount to increment
            tenant: Tenant (uses context if not provided)
            
        Returns:
            True if successful
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant or not tenant.quotas:
            return True
        
        # Check quota first
        check = QuotaService.check_quota(resource, amount, tenant)
        if not check['allowed']:
            logger.warning(f"Quota exceeded for {tenant.slug}: {resource}")
            return False
        
        tenant.quotas.increment_usage(resource, amount)
        db.session.commit()
        
        logger.debug(f"Incremented {resource} usage for {tenant.slug} by {amount}")
        return True
    
    @staticmethod
    def decrement_usage(resource: str, amount: int = 1, tenant: Tenant = None) -> bool:
        """
        Decrement resource usage
        
        Args:
            resource: Resource type
            amount: Amount to decrement
            tenant: Tenant (uses context if not provided)
            
        Returns:
            True if successful
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant or not tenant.quotas:
            return True
        
        tenant.quotas.decrement_usage(resource, amount)
        db.session.commit()
        
        logger.debug(f"Decremented {resource} usage for {tenant.slug} by {amount}")
        return True
    
    @staticmethod
    def get_usage_summary(tenant: Tenant = None) -> Dict[str, Any]:
        """
        Get complete usage summary for tenant
        
        Returns:
            Usage summary with all resources
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant or not tenant.quotas:
            return {'quotas': {}}
        
        return tenant.quotas.to_dict()
    
    @staticmethod
    def reset_monthly_quotas():
        """
        Reset monthly usage counters for all tenants
        Should be called by scheduled task
        """
        today = datetime.utcnow().day
        
        # Get quotas due for reset today
        quotas = TenantQuota.query.filter(
            TenantQuota.usage_reset_day == today
        ).all()
        
        for quota in quotas:
            quota.reset_monthly_usage()
        
        db.session.commit()
        
        logger.info(f"Reset monthly quotas for {len(quotas)} tenants")
    
    @staticmethod
    def get_quota_alerts(tenant: Tenant = None) -> List[Dict[str, Any]]:
        """
        Get quota alerts for tenant
        
        Returns:
            List of resources near or at quota
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant or not tenant.quotas:
            return []
        
        alerts = []
        
        for resource in QuotaService.RESOURCES:
            check = QuotaService.check_quota(resource, 0, tenant)
            
            if check['limit'] is None:
                continue
            
            percentage = (check['used'] / check['limit']) * 100 if check['limit'] > 0 else 0
            
            if percentage >= 90:
                alerts.append({
                    'resource': resource,
                    'level': 'critical' if percentage >= 100 else 'warning',
                    'percentage': round(percentage, 1),
                    'used': check['used'],
                    'limit': check['limit'],
                })
            elif percentage >= 75:
                alerts.append({
                    'resource': resource,
                    'level': 'info',
                    'percentage': round(percentage, 1),
                    'used': check['used'],
                    'limit': check['limit'],
                })
        
        return alerts
    
    @staticmethod
    def recalculate_usage(tenant: Tenant):
        """
        Recalculate actual usage from database
        Used for periodic sync and corrections
        """
        if not tenant.quotas:
            return
        
        from app.tenancy.core.tenant_context import tenant_context
        
        with tenant_context(tenant):
            # Count users
            from app.models.user import User
            tenant.quotas.current_users = User.query.filter(
                User.organization_id == tenant.id,
                User.is_active == True
            ).count()
            
            # Count products
            from app.models.product import Product
            tenant.quotas.current_products = Product.query.count()
            
            # Count projects
            from app.models.project import Project
            tenant.quotas.current_projects = Project.query.count()
            
            # Count integrations
            from app.integrations.models.integration import Integration
            tenant.quotas.current_integrations = Integration.query.filter(
                Integration.status == 'connected'
            ).count()
            
            # Calculate storage
            # This would sum file sizes from documents, attachments, etc.
            
            db.session.commit()
        
        logger.info(f"Recalculated usage for tenant: {tenant.slug}")


class QuotaEnforcer:
    """Decorator and utilities for quota enforcement"""
    
    @staticmethod
    def enforce(resource: str, amount: int = 1):
        """
        Decorator to enforce quota before operation
        
        Usage:
            @QuotaEnforcer.enforce('invoices')
            def create_invoice(...):
                ...
        """
        def decorator(f):
            from functools import wraps
            
            @wraps(f)
            def wrapped(*args, **kwargs):
                check = QuotaService.check_quota(resource, amount)
                
                if not check['allowed']:
                    from flask import jsonify
                    return jsonify({
                        'success': False,
                        'error': f'Quota exceeded for {resource}',
                        'code': 'QUOTA_EXCEEDED',
                        'details': check,
                    }), 429
                
                result = f(*args, **kwargs)
                
                # Increment usage on success
                # This assumes the decorated function returns a tuple (response, status_code)
                # or just response (status 200)
                QuotaService.increment_usage(resource, amount)
                
                return result
            
            return wrapped
        return decorator
```

---

## TASK 8: FEATURE FLAGS SERVICE

### 8.1 Feature Flag Service

**File:** `backend/app/tenancy/services/feature_service.py`

```python
"""
Feature Service
Feature flag management for tenants
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from app.extensions import db
from app.tenancy.models.tenant import Tenant
from app.tenancy.models.tenant_feature import TenantFeature, FEATURE_DEFINITIONS, get_features_for_tier
from app.tenancy.core.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class FeatureService:
    """Service for feature flag management"""
    
    @staticmethod
    def is_enabled(feature_key: str, tenant: Tenant = None) -> bool:
        """
        Check if a feature is enabled for tenant
        
        Args:
            feature_key: Feature identifier
            tenant: Tenant (uses context if not provided)
            
        Returns:
            True if feature is enabled
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return False
        
        return tenant.has_feature(feature_key)
    
    @staticmethod
    def get_feature(feature_key: str, tenant: Tenant = None) -> Optional[Dict[str, Any]]:
        """
        Get feature details for tenant
        
        Returns:
            Feature details including config
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return None
        
        for feature in tenant.features:
            if feature.feature_key == feature_key:
                return feature.to_dict()
        
        return None
    
    @staticmethod
    def get_all_features(tenant: Tenant = None) -> List[Dict[str, Any]]:
        """
        Get all features for tenant with their status
        
        Returns:
            List of all features with enabled status
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return []
        
        # Build feature list with definitions
        features = []
        enabled_keys = {f.feature_key: f for f in tenant.features}
        
        for key, definition in FEATURE_DEFINITIONS.items():
            feature_data = {
                'key': key,
                'name': definition['name'],
                'description': definition['description'],
                'available_tiers': definition['tiers'],
                'is_enabled': False,
                'config': {},
            }
            
            if key in enabled_keys:
                tf = enabled_keys[key]
                feature_data['is_enabled'] = tf.is_active
                feature_data['config'] = tf.config or {}
                feature_data['enabled_at'] = tf.enabled_at.isoformat() if tf.enabled_at else None
                feature_data['expires_at'] = tf.expires_at.isoformat() if tf.expires_at else None
            
            features.append(feature_data)
        
        return features
    
    @staticmethod
    def enable_feature(
        feature_key: str,
        tenant: Tenant = None,
        config: Dict = None,
        expires_at: datetime = None
    ) -> bool:
        """
        Enable a feature for tenant
        
        Args:
            feature_key: Feature to enable
            tenant: Tenant (uses context if not provided)
            config: Feature-specific configuration
            expires_at: Optional expiration date
            
        Returns:
            True if successful
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return False
        
        # Check if feature exists in definitions
        if feature_key not in FEATURE_DEFINITIONS:
            logger.warning(f"Unknown feature: {feature_key}")
            return False
        
        # Find or create feature
        feature = TenantFeature.query.filter(
            TenantFeature.tenant_id == tenant.id,
            TenantFeature.feature_key == feature_key
        ).first()
        
        if feature:
            feature.enable(expires_at)
            if config:
                feature.config = config
        else:
            feature = TenantFeature(
                tenant_id=tenant.id,
                feature_key=feature_key,
                is_enabled=True,
                enabled_at=datetime.utcnow(),
                expires_at=expires_at,
                config=config or {},
            )
            db.session.add(feature)
        
        db.session.commit()
        
        logger.info(f"Enabled feature {feature_key} for tenant {tenant.slug}")
        return True
    
    @staticmethod
    def disable_feature(feature_key: str, tenant: Tenant = None) -> bool:
        """
        Disable a feature for tenant
        
        Args:
            feature_key: Feature to disable
            tenant: Tenant (uses context if not provided)
            
        Returns:
            True if successful
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return False
        
        feature = TenantFeature.query.filter(
            TenantFeature.tenant_id == tenant.id,
            TenantFeature.feature_key == feature_key
        ).first()
        
        if feature:
            feature.disable()
            db.session.commit()
            
            logger.info(f"Disabled feature {feature_key} for tenant {tenant.slug}")
            return True
        
        return False
    
    @staticmethod
    def update_feature_config(
        feature_key: str,
        config: Dict[str, Any],
        tenant: Tenant = None
    ) -> bool:
        """
        Update feature configuration
        
        Args:
            feature_key: Feature to update
            config: New configuration
            tenant: Tenant (uses context if not provided)
            
        Returns:
            True if successful
        """
        if tenant is None:
            tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return False
        
        feature = TenantFeature.query.filter(
            TenantFeature.tenant_id == tenant.id,
            TenantFeature.feature_key == feature_key
        ).first()
        
        if feature:
            feature.config = {**(feature.config or {}), **config}
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def sync_tier_features(tenant: Tenant):
        """
        Sync features based on tenant tier
        
        Enables features for current tier, disables others
        """
        tier_features = get_features_for_tier(tenant.tier)
        
        # Process each defined feature
        for key in FEATURE_DEFINITIONS.keys():
            if key in tier_features:
                FeatureService.enable_feature(key, tenant)
            else:
                FeatureService.disable_feature(key, tenant)
        
        logger.info(f"Synced features for tenant {tenant.slug} (tier: {tenant.tier})")


class FeatureGuard:
    """Decorator for feature-gated functionality"""
    
    @staticmethod
    def require(feature_key: str):
        """
        Decorator to require a feature
        
        Usage:
            @FeatureGuard.require('api_access')
            def api_endpoint(...):
                ...
        """
        def decorator(f):
            from functools import wraps
            
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not FeatureService.is_enabled(feature_key):
                    from flask import jsonify
                    return jsonify({
                        'success': False,
                        'error': f'Feature not available: {feature_key}',
                        'code': 'FEATURE_NOT_AVAILABLE',
                    }), 403
                
                return f(*args, **kwargs)
            
            return wrapped
        return decorator
```

---

## TASK 9: API ROUTES

### 9.1 Tenant Settings Routes

**File:** `backend/app/tenancy/routes/settings.py`

```python
"""
Tenant Settings Routes
API endpoints for tenant settings management
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.extensions import db
from app.tenancy.models.tenant_settings import TenantSettings
from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.core.tenant_middleware import require_tenant

logger = logging.getLogger(__name__)

settings_bp = Blueprint('tenant_settings', __name__, url_prefix='/api/v1/tenant')


@settings_bp.route('/settings', methods=['GET'])
@jwt_required()
@require_tenant
def get_settings():
    """Get current tenant settings"""
    tenant = TenantContext.get_current_tenant()
    
    return jsonify({
        'success': True,
        'tenant': tenant.to_dict(include_settings=True),
    })


@settings_bp.route('/settings', methods=['PUT'])
@jwt_required()
@require_tenant
def update_settings():
    """Update tenant settings"""
    tenant = TenantContext.get_current_tenant()
    
    if not tenant.settings:
        return jsonify({'success': False, 'error': 'Settings not found'}), 404
    
    data = request.get_json()
    settings = tenant.settings
    
    # Update allowed fields
    if 'locale' in data:
        locale = data['locale']
        if 'language' in locale:
            settings.default_language = locale['language']
        if 'timezone' in locale:
            settings.default_timezone = locale['timezone']
        if 'currency' in locale:
            settings.default_currency = locale['currency']
        if 'date_format' in locale:
            settings.date_format = locale['date_format']
        if 'number_format' in locale:
            settings.number_format = locale['number_format']
    
    if 'email' in data:
        email = data['email']
        if 'from_name' in email:
            settings.email_from_name = email['from_name']
        if 'from_address' in email:
            settings.email_from_address = email['from_address']
        if 'reply_to' in email:
            settings.email_reply_to = email['reply_to']
    
    if 'notification_settings' in data:
        settings.notification_settings = data['notification_settings']
    
    if 'custom_settings' in data:
        settings.custom_settings = {
            **(settings.custom_settings or {}),
            **data['custom_settings']
        }
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'settings': settings.to_dict(),
    })


@settings_bp.route('/settings/branding', methods=['PUT'])
@jwt_required()
@require_tenant
def update_branding():
    """Update tenant branding"""
    tenant = TenantContext.get_current_tenant()
    
    if not tenant.settings:
        return jsonify({'success': False, 'error': 'Settings not found'}), 404
    
    data = request.get_json()
    settings = tenant.settings
    
    if 'logo_url' in data:
        settings.logo_url = data['logo_url']
    if 'logo_dark_url' in data:
        settings.logo_dark_url = data['logo_dark_url']
    if 'favicon_url' in data:
        settings.favicon_url = data['favicon_url']
    if 'primary_color' in data:
        settings.primary_color = data['primary_color']
    if 'secondary_color' in data:
        settings.secondary_color = data['secondary_color']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'branding': settings.get_branding(),
    })


@settings_bp.route('/settings/security', methods=['PUT'])
@jwt_required()
@require_tenant
def update_security():
    """Update tenant security settings"""
    tenant = TenantContext.get_current_tenant()
    
    if not tenant.settings:
        return jsonify({'success': False, 'error': 'Settings not found'}), 404
    
    data = request.get_json()
    settings = tenant.settings
    
    if 'password_policy' in data:
        settings.password_policy = data['password_policy']
    if 'session_timeout_minutes' in data:
        settings.session_timeout_minutes = data['session_timeout_minutes']
    if 'mfa_required' in data:
        settings.mfa_required = data['mfa_required']
    if 'ip_whitelist' in data:
        settings.ip_whitelist = data['ip_whitelist']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'security': {
            'password_policy': settings.effective_password_policy,
            'session_timeout_minutes': settings.session_timeout_minutes,
            'mfa_required': settings.mfa_required,
            'ip_whitelist': settings.ip_whitelist or [],
        },
    })


@settings_bp.route('/quotas', methods=['GET'])
@jwt_required()
@require_tenant
def get_quotas():
    """Get current quota usage"""
    tenant = TenantContext.get_current_tenant()
    
    from app.tenancy.services.quota_service import QuotaService
    
    usage = QuotaService.get_usage_summary(tenant)
    alerts = QuotaService.get_quota_alerts(tenant)
    
    return jsonify({
        'success': True,
        'usage': usage,
        'alerts': alerts,
    })


@settings_bp.route('/features', methods=['GET'])
@jwt_required()
@require_tenant
def get_features():
    """Get enabled features"""
    from app.tenancy.services.feature_service import FeatureService
    
    features = FeatureService.get_all_features()
    
    return jsonify({
        'success': True,
        'features': features,
    })


@settings_bp.route('/features/<feature_key>', methods=['GET'])
@jwt_required()
@require_tenant
def get_feature(feature_key):
    """Check if specific feature is enabled"""
    from app.tenancy.services.feature_service import FeatureService
    
    feature = FeatureService.get_feature(feature_key)
    is_enabled = FeatureService.is_enabled(feature_key)
    
    return jsonify({
        'success': True,
        'feature_key': feature_key,
        'is_enabled': is_enabled,
        'details': feature,
    })
```

### 9.2 Subscription Routes

**File:** `backend/app/tenancy/routes/subscriptions.py`

```python
"""
Subscription Routes
API endpoints for subscription management
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required
import logging

from app.extensions import db
from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.core.tenant_middleware import require_tenant
from app.tenancy.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/api/v1/tenant')


@subscriptions_bp.route('/subscription', methods=['GET'])
@jwt_required()
@require_tenant
def get_subscription():
    """Get current subscription"""
    tenant = TenantContext.get_current_tenant()
    
    if not tenant.subscription:
        return jsonify({'success': False, 'error': 'No subscription'}), 404
    
    return jsonify({
        'success': True,
        'subscription': tenant.subscription.to_dict(),
        'tier': tenant.tier,
    })


@subscriptions_bp.route('/subscription/upgrade', methods=['POST'])
@jwt_required()
@require_tenant
def upgrade_subscription():
    """Upgrade subscription plan"""
    tenant = TenantContext.get_current_tenant()
    
    data = request.get_json()
    new_tier = data.get('tier')
    
    if not new_tier:
        return jsonify({'success': False, 'error': 'tier required'}), 400
    
    # Validate tier upgrade path
    tier_order = ['free', 'standard', 'professional', 'business', 'enterprise']
    current_idx = tier_order.index(tenant.tier) if tenant.tier in tier_order else 0
    new_idx = tier_order.index(new_tier) if new_tier in tier_order else 0
    
    if new_idx <= current_idx:
        return jsonify({
            'success': False,
            'error': 'Cannot upgrade to same or lower tier'
        }), 400
    
    # Process upgrade
    success = TenantService.change_tier(str(tenant.id), new_tier)
    
    if success:
        # Reload tenant
        tenant = TenantService.get_tenant(str(tenant.id))
        
        return jsonify({
            'success': True,
            'message': f'Upgraded to {new_tier}',
            'subscription': tenant.subscription.to_dict() if tenant.subscription else None,
        })
    
    return jsonify({'success': False, 'error': 'Upgrade failed'}), 500


@subscriptions_bp.route('/subscription/downgrade', methods=['POST'])
@jwt_required()
@require_tenant
def downgrade_subscription():
    """Downgrade subscription plan"""
    tenant = TenantContext.get_current_tenant()
    
    data = request.get_json()
    new_tier = data.get('tier')
    
    if not new_tier:
        return jsonify({'success': False, 'error': 'tier required'}), 400
    
    # Check if current usage fits in new tier
    from app.tenancy.services.quota_service import QuotaService
    
    new_quotas = TenantService._get_quotas_for_tier(new_tier)
    
    # Validate usage fits
    if tenant.quotas:
        for resource in ['users', 'products', 'projects', 'integrations']:
            current = getattr(tenant.quotas, f'current_{resource}', 0) or 0
            new_limit = new_quotas.get(f'max_{resource}')
            
            if new_limit is not None and current > new_limit:
                return jsonify({
                    'success': False,
                    'error': f'Current {resource} usage ({current}) exceeds new plan limit ({new_limit})',
                    'code': 'USAGE_EXCEEDS_LIMIT',
                }), 400
    
    # Process downgrade
    success = TenantService.change_tier(str(tenant.id), new_tier)
    
    if success:
        tenant = TenantService.get_tenant(str(tenant.id))
        
        return jsonify({
            'success': True,
            'message': f'Downgraded to {new_tier}',
            'subscription': tenant.subscription.to_dict() if tenant.subscription else None,
        })
    
    return jsonify({'success': False, 'error': 'Downgrade failed'}), 500


@subscriptions_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
@require_tenant
def cancel_subscription():
    """Cancel subscription"""
    tenant = TenantContext.get_current_tenant()
    
    if not tenant.subscription:
        return jsonify({'success': False, 'error': 'No subscription'}), 404
    
    data = request.get_json() or {}
    immediate = data.get('immediate', False)
    
    tenant.subscription.cancel(immediate=immediate)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Subscription cancelled',
        'effective_date': tenant.subscription.current_period_end.isoformat() if not immediate else 'immediate',
    })


@subscriptions_bp.route('/plans', methods=['GET'])
def list_plans():
    """List available subscription plans (public)"""
    plans = [
        {
            'id': 'free',
            'name': 'Free',
            'description': 'For individuals getting started',
            'price': {'monthly': 0, 'annual': 0},
            'limits': {
                'users': 2,
                'storage': '100 MB',
                'invoices': '10/month',
                'products': 50,
            },
            'features': ['Basic Invoicing'],
        },
        {
            'id': 'standard',
            'name': 'Standard',
            'description': 'For small businesses',
            'price': {'monthly': 29, 'annual': 290},
            'limits': {
                'users': 5,
                'storage': '1 GB',
                'invoices': '100/month',
                'products': 500,
            },
            'features': ['Basic Invoicing', 'Inventory', 'Reports'],
        },
        {
            'id': 'professional',
            'name': 'Professional',
            'description': 'For growing businesses',
            'price': {'monthly': 79, 'annual': 790},
            'limits': {
                'users': 15,
                'storage': '5 GB',
                'invoices': '500/month',
                'products': 2000,
            },
            'features': ['Basic Invoicing', 'Inventory', 'Reports', 'Projects', 'API Access'],
        },
        {
            'id': 'business',
            'name': 'Business',
            'description': 'For larger organizations',
            'price': {'monthly': 199, 'annual': 1990},
            'limits': {
                'users': 50,
                'storage': '20 GB',
                'invoices': '2000/month',
                'products': 10000,
            },
            'features': ['All Professional features', 'Audit Trail', 'SSO', 'Custom Domain'],
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'description': 'For large enterprises',
            'price': {'monthly': None, 'annual': None},
            'limits': {
                'users': 'Unlimited',
                'storage': 'Unlimited',
                'invoices': 'Unlimited',
                'products': 'Unlimited',
            },
            'features': ['All Business features', 'Dedicated Database', 'Priority Support', 'Custom SLA'],
            'contact_sales': True,
        },
    ]
    
    return jsonify({
        'success': True,
        'plans': plans,
    })
```

---

## Continue to Part 3 for Frontend Components

---

*Phase 16 Tasks Part 2 - LogiAccounting Pro*
*Services & Provisioning*
