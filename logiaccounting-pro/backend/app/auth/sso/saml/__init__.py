"""
SAML 2.0 Authentication Module
"""

from app.auth.sso.saml.config import SAMLConfig, SAMLServiceProvider, SAMLIdentityProvider
from app.auth.sso.saml.processor import SAMLProcessor, SAMLValidationError
from app.auth.sso.saml.metadata import SAMLMetadataGenerator

__all__ = [
    'SAMLConfig',
    'SAMLServiceProvider',
    'SAMLIdentityProvider',
    'SAMLProcessor',
    'SAMLValidationError',
    'SAMLMetadataGenerator',
]
