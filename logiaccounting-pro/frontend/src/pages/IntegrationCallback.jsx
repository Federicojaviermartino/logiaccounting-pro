/**
 * Phase 14: Integration OAuth Callback Page
 * Handles OAuth callback from external providers
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { completeOAuth } from '../services/integrationsApi';

const IntegrationCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');
  const [message, setMessage] = useState('Processing authentication...');
  const [integration, setIntegration] = useState(null);

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // Check for OAuth error
      if (error) {
        setStatus('error');
        setMessage(errorDescription || error || 'Authentication was denied or failed');
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        setStatus('error');
        setMessage('Invalid callback - missing required parameters');
        return;
      }

      // Extract provider from state or URL
      const pathParts = window.location.pathname.split('/');
      const provider = pathParts[pathParts.length - 1] !== 'callback'
        ? pathParts[pathParts.length - 1]
        : getProviderFromState(state);

      if (!provider) {
        setStatus('error');
        setMessage('Could not determine provider');
        return;
      }

      setMessage(`Completing ${provider} authentication...`);

      // Complete OAuth flow
      const redirectUri = `${window.location.origin}/integrations/callback`;
      const result = await completeOAuth(provider, code, state, redirectUri);

      setStatus('success');
      setMessage(`Successfully connected to ${result.integration?.name || provider}!`);
      setIntegration(result.integration);

      // Redirect after delay
      setTimeout(() => {
        navigate('/integrations');
      }, 2000);

    } catch (error) {
      console.error('OAuth callback error:', error);
      setStatus('error');
      setMessage(error.message || 'Failed to complete authentication');
    }
  };

  const getProviderFromState = (state) => {
    // Try to decode provider from state (if encoded)
    try {
      const decoded = atob(state);
      const parsed = JSON.parse(decoded);
      return parsed.provider;
    } catch {
      // State might contain provider as prefix
      const providers = ['quickbooks', 'xero', 'salesforce', 'hubspot', 'shopify', 'stripe', 'plaid'];
      for (const provider of providers) {
        if (state.toLowerCase().includes(provider)) {
          return provider;
        }
      }
      return null;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
        {/* Status Icon */}
        <div className="mb-6">
          {status === 'processing' && (
            <div className="mx-auto w-16 h-16 flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
            </div>
          )}
          {status === 'success' && (
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-3xl">✓</span>
            </div>
          )}
          {status === 'error' && (
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-3xl">✕</span>
            </div>
          )}
        </div>

        {/* Status Message */}
        <h1 className={`text-xl font-semibold mb-2 ${
          status === 'success' ? 'text-green-600' :
          status === 'error' ? 'text-red-600' :
          'text-gray-900'
        }`}>
          {status === 'processing' ? 'Connecting...' :
           status === 'success' ? 'Connected!' :
           'Connection Failed'}
        </h1>

        <p className="text-gray-600 mb-6">{message}</p>

        {/* Integration Details */}
        {integration && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-500 mb-1">Integration</div>
            <div className="font-medium text-gray-900">{integration.name}</div>
            <div className="text-sm text-gray-500">{integration.provider}</div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          {status === 'success' && (
            <p className="text-sm text-gray-500">Redirecting to integrations...</p>
          )}

          {status === 'error' && (
            <>
              <button
                onClick={() => navigate('/integrations')}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Back to Integrations
              </button>
              <button
                onClick={() => window.location.reload()}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Try Again
              </button>
            </>
          )}
        </div>

        {/* Help Link */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Having trouble? Check the{' '}
            <a href="/help" className="text-blue-600 hover:underline">
              help center
            </a>{' '}
            or contact support.
          </p>
        </div>
      </div>
    </div>
  );
};

export default IntegrationCallback;
