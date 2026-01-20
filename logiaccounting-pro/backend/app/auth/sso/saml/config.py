"""
SAML 2.0 Configuration Management
Supports both python3-saml (onelogin) and pysaml2 configuration formats
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
                """Convert to python3-saml settings format (legacy)"""
                return {
                    'strict': True,
                    'debug': os.getenv('SAML_DEBUG', 'false').lower() == 'true',
                    'sp': self._sp.to_dict(),
                    'idp': self._idp.to_dict(),
                    'security': self._security.to_dict(),
                }

    def to_pysaml2_config(self) -> Dict[str, Any]:
                """Convert to pysaml2 configuration format"""
                # Build metadata for IdP
                idp_metadata = self._build_idp_metadata_inline()

        config = {
                        'entityid': self._sp.entity_id,
                        'debug': os.getenv('SAML_DEBUG', 'false').lower() == 'true',
                        'service': {
                                            'sp': {
                                                                    'name': self._sp.org_name,
                                                                    'name_id_format': [self._sp.name_id_format],
                                                                    'endpoints': {
                                                                                                'assertion_consumer_service': [
                                                                                                                                (self._sp.acs_url, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'),
                                                                                                    ],
                                                                                                'single_logout_service': [
                                                                                                                                (self._sp.sls_url, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'),
                                                                                                    ],
                                                                    },
                                                                    'authn_requests_signed': self._security.authn_requests_signed,
                                                                    'want_assertions_signed': self._security.want_assertions_signed,
                                                                    'want_response_signed': self._security.want_messages_signed,
                                                                    'allow_unsolicited': True,
                                            },
                        },
                        'metadata': {
                                            'inline': [idp_metadata],
                        },
                        'allow_unknown_attributes': True,
        }

        # Add certificate/key if provided
        if self._sp.x509_cert:
                        config['cert_file'] = self._sp.x509_cert
                    if self._sp.private_key:
                                    config['key_file'] = self._sp.private_key

        # Contact information
        config['contact_person'] = [
                        {
                                            'contact_type': 'technical',
                                            'given_name': self._sp.technical_contact_name,
                                            'email_address': [self._sp.technical_contact_email],
                        },
        ]

        # Organization info
        config['organization'] = {
                        'name': [(self._sp.org_name, 'en')],
                        'display_name': [(self._sp.org_display_name, 'en')],
                        'url': [(self._sp.org_url, 'en')],
        }

        return config

    def _build_idp_metadata_inline(self) -> str:
                """Build inline IdP metadata XML for pysaml2"""
                cert_section = ""
                if self._idp.x509_cert:
                                cert_content = self._idp.x509_cert.strip()
                                cert_content = cert_content.replace('-----BEGIN CERTIFICATE-----', '')
                                cert_content = cert_content.replace('-----END CERTIFICATE-----', '')
                                cert_content = cert_content.replace('\\n', '').replace('\\r', '').strip()

            cert_section = f'''
                        <md:KeyDescriptor use="signing">
                                        <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                                                            <ds:X509Data>
                                                                                    <ds:X509Certificate>{cert_content}</ds:X509Certificate>
                                                                                                        </ds:X509Data>
                                                                                                                        </ds:KeyInfo>
                                                                                                                                    </md:KeyDescriptor>'''

        slo_section = ""
        if self._idp.slo_url:
                        slo_section = f'''
                                    <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="{self._idp.slo_url}"/>'''

        metadata = f'''<?xml version="1.0" encoding="UTF-8"?>
        <md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{self._idp.entity_id}">
            <md:IDPSSODescriptor WantAuthnRequestsSigned="false" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    {cert_section}
                            <md:NameIDFormat>{self._sp.name_id_format}</md:NameIDFormat>
                                    <md:SingleSignOnService Binding="{self._idp.sso_binding}" Location="{self._idp.sso_url}"/>{slo_section}
                                        </md:IDPSSODescriptor>
                                        </md:EntityDescriptor>'''

        return metadata

    @property
    def sp(self) -> SAMLServiceProvider:
                return self._sp

    @property
    def idp(self) -> SAMLIdentityProvider:
                return self._idp

    @property
    def security(self) -> SAMLSecurityConfig:
                return self._security
