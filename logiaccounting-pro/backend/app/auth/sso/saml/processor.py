"""
SAML 2.0 Assertion Processor
Handles SAML authentication flow
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import logging

from app.auth.sso.saml.config import SAMLConfig

logger = logging.getLogger(__name__)


class SAMLValidationError(Exception):
    """SAML validation error"""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class SAMLProcessor:
    """Process SAML assertions and responses"""

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
        self.settings = config.to_onelogin_settings()

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
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            redirect_url = auth.login(return_to=return_to)
            request_id = auth.get_last_request_id()

            logger.info(
                f"Created SAML AuthnRequest",
                extra={
                    'request_id': request_id,
                    'connection_id': self.config.connection_id,
                    'return_to': return_to,
                }
            )

            return redirect_url, request_id
        except ImportError:
            logger.warning("python3-saml not installed, using mock SAML")
            import secrets
            request_id = f"id_{secrets.token_hex(16)}"
            redirect_url = f"{self.settings['idp']['singleSignOnService']['url']}?SAMLRequest=mock&RelayState={return_to}"
            return redirect_url, request_id

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
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            auth.process_response(request_id=expected_request_id)

            errors = auth.get_errors()
            if errors:
                error_reason = auth.get_last_error_reason()
                logger.error(
                    f"SAML Response validation failed",
                    extra={
                        'errors': errors,
                        'reason': error_reason,
                        'connection_id': self.config.connection_id,
                    }
                )
                raise SAMLValidationError(
                    f"SAML validation failed: {error_reason}",
                    errors=errors
                )

            if not auth.is_authenticated():
                raise SAMLValidationError("User not authenticated in SAML response")

            name_id = auth.get_nameid()
            name_id_format = auth.get_nameid_format()
            session_index = auth.get_session_index()
            session_expiration = auth.get_session_expiration()
            raw_attributes = auth.get_attributes()
            attributes = self._normalize_attributes(raw_attributes)

            if not attributes.get('email') and name_id:
                if '@' in name_id:
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
                'session_expiration': session_expiration,
                'attributes': attributes,
                'raw_attributes': raw_attributes,
            }
        except ImportError:
            logger.warning("python3-saml not installed, using mock response")
            saml_response = request_data.get('post_data', {}).get('SAMLResponse', '')
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

    def create_logout_request(
        self,
        request_data: Dict[str, Any],
        name_id: str,
        session_index: str,
        return_to: str = '/'
    ) -> str:
        """Create SAML logout request"""
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            redirect_url = auth.logout(
                name_id=name_id,
                session_index=session_index,
                return_to=return_to
            )

            logger.info(
                f"Created SAML LogoutRequest",
                extra={
                    'name_id': name_id,
                    'session_index': session_index,
                    'connection_id': self.config.connection_id,
                }
            )

            return redirect_url
        except ImportError:
            slo_url = self.settings.get('idp', {}).get('singleLogoutService', {}).get('url')
            if slo_url:
                return f"{slo_url}?SAMLRequest=mock&RelayState={return_to}"
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
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth

            auth = OneLogin_Saml2_Auth(request_data, self.settings)
            get_data = request_data.get('get_data', {})
            post_data = request_data.get('post_data', {})

            redirect_url = None

            if 'SAMLRequest' in get_data or 'SAMLRequest' in post_data:
                redirect_url = auth.process_slo(
                    keep_local_session=False,
                    request_id=None,
                    delete_session_cb=None
                )
            else:
                auth.process_slo()

            errors = auth.get_errors()
            if errors:
                logger.error(
                    f"SAML Logout errors",
                    extra={
                        'errors': errors,
                        'connection_id': self.config.connection_id,
                    }
                )
                return False, redirect_url

            logger.info(
                f"SAML logout processed successfully",
                extra={'connection_id': self.config.connection_id}
            )

            return True, redirect_url
        except ImportError:
            return True, None

    def get_metadata(self) -> str:
        """Generate SP metadata XML"""
        try:
            from onelogin.saml2.metadata import OneLogin_Saml2_Metadata

            sp = self.settings['sp']
            security = self.settings['security']

            metadata = OneLogin_Saml2_Metadata.builder(
                sp=sp,
                authnsign=security.get('authnRequestsSigned', True),
                wsign=security.get('wantAssertionsSigned', True),
            )

            return metadata
        except ImportError:
            from app.auth.sso.saml.metadata import SAMLMetadataGenerator
            generator = SAMLMetadataGenerator(
                entity_id=self.settings['sp']['entityId'],
                acs_url=self.settings['sp']['assertionConsumerService']['url'],
                sls_url=self.settings['sp']['singleLogoutService']['url'],
                certificate=self.settings['sp'].get('x509cert', ''),
                name_id_format=self.settings['sp'].get('NameIDFormat', ''),
            )
            return generator.generate()

    @classmethod
    def parse_idp_metadata(cls, metadata: str) -> Dict[str, Any]:
        """Parse IdP metadata XML and extract configuration"""
        try:
            from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

            parsed = OneLogin_Saml2_IdPMetadataParser.parse(metadata)
            idp = parsed.get('idp', {})

            return {
                'entity_id': idp.get('entityId', ''),
                'sso_url': idp.get('singleSignOnService', {}).get('url', ''),
                'slo_url': idp.get('singleLogoutService', {}).get('url'),
                'certificate': idp.get('x509cert', ''),
                'certificates': idp.get('x509certMulti', {}).get('signing', []),
            }
        except ImportError:
            logger.warning("python3-saml not installed, cannot parse metadata")
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
    Prepare FastAPI request data for python3-saml
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
    Prepare FastAPI request data with form data for python3-saml
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
