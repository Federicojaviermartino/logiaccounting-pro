"""
SAML 2.0 Configuration Management
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import os


@dataclass
class SAMLSecurityConfig:
    """Security settings for SAML"""

    authn_requests_signed: bool = True
    logout_requests_signed: bool = True
    logout_responses_signed: bool = True
    sign_metadata: bool = True
    want_messages_signed: bool = True
    want_assertions_signed: bool = True
    want_assertions_encrypted: bool = False
    want_name_id_encrypted: bool = False
    signature_algorithm: str = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    digest_algorithm: str = "http://www.w3.org/2001/04/xmlenc#sha256"
    reject_deprecated_algorithms: bool = True
    fail_on_authn_context_mismatch: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'authnRequestsSigned': self.authn_requests_signed,
            'logoutRequestSigned': self.logout_requests_signed,
            'logoutResponseSigned': self.logout_responses_signed,
            'signMetadata': self.sign_metadata,
            'wantMessagesSigned': self.want_messages_signed,
            'wantAssertionsSigned': self.want_assertions_signed,
            'wantAssertionsEncrypted': self.want_assertions_encrypted,
            'wantNameIdEncrypted': self.want_name_id_encrypted,
            'signatureAlgorithm': self.signature_algorithm,
            'digestAlgorithm': self.digest_algorithm,
            'rejectDeprecatedAlgorithm': self.reject_deprecated_algorithms,
            'failOnAuthnContextMismatch': self.fail_on_authn_context_mismatch,
            'requestedAuthnContext': False,
        }


@dataclass
class SAMLServiceProvider:
    """Service Provider configuration"""

    entity_id: str
    acs_url: str
    sls_url: str
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    x509_cert: str = ""
    private_key: str = ""
    org_name: str = "LogiAccounting Pro"
    org_display_name: str = "LogiAccounting Pro"
    org_url: str = "https://logiaccounting-pro.onrender.com"
    technical_contact_name: str = "Support"
    technical_contact_email: str = "support@logiaccounting.com"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entityId': self.entity_id,
            'assertionConsumerService': {
                'url': self.acs_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            },
            'singleLogoutService': {
                'url': self.sls_url,
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            },
            'NameIDFormat': self.name_id_format,
            'x509cert': self.x509_cert,
            'privateKey': self.private_key,
        }


@dataclass
class SAMLIdentityProvider:
    """Identity Provider configuration"""

    entity_id: str
    sso_url: str
    slo_url: Optional[str] = None
    x509_cert: str = ""
    x509_cert_multi: List[str] = field(default_factory=list)
    sso_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    slo_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"

    def to_dict(self) -> Dict[str, Any]:
        config = {
            'entityId': self.entity_id,
            'singleSignOnService': {
                'url': self.sso_url,
                'binding': self.sso_binding,
            },
            'x509cert': self.x509_cert,
        }

        if self.slo_url:
            config['singleLogoutService'] = {
                'url': self.slo_url,
                'binding': self.slo_binding,
            }

        if self.x509_cert_multi:
            config['x509certMulti'] = {
                'signing': self.x509_cert_multi,
            }

        return config


class SAMLConfig:
    """Complete SAML configuration builder"""

    def __init__(
        self,
        connection_id: str,
        sp_config: Dict[str, Any],
        idp_config: Dict[str, Any],
        security_config: Optional[SAMLSecurityConfig] = None
    ):
        self.connection_id = connection_id
        self._sp = SAMLServiceProvider(**sp_config) if isinstance(sp_config, dict) else sp_config
        self._idp = SAMLIdentityProvider(**idp_config) if isinstance(idp_config, dict) else idp_config
        self._security = security_config or SAMLSecurityConfig()

    @classmethod
    def from_connection(cls, connection: Dict) -> 'SAMLConfig':
        """Build config from SSO connection data"""
        base_url = os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')

        sp_config = {
            'entity_id': f"{base_url}/api/v1/auth/sso/saml/{connection['id']}/metadata",
            'acs_url': f"{base_url}/api/v1/auth/sso/saml/{connection['id']}/acs",
            'sls_url': f"{base_url}/api/v1/auth/sso/saml/{connection['id']}/sls",
            'name_id_format': connection.get('saml_name_id_format', 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'),
            'x509_cert': os.getenv('SAML_SP_CERT', ''),
            'private_key': os.getenv('SAML_SP_KEY', ''),
        }

        idp_config = {
            'entity_id': connection.get('saml_entity_id', ''),
            'sso_url': connection.get('saml_sso_url', ''),
            'slo_url': connection.get('saml_slo_url'),
            'x509_cert': connection.get('saml_certificate', ''),
        }

        security = SAMLSecurityConfig(
            authn_requests_signed=connection.get('saml_sign_request', True),
            want_assertions_signed=connection.get('saml_want_assertions_signed', True),
        )

        return cls(
            connection_id=connection['id'],
            sp_config=sp_config,
            idp_config=idp_config,
            security_config=security
        )

    def to_onelogin_settings(self) -> Dict[str, Any]:
        """Convert to python3-saml settings format"""
        return {
            'strict': True,
            'debug': os.getenv('SAML_DEBUG', 'false').lower() == 'true',
            'sp': self._sp.to_dict(),
            'idp': self._idp.to_dict(),
            'security': self._security.to_dict(),
        }

    @property
    def sp(self) -> SAMLServiceProvider:
        return self._sp

    @property
    def idp(self) -> SAMLIdentityProvider:
        return self._idp

    @property
    def security(self) -> SAMLSecurityConfig:
        return self._security
