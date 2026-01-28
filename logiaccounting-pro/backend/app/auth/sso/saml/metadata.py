"""
SAML Service Provider Metadata Generator
"""

from typing import Optional
from datetime import timedelta
import os

from app.utils.datetime_utils import utc_now


class SAMLMetadataGenerator:
    """Generate SAML SP Metadata XML"""

    SAML_NS = "urn:oasis:names:tc:SAML:2.0:metadata"
    DS_NS = "http://www.w3.org/2000/09/xmldsig#"

    def __init__(
        self,
        entity_id: str,
        acs_url: str,
        sls_url: str,
        certificate: str,
        name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        org_name: str = "LogiAccounting Pro",
        org_url: str = None,
        contact_email: str = None,
        want_assertions_signed: bool = True,
        authn_requests_signed: bool = True,
        valid_days: int = 365,
    ):
        self.entity_id = entity_id
        self.acs_url = acs_url
        self.sls_url = sls_url
        self.certificate = self._clean_certificate(certificate)
        self.name_id_format = name_id_format
        self.org_name = org_name
        self.org_url = org_url or os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
        self.contact_email = contact_email or os.getenv('SUPPORT_EMAIL', 'support@logiaccounting.com')
        self.want_assertions_signed = want_assertions_signed
        self.authn_requests_signed = authn_requests_signed
        self.valid_days = valid_days

    def generate(self) -> str:
        """Generate metadata XML string"""
        valid_until = self._get_valid_until()

        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<md:EntityDescriptor xmlns:md="{self.SAML_NS}" xmlns:ds="{self.DS_NS}" '
            f'entityID="{self.entity_id}" validUntil="{valid_until}">',
            f'  <md:SPSSODescriptor AuthnRequestsSigned="{str(self.authn_requests_signed).lower()}" '
            f'WantAssertionsSigned="{str(self.want_assertions_signed).lower()}" '
            f'protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">',
        ]

        if self.certificate:
            xml_parts.extend([
                '    <md:KeyDescriptor use="signing">',
                '      <ds:KeyInfo>',
                '        <ds:X509Data>',
                f'          <ds:X509Certificate>{self.certificate}</ds:X509Certificate>',
                '        </ds:X509Data>',
                '      </ds:KeyInfo>',
                '    </md:KeyDescriptor>',
                '    <md:KeyDescriptor use="encryption">',
                '      <ds:KeyInfo>',
                '        <ds:X509Data>',
                f'          <ds:X509Certificate>{self.certificate}</ds:X509Certificate>',
                '        </ds:X509Data>',
                '      </ds:KeyInfo>',
                '    </md:KeyDescriptor>',
            ])

        xml_parts.extend([
            f'    <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" '
            f'Location="{self.sls_url}"/>',
            f'    <md:NameIDFormat>{self.name_id_format}</md:NameIDFormat>',
            f'    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" '
            f'Location="{self.acs_url}" index="0" isDefault="true"/>',
            '  </md:SPSSODescriptor>',
            '  <md:Organization>',
            f'    <md:OrganizationName xml:lang="en">{self.org_name}</md:OrganizationName>',
            f'    <md:OrganizationDisplayName xml:lang="en">{self.org_name}</md:OrganizationDisplayName>',
            f'    <md:OrganizationURL xml:lang="en">{self.org_url}</md:OrganizationURL>',
            '  </md:Organization>',
            '  <md:ContactPerson contactType="technical">',
            f'    <md:EmailAddress>{self.contact_email}</md:EmailAddress>',
            '  </md:ContactPerson>',
            '</md:EntityDescriptor>',
        ])

        return '\n'.join(xml_parts)

    def _clean_certificate(self, cert: str) -> str:
        """Remove PEM headers and whitespace from certificate"""
        if not cert:
            return ""

        return cert.replace(
            '-----BEGIN CERTIFICATE-----', ''
        ).replace(
            '-----END CERTIFICATE-----', ''
        ).replace('\n', '').replace('\r', '').strip()

    def _get_valid_until(self) -> str:
        """Get validity timestamp"""
        valid_until = utc_now() + timedelta(days=self.valid_days)
        return valid_until.strftime('%Y-%m-%dT%H:%M:%SZ')
