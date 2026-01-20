"""
SCIM 2.0 Schema Definitions
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SCIMSchemas(str, Enum):
    """SCIM 2.0 Schema URIs"""
    USER = "urn:ietf:params:scim:schemas:core:2.0:User"
    ENTERPRISE_USER = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
    GROUP = "urn:ietf:params:scim:schemas:core:2.0:Group"
    LIST_RESPONSE = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
    PATCH_OP = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
    ERROR = "urn:ietf:params:scim:api:messages:2.0:Error"


class SCIMMeta(BaseModel):
    """SCIM resource metadata"""
    resourceType: str
    created: Optional[str] = None
    lastModified: Optional[str] = None
    location: Optional[str] = None
    version: Optional[str] = None


class SCIMName(BaseModel):
    """SCIM user name structure"""
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None
    middleName: Optional[str] = None
    honorificPrefix: Optional[str] = None
    honorificSuffix: Optional[str] = None


class SCIMEmail(BaseModel):
    """SCIM email structure"""
    value: str
    type: Optional[str] = "work"
    primary: Optional[bool] = False


class SCIMPhoneNumber(BaseModel):
    """SCIM phone number structure"""
    value: str
    type: Optional[str] = "work"
    primary: Optional[bool] = False


class SCIMAddress(BaseModel):
    """SCIM address structure"""
    streetAddress: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = "work"
    primary: Optional[bool] = False
    formatted: Optional[str] = None


class SCIMEnterpriseUser(BaseModel):
    """SCIM Enterprise User extension"""
    employeeNumber: Optional[str] = None
    costCenter: Optional[str] = None
    organization: Optional[str] = None
    division: Optional[str] = None
    department: Optional[str] = None
    manager: Optional[Dict[str, str]] = None


class SCIMGroupMember(BaseModel):
    """SCIM group member reference"""
    value: str
    display: Optional[str] = None
    type: Optional[str] = "User"
    ref: Optional[str] = Field(None, alias="$ref")


class SCIMUser(BaseModel):
    """SCIM 2.0 User Resource"""
    schemas: List[str] = [SCIMSchemas.USER.value]
    id: Optional[str] = None
    externalId: Optional[str] = None
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
    emails: Optional[List[SCIMEmail]] = None
    phoneNumbers: Optional[List[SCIMPhoneNumber]] = None
    addresses: Optional[List[SCIMAddress]] = None
    groups: Optional[List[Dict[str, str]]] = None
    roles: Optional[List[Dict[str, str]]] = None
    meta: Optional[SCIMMeta] = None

    class Config:
        populate_by_name = True


class SCIMUserCreate(BaseModel):
    """SCIM User creation request"""
    schemas: List[str] = [SCIMSchemas.USER.value]
    externalId: Optional[str] = None
    userName: str
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    active: Optional[bool] = True
    emails: Optional[List[SCIMEmail]] = None
    phoneNumbers: Optional[List[SCIMPhoneNumber]] = None

    class Config:
        populate_by_name = True


class SCIMPatchOperation(BaseModel):
    """Single SCIM PATCH operation"""
    op: str
    path: Optional[str] = None
    value: Optional[Any] = None


class SCIMUserPatch(BaseModel):
    """SCIM User PATCH request"""
    schemas: List[str] = [SCIMSchemas.PATCH_OP.value]
    Operations: List[SCIMPatchOperation]


class SCIMPatchOp(BaseModel):
    """SCIM PATCH operation request"""
    schemas: List[str] = [SCIMSchemas.PATCH_OP.value]
    Operations: List[SCIMPatchOperation]


class SCIMGroup(BaseModel):
    """SCIM 2.0 Group Resource"""
    schemas: List[str] = [SCIMSchemas.GROUP.value]
    id: Optional[str] = None
    externalId: Optional[str] = None
    displayName: str
    members: Optional[List[SCIMGroupMember]] = None
    meta: Optional[SCIMMeta] = None

    class Config:
        populate_by_name = True


class SCIMListResponse(BaseModel):
    """SCIM 2.0 List Response"""
    schemas: List[str] = [SCIMSchemas.LIST_RESPONSE.value]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int = 100
    Resources: List[Any] = []


class SCIMError(BaseModel):
    """SCIM 2.0 Error Response"""
    schemas: List[str] = [SCIMSchemas.ERROR.value]
    status: str
    scimType: Optional[str] = None
    detail: Optional[str] = None


class SCIMServiceProviderConfig(BaseModel):
    """SCIM Service Provider Configuration"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"]
    documentationUri: Optional[str] = None
    patch: Dict[str, bool] = {"supported": True}
    bulk: Dict[str, Any] = {
        "supported": False,
        "maxOperations": 0,
        "maxPayloadSize": 0
    }
    filter: Dict[str, Any] = {
        "supported": True,
        "maxResults": 200
    }
    changePassword: Dict[str, bool] = {"supported": False}
    sort: Dict[str, bool] = {"supported": False}
    etag: Dict[str, bool] = {"supported": False}
    authenticationSchemes: List[Dict[str, Any]] = [
        {
            "type": "oauthbearertoken",
            "name": "OAuth Bearer Token",
            "description": "Authentication using Bearer tokens",
            "specUri": "https://tools.ietf.org/html/rfc6750",
            "primary": True
        }
    ]
    meta: Optional[SCIMMeta] = None


class SCIMResourceType(BaseModel):
    """SCIM Resource Type definition"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"]
    id: str
    name: str
    description: Optional[str] = None
    endpoint: str
    schema_uri: str = Field(alias="schema")
    schemaExtensions: Optional[List[Dict[str, Any]]] = None
    meta: Optional[SCIMMeta] = None

    class Config:
        populate_by_name = True


class SCIMSchema(BaseModel):
    """SCIM Schema definition"""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:Schema"]
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    attributes: List[Dict[str, Any]] = []
    meta: Optional[SCIMMeta] = None
