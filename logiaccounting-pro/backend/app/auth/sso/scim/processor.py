"""
SCIM 2.0 Request Processor
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import uuid4
import re

from app.auth.sso.scim.schemas import (
    SCIMUser,
    SCIMUserCreate,
    SCIMUserPatch,
    SCIMGroup,
    SCIMListResponse,
    SCIMError,
    SCIMMeta,
    SCIMName,
    SCIMEmail,
    SCIMServiceProviderConfig,
    SCIMResourceType,
    SCIMSchema,
    SCIMPatchOperation,
)


class SCIMException(Exception):
    """SCIM processing exception"""

    def __init__(
        self,
        status: int,
        detail: str,
        scim_type: str = None,
    ):
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.scim_type = scim_type

    def to_error_response(self) -> SCIMError:
        """Convert to SCIM error response"""
        return SCIMError(
            status=str(self.status),
            scimType=self.scim_type,
            detail=self.detail,
        )


class SCIMProcessor:
    """Process SCIM 2.0 requests"""

    def __init__(self, base_url: str, connection_id: str):
        self.base_url = base_url.rstrip("/")
        self.connection_id = connection_id

    def get_service_provider_config(self) -> SCIMServiceProviderConfig:
        """Get SCIM service provider configuration"""
        return SCIMServiceProviderConfig(
            documentationUri=f"{self.base_url}/docs",
            meta=SCIMMeta(
                resourceType="ServiceProviderConfig",
                location=f"{self.base_url}/ServiceProviderConfig",
            ),
        )

    def get_resource_types(self) -> List[SCIMResourceType]:
        """Get supported SCIM resource types"""
        return [
            SCIMResourceType(
                id="User",
                name="User",
                description="User Account",
                endpoint="/Users",
                schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
                schemaExtensions=[
                    {
                        "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                        "required": False,
                    }
                ],
                meta=SCIMMeta(
                    resourceType="ResourceType",
                    location=f"{self.base_url}/ResourceTypes/User",
                ),
            ),
            SCIMResourceType(
                id="Group",
                name="Group",
                description="Group",
                endpoint="/Groups",
                schema_uri="urn:ietf:params:scim:schemas:core:2.0:Group",
                meta=SCIMMeta(
                    resourceType="ResourceType",
                    location=f"{self.base_url}/ResourceTypes/Group",
                ),
            ),
        ]

    def get_schemas(self) -> List[SCIMSchema]:
        """Get SCIM schemas"""
        return [
            SCIMSchema(
                id="urn:ietf:params:scim:schemas:core:2.0:User",
                name="User",
                description="User Schema",
                attributes=self._get_user_schema_attributes(),
                meta=SCIMMeta(
                    resourceType="Schema",
                    location=f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:core:2.0:User",
                ),
            ),
            SCIMSchema(
                id="urn:ietf:params:scim:schemas:core:2.0:Group",
                name="Group",
                description="Group Schema",
                attributes=self._get_group_schema_attributes(),
                meta=SCIMMeta(
                    resourceType="Schema",
                    location=f"{self.base_url}/Schemas/urn:ietf:params:scim:schemas:core:2.0:Group",
                ),
            ),
        ]

    def _get_user_schema_attributes(self) -> List[Dict[str, Any]]:
        """Get user schema attributes definition"""
        return [
            {
                "name": "userName",
                "type": "string",
                "multiValued": False,
                "required": True,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "server",
            },
            {
                "name": "name",
                "type": "complex",
                "multiValued": False,
                "required": False,
                "subAttributes": [
                    {"name": "formatted", "type": "string"},
                    {"name": "familyName", "type": "string"},
                    {"name": "givenName", "type": "string"},
                ],
            },
            {
                "name": "displayName",
                "type": "string",
                "multiValued": False,
                "required": False,
            },
            {
                "name": "emails",
                "type": "complex",
                "multiValued": True,
                "required": False,
            },
            {
                "name": "active",
                "type": "boolean",
                "multiValued": False,
                "required": False,
            },
        ]

    def _get_group_schema_attributes(self) -> List[Dict[str, Any]]:
        """Get group schema attributes definition"""
        return [
            {
                "name": "displayName",
                "type": "string",
                "multiValued": False,
                "required": True,
            },
            {
                "name": "members",
                "type": "complex",
                "multiValued": True,
                "required": False,
            },
        ]

    def parse_filter(self, filter_str: Optional[str]) -> Dict[str, Any]:
        """Parse SCIM filter expression"""
        if not filter_str:
            return {}

        filters = {}

        eq_match = re.match(r'(\w+)\s+eq\s+"([^"]*)"', filter_str)
        if eq_match:
            filters[eq_match.group(1)] = eq_match.group(2)
            return filters

        username_match = re.match(r'userName\s+eq\s+"([^"]*)"', filter_str, re.IGNORECASE)
        if username_match:
            filters["userName"] = username_match.group(1)
            return filters

        email_match = re.match(r'emails\[type\s+eq\s+"work"\]\.value\s+eq\s+"([^"]*)"', filter_str, re.IGNORECASE)
        if email_match:
            filters["email"] = email_match.group(1)
            return filters

        external_id_match = re.match(r'externalId\s+eq\s+"([^"]*)"', filter_str, re.IGNORECASE)
        if external_id_match:
            filters["externalId"] = external_id_match.group(1)
            return filters

        return filters

    def user_to_scim(self, user: Dict[str, Any], external_identity: Dict[str, Any] = None) -> SCIMUser:
        """Convert internal user to SCIM user representation"""
        emails = []
        if user.get("email"):
            emails.append(SCIMEmail(
                value=user["email"],
                type="work",
                primary=True,
            ))

        name = None
        if user.get("first_name") or user.get("last_name"):
            name = SCIMName(
                givenName=user.get("first_name"),
                familyName=user.get("last_name"),
                formatted=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            )

        display_name = None
        if user.get("first_name") and user.get("last_name"):
            display_name = f"{user['first_name']} {user['last_name']}"
        elif user.get("first_name"):
            display_name = user["first_name"]
        elif user.get("email"):
            display_name = user["email"].split("@")[0]

        external_id = None
        if external_identity:
            external_id = external_identity.get("external_user_id")
        elif user.get("external_id"):
            external_id = user["external_id"]

        return SCIMUser(
            id=user["id"],
            externalId=external_id,
            userName=user.get("email", ""),
            name=name,
            displayName=display_name,
            active=user.get("status", "active") == "active",
            emails=emails if emails else None,
            meta=SCIMMeta(
                resourceType="User",
                created=user.get("created_at"),
                lastModified=user.get("updated_at"),
                location=f"{self.base_url}/Users/{user['id']}",
            ),
        )

    def scim_to_user_data(self, scim_user: SCIMUserCreate) -> Dict[str, Any]:
        """Convert SCIM user to internal user data"""
        user_data = {
            "email": scim_user.userName,
            "status": "active" if scim_user.active else "inactive",
        }

        if scim_user.name:
            user_data["first_name"] = scim_user.name.givenName
            user_data["last_name"] = scim_user.name.familyName

        if scim_user.emails:
            primary_email = next(
                (e.value for e in scim_user.emails if e.primary),
                scim_user.emails[0].value if scim_user.emails else None
            )
            if primary_email:
                user_data["email"] = primary_email

        if scim_user.displayName and not user_data.get("first_name"):
            name_parts = scim_user.displayName.split(" ", 1)
            user_data["first_name"] = name_parts[0]
            if len(name_parts) > 1:
                user_data["last_name"] = name_parts[1]

        if scim_user.phoneNumbers:
            primary_phone = next(
                (p.value for p in scim_user.phoneNumbers if p.primary),
                scim_user.phoneNumbers[0].value if scim_user.phoneNumbers else None
            )
            if primary_phone:
                user_data["phone"] = primary_phone

        return user_data

    def apply_patch_operations(
        self,
        user: Dict[str, Any],
        operations: List[SCIMPatchOperation],
    ) -> Dict[str, Any]:
        """Apply SCIM PATCH operations to user data"""
        updated_user = user.copy()

        for op in operations:
            operation = op.op.lower()
            path = op.path
            value = op.value

            if operation == "replace":
                updated_user = self._apply_replace(updated_user, path, value)
            elif operation == "add":
                updated_user = self._apply_add(updated_user, path, value)
            elif operation == "remove":
                updated_user = self._apply_remove(updated_user, path)
            else:
                raise SCIMException(
                    status=400,
                    detail=f"Unsupported operation: {operation}",
                    scim_type="invalidSyntax",
                )

        return updated_user

    def _apply_replace(
        self,
        user: Dict[str, Any],
        path: Optional[str],
        value: Any,
    ) -> Dict[str, Any]:
        """Apply SCIM replace operation"""
        if not path:
            if isinstance(value, dict):
                for key, val in value.items():
                    user = self._apply_replace(user, key, val)
            return user

        path_lower = path.lower()

        if path_lower == "active":
            user["status"] = "active" if value else "inactive"
        elif path_lower == "username":
            user["email"] = value
        elif path_lower == "name.givenname":
            user["first_name"] = value
        elif path_lower == "name.familyname":
            user["last_name"] = value
        elif path_lower == "displayname":
            if " " in value:
                parts = value.split(" ", 1)
                user["first_name"] = parts[0]
                user["last_name"] = parts[1]
            else:
                user["first_name"] = value
        elif path_lower.startswith("emails"):
            if isinstance(value, list) and value:
                primary_email = next(
                    (e.get("value") for e in value if e.get("primary")),
                    value[0].get("value") if value else None
                )
                if primary_email:
                    user["email"] = primary_email
            elif isinstance(value, str):
                user["email"] = value
        elif path_lower == "phonenumbers":
            if isinstance(value, list) and value:
                primary_phone = next(
                    (p.get("value") for p in value if p.get("primary")),
                    value[0].get("value") if value else None
                )
                if primary_phone:
                    user["phone"] = primary_phone

        return user

    def _apply_add(
        self,
        user: Dict[str, Any],
        path: Optional[str],
        value: Any,
    ) -> Dict[str, Any]:
        """Apply SCIM add operation"""
        return self._apply_replace(user, path, value)

    def _apply_remove(
        self,
        user: Dict[str, Any],
        path: Optional[str],
    ) -> Dict[str, Any]:
        """Apply SCIM remove operation"""
        if not path:
            return user

        path_lower = path.lower()

        if path_lower == "name.givenname":
            user["first_name"] = None
        elif path_lower == "name.familyname":
            user["last_name"] = None
        elif path_lower == "phonenumbers":
            user["phone"] = None

        return user

    def create_list_response(
        self,
        resources: List[Any],
        total_results: int,
        start_index: int = 1,
        items_per_page: int = 100,
    ) -> SCIMListResponse:
        """Create SCIM list response"""
        return SCIMListResponse(
            totalResults=total_results,
            startIndex=start_index,
            itemsPerPage=items_per_page,
            Resources=resources,
        )

    def validate_bearer_token(self, token: str, expected_token: str) -> bool:
        """Validate SCIM bearer token"""
        if not token or not expected_token:
            return False

        if token.startswith("Bearer "):
            token = token[7:]

        return token == expected_token
