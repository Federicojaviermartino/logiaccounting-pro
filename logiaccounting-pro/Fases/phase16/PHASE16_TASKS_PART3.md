# LogiAccounting Pro - Phase 16 Tasks Part 3

## FRONTEND COMPONENTS & TEAM MANAGEMENT

---

## TASK 10: INVITATION ROUTES

### 10.1 Team & Invitation API Routes

**File:** `backend/app/tenancy/routes/invitations.py`

```python
"""
Team & Invitation Routes
API endpoints for team management and invitations
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging

from app.extensions import db
from app.tenancy.models.tenant import Tenant
from app.tenancy.models.tenant_invitation import TenantInvitation
from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.core.tenant_middleware import require_tenant
from app.tenancy.services.quota_service import QuotaService

logger = logging.getLogger(__name__)

invitations_bp = Blueprint('invitations', __name__, url_prefix='/api/v1/tenant')


@invitations_bp.route('/team', methods=['GET'])
@jwt_required()
@require_tenant
def get_team_members():
    """Get team members for current tenant"""
    tenant = TenantContext.get_current_tenant()
    
    from app.models.user import User
    
    users = User.query.filter(
        User.organization_id == tenant.id,
        User.is_active == True
    ).order_by(User.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'members': [
            {
                'id': str(u.id),
                'email': u.email,
                'name': u.full_name,
                'role': u.role,
                'is_owner': str(u.id) == str(tenant.owner_id),
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'last_login': u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        'total': len(users),
    })


@invitations_bp.route('/team/<user_id>', methods=['PUT'])
@jwt_required()
@require_tenant
def update_team_member(user_id):
    """Update team member role"""
    tenant = TenantContext.get_current_tenant()
    current_user_id = get_jwt_identity()
    
    from app.models.user import User
    
    user = User.query.filter(
        User.id == user_id,
        User.organization_id == tenant.id
    ).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Cannot modify owner
    if str(user.id) == str(tenant.owner_id):
        return jsonify({'success': False, 'error': 'Cannot modify owner'}), 403
    
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Member updated',
    })


@invitations_bp.route('/team/<user_id>', methods=['DELETE'])
@jwt_required()
@require_tenant
def remove_team_member(user_id):
    """Remove team member"""
    tenant = TenantContext.get_current_tenant()
    current_user_id = get_jwt_identity()
    
    from app.models.user import User
    
    user = User.query.filter(
        User.id == user_id,
        User.organization_id == tenant.id
    ).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Cannot remove owner
    if str(user.id) == str(tenant.owner_id):
        return jsonify({'success': False, 'error': 'Cannot remove owner'}), 403
    
    # Cannot remove self
    if str(user.id) == current_user_id:
        return jsonify({'success': False, 'error': 'Cannot remove yourself'}), 403
    
    # Deactivate user
    user.is_active = False
    db.session.commit()
    
    # Decrement user quota
    QuotaService.decrement_usage('users', tenant=tenant)
    
    return jsonify({
        'success': True,
        'message': 'Member removed',
    })


@invitations_bp.route('/invitations', methods=['GET'])
@jwt_required()
@require_tenant
def list_invitations():
    """List pending invitations"""
    tenant = TenantContext.get_current_tenant()
    
    invitations = TenantInvitation.query.filter(
        TenantInvitation.tenant_id == tenant.id,
        TenantInvitation.status == 'pending'
    ).order_by(TenantInvitation.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'invitations': [inv.to_dict() for inv in invitations],
    })


@invitations_bp.route('/invitations', methods=['POST'])
@jwt_required()
@require_tenant
def send_invitation():
    """Send invitation to join tenant"""
    tenant = TenantContext.get_current_tenant()
    user_id = get_jwt_identity()
    
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'user')
    
    if not email:
        return jsonify({'success': False, 'error': 'email required'}), 400
    
    # Check user quota
    check = QuotaService.check_quota('users', tenant=tenant)
    if not check['allowed']:
        return jsonify({
            'success': False,
            'error': 'User limit reached',
            'code': 'QUOTA_EXCEEDED',
        }), 429
    
    # Check if email already in tenant
    from app.models.user import User
    existing = User.query.filter(
        User.email == email,
        User.organization_id == tenant.id
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'error': 'User already in organization'
        }), 409
    
    # Check if invitation already pending
    existing_inv = TenantInvitation.query.filter(
        TenantInvitation.tenant_id == tenant.id,
        TenantInvitation.email == email,
        TenantInvitation.status == 'pending'
    ).first()
    
    if existing_inv:
        return jsonify({
            'success': False,
            'error': 'Invitation already pending'
        }), 409
    
    # Create invitation
    invitation = TenantInvitation(
        tenant_id=tenant.id,
        email=email,
        role=role,
        invited_by=user_id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    
    db.session.add(invitation)
    db.session.commit()
    
    # TODO: Send invitation email
    
    return jsonify({
        'success': True,
        'invitation': invitation.to_dict(),
        'invite_url': f"/invitations/{invitation.token}",
    }), 201


@invitations_bp.route('/invitations/<invitation_id>', methods=['DELETE'])
@jwt_required()
@require_tenant
def cancel_invitation(invitation_id):
    """Cancel pending invitation"""
    tenant = TenantContext.get_current_tenant()
    
    invitation = TenantInvitation.query.filter(
        TenantInvitation.id == invitation_id,
        TenantInvitation.tenant_id == tenant.id,
        TenantInvitation.status == 'pending'
    ).first()
    
    if not invitation:
        return jsonify({'success': False, 'error': 'Invitation not found'}), 404
    
    invitation.cancel()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Invitation cancelled',
    })


# Public endpoint for accepting invitations
@invitations_bp.route('/invitations/<token>/accept', methods=['POST'])
def accept_invitation(token):
    """Accept invitation and create user"""
    invitation = TenantInvitation.find_by_token(token)
    
    if not invitation:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired invitation'
        }), 404
    
    data = request.get_json()
    password = data.get('password')
    name = data.get('name')
    
    if not password:
        return jsonify({'success': False, 'error': 'password required'}), 400
    
    tenant = invitation.tenant
    
    # Create user
    from app.models.user import User
    
    user = User(
        email=invitation.email,
        organization_id=tenant.id,
        role=invitation.role,
        first_name=name.split()[0] if name else '',
        last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
        is_active=True,
    )
    user.set_password(password)
    
    db.session.add(user)
    
    # Accept invitation
    invitation.accept()
    
    # Increment user quota
    QuotaService.increment_usage('users', tenant=tenant)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully',
        'user': {
            'id': str(user.id),
            'email': user.email,
        },
    })


@invitations_bp.route('/invitations/<token>/info', methods=['GET'])
def get_invitation_info(token):
    """Get invitation info (public)"""
    invitation = TenantInvitation.find_by_token(token)
    
    if not invitation:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired invitation'
        }), 404
    
    return jsonify({
        'success': True,
        'invitation': {
            'email': invitation.email,
            'role': invitation.role,
            'tenant_name': invitation.tenant.name,
            'expires_at': invitation.expires_at.isoformat(),
        },
    })
```

---

## TASK 11: FRONTEND COMPONENTS

### 11.1 Tenant Settings Page

**File:** `frontend/src/features/tenancy/pages/TenantSettingsPage.jsx`

```jsx
/**
 * Tenant Settings Page
 * Organization settings and configuration
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useTenant } from '../hooks/useTenant';
import BrandingSettings from '../components/BrandingSettings';
import LocaleSettings from '../components/LocaleSettings';
import SecuritySettings from '../components/SecuritySettings';

const TABS = [
  { id: 'general', label: 'General' },
  { id: 'branding', label: 'Branding' },
  { id: 'locale', label: 'Locale' },
  { id: 'security', label: 'Security' },
];

const TenantSettingsPage = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('general');
  
  const { tenant, settings, isLoading, updateSettings, updateBranding } = useTenant();
  
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {t('settings.title', 'Organization Settings')}
        </h1>
        <p className="text-gray-600 mt-1">
          {t('settings.description', 'Manage your organization configuration')}
        </p>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-8">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                pb-4 text-sm font-medium border-b-2 transition-colors
                ${activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {activeTab === 'general' && (
          <GeneralSettings tenant={tenant} onUpdate={updateSettings} />
        )}
        
        {activeTab === 'branding' && (
          <BrandingSettings settings={settings} onUpdate={updateBranding} />
        )}
        
        {activeTab === 'locale' && (
          <LocaleSettings settings={settings} onUpdate={updateSettings} />
        )}
        
        {activeTab === 'security' && (
          <SecuritySettings settings={settings} onUpdate={updateSettings} />
        )}
      </div>
    </div>
  );
};

const GeneralSettings = ({ tenant, onUpdate }) => {
  const [formData, setFormData] = useState({
    name: tenant?.name || '',
    email: tenant?.email || '',
    phone: tenant?.phone || '',
    address_line1: tenant?.address?.line1 || '',
    city: tenant?.address?.city || '',
    country: tenant?.address?.country || '',
  });
  const [isSaving, setIsSaving] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    
    try {
      await onUpdate(formData);
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Organization Name
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Phone
        </label>
        <input
          type="tel"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Address
        </label>
        <input
          type="text"
          value={formData.address_line1}
          onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            City
          </label>
          <input
            type="text"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Country
          </label>
          <input
            type="text"
            value={formData.country}
            onChange={(e) => setFormData({ ...formData, country: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
      
      <button
        type="submit"
        disabled={isSaving}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </button>
    </form>
  );
};

export default TenantSettingsPage;
```

### 11.2 Team Management Page

**File:** `frontend/src/features/tenancy/pages/TeamPage.jsx`

```jsx
/**
 * Team Page
 * Team members and invitations management
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useTeam } from '../hooks/useTeam';
import InviteMemberModal from '../components/InviteMemberModal';

const TeamPage = () => {
  const { t } = useTranslation();
  const [showInviteModal, setShowInviteModal] = useState(false);
  
  const {
    members,
    invitations,
    isLoading,
    sendInvitation,
    cancelInvitation,
    updateMember,
    removeMember,
  } = useTeam();
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('team.title', 'Team')}
          </h1>
          <p className="text-gray-600 mt-1">
            {t('team.description', 'Manage team members and invitations')}
          </p>
        </div>
        
        <button
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Invite Member
        </button>
      </div>
      
      {/* Team Members */}
      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Team Members ({members.length})</h2>
        </div>
        
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mx-auto" />
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {members.map((member) => (
              <div key={member.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 font-medium">
                      {member.name?.charAt(0) || member.email.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      {member.name || member.email}
                      {member.is_owner && (
                        <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                          Owner
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">{member.email}</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  <select
                    value={member.role}
                    onChange={(e) => updateMember(member.id, { role: e.target.value })}
                    disabled={member.is_owner}
                    className="text-sm border border-gray-300 rounded px-2 py-1 disabled:opacity-50"
                  >
                    <option value="admin">Admin</option>
                    <option value="user">User</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  
                  {!member.is_owner && (
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to remove this member?')) {
                          removeMember(member.id);
                        }
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Pending Invitations */}
      {invitations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Pending Invitations ({invitations.length})</h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {invitations.map((invitation) => (
              <div key={invitation.id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">{invitation.email}</div>
                  <div className="text-sm text-gray-500">
                    Role: {invitation.role} • Expires: {new Date(invitation.expires_at).toLocaleDateString()}
                  </div>
                </div>
                
                <button
                  onClick={() => cancelInvitation(invitation.id)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Cancel
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Invite Modal */}
      {showInviteModal && (
        <InviteMemberModal
          onClose={() => setShowInviteModal(false)}
          onInvite={sendInvitation}
        />
      )}
    </div>
  );
};

export default TeamPage;
```

### 11.3 Usage Dashboard Component

**File:** `frontend/src/features/tenancy/components/UsageMetrics.jsx`

```jsx
/**
 * Usage Metrics Component
 * Display resource usage and quotas
 */

import React from 'react';

const UsageMetrics = ({ usage, alerts = [] }) => {
  if (!usage || !usage.quotas) {
    return null;
  }
  
  const getProgressColor = (percentage) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-blue-500';
  };
  
  const formatLimit = (limit) => {
    if (limit === null) return 'Unlimited';
    return limit.toLocaleString();
  };
  
  const resources = [
    { key: 'users', label: 'Users', icon: '👥' },
    { key: 'storage_mb', label: 'Storage', icon: '💾', format: (v) => `${v} MB` },
    { key: 'api_calls_per_month', label: 'API Calls', icon: '🔗', suffix: '/month' },
    { key: 'invoices_per_month', label: 'Invoices', icon: '📄', suffix: '/month' },
    { key: 'products', label: 'Products', icon: '📦' },
    { key: 'projects', label: 'Projects', icon: '📋' },
    { key: 'integrations', label: 'Integrations', icon: '🔌' },
  ];
  
  return (
    <div className="space-y-4">
      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2 mb-4">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`
                px-4 py-2 rounded-lg text-sm
                ${alert.level === 'critical' ? 'bg-red-100 text-red-800' :
                  alert.level === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }
              `}
            >
              {alert.resource} usage at {alert.percentage}% ({alert.used}/{alert.limit})
            </div>
          ))}
        </div>
      )}
      
      {/* Resource Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {resources.map(({ key, label, icon, format, suffix }) => {
          const quota = usage.quotas[key];
          if (!quota) return null;
          
          const percentage = quota.percentage || 0;
          const used = format ? format(quota.used) : quota.used;
          const limit = quota.limit === null ? 'Unlimited' : (format ? format(quota.limit) : quota.limit);
          
          return (
            <div key={key} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span>{icon}</span>
                  <span className="font-medium text-gray-900">{label}</span>
                </div>
                <span className="text-sm text-gray-600">
                  {used} / {limit}{suffix || ''}
                </span>
              </div>
              
              {quota.limit !== null && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${getProgressColor(percentage)}`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
              )}
              
              {quota.limit === null && (
                <div className="text-xs text-green-600">Unlimited</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default UsageMetrics;
```

### 11.4 Subscription Card Component

**File:** `frontend/src/features/tenancy/components/SubscriptionCard.jsx`

```jsx
/**
 * Subscription Card Component
 */

import React from 'react';
import { Link } from 'react-router-dom';

const SubscriptionCard = ({ subscription, tier }) => {
  if (!subscription) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500">No active subscription</p>
      </div>
    );
  }
  
  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      trial: 'bg-blue-100 text-blue-800',
      past_due: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.active}`}>
        {status === 'trial' ? `Trial (${subscription.trial_days_remaining} days left)` : status}
      </span>
    );
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{subscription.plan_name}</h3>
          <p className="text-sm text-gray-500 capitalize">{tier} Plan</p>
        </div>
        {getStatusBadge(subscription.status)}
      </div>
      
      {/* Pricing */}
      <div className="mb-4">
        {subscription.price.amount > 0 ? (
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-gray-900">
              ${subscription.price.amount}
            </span>
            <span className="text-gray-500">/{subscription.billing_cycle}</span>
          </div>
        ) : (
          <div className="text-3xl font-bold text-gray-900">Free</div>
        )}
      </div>
      
      {/* Period Info */}
      <div className="space-y-2 text-sm text-gray-600 mb-4">
        {subscription.current_period_end && (
          <div className="flex justify-between">
            <span>Current period ends</span>
            <span>{new Date(subscription.current_period_end).toLocaleDateString()}</span>
          </div>
        )}
        
        <div className="flex justify-between">
          <span>Auto-renew</span>
          <span>{subscription.auto_renew ? 'Yes' : 'No'}</span>
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex gap-2">
        <Link
          to="/settings/subscription"
          className="flex-1 px-4 py-2 text-center text-sm font-medium text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50"
        >
          Manage
        </Link>
        {tier !== 'enterprise' && (
          <Link
            to="/settings/subscription/upgrade"
            className="flex-1 px-4 py-2 text-center text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Upgrade
          </Link>
        )}
      </div>
    </div>
  );
};

export default SubscriptionCard;
```

### 11.5 Tenant Hooks

**File:** `frontend/src/features/tenancy/hooks/useTenant.js`

```javascript
/**
 * useTenant Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tenantApi } from '../api/tenantApi';
import { toast } from 'react-hot-toast';

export const useTenant = () => {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['tenant-settings'],
    queryFn: () => tenantApi.getSettings(),
  });
  
  const updateSettingsMutation = useMutation({
    mutationFn: (data) => tenantApi.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['tenant-settings']);
      toast.success('Settings updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update settings');
    },
  });
  
  const updateBrandingMutation = useMutation({
    mutationFn: (data) => tenantApi.updateBranding(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['tenant-settings']);
      toast.success('Branding updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update branding');
    },
  });
  
  return {
    tenant: data?.tenant,
    settings: data?.tenant?.settings,
    isLoading,
    updateSettings: updateSettingsMutation.mutateAsync,
    updateBranding: updateBrandingMutation.mutateAsync,
  };
};

export const useUsage = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['tenant-quotas'],
    queryFn: () => tenantApi.getQuotas(),
    refetchInterval: 60000, // Refresh every minute
  });
  
  return {
    usage: data?.usage,
    alerts: data?.alerts || [],
    isLoading,
  };
};

export const useSubscription = () => {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['tenant-subscription'],
    queryFn: () => tenantApi.getSubscription(),
  });
  
  const upgradeMutation = useMutation({
    mutationFn: (tier) => tenantApi.upgradeSubscription(tier),
    onSuccess: () => {
      queryClient.invalidateQueries(['tenant-subscription']);
      queryClient.invalidateQueries(['tenant-quotas']);
      toast.success('Subscription upgraded');
    },
    onError: (error) => {
      toast.error(error.message || 'Upgrade failed');
    },
  });
  
  return {
    subscription: data?.subscription,
    tier: data?.tier,
    isLoading,
    upgrade: upgradeMutation.mutateAsync,
    isUpgrading: upgradeMutation.isPending,
  };
};

export default useTenant;
```

**File:** `frontend/src/features/tenancy/hooks/useTeam.js`

```javascript
/**
 * useTeam Hook
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tenantApi } from '../api/tenantApi';
import { toast } from 'react-hot-toast';

export const useTeam = () => {
  const queryClient = useQueryClient();
  
  const { data: membersData, isLoading: isLoadingMembers } = useQuery({
    queryKey: ['team-members'],
    queryFn: () => tenantApi.getTeamMembers(),
  });
  
  const { data: invitationsData, isLoading: isLoadingInvitations } = useQuery({
    queryKey: ['team-invitations'],
    queryFn: () => tenantApi.getInvitations(),
  });
  
  const inviteMutation = useMutation({
    mutationFn: ({ email, role }) => tenantApi.sendInvitation(email, role),
    onSuccess: () => {
      queryClient.invalidateQueries(['team-invitations']);
      toast.success('Invitation sent');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to send invitation');
    },
  });
  
  const cancelInvitationMutation = useMutation({
    mutationFn: (invitationId) => tenantApi.cancelInvitation(invitationId),
    onSuccess: () => {
      queryClient.invalidateQueries(['team-invitations']);
      toast.success('Invitation cancelled');
    },
  });
  
  const updateMemberMutation = useMutation({
    mutationFn: ({ userId, data }) => tenantApi.updateTeamMember(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['team-members']);
      toast.success('Member updated');
    },
  });
  
  const removeMemberMutation = useMutation({
    mutationFn: (userId) => tenantApi.removeTeamMember(userId),
    onSuccess: () => {
      queryClient.invalidateQueries(['team-members']);
      toast.success('Member removed');
    },
  });
  
  return {
    members: membersData?.members || [],
    invitations: invitationsData?.invitations || [],
    isLoading: isLoadingMembers || isLoadingInvitations,
    sendInvitation: inviteMutation.mutateAsync,
    cancelInvitation: cancelInvitationMutation.mutateAsync,
    updateMember: (userId, data) => updateMemberMutation.mutateAsync({ userId, data }),
    removeMember: removeMemberMutation.mutateAsync,
  };
};

export default useTeam;
```

### 11.6 Tenant API Service

**File:** `frontend/src/features/tenancy/api/tenantApi.js`

```javascript
/**
 * Tenant API Service
 */

import api from '../../../services/api';

export const tenantApi = {
  // Settings
  async getSettings() {
    const response = await api.get('/tenant/settings');
    return response.data;
  },
  
  async updateSettings(data) {
    const response = await api.put('/tenant/settings', data);
    return response.data;
  },
  
  async updateBranding(data) {
    const response = await api.put('/tenant/settings/branding', data);
    return response.data;
  },
  
  async updateSecurity(data) {
    const response = await api.put('/tenant/settings/security', data);
    return response.data;
  },
  
  // Quotas & Usage
  async getQuotas() {
    const response = await api.get('/tenant/quotas');
    return response.data;
  },
  
  // Features
  async getFeatures() {
    const response = await api.get('/tenant/features');
    return response.data;
  },
  
  async checkFeature(featureKey) {
    const response = await api.get(`/tenant/features/${featureKey}`);
    return response.data;
  },
  
  // Subscription
  async getSubscription() {
    const response = await api.get('/tenant/subscription');
    return response.data;
  },
  
  async upgradeSubscription(tier) {
    const response = await api.post('/tenant/subscription/upgrade', { tier });
    return response.data;
  },
  
  async downgradeSubscription(tier) {
    const response = await api.post('/tenant/subscription/downgrade', { tier });
    return response.data;
  },
  
  async cancelSubscription(immediate = false) {
    const response = await api.post('/tenant/subscription/cancel', { immediate });
    return response.data;
  },
  
  // Team
  async getTeamMembers() {
    const response = await api.get('/tenant/team');
    return response.data;
  },
  
  async updateTeamMember(userId, data) {
    const response = await api.put(`/tenant/team/${userId}`, data);
    return response.data;
  },
  
  async removeTeamMember(userId) {
    const response = await api.delete(`/tenant/team/${userId}`);
    return response.data;
  },
  
  // Invitations
  async getInvitations() {
    const response = await api.get('/tenant/invitations');
    return response.data;
  },
  
  async sendInvitation(email, role) {
    const response = await api.post('/tenant/invitations', { email, role });
    return response.data;
  },
  
  async cancelInvitation(invitationId) {
    const response = await api.delete(`/tenant/invitations/${invitationId}`);
    return response.data;
  },
  
  // Public
  async getInvitationInfo(token) {
    const response = await api.get(`/tenant/invitations/${token}/info`);
    return response.data;
  },
  
  async acceptInvitation(token, data) {
    const response = await api.post(`/tenant/invitations/${token}/accept`, data);
    return response.data;
  },
  
  // Plans
  async getPlans() {
    const response = await api.get('/plans');
    return response.data;
  },
};

export default tenantApi;
```

---

## SUMMARY

### Phase 16 Complete Implementation

| Part | Content |
|------|---------|
| **Part 1** | Tenant models, Context/Middleware, Tenant-aware base model, Query filtering |
| **Part 2** | Tenant service, Provisioning, Quota service, Feature flags service, Settings/Subscription routes |
| **Part 3** | Team/Invitations routes, Frontend pages, Components, Hooks, API service |

### Key Features

| Feature | Implementation |
|---------|----------------|
| **Tenant Resolution** | Domain, Subdomain, Header, JWT |
| **Data Isolation** | Row-level (tenant_id), Schema, Database |
| **Automatic Filtering** | SQLAlchemy events + middleware |
| **Quota Management** | Per-resource limits with enforcement |
| **Feature Flags** | Tier-based + custom enablement |
| **Team Management** | Invitations, roles, member CRUD |
| **Subscription** | Tiers, upgrade/downgrade, billing |

### Subscription Tiers

| Tier | Price | Users | Storage | Key Features |
|------|-------|-------|---------|--------------|
| Free | $0 | 2 | 100MB | Basic |
| Standard | $29 | 5 | 1GB | + Inventory, Reports |
| Professional | $79 | 15 | 5GB | + Projects, API |
| Business | $199 | 50 | 20GB | + Audit, SSO |
| Enterprise | Custom | ∞ | ∞ | + Dedicated DB |

---

*Phase 16 Tasks Part 3 - LogiAccounting Pro*
*Frontend Components & Team Management*
