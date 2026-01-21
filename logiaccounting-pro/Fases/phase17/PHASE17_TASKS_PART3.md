# LogiAccounting Pro - Phase 17 Tasks Part 3

## API ROUTES & FRONTEND

---

## TASK 10: API KEY ROUTES

### 10.1 API Key Management Endpoints

**File:** `backend/app/gateway/routes/api_keys.py`

```python
"""
API Key Routes
Endpoints for API key management
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.gateway.services.api_key_service import APIKeyService
from app.gateway.models.api_key import APIKey
from app.tenancy.core.tenant_middleware import require_tenant

logger = logging.getLogger(__name__)

api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api/v1/api-keys')


@api_keys_bp.route('', methods=['GET'])
@jwt_required()
@require_tenant
def list_api_keys():
    """List API keys for current tenant"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
    environment = request.args.get('environment')
    
    keys, total = APIKeyService.list_api_keys(
        is_active=is_active,
        environment=environment,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'success': True,
        'api_keys': [k.to_dict() for k in keys],
        'total': total,
        'page': page,
        'per_page': per_page,
    })


@api_keys_bp.route('', methods=['POST'])
@jwt_required()
@require_tenant
def create_api_key():
    """Create a new API key"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'name required'}), 400
    
    try:
        result = APIKeyService.create_api_key(
            name=name,
            description=data.get('description'),
            scopes=data.get('scopes'),
            environment=data.get('environment', 'production'),
            expires_in_days=data.get('expires_in_days'),
            allowed_ips=data.get('allowed_ips'),
            rate_limit_per_minute=data.get('rate_limit_per_minute'),
            created_by=user_id,
        )
        
        # Include the raw key in response (only shown once!)
        response_data = result['api_key'].to_dict()
        response_data['key'] = result['raw_key']
        
        return jsonify({
            'success': True,
            'api_key': response_data,
            'warning': 'Save this key now. It will not be shown again.',
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_keys_bp.route('/<key_id>', methods=['GET'])
@jwt_required()
@require_tenant
def get_api_key(key_id):
    """Get API key details"""
    api_key = APIKeyService.get_api_key(key_id)
    
    if not api_key:
        return jsonify({'success': False, 'error': 'API key not found'}), 404
    
    return jsonify({
        'success': True,
        'api_key': api_key.to_dict(),
    })


@api_keys_bp.route('/<key_id>', methods=['PUT'])
@jwt_required()
@require_tenant
def update_api_key(key_id):
    """Update API key"""
    data = request.get_json()
    
    try:
        api_key = APIKeyService.update_api_key(
            key_id,
            name=data.get('name'),
            description=data.get('description'),
            scopes=data.get('scopes'),
            allowed_ips=data.get('allowed_ips'),
            rate_limit_per_minute=data.get('rate_limit_per_minute'),
            is_active=data.get('is_active'),
        )
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key not found'}), 404
        
        return jsonify({
            'success': True,
            'api_key': api_key.to_dict(),
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_keys_bp.route('/<key_id>', methods=['DELETE'])
@jwt_required()
@require_tenant
def delete_api_key(key_id):
    """Delete API key"""
    success = APIKeyService.delete_api_key(key_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'API key not found'}), 404
    
    return jsonify({
        'success': True,
        'message': 'API key deleted',
    })


@api_keys_bp.route('/<key_id>/regenerate', methods=['POST'])
@jwt_required()
@require_tenant
def regenerate_api_key(key_id):
    """Regenerate API key (new key value)"""
    result = APIKeyService.regenerate_api_key(key_id)
    
    if not result:
        return jsonify({'success': False, 'error': 'API key not found'}), 404
    
    response_data = result['api_key'].to_dict()
    response_data['key'] = result['raw_key']
    
    return jsonify({
        'success': True,
        'api_key': response_data,
        'warning': 'Save this new key now. The old key is now invalid.',
    })


@api_keys_bp.route('/<key_id>/revoke', methods=['POST'])
@jwt_required()
@require_tenant
def revoke_api_key(key_id):
    """Revoke (deactivate) API key"""
    success = APIKeyService.revoke_api_key(key_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'API key not found'}), 404
    
    return jsonify({
        'success': True,
        'message': 'API key revoked',
    })


@api_keys_bp.route('/<key_id>/usage', methods=['GET'])
@jwt_required()
@require_tenant
def get_api_key_usage(key_id):
    """Get usage statistics for API key"""
    days = request.args.get('days', 30, type=int)
    
    stats = APIKeyService.get_usage_stats(key_id, days=days)
    
    if not stats:
        return jsonify({'success': False, 'error': 'API key not found'}), 404
    
    return jsonify({
        'success': True,
        'usage': stats,
    })


@api_keys_bp.route('/scopes', methods=['GET'])
@jwt_required()
def list_available_scopes():
    """List all available API scopes"""
    scopes = [
        {'scope': s, 'description': _get_scope_description(s)}
        for s in APIKey.AVAILABLE_SCOPES
    ]
    
    return jsonify({
        'success': True,
        'scopes': scopes,
    })


def _get_scope_description(scope: str) -> str:
    """Get human-readable description for scope"""
    descriptions = {
        'invoices:read': 'View invoices',
        'invoices:write': 'Create and update invoices',
        'inventory:read': 'View products and inventory',
        'inventory:write': 'Manage products and inventory',
        'customers:read': 'View customers',
        'customers:write': 'Manage customers',
        'suppliers:read': 'View suppliers',
        'suppliers:write': 'Manage suppliers',
        'projects:read': 'View projects',
        'projects:write': 'Manage projects',
        'payments:read': 'View payments',
        'payments:write': 'Process payments',
        'reports:read': 'Generate reports',
        'documents:read': 'View documents',
        'documents:write': 'Upload and manage documents',
        'webhooks:manage': 'Manage webhooks',
        '*': 'Full access to all resources',
    }
    return descriptions.get(scope, scope)
```

---

## TASK 11: WEBHOOK ROUTES

### 11.1 Webhook Management Endpoints

**File:** `backend/app/webhooks/routes/webhooks.py`

```python
"""
Webhook Routes
Endpoints for webhook management
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.extensions import db
from app.webhooks.models.webhook_endpoint import WebhookEndpoint, WebhookEventType
from app.webhooks.models.webhook_delivery import WebhookDelivery
from app.webhooks.core.delivery_manager import DeliveryManager
from app.webhooks.core.event_types import EVENT_DEFINITIONS, get_all_categories
from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.core.tenant_middleware import require_tenant

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/v1/webhooks')


@webhooks_bp.route('', methods=['GET'])
@jwt_required()
@require_tenant
def list_webhooks():
    """List webhook endpoints"""
    tenant = TenantContext.get_current_tenant()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
    
    query = WebhookEndpoint.query.filter(WebhookEndpoint.tenant_id == tenant.id)
    
    if is_active is not None:
        query = query.filter(WebhookEndpoint.is_active == is_active)
    
    query = query.order_by(WebhookEndpoint.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'webhooks': [w.to_dict() for w in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@webhooks_bp.route('', methods=['POST'])
@jwt_required()
@require_tenant
def create_webhook():
    """Create a new webhook endpoint"""
    tenant = TenantContext.get_current_tenant()
    user_id = get_jwt_identity()
    
    data = request.get_json()
    
    # Validate required fields
    name = data.get('name')
    url = data.get('url')
    events = data.get('events', [])
    
    if not name:
        return jsonify({'success': False, 'error': 'name required'}), 400
    if not url:
        return jsonify({'success': False, 'error': 'url required'}), 400
    if not events:
        return jsonify({'success': False, 'error': 'events required'}), 400
    
    # Validate URL
    if not url.startswith('https://'):
        return jsonify({'success': False, 'error': 'URL must use HTTPS'}), 400
    
    # Validate events
    valid_events = list(EVENT_DEFINITIONS.keys()) + ['*']
    invalid = [e for e in events if e not in valid_events and not e.endswith('.*')]
    if invalid:
        return jsonify({'success': False, 'error': f'Invalid events: {invalid}'}), 400
    
    # Create webhook
    webhook = WebhookEndpoint(
        tenant_id=tenant.id,
        name=name,
        description=data.get('description'),
        url=url,
        events=events,
        custom_headers=data.get('custom_headers'),
        content_type=data.get('content_type', 'application/json'),
        timeout_seconds=data.get('timeout_seconds', 30),
        max_retries=data.get('max_retries', 5),
        created_by=user_id,
    )
    
    db.session.add(webhook)
    db.session.commit()
    
    logger.info(f"Created webhook: {webhook.id} for tenant {tenant.slug}")
    
    return jsonify({
        'success': True,
        'webhook': webhook.to_dict(include_secret=True),
        'warning': 'Save the secret now. It will not be shown in full again.',
    }), 201


@webhooks_bp.route('/<webhook_id>', methods=['GET'])
@jwt_required()
@require_tenant
def get_webhook(webhook_id):
    """Get webhook details"""
    tenant = TenantContext.get_current_tenant()
    
    webhook = WebhookEndpoint.query.filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant.id
    ).first()
    
    if not webhook:
        return jsonify({'success': False, 'error': 'Webhook not found'}), 404
    
    return jsonify({
        'success': True,
        'webhook': webhook.to_dict(),
    })


@webhooks_bp.route('/<webhook_id>', methods=['PUT'])
@jwt_required()
@require_tenant
def update_webhook(webhook_id):
    """Update webhook endpoint"""
    tenant = TenantContext.get_current_tenant()
    
    webhook = WebhookEndpoint.query.filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant.id
    ).first()
    
    if not webhook:
        return jsonify({'success': False, 'error': 'Webhook not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        webhook.name = data['name']
    if 'description' in data:
        webhook.description = data['description']
    if 'url' in data:
        if not data['url'].startswith('https://'):
            return jsonify({'success': False, 'error': 'URL must use HTTPS'}), 400
        webhook.url = data['url']
    if 'events' in data:
        webhook.events = data['events']
    if 'custom_headers' in data:
        webhook.custom_headers = data['custom_headers']
    if 'timeout_seconds' in data:
        webhook.timeout_seconds = data['timeout_seconds']
    if 'max_retries' in data:
        webhook.max_retries = data['max_retries']
    if 'is_active' in data:
        webhook.is_active = data['is_active']
        if data['is_active'] and webhook.disabled_at:
            webhook.reactivate()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'webhook': webhook.to_dict(),
    })


@webhooks_bp.route('/<webhook_id>', methods=['DELETE'])
@jwt_required()
@require_tenant
def delete_webhook(webhook_id):
    """Delete webhook endpoint"""
    tenant = TenantContext.get_current_tenant()
    
    webhook = WebhookEndpoint.query.filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant.id
    ).first()
    
    if not webhook:
        return jsonify({'success': False, 'error': 'Webhook not found'}), 404
    
    db.session.delete(webhook)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Webhook deleted',
    })


@webhooks_bp.route('/<webhook_id>/secret', methods=['POST'])
@jwt_required()
@require_tenant
def regenerate_secret(webhook_id):
    """Regenerate webhook signing secret"""
    tenant = TenantContext.get_current_tenant()
    
    webhook = WebhookEndpoint.query.filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant.id
    ).first()
    
    if not webhook:
        return jsonify({'success': False, 'error': 'Webhook not found'}), 404
    
    new_secret = webhook.regenerate_secret()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'secret': new_secret,
        'warning': 'Update your application with the new secret.',
    })


@webhooks_bp.route('/<webhook_id>/test', methods=['POST'])
@jwt_required()
@require_tenant
def test_webhook(webhook_id):
    """Send a test event to webhook"""
    tenant = TenantContext.get_current_tenant()
    
    webhook = WebhookEndpoint.query.filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.tenant_id == tenant.id
    ).first()
    
    if not webhook:
        return jsonify({'success': False, 'error': 'Webhook not found'}), 404
    
    result = DeliveryManager.send_test(webhook_id)
    
    return jsonify({
        'success': result.get('success', False),
        'test_result': result,
    })


@webhooks_bp.route('/<webhook_id>/deliveries', methods=['GET'])
@jwt_required()
@require_tenant
def list_deliveries(webhook_id):
    """List deliveries for a webhook"""
    tenant = TenantContext.get_current_tenant()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = WebhookDelivery.query.filter(
        WebhookDelivery.endpoint_id == webhook_id,
        WebhookDelivery.tenant_id == tenant.id
    )
    
    if status:
        query = query.filter(WebhookDelivery.status == status)
    
    query = query.order_by(WebhookDelivery.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'deliveries': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@webhooks_bp.route('/<webhook_id>/deliveries/<delivery_id>/retry', methods=['POST'])
@jwt_required()
@require_tenant
def retry_delivery(webhook_id, delivery_id):
    """Retry a failed delivery"""
    tenant = TenantContext.get_current_tenant()
    
    delivery = WebhookDelivery.query.filter(
        WebhookDelivery.id == delivery_id,
        WebhookDelivery.endpoint_id == webhook_id,
        WebhookDelivery.tenant_id == tenant.id
    ).first()
    
    if not delivery:
        return jsonify({'success': False, 'error': 'Delivery not found'}), 404
    
    if delivery.status == 'delivered':
        return jsonify({'success': False, 'error': 'Already delivered'}), 400
    
    # Reset for retry
    delivery.status = 'pending'
    delivery.next_retry_at = None
    db.session.commit()
    
    # Queue for delivery
    from app.webhooks.tasks.delivery_tasks import deliver_webhook
    deliver_webhook.delay(str(delivery.id))
    
    return jsonify({
        'success': True,
        'message': 'Delivery queued for retry',
    })


# Event Types Endpoints
@webhooks_bp.route('/events', methods=['GET'])
@jwt_required()
def list_event_types():
    """List available webhook event types"""
    category = request.args.get('category')
    
    events = []
    for event_type, definition in EVENT_DEFINITIONS.items():
        if category and definition.category.value != category:
            continue
        
        events.append({
            'event_type': event_type,
            'category': definition.category.value,
            'name': definition.name,
            'description': definition.description,
        })
    
    return jsonify({
        'success': True,
        'events': events,
        'categories': get_all_categories(),
    })


@webhooks_bp.route('/events/<event_type>', methods=['GET'])
@jwt_required()
def get_event_type(event_type):
    """Get event type details with payload schema"""
    definition = EVENT_DEFINITIONS.get(event_type)
    
    if not definition:
        return jsonify({'success': False, 'error': 'Event type not found'}), 404
    
    # Get from database for full schema
    db_event = WebhookEventType.query.filter(
        WebhookEventType.event_type == event_type
    ).first()
    
    return jsonify({
        'success': True,
        'event': {
            'event_type': event_type,
            'category': definition.category.value,
            'name': definition.name,
            'description': definition.description,
            'payload_fields': definition.payload_fields,
            'payload_schema': db_event.payload_schema if db_event else None,
            'sample_payload': db_event.sample_payload if db_event else None,
        },
    })
```

---

## TASK 12: FRONTEND - API KEYS PAGE

### 12.1 API Keys Page

**File:** `frontend/src/features/api/pages/ApiKeysPage.jsx`

```jsx
/**
 * API Keys Page
 * Manage API keys
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiKeys } from '../hooks/useApiKeys';
import ApiKeyCard from '../components/ApiKeyCard';
import ApiKeyModal from '../components/ApiKeyModal';

const ApiKeysPage = () => {
  const { t } = useTranslation();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const [newKeyValue, setNewKeyValue] = useState(null);
  
  const {
    apiKeys,
    isLoading,
    createApiKey,
    updateApiKey,
    deleteApiKey,
    regenerateApiKey,
    revokeApiKey,
  } = useApiKeys();
  
  const handleCreate = async (data) => {
    const result = await createApiKey(data);
    if (result?.key) {
      setNewKeyValue(result.key);
    }
    setShowCreateModal(false);
  };
  
  const handleRegenerate = async (keyId) => {
    if (confirm('This will invalidate the current key. Continue?')) {
      const result = await regenerateApiKey(keyId);
      if (result?.key) {
        setNewKeyValue(result.key);
      }
    }
  };
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600 mt-1">
            Manage your API keys for external integrations
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create API Key
        </button>
      </div>
      
      {/* New Key Alert */}
      {newKeyValue && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-green-900">Save Your API Key</h3>
              <p className="text-sm text-green-700 mt-1">
                This key will only be shown once. Copy it now.
              </p>
              <div className="mt-2 p-2 bg-white rounded border font-mono text-sm break-all">
                {newKeyValue}
              </div>
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(newKeyValue);
                setNewKeyValue(null);
              }}
              className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
            >
              Copy & Close
            </button>
          </div>
        </div>
      )}
      
      {/* API Keys List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : apiKeys.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No API Keys</h3>
          <p className="text-gray-500 mb-4">Create your first API key to get started</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create API Key
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {apiKeys.map((apiKey) => (
            <ApiKeyCard
              key={apiKey.id}
              apiKey={apiKey}
              onEdit={() => setSelectedKey(apiKey)}
              onRevoke={() => revokeApiKey(apiKey.id)}
              onRegenerate={() => handleRegenerate(apiKey.id)}
              onDelete={() => {
                if (confirm('Delete this API key permanently?')) {
                  deleteApiKey(apiKey.id);
                }
              }}
            />
          ))}
        </div>
      )}
      
      {/* Create Modal */}
      {showCreateModal && (
        <ApiKeyModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
        />
      )}
      
      {/* Edit Modal */}
      {selectedKey && (
        <ApiKeyModal
          apiKey={selectedKey}
          onClose={() => setSelectedKey(null)}
          onSave={(data) => {
            updateApiKey(selectedKey.id, data);
            setSelectedKey(null);
          }}
        />
      )}
    </div>
  );
};

export default ApiKeysPage;
```

### 12.2 API Key Components

**File:** `frontend/src/features/api/components/ApiKeyCard.jsx`

```jsx
/**
 * API Key Card Component
 */

import React, { useState } from 'react';

const ApiKeyCard = ({ apiKey, onEdit, onRevoke, onRegenerate, onDelete }) => {
  const [showMenu, setShowMenu] = useState(false);
  
  const getStatusBadge = () => {
    if (!apiKey.is_active) {
      return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">Revoked</span>;
    }
    if (apiKey.is_expired) {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Expired</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Active</span>;
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold text-gray-900">{apiKey.name}</h3>
            {getStatusBadge()}
            <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
              {apiKey.environment}
            </span>
          </div>
          
          <div className="font-mono text-sm text-gray-500 mb-2">
            {apiKey.key_prefix}
          </div>
          
          {apiKey.description && (
            <p className="text-sm text-gray-600 mb-3">{apiKey.description}</p>
          )}
          
          <div className="flex flex-wrap gap-2 mb-3">
            {apiKey.scopes.slice(0, 5).map((scope) => (
              <span key={scope} className="px-2 py-1 text-xs rounded bg-blue-50 text-blue-700">
                {scope}
              </span>
            ))}
            {apiKey.scopes.length > 5 && (
              <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
                +{apiKey.scopes.length - 5} more
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Created: {new Date(apiKey.created_at).toLocaleDateString()}</span>
            {apiKey.last_used_at && (
              <span>Last used: {new Date(apiKey.last_used_at).toLocaleDateString()}</span>
            )}
            <span>Requests: {apiKey.total_requests?.toLocaleString() || 0}</span>
          </div>
        </div>
        
        {/* Actions Menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
          </button>
          
          {showMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
              <button
                onClick={() => { onEdit(); setShowMenu(false); }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
              >
                Edit
              </button>
              <button
                onClick={() => { onRegenerate(); setShowMenu(false); }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
              >
                Regenerate Key
              </button>
              {apiKey.is_active && (
                <button
                  onClick={() => { onRevoke(); setShowMenu(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-yellow-600 hover:bg-gray-50"
                >
                  Revoke
                </button>
              )}
              <button
                onClick={() => { onDelete(); setShowMenu(false); }}
                className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-50"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiKeyCard;
```

---

## TASK 13: FRONTEND - WEBHOOKS PAGE

### 13.1 Webhooks Page

**File:** `frontend/src/features/api/pages/WebhooksPage.jsx`

```jsx
/**
 * Webhooks Page
 * Manage webhook endpoints
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useWebhooks } from '../hooks/useWebhooks';
import WebhookCard from '../components/WebhookCard';
import WebhookModal from '../components/WebhookModal';
import DeliveryLog from '../components/DeliveryLog';

const WebhooksPage = () => {
  const { t } = useTranslation();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState(null);
  const [showDeliveries, setShowDeliveries] = useState(null);
  
  const {
    webhooks,
    eventTypes,
    isLoading,
    createWebhook,
    updateWebhook,
    deleteWebhook,
    testWebhook,
    regenerateSecret,
  } = useWebhooks();
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
          <p className="text-gray-600 mt-1">
            Receive real-time event notifications
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Endpoint
        </button>
      </div>
      
      {/* Webhooks List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : webhooks.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Webhooks</h3>
          <p className="text-gray-500 mb-4">Add a webhook endpoint to receive event notifications</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Endpoint
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {webhooks.map((webhook) => (
            <WebhookCard
              key={webhook.id}
              webhook={webhook}
              onEdit={() => setSelectedWebhook(webhook)}
              onTest={() => testWebhook(webhook.id)}
              onViewDeliveries={() => setShowDeliveries(webhook.id)}
              onRegenerateSecret={() => {
                if (confirm('This will invalidate the current secret. Continue?')) {
                  regenerateSecret(webhook.id);
                }
              }}
              onDelete={() => {
                if (confirm('Delete this webhook endpoint?')) {
                  deleteWebhook(webhook.id);
                }
              }}
            />
          ))}
        </div>
      )}
      
      {/* Create Modal */}
      {showCreateModal && (
        <WebhookModal
          eventTypes={eventTypes}
          onClose={() => setShowCreateModal(false)}
          onSave={(data) => {
            createWebhook(data);
            setShowCreateModal(false);
          }}
        />
      )}
      
      {/* Edit Modal */}
      {selectedWebhook && (
        <WebhookModal
          webhook={selectedWebhook}
          eventTypes={eventTypes}
          onClose={() => setSelectedWebhook(null)}
          onSave={(data) => {
            updateWebhook(selectedWebhook.id, data);
            setSelectedWebhook(null);
          }}
        />
      )}
      
      {/* Deliveries Modal */}
      {showDeliveries && (
        <DeliveryLog
          webhookId={showDeliveries}
          onClose={() => setShowDeliveries(null)}
        />
      )}
    </div>
  );
};

export default WebhooksPage;
```

### 13.2 Webhook Components

**File:** `frontend/src/features/api/components/WebhookCard.jsx`

```jsx
/**
 * Webhook Card Component
 */

import React from 'react';

const WebhookCard = ({ webhook, onEdit, onTest, onViewDeliveries, onRegenerateSecret, onDelete }) => {
  const getStatusIndicator = () => {
    if (!webhook.is_active) {
      return <span className="w-3 h-3 rounded-full bg-gray-400" />;
    }
    if (!webhook.is_healthy) {
      return <span className="w-3 h-3 rounded-full bg-red-500" />;
    }
    return <span className="w-3 h-3 rounded-full bg-green-500" />;
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            {getStatusIndicator()}
            <h3 className="font-semibold text-gray-900">{webhook.name}</h3>
            {!webhook.is_active && (
              <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">Disabled</span>
            )}
            {webhook.consecutive_failures > 0 && (
              <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
                {webhook.consecutive_failures} failures
              </span>
            )}
          </div>
          
          <div className="text-sm text-gray-600 mb-2 truncate">
            {webhook.url}
          </div>
          
          <div className="flex flex-wrap gap-2 mb-3">
            {webhook.events.slice(0, 4).map((event) => (
              <span key={event} className="px-2 py-1 text-xs rounded bg-purple-50 text-purple-700">
                {event}
              </span>
            ))}
            {webhook.events.length > 4 && (
              <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
                +{webhook.events.length - 4} more
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            {webhook.last_success_at && (
              <span className="text-green-600">
                Last success: {new Date(webhook.last_success_at).toLocaleString()}
              </span>
            )}
            {webhook.last_failure_at && (
              <span className="text-red-600">
                Last failure: {new Date(webhook.last_failure_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onTest}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Test
          </button>
          <button
            onClick={onViewDeliveries}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Logs
          </button>
          <button
            onClick={onEdit}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default WebhookCard;
```

---

## TASK 14: FRONTEND HOOKS & API

### 14.1 API Keys Hook

**File:** `frontend/src/features/api/hooks/useApiKeys.js`

```javascript
/**
 * useApiKeys Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { gatewayApi } from '../api/gatewayApi';
import { toast } from 'react-hot-toast';

export const useApiKeys = () => {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => gatewayApi.getApiKeys(),
  });
  
  const createMutation = useMutation({
    mutationFn: (data) => gatewayApi.createApiKey(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries(['api-keys']);
      toast.success('API key created');
      return result;
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create API key');
    },
  });
  
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => gatewayApi.updateApiKey(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['api-keys']);
      toast.success('API key updated');
    },
  });
  
  const deleteMutation = useMutation({
    mutationFn: (id) => gatewayApi.deleteApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['api-keys']);
      toast.success('API key deleted');
    },
  });
  
  const regenerateMutation = useMutation({
    mutationFn: (id) => gatewayApi.regenerateApiKey(id),
    onSuccess: (result) => {
      queryClient.invalidateQueries(['api-keys']);
      toast.success('API key regenerated');
      return result;
    },
  });
  
  const revokeMutation = useMutation({
    mutationFn: (id) => gatewayApi.revokeApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['api-keys']);
      toast.success('API key revoked');
    },
  });
  
  return {
    apiKeys: data?.api_keys || [],
    isLoading,
    createApiKey: createMutation.mutateAsync,
    updateApiKey: (id, data) => updateMutation.mutateAsync({ id, data }),
    deleteApiKey: deleteMutation.mutateAsync,
    regenerateApiKey: regenerateMutation.mutateAsync,
    revokeApiKey: revokeMutation.mutateAsync,
  };
};
```

### 14.2 Webhooks Hook

**File:** `frontend/src/features/api/hooks/useWebhooks.js`

```javascript
/**
 * useWebhooks Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { gatewayApi } from '../api/gatewayApi';
import { toast } from 'react-hot-toast';

export const useWebhooks = () => {
  const queryClient = useQueryClient();
  
  const { data: webhooksData, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => gatewayApi.getWebhooks(),
  });
  
  const { data: eventTypesData } = useQuery({
    queryKey: ['webhook-events'],
    queryFn: () => gatewayApi.getEventTypes(),
  });
  
  const createMutation = useMutation({
    mutationFn: (data) => gatewayApi.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
      toast.success('Webhook created');
    },
  });
  
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => gatewayApi.updateWebhook(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
      toast.success('Webhook updated');
    },
  });
  
  const deleteMutation = useMutation({
    mutationFn: (id) => gatewayApi.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
      toast.success('Webhook deleted');
    },
  });
  
  const testMutation = useMutation({
    mutationFn: (id) => gatewayApi.testWebhook(id),
    onSuccess: (result) => {
      if (result.success) {
        toast.success('Test webhook sent successfully');
      } else {
        toast.error(`Test failed: ${result.test_result?.error_message || 'Unknown error'}`);
      }
    },
  });
  
  const regenerateSecretMutation = useMutation({
    mutationFn: (id) => gatewayApi.regenerateWebhookSecret(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
      toast.success('Secret regenerated');
    },
  });
  
  return {
    webhooks: webhooksData?.webhooks || [],
    eventTypes: eventTypesData?.events || [],
    categories: eventTypesData?.categories || [],
    isLoading,
    createWebhook: createMutation.mutateAsync,
    updateWebhook: (id, data) => updateMutation.mutateAsync({ id, data }),
    deleteWebhook: deleteMutation.mutateAsync,
    testWebhook: testMutation.mutateAsync,
    regenerateSecret: regenerateSecretMutation.mutateAsync,
  };
};
```

### 14.3 Gateway API Service

**File:** `frontend/src/features/api/api/gatewayApi.js`

```javascript
/**
 * Gateway API Service
 */

import api from '../../../services/api';

export const gatewayApi = {
  // API Keys
  async getApiKeys(params = {}) {
    const response = await api.get('/api-keys', { params });
    return response.data;
  },
  
  async createApiKey(data) {
    const response = await api.post('/api-keys', data);
    return response.data;
  },
  
  async getApiKey(id) {
    const response = await api.get(`/api-keys/${id}`);
    return response.data;
  },
  
  async updateApiKey(id, data) {
    const response = await api.put(`/api-keys/${id}`, data);
    return response.data;
  },
  
  async deleteApiKey(id) {
    const response = await api.delete(`/api-keys/${id}`);
    return response.data;
  },
  
  async regenerateApiKey(id) {
    const response = await api.post(`/api-keys/${id}/regenerate`);
    return response.data;
  },
  
  async revokeApiKey(id) {
    const response = await api.post(`/api-keys/${id}/revoke`);
    return response.data;
  },
  
  async getApiKeyUsage(id, days = 30) {
    const response = await api.get(`/api-keys/${id}/usage`, { params: { days } });
    return response.data;
  },
  
  // Webhooks
  async getWebhooks(params = {}) {
    const response = await api.get('/webhooks', { params });
    return response.data;
  },
  
  async createWebhook(data) {
    const response = await api.post('/webhooks', data);
    return response.data;
  },
  
  async getWebhook(id) {
    const response = await api.get(`/webhooks/${id}`);
    return response.data;
  },
  
  async updateWebhook(id, data) {
    const response = await api.put(`/webhooks/${id}`, data);
    return response.data;
  },
  
  async deleteWebhook(id) {
    const response = await api.delete(`/webhooks/${id}`);
    return response.data;
  },
  
  async testWebhook(id) {
    const response = await api.post(`/webhooks/${id}/test`);
    return response.data;
  },
  
  async regenerateWebhookSecret(id) {
    const response = await api.post(`/webhooks/${id}/secret`);
    return response.data;
  },
  
  async getWebhookDeliveries(id, params = {}) {
    const response = await api.get(`/webhooks/${id}/deliveries`, { params });
    return response.data;
  },
  
  async retryDelivery(webhookId, deliveryId) {
    const response = await api.post(`/webhooks/${webhookId}/deliveries/${deliveryId}/retry`);
    return response.data;
  },
  
  // Event Types
  async getEventTypes(category) {
    const params = category ? { category } : {};
    const response = await api.get('/webhooks/events', { params });
    return response.data;
  },
  
  async getEventType(eventType) {
    const response = await api.get(`/webhooks/events/${eventType}`);
    return response.data;
  },
  
  // Scopes
  async getAvailableScopes() {
    const response = await api.get('/api-keys/scopes');
    return response.data;
  },
};

export default gatewayApi;
```

---

## SUMMARY

### Phase 17 Complete Implementation

| Part | Content | Size |
|------|---------|------|
| **Part 1** | API Key models, Auth, Rate Limiter, Request Logger, API Key Service | ~54KB |
| **Part 2** | Webhook models, Event Types, Event Emitter, Signature, Delivery Manager, Celery Tasks | ~51KB |
| **Part 3** | API Routes, Frontend Pages, Components, Hooks, API Service | ~37KB |

### Key Features

| Feature | Description |
|---------|-------------|
| **API Keys** | Create, manage, scoped permissions, rate limits |
| **Rate Limiting** | Redis-based, sliding window, per-key/tenant limits |
| **Request Logging** | Complete audit trail, analytics |
| **Webhooks** | Subscribe to 20+ event types |
| **Event Delivery** | Async with retry, HMAC signatures |
| **Developer Portal** | Interactive API documentation |

### Event Types by Category

| Category | Events |
|----------|--------|
| **Invoices** | created, updated, sent, paid, overdue, voided, deleted |
| **Payments** | received, refunded, failed |
| **Inventory** | product.*, stock.low, stock.out, stock.adjusted |
| **Projects** | created, updated, status_changed, completed, milestone_completed |
| **Customers** | created, updated, deleted |
| **Documents** | uploaded, processed, signed |

### Rate Limits by Plan

| Plan | /min | /hour | /day |
|------|------|-------|------|
| Free | 30 | 500 | 5,000 |
| Standard | 100 | 2,000 | 20,000 |
| Professional | 300 | 10,000 | 100,000 |
| Business | 1,000 | 50,000 | 500,000 |
| Enterprise | Custom | Custom | Custom |

---

*Phase 17 Tasks Part 3 - LogiAccounting Pro*
*API Routes & Frontend*
