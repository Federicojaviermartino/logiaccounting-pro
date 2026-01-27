"""
Phase 14: OAuth Manager
Handles OAuth flows and token management for integrations
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx
import logging
import os

from app.models.integrations_store import (
    integrations_store, oauth_states_store, PROVIDER_CONFIGS, IntegrationStatus
)

logger = logging.getLogger(__name__)


# Provider OAuth configurations
OAUTH_CONFIGS = {
    'quickbooks': {
        'authorization_url': 'https://appcenter.intuit.com/connect/oauth2',
        'token_url': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
        'scopes': ['com.intuit.quickbooks.accounting'],
    },
    'xero': {
        'authorization_url': 'https://login.xero.com/identity/connect/authorize',
        'token_url': 'https://identity.xero.com/connect/token',
        'scopes': ['openid', 'profile', 'email', 'accounting.transactions', 'accounting.contacts', 'accounting.settings'],
    },
    'salesforce': {
        'authorization_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'scopes': ['api', 'refresh_token', 'offline_access'],
    },
    'hubspot': {
        'authorization_url': 'https://app.hubspot.com/oauth/authorize',
        'token_url': 'https://api.hubapi.com/oauth/v1/token',
        'scopes': ['crm.objects.contacts.read', 'crm.objects.contacts.write', 'crm.objects.companies.read', 'crm.objects.deals.read'],
    },
    'shopify': {
        'authorization_url': 'https://{shop}.myshopify.com/admin/oauth/authorize',
        'token_url': 'https://{shop}.myshopify.com/admin/oauth/access_token',
        'scopes': ['read_products', 'write_products', 'read_orders', 'write_orders', 'read_customers', 'write_customers', 'read_inventory', 'write_inventory'],
    },
    'stripe': {
        'authorization_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scopes': ['read_write'],
    },
}


class OAuthManager:
    """Manages OAuth authentication for integrations"""

    def __init__(self, provider: str):
        self.provider = provider
        self.config = OAUTH_CONFIGS.get(provider, {})

        if not self.config:
            raise ValueError(f"Unknown OAuth provider: {provider}")

    def get_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str,
        scopes: list = None,
        extra_params: Dict[str, str] = None
    ) -> str:
        """
        Generate OAuth authorization URL

        Args:
            client_id: OAuth client ID
            redirect_uri: Callback URL
            state: CSRF state token
            scopes: Override default scopes
            extra_params: Additional URL parameters

        Returns:
            Authorization URL
        """
        base_url = self.config['authorization_url']

        # Handle Shopify's shop-specific URL
        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            base_url = base_url.format(shop=extra_params['shop'])

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': ' '.join(scopes or self.config.get('scopes', [])),
        }

        # Add extra params
        if extra_params:
            params.update({k: v for k, v in extra_params.items() if k != 'shop'})

        return f"{base_url}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        extra_params: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens

        Args:
            code: Authorization code
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Callback URL (must match original)
            extra_params: Additional parameters

        Returns:
            Token response
        """
        token_url = self.config['token_url']

        # Handle Shopify's shop-specific URL
        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            token_url = token_url.format(shop=extra_params['shop'])

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }

        # Some providers expect credentials in body, others in header
        if self.provider in ['quickbooks', 'xero']:
            # Basic auth header
            import base64
            auth_string = f"{client_id}:{client_secret}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': f'Basic {auth_header}',
            }
        else:
            # Credentials in body
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            data['client_id'] = client_id
            data['client_secret'] = client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")

            return response.json()

    async def refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        extra_params: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token
            client_id: OAuth client ID
            client_secret: OAuth client secret
            extra_params: Additional parameters

        Returns:
            New token response
        """
        token_url = self.config['token_url']

        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            token_url = token_url.format(shop=extra_params['shop'])

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        if self.provider in ['quickbooks', 'xero']:
            import base64
            auth_string = f"{client_id}:{client_secret}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': f'Basic {auth_header}',
            }
        else:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            data['client_id'] = client_id
            data['client_secret'] = client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")

            return response.json()


class IntegrationOAuthService:
    """High-level OAuth service for integrations"""

    @staticmethod
    def initiate_oauth(
        organization_id: str,
        provider: str,
        user_id: str,
        redirect_uri: str,
        extra_params: Dict[str, str] = None
    ) -> str:
        """
        Initiate OAuth flow

        Args:
            organization_id: Organization ID
            provider: Provider name
            user_id: User initiating connection
            redirect_uri: Callback URL
            extra_params: Additional parameters

        Returns:
            Authorization URL
        """
        # Create state
        oauth_state = oauth_states_store.create(
            organization_id=organization_id,
            provider=provider,
            user_id=user_id,
            redirect_uri=redirect_uri,
            additional_data=extra_params
        )

        # Get OAuth manager
        oauth_manager = OAuthManager(provider)

        # Get client credentials from environment
        client_id = os.getenv(f'{provider.upper()}_CLIENT_ID')

        if not client_id:
            # Use demo credentials for testing
            client_id = f'demo_{provider}_client_id'
            logger.warning(f"Using demo client_id for {provider}")

        # Generate authorization URL
        return oauth_manager.get_authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=oauth_state["state"],
            extra_params=extra_params
        )

    @staticmethod
    async def complete_oauth(
        provider: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Dict:
        """
        Complete OAuth flow and create/update integration

        Args:
            provider: Provider name
            code: Authorization code
            state: State token
            redirect_uri: Callback URL

        Returns:
            Integration dict
        """
        # Validate state
        oauth_state = oauth_states_store.validate_and_consume(state, provider)

        if not oauth_state:
            raise ValueError("Invalid or expired OAuth state")

        # Exchange code for tokens
        oauth_manager = OAuthManager(provider)

        client_id = os.getenv(f'{provider.upper()}_CLIENT_ID', f'demo_{provider}_client_id')
        client_secret = os.getenv(f'{provider.upper()}_CLIENT_SECRET', f'demo_{provider}_client_secret')

        tokens = await oauth_manager.exchange_code(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            extra_params=oauth_state.get("additional_data")
        )

        # Find or create integration
        integration = integrations_store.find_by_provider(
            oauth_state["organization_id"],
            provider
        )

        if not integration:
            integration = integrations_store.create({
                "organization_id": oauth_state["organization_id"],
                "provider": provider,
                "category": get_provider_category(provider),
                "name": get_provider_label(provider),
            })

        # Update tokens
        integrations_store.update_tokens(
            integration["id"],
            access_token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            expires_in=tokens.get('expires_in'),
            scope=tokens.get('scope')
        )

        # Store additional config
        config = integration.get("config", {})
        if oauth_state.get("additional_data"):
            config.update(oauth_state["additional_data"])

        # Provider-specific config
        if provider == 'quickbooks' and 'realmId' in tokens:
            config['realm_id'] = tokens['realmId']
        elif provider == 'salesforce' and 'instance_url' in tokens:
            config['instance_url'] = tokens['instance_url']

        integrations_store.update(integration["id"], {"config": config})
        integrations_store.mark_connected(integration["id"], oauth_state["user_id"])

        logger.info(f"OAuth completed for {provider}, integration {integration['id']}")

        return integrations_store.find_by_id(integration["id"])

    @staticmethod
    async def refresh_integration_token(integration_id: str) -> bool:
        """
        Refresh token for an integration

        Args:
            integration_id: Integration ID

        Returns:
            True if successful
        """
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            logger.warning(f"Integration not found: {integration_id}")
            return False

        if not integration.get("oauth_refresh_token"):
            logger.warning(f"No refresh token for integration {integration_id}")
            return False

        try:
            oauth_manager = OAuthManager(integration["provider"])

            client_id = os.getenv(f'{integration["provider"].upper()}_CLIENT_ID', f'demo_{integration["provider"]}_client_id')
            client_secret = os.getenv(f'{integration["provider"].upper()}_CLIENT_SECRET', f'demo_{integration["provider"]}_client_secret')

            tokens = await oauth_manager.refresh_token(
                refresh_token=integration["oauth_refresh_token"],
                client_id=client_id,
                client_secret=client_secret,
                extra_params=integration.get("config")
            )

            integrations_store.update_tokens(
                integration_id,
                access_token=tokens.get('access_token'),
                refresh_token=tokens.get('refresh_token', integration["oauth_refresh_token"]),
                expires_in=tokens.get('expires_in')
            )

            logger.info(f"Token refreshed for integration {integration_id}")
            return True

        except Exception as e:
            logger.error(f"Token refresh failed for integration {integration_id}: {e}")
            integrations_store.mark_error(integration_id, str(e))
            return False


def get_provider_category(provider: str) -> str:
    """Get category for a provider"""
    categories = {
        'quickbooks': 'accounting',
        'xero': 'accounting',
        'sage': 'accounting',
        'freshbooks': 'accounting',
        'salesforce': 'crm',
        'hubspot': 'crm',
        'zoho': 'crm',
        'pipedrive': 'crm',
        'shopify': 'ecommerce',
        'woocommerce': 'ecommerce',
        'magento': 'ecommerce',
        'bigcommerce': 'ecommerce',
        'sap': 'erp',
        'netsuite': 'erp',
        'dynamics': 'erp',
        'plaid': 'banking',
        'stripe': 'payments',
        'paypal': 'payments',
        'fedex': 'shipping',
        'ups': 'shipping',
        'dhl': 'shipping',
    }
    return categories.get(provider, 'generic')


def get_provider_label(provider: str) -> str:
    """Get display label for a provider"""
    labels = {
        'quickbooks': 'QuickBooks Online',
        'xero': 'Xero',
        'sage': 'Sage',
        'salesforce': 'Salesforce',
        'hubspot': 'HubSpot',
        'zoho': 'Zoho CRM',
        'shopify': 'Shopify',
        'woocommerce': 'WooCommerce',
        'plaid': 'Plaid',
        'stripe': 'Stripe',
        'fedex': 'FedEx',
        'ups': 'UPS',
        'dhl': 'DHL',
    }
    return labels.get(provider, provider.title())
