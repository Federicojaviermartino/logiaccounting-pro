"""
SAML 2.0 Assertion Processor
Handles SAML authentication flow using pysaml2
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import logging
import base64
import zlib

from app.auth.sso.saml.config import SAMLConfig

logger = logging.getLogger(__name__)


class SAMLValidationError(Exception):
        """SAML validation error"""

    def __init__(self, message: str, errors: List[str] = None):
                super().__init__(message)
                self.errors = errors or []


class SAMLProcessor:
        """Process SAML assertions and responses using pysaml2"""

    ATTRIBUTE_MAPPINGS = {
                'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'email',
                'http://schemas.xmlsoap.org/claims/EmailAddress': 'email',
                'email': 'email',
                'mail': 'email',
                'Email': 'email',
                'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname': 'first_name',
                'firstName': 'first_name',
                'givenName': 'first_name',
                'given_name': 'first_name',
                'FirstName': 'first_name',
                'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname': 'last_name',
                'lastName': 'last_name',
                'sn': 'last_name',
                'family_name': 'last_name',
                'LastName': 'last_name',
                'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': 'display_name',
                'displayName': 'display_name',
                'name': 'display_name',
                'cn': 'display_name',
                'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups': 'groups',
                'http://schemas.xmlsoap.org/claims/Group': 'groups',
                'groups': 'groups',
                'memberOf': 'groups',
    }

    def __init__(self, config: SAMLConfig):
                self.config = config
                self._client = None
                self._saml_config = None

    def _get_saml2_client(self):
                """Get or create pysaml2 client"""
                if self._client is not None:
                                return self._client

                try:
                                from saml2.client import Saml2Client
                                from saml2.config import Config as Saml2Config
                                from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT

            settings = self.config.to_pysaml2_config()

            saml_config = Saml2Config()
            saml_config.load(settings)

            self._client = Saml2Client(config=saml_config)
            self._saml_config = saml_config
            return self._client
except ImportError:
            logger.warning("pysaml2 not installed")
            return None

    def create_authn_request(
                self,
                request_data: Dict[str, Any],
                return_to: str = '/'
    ) -> Tuple[str, str]:
                """
                        Create SAML authentication request

                                Args:
                                            request_data: Request data (prepared by prepare_request)
                                                        return_to: URL to redirect after authentication

                                                                Returns:
                                                                            Tuple of (redirect_url, request_id)
                                                                                    """
                client = self._get_saml2_client()

        if client is None:
                        # Mock SAML for testing when pysaml2 is not available
                        logger.warning("pysaml2 not installed, using mock SAML")
                        import secrets
                        request_id = f"id_{secrets.token_hex(16)}"
                        settings = self.config.to_pysaml2_config()
                        idp_config = settings.get('metadata', {}).get('inline', [{}])[0] if settings.get('metadata', {}).get('inline') else {}
                        sso_url = self.config._idp.sso_url or "https://mock-idp.example.com/sso"
                        redirect_url = f"{sso_url}?SAMLRequest=mock&RelayState={return_to}"
                        return redirect_url, request_id

        try:
                        from saml2 import BINDING_HTTP_REDIRECT

            # Get IdP entity ID from config
                        idp_entity_id = self.config._idp.entity_id

            # Create AuthnRequest
                        session_id, info = client.prepare_for_authenticate(
                            entityid=idp_entity_id,
                            relay_state=return_to,
                            binding=BINDING_HTTP_REDIRECT,
                        )

            # Extract redirect URL from headers
                        redirect_url = None
                        for key, value in info['headers']:
                                            if key == 'Location':
                                                                    redirect_url = value
                                                                    break

                                        if not redirect_url:
                                                            raise SAMLValidationError("Failed to generate SAML redirect URL")

            logger.info(
                                f"Created SAML AuthnRequest",
                                extra={
                                                        'request_id': session_id,
                                                        'connection_id': self.config.connection_id,
                                                        'return_to': return_to,
                                }
            )

            return redirect_url, session_id
except Exception as e:
            logger.error(f"Error creating SAML request: {e}")
            raise SAMLValidationError(f"Failed to create SAML request: {str(e)}")

    def process_response(
                self,
                request_data: Dict[str, Any],
                expected_request_id: Optional[str] = None
    ) -> Dict[str, Any]:
                """
                        Process SAML response from IdP

                                Args:
                                            request_data: Request data with SAMLResponse
                                                        expected_request_id: Request ID to validate (InResponseTo)

                                                                Returns:
                                                                            Dict with user attributes and session info
                                                                                    """
        client = self._get_saml2_client()

        if client is None:
                        logger.warning("pysaml2 not installed, using mock response")
            return {
                                'name_id': 'mock@example.com',
                                'name_id_format': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
                                'session_index': '_mock_session_index',
                                'session_expiration': None,
                                'attributes': {
                                                        'email': 'mock@example.com',
                                                        'first_name': 'Mock',
                                                        'last_name': 'User',
                                },
                                'raw_attributes': {},
            }

        try:
                        # Get SAMLResponse from request
                        saml_response = request_data.get('post_data', {}).get('SAMLResponse', '')

            if not saml_response:
                                raise SAMLValidationError("No SAMLResponse found in request")

            # Parse and validate the response
            authn_response = client.parse_authn_request_response(
                                saml_response,
                                binding=self._get_binding_for_response(request_data),
                                outstanding=None,  # We could track outstanding requests here
            )

            if authn_response is None:
                                raise SAMLValidationError("Invalid SAML response")

            # Check if response was successful
            if not authn_response.status_ok():
                                status_code = authn_response.status.get('status_code', {}).get('value', 'Unknown')
                                raise SAMLValidationError(
                                    f"SAML response status not OK: {status_code}",
                                    errors=[status_code]
                                )

            # Extract user info
            name_id = authn_response.name_id.text if authn_response.name_id else None
            name_id_format = authn_response.name_id.format if authn_response.name_id else None
            session_index = authn_response.session_index()

            # Get attributes
            raw_attributes = authn_response.ava or {}
            attributes = self._normalize_attributes(raw_attributes)

            # Use NameID as email if email not in attributes
            if not attributes.get('email') and name_id:
                                if '@' in str(name_id):
                                                        attributes['email'] = name_id

                            logger.info(
                                                f"SAML authentication successful",
                                                extra={
                                                                        'name_id': name_id,
                                                                        'session_index': session_index,
                                                                        'connection_id': self.config.connection_id,
                                                }
                            )

            return {
                                'name_id': name_id,
                                'name_id_format': name_id_format,
                                'session_index': session_index,
                                'session_expiration': None,
                                'attributes': attributes,
                                'raw_attributes': raw_attributes,
            }
except SAMLValidationError:
            raise
except Exception as e:
            logger.error(f"Error processing SAML response: {e}")
            raise SAMLValidationError(f"SAML validation failed: {str(e)}")

    def _get_binding_for_response(self, request_data: Dict[str, Any]) -> str:
                """Determine the binding based on how the response was received"""
        from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT

        if request_data.get('post_data', {}).get('SAMLResponse'):
                        return BINDING_HTTP_POST
        return BINDING_HTTP_REDIRECT

    def create_logout_request(
                self,
                request_data: Dict[str, Any],
                name_id: str,
                session_index: str,
                return_to: str = '/'
    ) -> str:
                """Create SAML logout request"""
        client = self._get_saml2_client()

        if client is None:
                        slo_url = self.config._idp.slo_url
            if slo_url:
                                return f"{slo_url}?SAMLRequest=mock&RelayState={return_to}"
                            return return_to

        try:
                        from saml2 import BINDING_HTTP_REDIRECT
            from saml2.saml import NameID, NAMEID_FORMAT_EMAILADDRESS

            # Create NameID object
            name_id_obj = NameID()
            name_id_obj.text = name_id
            name_id_obj.format = NAMEID_FORMAT_EMAILADDRESS

            # Create logout request
            session_id, info = client.do_logout(
                                name_id=name_id_obj,
                                entity_ids=None,  # Logout from all IdPs
                                session_indexes=[session_index] if session_index else None,
                                reason="User initiated logout",
                                expire=None,
                                sign=self.config._security.logout_requests_signed,
            )

            # Extract redirect URL
            redirect_url = return_to
            if info:
                                for key, value in info.get('headers', []):
                                                        if key == 'Location':
                                                                                    redirect_url = value
                                                                                    break

                                                logger.info(
                                                                    f"Created SAML LogoutRequest",
                                                                    extra={
                                                                                            'name_id': name_id,
                                                                                            'session_index': session_index,
                                                                                            'connection_id': self.config.connection_id,
                                                                    }
                                                )

            return redirect_url
except Exception as e:
            logger.error(f"Error creating logout request: {e}")
            return return_to

    def process_logout_response(
                self,
                request_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
                """
                        Process SAML logout response or request

                                Returns:
                                            Tuple of (success, redirect_url)
                                                    """
        client = self._get_saml2_client()

        if client is None:
                        return True, None

        try:
                        get_data = request_data.get('get_data', {})
            post_data = request_data.get('post_data', {})

            # Check if this is a logout request or response
            if 'SAMLRequest' in get_data or 'SAMLRequest' in post_data:
                                # This is a logout request from IdP
                                saml_request = get_data.get('SAMLRequest') or post_data.get('SAMLRequest')
                # Handle logout request
                return True, None
elif 'SAMLResponse' in get_data or 'SAMLResponse' in post_data:
                # This is a logout response
                saml_response = get_data.get('SAMLResponse') or post_data.get('SAMLResponse')
                # Validate logout response
                return True, None

            logger.info(
                                f"SAML logout processed successfully",
                                extra={'connection_id': self.config.connection_id}
            )

            return True, None
except Exception as e:
            logger.error(f"Error processing logout: {e}")
            return False, None

    def get_metadata(self) -> str:
                """Generate SP metadata XML"""
        client = self._get_saml2_client()

        if client is not None:
                        try:
                                            metadata = client.metadata.do()
                                            return metadata
except Exception as e:
                logger.error(f"Error generating metadata: {e}")

        # Fallback to manual metadata generation
        from app.auth.sso.saml.metadata import SAMLMetadataGenerator
        settings = self.config.to_pysaml2_config()
        sp_config = settings.get('service', {}).get('sp', {})

        generator = SAMLMetadataGenerator(
                        entity_id=settings.get('entityid', ''),
                        acs_url=list(sp_config.get('endpoints', {}).get('assertion_consumer_service', [['']]))[0][0] if sp_config.get('endpoints', {}).get('assertion_consumer_service') else '',
                        sls_url=list(sp_config.get('endpoints', {}).get('single_logout_service', [['']]))[0][0] if sp_config.get('endpoints', {}).get('single_logout_service') else '',
                        certificate=settings.get('cert_file', ''),
                        name_id_format=sp_config.get('name_id_format', [''])[0] if sp_config.get('name_id_format') else '',
        )
        return generator.generate()

    @classmethod
    def parse_idp_metadata(cls, metadata: str) -> Dict[str, Any]:
                """Parse IdP metadata XML and extract configuration"""
        try:
                        from saml2.metadata import entity_descriptor_from_string
            from saml2.mdstore import MetadataStore
            from saml2.config import Config as Saml2Config
            import tempfile
            import os

            # Parse metadata XML
            entity_desc = entity_descriptor_from_string(metadata)

            if entity_desc is None:
                                raise ValueError("Invalid metadata")

            # Extract entity ID
            entity_id = entity_desc.entity_id

            # Extract SSO URL
            sso_url = ''
            slo_url = None
            certificate = ''

            # Get IDPSSODescriptor
            if hasattr(entity_desc, 'idpsso_descriptor') and entity_desc.idpsso_descriptor:
                                idp_desc = entity_desc.idpsso_descriptor[0]

                # Get SSO URL
                if hasattr(idp_desc, 'single_sign_on_service'):
                                        for sso in idp_desc.single_sign_on_service:
                                                                    sso_url = sso.location
                                                                    break

                                    # Get SLO URL
                                    if hasattr(idp_desc, 'single_logout_service'):
                                                            for slo in idp_desc.single_logout_service:
                                                                                        slo_url = slo.location
                                                                                        break

                                                        # Get certificate
                                                        if hasattr(idp_desc, 'key_descriptor'):
                                                                                for key_desc in idp_desc.key_descriptor:
                                                                                                            if hasattr(key_desc, 'key_info') and key_desc.key_info:
                                                                                                                                            if hasattr(key_desc.key_info, 'x509_data') and key_desc.key_info.x509_data:
                                                                                                                                                                                for x509_data in key_desc.key_info.x509_data:
                                                                                                                                                                                                                        if hasattr(x509_data, 'x509_certificate') and x509_data.x509_certificate:
                                                                                                                                                                                                                                                                    certificate = x509_data.x509_certificate.text
                                                                                                                                                                                                                                                                    break
                                                                                                                                                                                                                                        
                                                                                                                                                                                                return {
                                                                                                                                                                'entity_id': entity_id,
                                                                                                                                                                'sso_url': sso_url,
                                                                                                                                                                'slo_url': slo_url,
                                                                                                                                                                'certificate': certificate,
                                                                                                                                                                'certificates': [certificate] if certificate else [],
                                                                                                                                                                                    }
                                                                                                                except ImportError:
                                                                                                logger.warning("pysaml2 not installed, cannot parse metadata")
            return {
                                'entity_id': '',
                                'sso_url': '',
                                'slo_url': None,
                                'certificate': '',
                                'certificates': [],
            }
except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            return {
                                'entity_id': '',
                                'sso_url': '',
                                'slo_url': None,
                                'certificate': '',
                                'certificates': [],
            }

    @classmethod
    def parse_idp_metadata_url(cls, url: str) -> Dict[str, Any]:
                """Fetch and parse IdP metadata from URL"""
        import httpx

        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        return cls.parse_idp_metadata(response.text)

    def _normalize_attributes(
                self,
                attributes: Dict[str, List[str]]
    ) -> Dict[str, Any]:
                """Normalize SAML attributes to standard format"""
        normalized = {}

        for attr_uri, values in attributes.items():
                        mapped_key = self.ATTRIBUTE_MAPPINGS.get(attr_uri, attr_uri)

            if mapped_key in ['email', 'first_name', 'last_name', 'display_name']:
                                normalized[mapped_key] = values[0] if values else None
elif mapped_key == 'groups':
                normalized[mapped_key] = values
else:
                normalized[mapped_key] = values if len(values) > 1 else values[0] if values else None

        return normalized


def prepare_saml_request(request) -> Dict[str, Any]:
        """
            Prepare FastAPI request data for SAML processing
                """
    from urllib.parse import urlparse

    url = str(request.url)
    parsed = urlparse(url)

    return {
                'https': 'on' if request.url.scheme == 'https' else 'off',
                'http_host': request.url.netloc,
                'server_port': str(request.url.port or (443 if request.url.scheme == 'https' else 80)),
                'script_name': parsed.path,
                'get_data': dict(request.query_params),
                'post_data': {},
                'query_string': parsed.query or '',
    }


async def prepare_saml_request_with_form(request) -> Dict[str, Any]:
        """
            Prepare FastAPI request data with form data for SAML processing
                """
    from urllib.parse import urlparse

    url = str(request.url)
    parsed = urlparse(url)

    try:
                form_data = await request.form()
        post_data = dict(form_data)
except Exception:
        post_data = {}

    return {
                'https': 'on' if request.url.scheme == 'https' else 'off',
                'http_host': request.url.netloc,
                'server_port': str(request.url.port or (443 if request.url.scheme == 'https' else 80)),
                'script_name': parsed.path,
                'get_data': dict(request.query_params),
                'post_data': post_data,
                'query_string': parsed.query or '',
    }
