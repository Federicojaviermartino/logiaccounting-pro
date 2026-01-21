# LogiAccounting Pro - Phase 12 Tasks Part 3

## SCIM 2.0 PROVISIONING & FRONTEND SSO UI

---

## TASK 8: SCIM 2.0 IMPLEMENTATION

### 8.1 SCIM Schemas

**File:** `backend/app/schemas/scim.py`

```python
"""
SCIM 2.0 Schemas
RFC 7643 - SCIM Core Schema
RFC 7644 - SCIM Protocol
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


# ==================== SCIM Base Types ====================

class SCIMSchemaType(str, Enum):
    """SCIM Schema URIs"""
    USER = "urn:ietf:params:scim:schemas:core:2.0:User"
    GROUP = "urn:ietf:params:scim:schemas:core:2.0:Group"
    ENTERPRISE_USER = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
    LIST_RESPONSE = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
    PATCH_OP = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
    ERROR = "urn:ietf:params:scim:api:messages:2.0:Error"
    SEARCH_REQUEST = "urn:ietf:params:scim:api:messages:2.0:SearchRequest"


class SCIMMeta(BaseModel):
    """SCIM Resource Metadata"""
    resourceType: str
    created: Optional[datetime] = None
    lastModified: Optional[datetime] = None
    location: Optional[str] = None
    version: Optional[str] = None


class SCIMName(BaseModel):
    """SCIM Name component"""
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None
    middleName: Optional[str] = None
    honorificPrefix: Optional[str] = None
    honorificSuffix: Optional[str] = None


class SCIMEmail(BaseModel):
    """SCIM Email component"""
    value: EmailStr
    type: Optional[str] = "work"
    primary: Optional[bool] = False
    display: Optional[str] = None


class SCIMPhoneNumber(BaseModel):
    """SCIM Phone Number component"""
    value: str
    type: Optional[str] = "work"
    primary: Optional[bool] = False


class SCIMAddress(BaseModel):
    """SCIM Address component"""
    formatted: Optional[str] = None
    streetAddress: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = "work"
    primary: Optional[bool] = False


class SCIMGroupMember(BaseModel):
    """SCIM Group Member reference"""
    value: str  # User ID
    display: Optional[str] = None
    type: Optional[str] = "User"
    ref: Optional[str] = Field(None, alias="$ref")


class SCIMUserGroup(BaseModel):
    """SCIM User's Group membership"""
    value: str  # Group ID
    display: Optional[str] = None
    type: Optional[str] = "direct"
    ref: Optional[str] = Field(None, alias="$ref")


# ==================== SCIM User Schema ====================

class SCIMEnterpriseUser(BaseModel):
    """Enterprise User Extension"""
    employeeNumber: Optional[str] = None
    costCenter: Optional[str] = None
    organization: Optional[str] = None
    division: Optional[str] = None
    department: Optional[str] = None
    manager: Optional[Dict[str, Any]] = None


class SCIMUserBase(BaseModel):
    """SCIM User Base (for create/update)"""
    userName: str
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    nickName: Optional[str] = None
    profileUrl: Optional[str] = None
    title: Optional[str] = None
    userType: Optional[str] = None
    preferredLanguage: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = True
    password: Optional[str] = None
    emails: Optional[List[SCIMEmail]] = []
    phoneNumbers: Optional[List[SCIMPhoneNumber]] = []
    addresses: Optional[List[SCIMAddress]] = []
    
    # Enterprise extension
    enterprise: Optional[SCIMEnterpriseUser] = Field(
        None, 
        alias="urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
    )
    
    class Config:
        populate_by_name = True


class SCIMUser(SCIMUserBase):
    """SCIM User Resource (full response)"""
    schemas: List[str] = [SCIMSchemaType.USER.value]
    id: str
    externalId: Optional[str] = None
    meta: Optional[SCIMMeta] = None
    groups: Optional[List[SCIMUserGroup]] = []


class SCIMUserCreate(SCIMUserBase):
    """SCIM User Create Request"""
    schemas: List[str] = [SCIMSchemaType.USER.value]
    externalId: Optional[str] = None


class SCIMUserUpdate(SCIMUserBase):
    """SCIM User Update Request (PUT - full replace)"""
    schemas: List[str] = [SCIMSchemaType.USER.value]
    id: Optional[str] = None
    externalId: Optional[str] = None


# ==================== SCIM Group Schema ====================

class SCIMGroupBase(BaseModel):
    """SCIM Group Base"""
    displayName: str
    members: Optional[List[SCIMGroupMember]] = []


class SCIMGroup(SCIMGroupBase):
    """SCIM Group Resource"""
    schemas: List[str] = [SCIMSchemaType.GROUP.value]
    id: str
    externalId: Optional[str] = None
    meta: Optional[SCIMMeta] = None


class SCIMGroupCreate(SCIMGroupBase):
    """SCIM Group Create Request"""
    schemas: List[str] = [SCIMSchemaType.GROUP.value]
    externalId: Optional[str] = None


# ==================== SCIM Operations ====================

class SCIMPatchOperation(BaseModel):
    """SCIM Patch Operation"""
    op: str  # 'add', 'remove', 'replace'
    path: Optional[str] = None
    value: Optional[Any] = None


class SCIMPatchRequest(BaseModel):
    """SCIM Patch Request"""
    schemas: List[str] = [SCIMSchemaType.PATCH_OP.value]
    Operations: List[SCIMPatchOperation]


class SCIMListResponse(BaseModel):
    """SCIM List Response"""
    schemas: List[str] = [SCIMSchemaType.LIST_RESPONSE.value]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: List[Any] = []


class SCIMError(BaseModel):
    """SCIM Error Response"""
    schemas: List[str] = [SCIMSchemaType.ERROR.value]
    status: str
    scimType: Optional[str] = None
    detail: Optional[str] = None


class SCIMSearchRequest(BaseModel):
    """SCIM Search Request (POST /.search)"""
    schemas: List[str] = [SCIMSchemaType.SEARCH_REQUEST.value]
    filter: Optional[str] = None
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = "ascending"
    startIndex: Optional[int] = 1
    count: Optional[int] = 100
    attributes: Optional[List[str]] = None
    excludedAttributes: Optional[List[str]] = None


# ==================== Service Provider Config ====================

class SCIMAuthenticationScheme(BaseModel):
    """SCIM Authentication Scheme"""
    type: str
    name: str
    description: str
    specUri: Optional[str] = None
    documentationUri: Optional[str] = None
    primary: Optional[bool] = False


class SCIMBulkConfig(BaseModel):
    """SCIM Bulk Operations Config"""
    supported: bool = False
    maxOperations: int = 0
    maxPayloadSize: int = 0


class SCIMFilterConfig(BaseModel):
    """SCIM Filter Config"""
    supported: bool = True
    maxResults: int = 200


class SCIMChangePasswordConfig(BaseModel):
    """SCIM Change Password Config"""
    supported: bool = False


class SCIMSortConfig(BaseModel):
    """SCIM Sort Config"""
    supported: bool = True


class SCIMETagConfig(BaseModel):
    """SCIM ETag Config"""
    supported: bool = False


class SCIMPatchConfig(BaseModel):
    """SCIM Patch Config"""
    supported: bool = True


class SCIMServiceProviderConfig(BaseModel):
    """SCIM Service Provider Configuration"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"]
    documentationUri: Optional[str] = None
    patch: SCIMPatchConfig = SCIMPatchConfig()
    bulk: SCIMBulkConfig = SCIMBulkConfig()
    filter: SCIMFilterConfig = SCIMFilterConfig()
    changePassword: SCIMChangePasswordConfig = SCIMChangePasswordConfig()
    sort: SCIMSortConfig = SCIMSortConfig()
    etag: SCIMETagConfig = SCIMETagConfig()
    authenticationSchemes: List[SCIMAuthenticationScheme] = []
    meta: Optional[SCIMMeta] = None
```

### 8.2 SCIM Service

**File:** `backend/app/services/sso/scim_service.py`

```python
"""
SCIM 2.0 Service
Handles user provisioning from Identity Providers
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from flask import current_app, request
import re
import logging

from app.extensions import db
from app.models.user import User
from app.models.sso_connection import SSOConnection
from app.models.scim_log import SCIMSyncLog
from app.schemas.scim import (
    SCIMUser, SCIMUserCreate, SCIMUserUpdate, SCIMPatchRequest,
    SCIMGroup, SCIMGroupCreate, SCIMPatchOperation,
    SCIMListResponse, SCIMMeta, SCIMName, SCIMEmail
)

logger = logging.getLogger(__name__)


class SCIMService:
    """SCIM 2.0 Provisioning Service"""
    
    # SCIM Filter operators
    FILTER_OPERATORS = {
        'eq': lambda a, b: a == b,
        'ne': lambda a, b: a != b,
        'co': lambda a, b: b.lower() in a.lower() if a else False,
        'sw': lambda a, b: a.lower().startswith(b.lower()) if a else False,
        'ew': lambda a, b: a.lower().endswith(b.lower()) if a else False,
        'gt': lambda a, b: a > b,
        'ge': lambda a, b: a >= b,
        'lt': lambda a, b: a < b,
        'le': lambda a, b: a <= b,
        'pr': lambda a, b: a is not None,
    }
    
    def __init__(self, connection: SSOConnection):
        self.connection = connection
        self.org_id = connection.organization_id
    
    # ==================== User Operations ====================
    
    def list_users(
        self,
        filter_query: Optional[str] = None,
        start_index: int = 1,
        count: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = 'ascending',
        attributes: Optional[List[str]] = None
    ) -> SCIMListResponse:
        """
        List users with SCIM filtering and pagination
        """
        # Base query for organization
        query = User.query.filter(User.organization_id == self.org_id)
        
        # Apply filter
        if filter_query:
            query = self._apply_filter(query, filter_query)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        if sort_by:
            order_field = self._get_sort_field(sort_by)
            if order_field:
                if sort_order == 'descending':
                    query = query.order_by(order_field.desc())
                else:
                    query = query.order_by(order_field.asc())
        else:
            query = query.order_by(User.created_at.desc())
        
        # Apply pagination (SCIM uses 1-based indexing)
        offset = start_index - 1
        users = query.offset(offset).limit(count).all()
        
        # Convert to SCIM format
        resources = [self._user_to_scim(u, attributes) for u in users]
        
        return SCIMListResponse(
            totalResults=total,
            startIndex=start_index,
            itemsPerPage=len(resources),
            Resources=resources
        )
    
    def get_user(self, user_id: str, attributes: Optional[List[str]] = None) -> Optional[SCIMUser]:
        """Get single user by ID"""
        user = User.query.filter(
            User.id == user_id,
            User.organization_id == self.org_id
        ).first()
        
        if not user:
            return None
        
        return self._user_to_scim(user, attributes)
    
    def create_user(self, data: SCIMUserCreate) -> Tuple[SCIMUser, bool]:
        """
        Create user from SCIM request
        Returns: (user, created) - created is True if new user
        """
        # Check for existing user by userName (email)
        existing = User.query.filter(
            User.email == data.userName.lower(),
            User.organization_id == self.org_id
        ).first()
        
        if existing:
            # Update existing user
            return self._update_user_from_scim(existing, data), False
        
        # Create new user
        user = self._create_user_from_scim(data)
        
        # Log operation
        SCIMSyncLog.log_operation(
            connection_id=str(self.connection.id),
            operation='create',
            resource_type='user',
            status='success',
            external_id=data.externalId,
            internal_id=user.id,
            request_payload=data.dict()
        )
        
        logger.info(f"SCIM: Created user {user.email}")
        
        return self._user_to_scim(user), True
    
    def update_user(self, user_id: str, data: SCIMUserUpdate) -> Optional[SCIMUser]:
        """Replace user (PUT - full update)"""
        user = User.query.filter(
            User.id == user_id,
            User.organization_id == self.org_id
        ).first()
        
        if not user:
            return None
        
        scim_user = self._update_user_from_scim(user, data)
        
        SCIMSyncLog.log_operation(
            connection_id=str(self.connection.id),
            operation='update',
            resource_type='user',
            status='success',
            external_id=data.externalId,
            internal_id=user.id,
            request_payload=data.dict()
        )
        
        logger.info(f"SCIM: Updated user {user.email}")
        
        return scim_user
    
    def patch_user(self, user_id: str, patch: SCIMPatchRequest) -> Optional[SCIMUser]:
        """Partial update user (PATCH)"""
        user = User.query.filter(
            User.id == user_id,
            User.organization_id == self.org_id
        ).first()
        
        if not user:
            return None
        
        # Apply patch operations
        for op in patch.Operations:
            self._apply_patch_operation(user, op)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        SCIMSyncLog.log_operation(
            connection_id=str(self.connection.id),
            operation='patch',
            resource_type='user',
            status='success',
            internal_id=user.id,
            request_payload=patch.dict()
        )
        
        logger.info(f"SCIM: Patched user {user.email}")
        
        return self._user_to_scim(user)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete/deactivate user"""
        user = User.query.filter(
            User.id == user_id,
            User.organization_id == self.org_id
        ).first()
        
        if not user:
            return False
        
        # Deactivate rather than delete (soft delete)
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        SCIMSyncLog.log_operation(
            connection_id=str(self.connection.id),
            operation='delete',
            resource_type='user',
            status='success',
            internal_id=user.id
        )
        
        logger.info(f"SCIM: Deactivated user {user.email}")
        
        return True
    
    # ==================== Helper Methods ====================
    
    def _user_to_scim(
        self, 
        user: User, 
        attributes: Optional[List[str]] = None
    ) -> SCIMUser:
        """Convert User model to SCIM User"""
        base_url = current_app.config.get('BASE_URL', '')
        
        scim_user = SCIMUser(
            id=str(user.id),
            externalId=user.external_id,
            userName=user.email,
            name=SCIMName(
                givenName=user.first_name,
                familyName=user.last_name,
                formatted=f"{user.first_name} {user.last_name}".strip()
            ),
            displayName=user.name or f"{user.first_name} {user.last_name}".strip(),
            active=user.is_active,
            emails=[
                SCIMEmail(
                    value=user.email,
                    type="work",
                    primary=True
                )
            ],
            meta=SCIMMeta(
                resourceType="User",
                created=user.created_at,
                lastModified=user.updated_at,
                location=f"{base_url}/scim/v2/Users/{user.id}"
            ),
            groups=[]  # TODO: Add group memberships
        )
        
        # Filter attributes if specified
        if attributes:
            return self._filter_attributes(scim_user, attributes)
        
        return scim_user
    
    def _create_user_from_scim(self, data: SCIMUserCreate) -> User:
        """Create User model from SCIM data"""
        import secrets
        
        # Extract name components
        first_name = ""
        last_name = ""
        if data.name:
            first_name = data.name.givenName or ""
            last_name = data.name.familyName or ""
        
        # Extract primary email
        email = data.userName
        if data.emails:
            primary = next((e for e in data.emails if e.primary), data.emails[0] if data.emails else None)
            if primary:
                email = primary.value
        
        user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            organization_id=self.org_id,
            is_active=data.active if data.active is not None else True,
            external_id=data.externalId,
            sso_connection_id=self.connection.id,
            role=self.connection.default_role or 'client',
        )
        
        # Set random password (user will use SSO)
        user.set_password(secrets.token_urlsafe(32))
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def _update_user_from_scim(
        self, 
        user: User, 
        data: SCIMUserUpdate
    ) -> SCIMUser:
        """Update User model from SCIM data"""
        
        if data.name:
            if data.name.givenName is not None:
                user.first_name = data.name.givenName
            if data.name.familyName is not None:
                user.last_name = data.name.familyName
        
        if data.displayName:
            user.name = data.displayName
        
        if data.active is not None:
            user.is_active = data.active
            if not data.active:
                user.deactivated_at = datetime.utcnow()
        
        if data.emails:
            primary = next((e for e in data.emails if e.primary), data.emails[0] if data.emails else None)
            if primary:
                user.email = primary.value.lower()
        
        if data.externalId:
            user.external_id = data.externalId
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return self._user_to_scim(user)
    
    def _apply_patch_operation(self, user: User, op: SCIMPatchOperation):
        """Apply a single SCIM patch operation"""
        operation = op.op.lower()
        path = op.path
        value = op.value
        
        if operation == 'replace':
            if path == 'active' or path is None and isinstance(value, dict) and 'active' in value:
                active_value = value if path == 'active' else value.get('active')
                user.is_active = active_value
                if not active_value:
                    user.deactivated_at = datetime.utcnow()
            
            elif path == 'name.givenName':
                user.first_name = value
            
            elif path == 'name.familyName':
                user.last_name = value
            
            elif path == 'displayName':
                user.name = value
            
            elif path == 'userName':
                user.email = value.lower()
            
            elif path == 'emails[type eq "work"].value':
                user.email = value.lower()
            
            elif path is None and isinstance(value, dict):
                # Bulk update
                if 'name' in value:
                    if 'givenName' in value['name']:
                        user.first_name = value['name']['givenName']
                    if 'familyName' in value['name']:
                        user.last_name = value['name']['familyName']
                if 'displayName' in value:
                    user.name = value['displayName']
        
        elif operation == 'add':
            # Handle add operations (mainly for groups)
            pass
        
        elif operation == 'remove':
            # Handle remove operations
            if path == 'active':
                user.is_active = False
                user.deactivated_at = datetime.utcnow()
    
    def _apply_filter(self, query, filter_query: str):
        """Apply SCIM filter to SQLAlchemy query"""
        # Parse simple filters like: userName eq "john@example.com"
        # More complex filters would need a proper parser
        
        # Simple pattern: attribute op "value"
        pattern = r'(\w+(?:\.\w+)?)\s+(eq|ne|co|sw|ew|pr|gt|ge|lt|le)\s+"?([^"]*)"?'
        match = re.match(pattern, filter_query, re.IGNORECASE)
        
        if not match:
            return query
        
        attr, op, value = match.groups()
        op = op.lower()
        
        # Map SCIM attributes to model fields
        attr_map = {
            'userName': User.email,
            'name.givenName': User.first_name,
            'name.familyName': User.last_name,
            'displayName': User.name,
            'active': User.is_active,
            'externalId': User.external_id,
            'emails.value': User.email,
        }
        
        field = attr_map.get(attr)
        if not field:
            return query
        
        # Apply operator
        if op == 'eq':
            query = query.filter(field == value)
        elif op == 'ne':
            query = query.filter(field != value)
        elif op == 'co':
            query = query.filter(field.ilike(f'%{value}%'))
        elif op == 'sw':
            query = query.filter(field.ilike(f'{value}%'))
        elif op == 'ew':
            query = query.filter(field.ilike(f'%{value}'))
        elif op == 'pr':
            query = query.filter(field.isnot(None))
        
        return query
    
    def _get_sort_field(self, sort_by: str):
        """Map SCIM sort field to model field"""
        sort_map = {
            'userName': User.email,
            'name.givenName': User.first_name,
            'name.familyName': User.last_name,
            'displayName': User.name,
            'meta.created': User.created_at,
            'meta.lastModified': User.updated_at,
        }
        return sort_map.get(sort_by)
    
    def _filter_attributes(
        self, 
        scim_user: SCIMUser, 
        attributes: List[str]
    ) -> SCIMUser:
        """Filter SCIM user to only include specified attributes"""
        # Always include id and schemas
        data = {'id': scim_user.id, 'schemas': scim_user.schemas}
        
        full_data = scim_user.dict()
        
        for attr in attributes:
            if '.' in attr:
                # Nested attribute
                parts = attr.split('.')
                if parts[0] in full_data:
                    if parts[0] not in data:
                        data[parts[0]] = {}
                    if isinstance(full_data[parts[0]], dict) and parts[1] in full_data[parts[0]]:
                        data[parts[0]][parts[1]] = full_data[parts[0]][parts[1]]
            elif attr in full_data:
                data[attr] = full_data[attr]
        
        return SCIMUser(**data)
```

### 8.3 SCIM Routes

**File:** `backend/app/routes/scim.py`

```python
"""
SCIM 2.0 REST API Routes
RFC 7644 - SCIM Protocol
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from typing import Optional
import logging

from app.models.sso_connection import SSOConnection
from app.services.sso.scim_service import SCIMService
from app.schemas.scim import (
    SCIMUserCreate, SCIMUserUpdate, SCIMPatchRequest,
    SCIMGroupCreate, SCIMPatchRequest,
    SCIMListResponse, SCIMError, SCIMServiceProviderConfig,
    SCIMAuthenticationScheme, SCIMMeta, SCIMPatchConfig, SCIMFilterConfig
)

logger = logging.getLogger(__name__)

scim_bp = Blueprint('scim', __name__, url_prefix='/scim/v2')


# ==================== SCIM Authentication ====================

def scim_auth_required(f):
    """
    Validate SCIM bearer token authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return scim_error_response(
                'Authentication required',
                status=401,
                scim_type='invalidAuthentication'
            )
        
        token = auth_header.replace('Bearer ', '').strip()
        
        if not token:
            return scim_error_response(
                'Invalid bearer token',
                status=401,
                scim_type='invalidAuthentication'
            )
        
        # Validate token and get connection
        connection = validate_scim_token(token)
        
        if not connection:
            return scim_error_response(
                'Invalid or expired token',
                status=401,
                scim_type='invalidAuthentication'
            )
        
        if not connection.scim_enabled:
            return scim_error_response(
                'SCIM is not enabled for this connection',
                status=403,
                scim_type='invalidConfiguration'
            )
        
        # Store connection in request context
        g.scim_connection = connection
        g.scim_service = SCIMService(connection)
        
        return f(*args, **kwargs)
    
    return decorated


def validate_scim_token(token: str) -> Optional[SSOConnection]:
    """Validate SCIM token and return associated connection"""
    import hashlib
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find connection with matching token
    connection = SSOConnection.query.filter(
        SSOConnection.scim_enabled == True,
        SSOConnection._scim_token == token_hash
    ).first()
    
    return connection


def scim_error_response(detail: str, status: int = 400, scim_type: str = None):
    """Generate SCIM error response"""
    error = SCIMError(
        status=str(status),
        detail=detail,
        scimType=scim_type
    )
    
    response = jsonify(error.dict())
    response.status_code = status
    response.headers['Content-Type'] = 'application/scim+json'
    
    return response


def scim_response(data, status: int = 200):
    """Generate SCIM response with proper content type"""
    if hasattr(data, 'dict'):
        data = data.dict(by_alias=True, exclude_none=True)
    
    response = jsonify(data)
    response.status_code = status
    response.headers['Content-Type'] = 'application/scim+json'
    
    return response


# ==================== Service Provider Config ====================

@scim_bp.route('/ServiceProviderConfig', methods=['GET'])
def get_service_provider_config():
    """
    Get SCIM Service Provider Configuration
    """
    config = SCIMServiceProviderConfig(
        documentationUri="https://docs.logiaccounting.com/scim",
        patch=SCIMPatchConfig(supported=True),
        filter=SCIMFilterConfig(supported=True, maxResults=200),
        authenticationSchemes=[
            SCIMAuthenticationScheme(
                type="oauthbearertoken",
                name="OAuth Bearer Token",
                description="Authentication scheme using OAuth 2.0 Bearer Token",
                specUri="https://tools.ietf.org/html/rfc6750",
                primary=True
            )
        ],
        meta=SCIMMeta(
            resourceType="ServiceProviderConfig",
            location=f"{request.url_root}scim/v2/ServiceProviderConfig"
        )
    )
    
    return scim_response(config)


@scim_bp.route('/Schemas', methods=['GET'])
def get_schemas():
    """
    Get SCIM Schemas
    """
    schemas = [
        {
            "id": "urn:ietf:params:scim:schemas:core:2.0:User",
            "name": "User",
            "description": "User Schema",
            "attributes": [
                {"name": "userName", "type": "string", "required": True},
                {"name": "name", "type": "complex"},
                {"name": "displayName", "type": "string"},
                {"name": "emails", "type": "complex", "multiValued": True},
                {"name": "active", "type": "boolean"},
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{request.url_root}scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User"
            }
        },
        {
            "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "name": "Group",
            "description": "Group Schema",
            "attributes": [
                {"name": "displayName", "type": "string", "required": True},
                {"name": "members", "type": "complex", "multiValued": True},
            ],
            "meta": {
                "resourceType": "Schema",
                "location": f"{request.url_root}scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:Group"
            }
        }
    ]
    
    return scim_response({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(schemas),
        "Resources": schemas
    })


@scim_bp.route('/ResourceTypes', methods=['GET'])
def get_resource_types():
    """
    Get SCIM Resource Types
    """
    resource_types = [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "User",
            "name": "User",
            "endpoint": "/Users",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
            "meta": {
                "resourceType": "ResourceType",
                "location": f"{request.url_root}scim/v2/ResourceTypes/User"
            }
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "Group",
            "name": "Group",
            "endpoint": "/Groups",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "meta": {
                "resourceType": "ResourceType",
                "location": f"{request.url_root}scim/v2/ResourceTypes/Group"
            }
        }
    ]
    
    return scim_response({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resource_types),
        "Resources": resource_types
    })


# ==================== Users Endpoints ====================

@scim_bp.route('/Users', methods=['GET'])
@scim_auth_required
def list_users():
    """
    List users with SCIM filtering
    
    Query params:
    - filter: SCIM filter expression
    - startIndex: 1-based start index
    - count: Number of results
    - sortBy: Sort attribute
    - sortOrder: ascending or descending
    - attributes: Comma-separated list of attributes to return
    """
    service: SCIMService = g.scim_service
    
    filter_query = request.args.get('filter')
    start_index = int(request.args.get('startIndex', 1))
    count = min(int(request.args.get('count', 100)), 200)
    sort_by = request.args.get('sortBy')
    sort_order = request.args.get('sortOrder', 'ascending')
    attributes = request.args.get('attributes')
    
    attr_list = attributes.split(',') if attributes else None
    
    result = service.list_users(
        filter_query=filter_query,
        start_index=start_index,
        count=count,
        sort_by=sort_by,
        sort_order=sort_order,
        attributes=attr_list
    )
    
    return scim_response(result)


@scim_bp.route('/Users/<user_id>', methods=['GET'])
@scim_auth_required
def get_user(user_id: str):
    """Get single user by ID"""
    service: SCIMService = g.scim_service
    
    attributes = request.args.get('attributes')
    attr_list = attributes.split(',') if attributes else None
    
    user = service.get_user(user_id, attributes=attr_list)
    
    if not user:
        return scim_error_response(
            f'User {user_id} not found',
            status=404,
            scim_type='notFound'
        )
    
    return scim_response(user)


@scim_bp.route('/Users', methods=['POST'])
@scim_auth_required
def create_user():
    """Create new user"""
    service: SCIMService = g.scim_service
    
    try:
        data = SCIMUserCreate(**request.get_json())
    except Exception as e:
        return scim_error_response(
            f'Invalid request body: {str(e)}',
            status=400,
            scim_type='invalidSyntax'
        )
    
    try:
        user, created = service.create_user(data)
        
        status = 201 if created else 200
        return scim_response(user, status=status)
        
    except Exception as e:
        logger.exception(f"SCIM create user error: {e}")
        return scim_error_response(
            f'Failed to create user: {str(e)}',
            status=500
        )


@scim_bp.route('/Users/<user_id>', methods=['PUT'])
@scim_auth_required
def update_user(user_id: str):
    """Replace user (full update)"""
    service: SCIMService = g.scim_service
    
    try:
        data = SCIMUserUpdate(**request.get_json())
    except Exception as e:
        return scim_error_response(
            f'Invalid request body: {str(e)}',
            status=400,
            scim_type='invalidSyntax'
        )
    
    user = service.update_user(user_id, data)
    
    if not user:
        return scim_error_response(
            f'User {user_id} not found',
            status=404,
            scim_type='notFound'
        )
    
    return scim_response(user)


@scim_bp.route('/Users/<user_id>', methods=['PATCH'])
@scim_auth_required
def patch_user(user_id: str):
    """Partial update user"""
    service: SCIMService = g.scim_service
    
    try:
        data = SCIMPatchRequest(**request.get_json())
    except Exception as e:
        return scim_error_response(
            f'Invalid request body: {str(e)}',
            status=400,
            scim_type='invalidSyntax'
        )
    
    user = service.patch_user(user_id, data)
    
    if not user:
        return scim_error_response(
            f'User {user_id} not found',
            status=404,
            scim_type='notFound'
        )
    
    return scim_response(user)


@scim_bp.route('/Users/<user_id>', methods=['DELETE'])
@scim_auth_required
def delete_user(user_id: str):
    """Delete/deactivate user"""
    service: SCIMService = g.scim_service
    
    success = service.delete_user(user_id)
    
    if not success:
        return scim_error_response(
            f'User {user_id} not found',
            status=404,
            scim_type='notFound'
        )
    
    return '', 204


# ==================== Groups Endpoints ====================

@scim_bp.route('/Groups', methods=['GET'])
@scim_auth_required
def list_groups():
    """List groups (placeholder - implement if needed)"""
    return scim_response(SCIMListResponse(
        totalResults=0,
        startIndex=1,
        itemsPerPage=0,
        Resources=[]
    ))


@scim_bp.route('/Groups/<group_id>', methods=['GET'])
@scim_auth_required
def get_group(group_id: str):
    """Get group (placeholder)"""
    return scim_error_response(
        'Groups not implemented',
        status=501,
        scim_type='notImplemented'
    )


@scim_bp.route('/Groups', methods=['POST'])
@scim_auth_required
def create_group():
    """Create group (placeholder)"""
    return scim_error_response(
        'Groups not implemented',
        status=501,
        scim_type='notImplemented'
    )


@scim_bp.route('/Groups/<group_id>', methods=['PUT', 'PATCH', 'DELETE'])
@scim_auth_required
def modify_group(group_id: str):
    """Modify group (placeholder)"""
    return scim_error_response(
        'Groups not implemented',
        status=501,
        scim_type='notImplemented'
    )
```

---

## TASK 9: SSO SERVICE

**File:** `backend/app/services/sso_service.py`

```python
"""
SSO Service
Main service for SSO operations including user provisioning
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
import logging

from app.extensions import db
from app.models.user import User
from app.models.sso_connection import SSOConnection
from app.models.sso_session import SSOSession, UserExternalIdentity
from app.auth.sso.oauth.providers.base import OAuthUserInfo

logger = logging.getLogger(__name__)


class SSOService:
    """SSO Service for authentication and provisioning"""
    
    @staticmethod
    def get_connection(connection_id: str) -> Optional[SSOConnection]:
        """Get SSO connection by ID"""
        return SSOConnection.query.get(connection_id)
    
    @staticmethod
    def get_connections(organization_id: str) -> List[SSOConnection]:
        """Get all SSO connections for an organization"""
        return SSOConnection.query.filter(
            SSOConnection.organization_id == organization_id
        ).all()
    
    @staticmethod
    def get_connections_by_domain(domain: str) -> List[SSOConnection]:
        """Get SSO connections that allow a specific email domain"""
        connections = SSOConnection.query.filter(
            SSOConnection.status == 'active'
        ).all()
        
        # Filter by allowed domains
        matching = []
        for conn in connections:
            if not conn.allowed_domains:
                # No domain restriction
                matching.append(conn)
            elif domain.lower() in [d.lower() for d in conn.allowed_domains]:
                matching.append(conn)
        
        return matching
    
    @staticmethod
    def create_connection(
        organization_id: str, 
        data: Dict[str, Any]
    ) -> SSOConnection:
        """Create new SSO connection"""
        connection = SSOConnection(
            organization_id=organization_id,
            **data
        )
        
        db.session.add(connection)
        db.session.commit()
        
        logger.info(f"Created SSO connection {connection.name} for org {organization_id}")
        
        return connection
    
    @staticmethod
    def update_connection(
        connection_id: str, 
        data: Dict[str, Any]
    ) -> Optional[SSOConnection]:
        """Update SSO connection"""
        connection = SSOConnection.query.get(connection_id)
        
        if not connection:
            return None
        
        for key, value in data.items():
            if hasattr(connection, key):
                setattr(connection, key, value)
        
        connection.updated_at = datetime.utcnow()
        db.session.commit()
        
        return connection
    
    @staticmethod
    def delete_connection(connection_id: str) -> bool:
        """Delete SSO connection"""
        connection = SSOConnection.query.get(connection_id)
        
        if not connection:
            return False
        
        db.session.delete(connection)
        db.session.commit()
        
        return True
    
    @staticmethod
    def test_connection(connection_id: str) -> Dict[str, Any]:
        """Test SSO connection configuration"""
        connection = SSOConnection.query.get(connection_id)
        
        if not connection:
            return {'success': False, 'error': 'Connection not found'}
        
        results = {
            'success': True,
            'checks': []
        }
        
        # Check required fields based on protocol
        if connection.protocol == 'saml':
            if connection.saml_entity_id:
                results['checks'].append({'name': 'Entity ID', 'status': 'ok'})
            else:
                results['checks'].append({'name': 'Entity ID', 'status': 'missing'})
                results['success'] = False
            
            if connection.saml_sso_url:
                results['checks'].append({'name': 'SSO URL', 'status': 'ok'})
            else:
                results['checks'].append({'name': 'SSO URL', 'status': 'missing'})
                results['success'] = False
            
            if connection.saml_certificate:
                results['checks'].append({'name': 'Certificate', 'status': 'ok'})
            else:
                results['checks'].append({'name': 'Certificate', 'status': 'missing'})
                results['success'] = False
        
        elif connection.protocol in ['oauth2', 'oidc']:
            if connection.oauth_client_id:
                results['checks'].append({'name': 'Client ID', 'status': 'ok'})
            else:
                results['checks'].append({'name': 'Client ID', 'status': 'missing'})
                results['success'] = False
            
            if connection.oauth_client_secret:
                results['checks'].append({'name': 'Client Secret', 'status': 'ok'})
            else:
                results['checks'].append({'name': 'Client Secret', 'status': 'missing'})
                results['success'] = False
        
        return results
    
    @staticmethod
    def find_or_create_user(
        connection: SSOConnection,
        attributes: Dict[str, Any],
        name_id: str,
        session_index: str = None
    ) -> User:
        """
        Find existing user or create new one from SAML assertion
        Just-in-Time (JIT) Provisioning
        """
        email = attributes.get('email', name_id)
        if not email or '@' not in email:
            email = name_id
        
        email = email.lower()
        
        # First, try to find by external identity
        identity = UserExternalIdentity.find_by_external_id(
            str(connection.id), 
            name_id
        )
        
        if identity:
            user = identity.user
            
            # Update profile if enabled
            if connection.attribute_mapping:
                SSOService._update_user_profile(user, attributes, connection)
            
            return user
        
        # Try to find by email
        user = User.query.filter(
            User.email == email,
            User.organization_id == connection.organization_id
        ).first()
        
        if user:
            # Link existing user to IdP
            UserExternalIdentity.find_or_create(
                user_id=str(user.id),
                connection_id=str(connection.id),
                external_id=name_id,
                email=email,
                profile_data=attributes
            )
            
            return user
        
        # Create new user (JIT provisioning)
        user = SSOService._create_user_from_attributes(
            connection=connection,
            attributes=attributes,
            email=email
        )
        
        # Create external identity link
        UserExternalIdentity.find_or_create(
            user_id=str(user.id),
            connection_id=str(connection.id),
            external_id=name_id,
            email=email,
            profile_data=attributes
        )
        
        logger.info(f"JIT provisioned user {email} from SAML")
        
        return user
    
    @staticmethod
    def find_or_create_user_oauth(
        connection: SSOConnection,
        user_info: OAuthUserInfo,
        tokens: Dict[str, Any]
    ) -> User:
        """
        Find existing user or create from OAuth user info
        """
        email = user_info.email.lower()
        external_id = user_info.id
        
        # Try to find by external identity
        identity = UserExternalIdentity.find_by_external_id(
            str(connection.id),
            external_id
        )
        
        if identity:
            user = identity.user
            
            # Update profile
            SSOService._update_user_profile_oauth(user, user_info, connection)
            
            return user
        
        # Try to find by email
        user = User.query.filter(
            User.email == email,
            User.organization_id == connection.organization_id
        ).first()
        
        if user:
            # Link existing user
            UserExternalIdentity.find_or_create(
                user_id=str(user.id),
                connection_id=str(connection.id),
                external_id=external_id,
                email=email,
                profile_data=user_info.raw_data
            )
            
            return user
        
        # Create new user
        user = SSOService._create_user_from_oauth(connection, user_info)
        
        # Create identity link
        UserExternalIdentity.find_or_create(
            user_id=str(user.id),
            connection_id=str(connection.id),
            external_id=external_id,
            email=email,
            profile_data=user_info.raw_data
        )
        
        logger.info(f"JIT provisioned user {email} from OAuth")
        
        return user
    
    @staticmethod
    def create_session(
        user: User,
        connection: SSOConnection,
        saml_data: Dict[str, Any] = None,
        oauth_data: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Create application session after SSO authentication
        Returns JWT tokens
        """
        # Create SSO session record
        sso_session = SSOSession.create_session(
            user_id=str(user.id),
            connection_id=str(connection.id),
            duration_hours=connection.session_duration_hours or 8
        )
        
        if saml_data:
            sso_session.name_id = saml_data.get('name_id')
            sso_session.name_id_format = saml_data.get('name_id_format')
            sso_session.session_index = saml_data.get('session_index')
        
        if oauth_data:
            sso_session.access_token = oauth_data.get('access_token')
            sso_session.refresh_token = oauth_data.get('refresh_token')
            sso_session.id_token = oauth_data.get('id_token')
            
            if oauth_data.get('expires_in'):
                sso_session.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=oauth_data['expires_in']
                )
        
        db.session.commit()
        
        # Create JWT tokens
        additional_claims = {
            'role': user.role,
            'org_id': str(user.organization_id),
            'sso_session_id': str(sso_session.id)
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims,
            expires_delta=timedelta(days=7)
        )
        
        # Update user last login
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    @staticmethod
    def logout_user_sso(connection_id: str):
        """Invalidate SSO sessions for connection"""
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if user_id:
            SSOSession.invalidate_user_sessions(user_id, connection_id)
    
    @staticmethod
    def _create_user_from_attributes(
        connection: SSOConnection,
        attributes: Dict[str, Any],
        email: str
    ) -> User:
        """Create user from SAML/OIDC attributes"""
        import secrets
        
        # Map attributes
        mapping = connection.attribute_mapping or {}
        
        first_name = attributes.get(mapping.get('first_name', 'first_name'), '')
        last_name = attributes.get(mapping.get('last_name', 'last_name'), '')
        display_name = attributes.get(mapping.get('display_name', 'display_name'))
        
        # Determine role from groups
        groups = attributes.get(mapping.get('groups', 'groups'), [])
        role = connection.map_user_role(groups)
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            name=display_name,
            organization_id=connection.organization_id,
            role=role,
            is_active=True,
            sso_connection_id=connection.id
        )
        
        # Set random password (user uses SSO)
        user.set_password(secrets.token_urlsafe(32))
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def _create_user_from_oauth(
        connection: SSOConnection,
        user_info: OAuthUserInfo
    ) -> User:
        """Create user from OAuth user info"""
        import secrets
        
        # Determine role from groups
        role = connection.map_user_role(user_info.groups)
        
        user = User(
            email=user_info.email.lower(),
            first_name=user_info.first_name or '',
            last_name=user_info.last_name or '',
            name=user_info.display_name,
            organization_id=connection.organization_id,
            role=role,
            is_active=True,
            sso_connection_id=connection.id
        )
        
        user.set_password(secrets.token_urlsafe(32))
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def _update_user_profile(
        user: User,
        attributes: Dict[str, Any],
        connection: SSOConnection
    ):
        """Update user profile from IdP attributes"""
        mapping = connection.attribute_mapping or {}
        
        first_name = attributes.get(mapping.get('first_name', 'first_name'))
        if first_name:
            user.first_name = first_name
        
        last_name = attributes.get(mapping.get('last_name', 'last_name'))
        if last_name:
            user.last_name = last_name
        
        display_name = attributes.get(mapping.get('display_name', 'display_name'))
        if display_name:
            user.name = display_name
        
        # Update role from groups
        groups = attributes.get(mapping.get('groups', 'groups'), [])
        if groups:
            user.role = connection.map_user_role(groups)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def _update_user_profile_oauth(
        user: User,
        user_info: OAuthUserInfo,
        connection: SSOConnection
    ):
        """Update user profile from OAuth user info"""
        if user_info.first_name:
            user.first_name = user_info.first_name
        
        if user_info.last_name:
            user.last_name = user_info.last_name
        
        if user_info.display_name:
            user.name = user_info.display_name
        
        if user_info.groups:
            user.role = connection.map_user_role(user_info.groups)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
```

---

## TASK 10: FRONTEND SSO COMPONENTS

### 10.1 SSO Login Button

**File:** `frontend/src/components/sso/SSOLoginButton.jsx`

```jsx
/**
 * SSO Login Button Component
 * Displays "Sign in with [Provider]" button
 */

import React from 'react';
import PropTypes from 'prop-types';

// Provider icons and colors
const PROVIDER_CONFIG = {
  microsoft: {
    name: 'Microsoft',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 21 21">
        <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
        <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
        <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
        <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
      </svg>
    ),
    bgColor: 'bg-white',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-300',
    hoverBg: 'hover:bg-gray-50',
  },
  azure_ad: {
    name: 'Microsoft',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 21 21">
        <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
        <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
        <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
        <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
      </svg>
    ),
    bgColor: 'bg-white',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-300',
    hoverBg: 'hover:bg-gray-50',
  },
  google: {
    name: 'Google',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
    ),
    bgColor: 'bg-white',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-300',
    hoverBg: 'hover:bg-gray-50',
  },
  okta: {
    name: 'Okta',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path fill="#007DC1" d="M12 0C5.389 0 0 5.35 0 12s5.35 12 12 12 12-5.35 12-12S18.611 0 12 0zm0 18c-3.325 0-6-2.675-6-6s2.675-6 6-6 6 2.675 6 6-2.675 6-6 6z"/>
      </svg>
    ),
    bgColor: 'bg-white',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-300',
    hoverBg: 'hover:bg-gray-50',
  },
  github: {
    name: 'GitHub',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
      </svg>
    ),
    bgColor: 'bg-gray-900',
    textColor: 'text-white',
    borderColor: 'border-gray-900',
    hoverBg: 'hover:bg-gray-800',
  },
  saml: {
    name: 'SSO',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
        <polyline points="10 17 15 12 10 7"/>
        <line x1="15" y1="12" x2="3" y2="12"/>
      </svg>
    ),
    bgColor: 'bg-blue-600',
    textColor: 'text-white',
    borderColor: 'border-blue-600',
    hoverBg: 'hover:bg-blue-700',
  },
  custom: {
    name: 'SSO',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
    bgColor: 'bg-indigo-600',
    textColor: 'text-white',
    borderColor: 'border-indigo-600',
    hoverBg: 'hover:bg-indigo-700',
  },
};

const SSOLoginButton = ({ 
  provider, 
  connectionId, 
  connectionName,
  protocol = 'saml',
  className = '',
  disabled = false,
  fullWidth = true,
}) => {
  const config = PROVIDER_CONFIG[provider] || PROVIDER_CONFIG.custom;
  const displayName = connectionName || config.name;
  
  const handleClick = () => {
    if (disabled) return;
    
    // Redirect to SSO login endpoint
    const baseUrl = import.meta.env.VITE_API_URL || '';
    const loginUrl = `${baseUrl}/api/v1/auth/sso/${protocol}/${connectionId}/login`;
    
    // Add return URL
    const returnTo = encodeURIComponent(window.location.pathname);
    window.location.href = `${loginUrl}?return_to=${returnTo}`;
  };
  
  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`
        flex items-center justify-center gap-3
        px-4 py-3
        ${config.bgColor}
        ${config.textColor}
        border ${config.borderColor}
        ${config.hoverBg}
        rounded-lg
        font-medium
        transition-colors duration-200
        ${fullWidth ? 'w-full' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >
      {config.icon}
      <span>Continue with {displayName}</span>
    </button>
  );
};

SSOLoginButton.propTypes = {
  provider: PropTypes.string.isRequired,
  connectionId: PropTypes.string.isRequired,
  connectionName: PropTypes.string,
  protocol: PropTypes.oneOf(['saml', 'oauth', 'oidc']),
  className: PropTypes.string,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
};

export default SSOLoginButton;
```

### 10.2 SSO Login Page

**File:** `frontend/src/pages/auth/SSOLoginPage.jsx`

```jsx
/**
 * SSO Login Page
 * Shows available SSO options and email domain discovery
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import SSOLoginButton from '../../components/sso/SSOLoginButton';
import { ssoApi } from '../../services/ssoApi';

const SSOLoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ssoConnections, setSsoConnections] = useState([]);
  const [showSSOOptions, setShowSSOOptions] = useState(false);
  
  // Check for error from callback
  useEffect(() => {
    const errorParam = searchParams.get('error');
    const message = searchParams.get('message');
    
    if (errorParam) {
      setError(message || t(`auth.errors.${errorParam}`, errorParam));
    }
  }, [searchParams, t]);
  
  // Discover SSO by email domain
  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !email.includes('@')) {
      setError(t('auth.errors.invalidEmail'));
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await ssoApi.discoverSSO(email);
      
      if (result.sso_available && result.connections.length > 0) {
        setSsoConnections(result.connections);
        setShowSSOOptions(true);
      } else {
        // No SSO configured, redirect to regular login
        navigate(`/login?email=${encodeURIComponent(email)}`);
      }
    } catch (err) {
      console.error('SSO discovery error:', err);
      // Fall back to regular login
      navigate(`/login?email=${encodeURIComponent(email)}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleBackToEmail = () => {
    setShowSSOOptions(false);
    setSsoConnections([]);
  };
  
  const handleUsePassword = () => {
    navigate(`/login?email=${encodeURIComponent(email)}`);
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-xl flex items-center justify-center">
            <span className="text-2xl font-bold text-white">LA</span>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            {t('auth.signIn', 'Sign in to your account')}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            LogiAccounting Pro
          </p>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
        
        {/* SSO Options */}
        {showSSOOptions ? (
          <div className="space-y-4">
            <p className="text-center text-gray-600">
              {t('auth.ssoAvailable', 'SSO is available for your organization')}
            </p>
            
            <div className="space-y-3">
              {ssoConnections.map((connection) => (
                <SSOLoginButton
                  key={connection.id}
                  provider={connection.provider}
                  connectionId={connection.id}
                  connectionName={connection.name}
                  protocol={connection.protocol}
                />
              ))}
            </div>
            
            <div className="relative py-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">
                  {t('common.or', 'or')}
                </span>
              </div>
            </div>
            
            <button
              type="button"
              onClick={handleUsePassword}
              className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              {t('auth.usePassword', 'Sign in with password instead')}
            </button>
            
            <button
              type="button"
              onClick={handleBackToEmail}
              className="w-full px-4 py-2 text-sm text-blue-600 hover:text-blue-700"
            >
              {t('common.back', '← Back')}
            </button>
          </div>
        ) : (
          /* Email Discovery Form */
          <form onSubmit={handleEmailSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                {t('auth.email', 'Email address')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="you@company.com"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                t('auth.continue', 'Continue')
              )}
            </button>
            
            <div className="relative py-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">
                  {t('auth.quickAccess', 'Quick access')}
                </span>
              </div>
            </div>
            
            {/* Common SSO Providers */}
            <div className="space-y-3">
              <SSOLoginButton
                provider="microsoft"
                connectionId="microsoft-default"
                protocol="oauth"
              />
              <SSOLoginButton
                provider="google"
                connectionId="google-default"
                protocol="oauth"
              />
            </div>
          </form>
        )}
        
        {/* Footer Links */}
        <div className="text-center text-sm text-gray-600">
          <a href="/help" className="hover:text-blue-600">
            {t('auth.needHelp', 'Need help signing in?')}
          </a>
        </div>
      </div>
    </div>
  );
};

export default SSOLoginPage;
```

### 10.3 SSO Callback Page

**File:** `frontend/src/pages/auth/SSOCallbackPage.jsx`

```jsx
/**
 * SSO Callback Page
 * Handles OAuth/SAML callback and token exchange
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setCredentials } from '../../store/slices/authSlice';

const SSOCallbackPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const processCallback = async () => {
      // Get tokens from URL params
      const token = searchParams.get('token');
      const refresh = searchParams.get('refresh');
      const returnTo = searchParams.get('return_to') || '/dashboard';
      const errorParam = searchParams.get('error');
      const errorMessage = searchParams.get('message');
      
      // Check for errors
      if (errorParam) {
        setError(errorMessage || `Authentication failed: ${errorParam}`);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }
      
      // Validate tokens
      if (!token) {
        setError('No authentication token received');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }
      
      try {
        // Store tokens
        localStorage.setItem('access_token', token);
        if (refresh) {
          localStorage.setItem('refresh_token', refresh);
        }
        
        // Fetch user profile
        const response = await fetch('/api/v1/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch user profile');
        }
        
        const userData = await response.json();
        
        // Update Redux store
        dispatch(setCredentials({
          user: userData,
          token,
          refreshToken: refresh,
        }));
        
        // Redirect to intended destination
        navigate(returnTo, { replace: true });
        
      } catch (err) {
        console.error('SSO callback error:', err);
        setError(err.message || 'Authentication failed');
        setTimeout(() => navigate('/login'), 3000);
      }
    };
    
    processCallback();
  }, [searchParams, navigate, dispatch]);
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-6 text-center">
          <div className="mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Authentication Failed
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-6 text-center">
        <div className="animate-spin mx-auto h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Completing Sign In
        </h2>
        <p className="text-gray-600">
          Please wait while we verify your authentication...
        </p>
      </div>
    </div>
  );
};

export default SSOCallbackPage;
```

### 10.4 SSO API Service

**File:** `frontend/src/services/ssoApi.js`

```javascript
/**
 * SSO API Service
 * Client for SSO-related API endpoints
 */

import api from './api';

export const ssoApi = {
  /**
   * Discover SSO by email domain
   * @param {string} email - User email
   * @returns {Promise<{sso_available: boolean, connections: Array}>}
   */
  async discoverSSO(email) {
    const response = await api.post('/auth/sso/discover', { email });
    return response.data;
  },
  
  /**
   * List SSO connections for organization
   * @returns {Promise<Array>}
   */
  async listConnections() {
    const response = await api.get('/sso/connections');
    return response.data.connections;
  },
  
  /**
   * Get SSO connection details
   * @param {string} connectionId 
   * @returns {Promise<Object>}
   */
  async getConnection(connectionId) {
    const response = await api.get(`/sso/connections/${connectionId}`);
    return response.data;
  },
  
  /**
   * Create SSO connection
   * @param {Object} data - Connection configuration
   * @returns {Promise<Object>}
   */
  async createConnection(data) {
    const response = await api.post('/sso/connections', data);
    return response.data;
  },
  
  /**
   * Update SSO connection
   * @param {string} connectionId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async updateConnection(connectionId, data) {
    const response = await api.put(`/sso/connections/${connectionId}`, data);
    return response.data;
  },
  
  /**
   * Delete SSO connection
   * @param {string} connectionId 
   * @returns {Promise<void>}
   */
  async deleteConnection(connectionId) {
    await api.delete(`/sso/connections/${connectionId}`);
  },
  
  /**
   * Test SSO connection
   * @param {string} connectionId 
   * @returns {Promise<{success: boolean, checks: Array}>}
   */
  async testConnection(connectionId) {
    const response = await api.post(`/sso/connections/${connectionId}/test`);
    return response.data;
  },
  
  /**
   * Get SP metadata for SAML
   * @param {string} connectionId 
   * @returns {Promise<string>} XML metadata
   */
  async getSPMetadata(connectionId) {
    const response = await api.get(`/saml/${connectionId}/metadata`, {
      responseType: 'text',
    });
    return response.data;
  },
  
  /**
   * Parse IdP metadata
   * @param {string} connectionId 
   * @param {{metadata_url?: string, metadata_xml?: string}} data 
   * @returns {Promise<Object>}
   */
  async parseIdPMetadata(connectionId, data) {
    const response = await api.post(`/saml/${connectionId}/parse-metadata`, data);
    return response.data.parsed;
  },
  
  /**
   * Initiate SSO logout
   * @param {string} connectionId 
   * @returns {Promise<{success: boolean, redirect?: string}>}
   */
  async logout(connectionId) {
    const response = await api.post(`/sso/oauth/${connectionId}/logout`);
    return response.data;
  },
  
  /**
   * Generate SCIM token
   * @param {string} connectionId 
   * @returns {Promise<{token: string}>}
   */
  async generateSCIMToken(connectionId) {
    const response = await api.post(`/sso/connections/${connectionId}/scim-token`);
    return response.data;
  },
  
  /**
   * Get SCIM sync logs
   * @param {string} connectionId 
   * @param {number} limit 
   * @returns {Promise<Array>}
   */
  async getSCIMLogs(connectionId, limit = 100) {
    const response = await api.get(`/sso/connections/${connectionId}/scim-logs`, {
      params: { limit },
    });
    return response.data.logs;
  },
};

export default ssoApi;
```

---

## TASK 11: SSO ADMIN CONFIGURATION PAGE

**File:** `frontend/src/pages/admin/sso/SSOConfigPage.jsx`

```jsx
/**
 * SSO Configuration Page
 * Admin interface for managing SSO connections
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ssoApi } from '../../../services/ssoApi';
import Card from '../../../components/common/Card';
import Button from '../../../components/common/Button';
import Badge from '../../../components/common/Badge';
import Modal from '../../../components/common/Modal';
import SSOConfigForm from './SSOConfigForm';

// Provider icons
const providerIcons = {
  microsoft: '🔷',
  azure_ad: '🔷',
  google: '🔴',
  okta: '🟠',
  onelogin: '🟣',
  github: '⚫',
  saml: '🔐',
  custom: '⚙️',
};

const SSOConfigPage = () => {
  const { t } = useTranslation();
  
  const [connections, setConnections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingConnection, setEditingConnection] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [testResult, setTestResult] = useState(null);
  
  useEffect(() => {
    loadConnections();
  }, []);
  
  const loadConnections = async () => {
    try {
      setIsLoading(true);
      const data = await ssoApi.listConnections();
      setConnections(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCreateNew = () => {
    setEditingConnection(null);
    setShowModal(true);
  };
  
  const handleEdit = (connection) => {
    setEditingConnection(connection);
    setShowModal(true);
  };
  
  const handleSave = async (data) => {
    try {
      if (editingConnection) {
        await ssoApi.updateConnection(editingConnection.id, data);
      } else {
        await ssoApi.createConnection(data);
      }
      setShowModal(false);
      loadConnections();
    } catch (err) {
      throw err;
    }
  };
  
  const handleDelete = async (connectionId) => {
    if (!window.confirm(t('sso.confirmDelete'))) return;
    
    try {
      await ssoApi.deleteConnection(connectionId);
      loadConnections();
    } catch (err) {
      setError(err.message);
    }
  };
  
  const handleTest = async (connectionId) => {
    setTestingId(connectionId);
    setTestResult(null);
    
    try {
      const result = await ssoApi.testConnection(connectionId);
      setTestResult({ connectionId, ...result });
    } catch (err) {
      setTestResult({ connectionId, success: false, error: err.message });
    } finally {
      setTestingId(null);
    }
  };
  
  const handleToggleStatus = async (connection) => {
    try {
      await ssoApi.updateConnection(connection.id, {
        status: connection.status === 'active' ? 'inactive' : 'active',
      });
      loadConnections();
    } catch (err) {
      setError(err.message);
    }
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }
  
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('sso.title', 'Single Sign-On')}
          </h1>
          <p className="mt-1 text-gray-600">
            {t('sso.description', 'Configure identity providers for your organization')}
          </p>
        </div>
        <Button onClick={handleCreateNew}>
          {t('sso.addProvider', '+ Add Identity Provider')}
        </Button>
      </div>
      
      {/* Error */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      
      {/* Connections List */}
      <div className="space-y-4">
        {connections.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <div className="text-5xl mb-4">🔐</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {t('sso.noProviders', 'No Identity Providers Configured')}
              </h3>
              <p className="text-gray-600 mb-4">
                {t('sso.noProvidersDescription', 'Add an identity provider to enable SSO for your organization')}
              </p>
              <Button onClick={handleCreateNew}>
                {t('sso.addFirst', 'Add Your First Provider')}
              </Button>
            </div>
          </Card>
        ) : (
          connections.map((connection) => (
            <Card key={connection.id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Provider Icon */}
                  <div className="text-3xl">
                    {providerIcons[connection.provider] || '🔐'}
                  </div>
                  
                  {/* Connection Info */}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">
                        {connection.name}
                      </h3>
                      <Badge
                        variant={connection.status === 'active' ? 'success' : 'warning'}
                      >
                        {connection.status}
                      </Badge>
                      {connection.is_default && (
                        <Badge variant="info">Default</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      {connection.protocol.toUpperCase()} • {connection.provider}
                    </p>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTest(connection.id)}
                    disabled={testingId === connection.id}
                  >
                    {testingId === connection.id ? (
                      <span className="animate-spin">⟳</span>
                    ) : (
                      t('sso.test', 'Test')
                    )}
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(connection)}
                  >
                    {t('common.edit', 'Edit')}
                  </Button>
                  
                  <Button
                    variant={connection.status === 'active' ? 'warning' : 'success'}
                    size="sm"
                    onClick={() => handleToggleStatus(connection)}
                  >
                    {connection.status === 'active' ? t('sso.disable', 'Disable') : t('sso.enable', 'Enable')}
                  </Button>
                  
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(connection.id)}
                  >
                    {t('common.delete', 'Delete')}
                  </Button>
                </div>
              </div>
              
              {/* Test Result */}
              {testResult && testResult.connectionId === connection.id && (
                <div className={`mt-4 p-3 rounded-lg ${testResult.success ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="flex items-center gap-2">
                    <span>{testResult.success ? '✅' : '❌'}</span>
                    <span className={testResult.success ? 'text-green-700' : 'text-red-700'}>
                      {testResult.success ? t('sso.testSuccess', 'Configuration is valid') : t('sso.testFailed', 'Configuration has issues')}
                    </span>
                  </div>
                  {testResult.checks && (
                    <ul className="mt-2 space-y-1">
                      {testResult.checks.map((check, i) => (
                        <li key={i} className="text-sm flex items-center gap-2">
                          <span>{check.status === 'ok' ? '✓' : '✗'}</span>
                          <span>{check.name}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </Card>
          ))
        )}
      </div>
      
      {/* SCIM Configuration */}
      <Card className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {t('sso.scim.title', 'SCIM Provisioning')}
        </h2>
        <p className="text-gray-600 mb-4">
          {t('sso.scim.description', 'Automatically sync users from your identity provider')}
        </p>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('sso.scim.endpoint', 'SCIM Endpoint')}
              </label>
              <code className="block mt-1 text-sm bg-gray-100 px-3 py-2 rounded">
                {window.location.origin}/scim/v2
              </code>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('sso.scim.token', 'Bearer Token')}
              </label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 text-sm bg-gray-100 px-3 py-2 rounded">
                  ••••••••••••••••
                </code>
                <Button variant="outline" size="sm">
                  {t('sso.scim.regenerate', 'Regenerate')}
                </Button>
              </div>
            </div>
          </div>
        </div>
        
        <Link to="/admin/sso/scim-logs" className="inline-block mt-4 text-blue-600 hover:text-blue-700">
          {t('sso.scim.viewLogs', 'View Provisioning Logs →')}
        </Link>
      </Card>
      
      {/* Configuration Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingConnection ? t('sso.editProvider', 'Edit Identity Provider') : t('sso.addProvider', 'Add Identity Provider')}
        size="lg"
      >
        <SSOConfigForm
          connection={editingConnection}
          onSubmit={handleSave}
          onCancel={() => setShowModal(false)}
        />
      </Modal>
    </div>
  );
};

export default SSOConfigPage;
```

---

## SUMMARY

### Files Created in Part 3

| File | Purpose |
|------|---------|
| `backend/app/schemas/scim.py` | SCIM 2.0 Pydantic schemas |
| `backend/app/services/sso/scim_service.py` | SCIM service with user operations |
| `backend/app/routes/scim.py` | SCIM 2.0 REST API endpoints |
| `backend/app/services/sso_service.py` | Main SSO service |
| `frontend/src/components/sso/SSOLoginButton.jsx` | SSO login button component |
| `frontend/src/pages/auth/SSOLoginPage.jsx` | SSO login page with discovery |
| `frontend/src/pages/auth/SSOCallbackPage.jsx` | OAuth/SAML callback handler |
| `frontend/src/services/ssoApi.js` | SSO API client |
| `frontend/src/pages/admin/sso/SSOConfigPage.jsx` | Admin SSO configuration |

### Complete Phase 12 Implementation

| Part | Content |
|------|---------|
| **Part 1** | Database models, SAML 2.0 config, processor, metadata |
| **Part 2** | OAuth2/OIDC providers (Microsoft, Google, Okta, GitHub), State manager |
| **Part 3** | SCIM 2.0 provisioning, SSO Service, Frontend UI components |

---

*Phase 12 Tasks Part 3 - LogiAccounting Pro*
*SCIM 2.0 Provisioning & Frontend SSO UI*
