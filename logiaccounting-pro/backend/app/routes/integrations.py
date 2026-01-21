"""
Phase 14: Integration Routes
API endpoints for managing external integrations
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field

from app.utils.auth import get_current_user, require_roles
from app.services.integrations.integration_service import IntegrationService
from app.models.integrations_store import integrations_store, sync_configs_store

router = APIRouter()


# ==================== Pydantic Schemas ====================

class IntegrationCreate(BaseModel):
    provider: str
    name: Optional[str] = None
    config: Optional[dict] = None


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    settings: Optional[dict] = None


class OAuthInitiate(BaseModel):
    provider: str
    redirect_uri: str
    extra_params: Optional[dict] = None


class OAuthCallback(BaseModel):
    code: str
    state: str
    redirect_uri: str


class SyncConfigCreate(BaseModel):
    entity_type: str
    direction: str = 'bidirectional'
    remote_entity: Optional[str] = None
    sync_interval: int = 3600
    conflict_resolution: str = 'last_write_wins'


class SyncConfigUpdate(BaseModel):
    direction: Optional[str] = None
    sync_interval: Optional[int] = None
    conflict_resolution: Optional[str] = None
    enabled: Optional[bool] = None
    filters: Optional[dict] = None
    settings: Optional[dict] = None


class FieldMappingCreate(BaseModel):
    local_field: str
    remote_field: str
    transform_type: str = 'direct'
    transform_config: Optional[dict] = None
    direction: str = 'bidirectional'


class FieldMappingUpdate(BaseModel):
    local_field: Optional[str] = None
    remote_field: Optional[str] = None
    transform_type: Optional[str] = None
    transform_config: Optional[dict] = None
    direction: Optional[str] = None


class WebhookCreate(BaseModel):
    event_types: List[str]
    url: str
    secret: Optional[str] = None


class SyncRequest(BaseModel):
    entity_type: Optional[str] = None
    full_sync: bool = False


# ==================== Provider Endpoints ====================

@router.get("/providers")
async def list_providers(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all available integration providers"""
    providers = IntegrationService.list_available_providers()

    if category:
        providers = [p for p in providers if p['category'] == category]

    return {"providers": providers}


@router.get("/providers/{provider}")
async def get_provider(
    provider: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed info about a provider"""
    info = IntegrationService.get_provider_info(provider)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider not found: {provider}"
        )
    return info


# ==================== Integration CRUD ====================

@router.get("")
async def list_integrations(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all integrations for the organization"""
    organization_id = current_user.get('organization_id', current_user['id'])

    integrations = IntegrationService.list_integrations(
        organization_id=organization_id,
        category=category
    )

    return {"integrations": integrations}


@router.get("/{integration_id}")
async def get_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get integration details"""
    integration = IntegrationService.get_integration(integration_id)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    return integration


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: IntegrationCreate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Create a new integration"""
    organization_id = current_user.get('organization_id', current_user['id'])

    try:
        integration = IntegrationService.create_integration(
            organization_id=organization_id,
            provider=data.provider,
            name=data.name,
            config=data.config
        )
        return integration
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{integration_id}")
async def update_integration(
    integration_id: str,
    data: IntegrationUpdate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Update integration settings"""
    integration = IntegrationService.update_integration(
        integration_id=integration_id,
        data=data.model_dump(exclude_unset=True)
    )

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    return integration


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete an integration"""
    success = IntegrationService.delete_integration(integration_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    return {"message": "Integration deleted successfully"}


# ==================== OAuth Endpoints ====================

@router.post("/oauth/initiate")
async def initiate_oauth(
    data: OAuthInitiate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Initiate OAuth flow for a provider"""
    organization_id = current_user.get('organization_id', current_user['id'])

    try:
        authorization_url = IntegrationService.initiate_oauth(
            organization_id=organization_id,
            provider=data.provider,
            user_id=current_user['id'],
            redirect_uri=data.redirect_uri,
            extra_params=data.extra_params
        )

        return {"authorization_url": authorization_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/oauth/callback/{provider}")
async def oauth_callback(
    provider: str,
    data: OAuthCallback,
    current_user: dict = Depends(get_current_user)
):
    """Handle OAuth callback"""
    try:
        integration = await IntegrationService.complete_oauth(
            provider=provider,
            code=data.code,
            state=data.state,
            redirect_uri=data.redirect_uri
        )

        return {
            "message": "OAuth completed successfully",
            "integration": integration
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth failed: {str(e)}"
        )


@router.post("/{integration_id}/refresh-token")
async def refresh_token(
    integration_id: str,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Refresh OAuth token for an integration"""
    success = await IntegrationService.refresh_token(integration_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token refresh failed"
        )

    return {"message": "Token refreshed successfully"}


# ==================== Connection Test ====================

@router.post("/{integration_id}/test")
async def test_connection(
    integration_id: str,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Test integration connection"""
    success, message = await IntegrationService.test_connection(integration_id)

    return {
        "success": success,
        "message": message
    }


# ==================== Sync Configuration ====================

@router.get("/{integration_id}/sync-configs")
async def list_sync_configs(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List sync configurations for an integration"""
    configs = sync_configs_store.find_by_integration(integration_id)
    return {"sync_configs": configs}


@router.post("/{integration_id}/sync-configs", status_code=status.HTTP_201_CREATED)
async def create_sync_config(
    integration_id: str,
    data: SyncConfigCreate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Create a sync configuration"""
    try:
        config = IntegrationService.create_sync_config(
            integration_id=integration_id,
            entity_type=data.entity_type,
            direction=data.direction,
            remote_entity=data.remote_entity,
            sync_interval=data.sync_interval,
            conflict_resolution=data.conflict_resolution
        )
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{integration_id}/sync-configs/{config_id}")
async def update_sync_config(
    integration_id: str,
    config_id: str,
    data: SyncConfigUpdate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Update a sync configuration"""
    config = IntegrationService.update_sync_config(
        sync_config_id=config_id,
        data=data.model_dump(exclude_unset=True)
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync config not found"
        )

    return config


@router.delete("/{integration_id}/sync-configs/{config_id}")
async def delete_sync_config(
    integration_id: str,
    config_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete a sync configuration"""
    success = IntegrationService.delete_sync_config(config_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync config not found"
        )

    return {"message": "Sync config deleted successfully"}


# ==================== Field Mappings ====================

@router.get("/{integration_id}/sync-configs/{config_id}/mappings")
async def list_field_mappings(
    integration_id: str,
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List field mappings for a sync config"""
    mappings = IntegrationService.get_field_mappings(config_id)
    return {"mappings": mappings}


@router.post("/{integration_id}/sync-configs/{config_id}/mappings", status_code=status.HTTP_201_CREATED)
async def create_field_mapping(
    integration_id: str,
    config_id: str,
    data: FieldMappingCreate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Create a field mapping"""
    mapping = IntegrationService.create_field_mapping(
        sync_config_id=config_id,
        local_field=data.local_field,
        remote_field=data.remote_field,
        transform_type=data.transform_type,
        transform_config=data.transform_config,
        direction=data.direction
    )
    return mapping


@router.patch("/{integration_id}/sync-configs/{config_id}/mappings/{mapping_id}")
async def update_field_mapping(
    integration_id: str,
    config_id: str,
    mapping_id: str,
    data: FieldMappingUpdate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Update a field mapping"""
    mapping = IntegrationService.update_field_mapping(
        mapping_id=mapping_id,
        data=data.model_dump(exclude_unset=True)
    )

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field mapping not found"
        )

    return mapping


@router.delete("/{integration_id}/sync-configs/{config_id}/mappings/{mapping_id}")
async def delete_field_mapping(
    integration_id: str,
    config_id: str,
    mapping_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete a field mapping"""
    success = IntegrationService.delete_field_mapping(mapping_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field mapping not found"
        )

    return {"message": "Field mapping deleted successfully"}


# ==================== Synchronization ====================

@router.post("/{integration_id}/sync")
async def trigger_sync(
    integration_id: str,
    data: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Trigger sync for an integration"""
    integration = integrations_store.find_by_id(integration_id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )

    if data.entity_type:
        # Sync specific entity
        background_tasks.add_task(
            IntegrationService.sync_entity,
            integration_id,
            data.entity_type,
            data.full_sync
        )
        return {"message": f"Sync started for entity: {data.entity_type}"}
    else:
        # Sync all entities
        background_tasks.add_task(
            IntegrationService.sync_all,
            integration_id,
            data.full_sync
        )
        return {"message": "Sync started for all entities"}


@router.get("/{integration_id}/sync-logs")
async def get_sync_logs(
    integration_id: str,
    limit: int = 20,
    entity_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get sync logs for an integration"""
    from app.models.integrations_store import sync_logs_store

    logs = sync_logs_store.find_by_integration(integration_id, limit=limit)

    if entity_type:
        logs = [log for log in logs if log.get('entity_type') == entity_type]

    return {"sync_logs": logs}


@router.get("/{integration_id}/sync-logs/{log_id}")
async def get_sync_log(
    integration_id: str,
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed sync log"""
    from app.models.integrations_store import sync_logs_store, sync_records_store

    log = sync_logs_store.find_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync log not found"
        )

    # Get sync records
    log['records'] = sync_records_store.find_by_sync_log(log_id)

    return log


# ==================== Webhooks ====================

@router.get("/{integration_id}/webhooks")
async def list_webhooks(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List webhooks for an integration"""
    from app.models.integrations_store import webhooks_store

    webhooks = webhooks_store.find_by_integration(integration_id)
    return {"webhooks": webhooks}


@router.post("/{integration_id}/webhooks", status_code=status.HTTP_201_CREATED)
async def create_webhook(
    integration_id: str,
    data: WebhookCreate,
    current_user: dict = Depends(require_roles(["admin", "accountant"]))
):
    """Create a webhook"""
    webhook = IntegrationService.register_webhook(
        integration_id=integration_id,
        event_types=data.event_types,
        url=data.url,
        secret=data.secret
    )
    return webhook


@router.delete("/{integration_id}/webhooks/{webhook_id}")
async def delete_webhook(
    integration_id: str,
    webhook_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete a webhook"""
    from app.models.integrations_store import webhooks_store

    success = webhooks_store.delete(webhook_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return {"message": "Webhook deleted successfully"}


# ==================== Incoming Webhooks ====================

@router.post("/webhooks/{provider}/{integration_id}")
async def handle_incoming_webhook(
    provider: str,
    integration_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle incoming webhook from provider"""
    try:
        body = await request.json()
    except:
        body = {}

    headers = dict(request.headers)

    # Determine event type from provider-specific headers/body
    event_type = _extract_event_type(provider, headers, body)

    # Process webhook in background
    background_tasks.add_task(
        IntegrationService.process_webhook,
        integration_id,
        event_type,
        body,
        headers
    )

    return {"status": "received"}


def _extract_event_type(provider: str, headers: dict, body: dict) -> str:
    """Extract event type from webhook payload"""
    if provider == 'shopify':
        return headers.get('x-shopify-topic', 'unknown')
    elif provider == 'stripe':
        return body.get('type', 'unknown')
    elif provider == 'quickbooks':
        return body.get('eventNotifications', [{}])[0].get('dataChangeEvent', {}).get('entities', [{}])[0].get('operation', 'unknown')
    elif provider == 'hubspot':
        return body.get('subscriptionType', 'unknown')
    elif provider == 'salesforce':
        return headers.get('x-sfdc-event-type', body.get('event', {}).get('type', 'unknown'))
    elif provider == 'xero':
        return body.get('events', [{}])[0].get('eventType', 'unknown')
    elif provider == 'plaid':
        return body.get('webhook_type', 'unknown') + '.' + body.get('webhook_code', '')
    else:
        return body.get('event', body.get('type', 'unknown'))


# ==================== Data Access ====================

@router.get("/{integration_id}/entities/{entity_type}")
async def list_remote_records(
    integration_id: str,
    entity_type: str,
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """List records from remote system"""
    connector = IntegrationService.get_connector(integration_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found or connector unavailable"
        )

    try:
        records, has_more = await connector.list_records(
            entity_name=entity_type,
            page=page,
            page_size=page_size
        )

        return {
            "records": records,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch records: {str(e)}"
        )


@router.get("/{integration_id}/entities/{entity_type}/{record_id}")
async def get_remote_record(
    integration_id: str,
    entity_type: str,
    record_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific record from remote system"""
    connector = IntegrationService.get_connector(integration_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found or connector unavailable"
        )

    try:
        record = await connector.get_record(entity_type, record_id)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found"
            )

        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch record: {str(e)}"
        )


@router.get("/{integration_id}/schema/{entity_type}")
async def get_entity_schema(
    integration_id: str,
    entity_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schema for a remote entity"""
    connector = IntegrationService.get_connector(integration_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found or connector unavailable"
        )

    schema = connector.get_entity_schema(entity_type)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found for entity: {entity_type}"
        )

    return {
        "name": schema.name,
        "label": schema.label,
        "id_field": schema.id_field,
        "supports_bulk": schema.supports_bulk,
        "fields": [
            {
                "name": f.name,
                "label": f.label,
                "type": f.type,
                "required": f.required,
                "readonly": f.readonly,
            }
            for f in schema.fields
        ]
    }
