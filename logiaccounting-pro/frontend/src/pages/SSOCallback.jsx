import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';

export default function SSOCallback() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { setUser, setToken } = useAuth();

  useEffect(() => {
    const processCallback = async () => {
      const token = searchParams.get('token');
      const errorMsg = searchParams.get('message') || searchParams.get('error');
      const redirect = searchParams.get('redirect');

      if (errorMsg) {
        setStatus('error');
        setError(errorMsg);
        return;
      }

      if (!token) {
        setStatus('error');
        setError('No authentication token received');
        return;
      }

      try {
        localStorage.setItem('token', token);

        const response = await authAPI.getMe();
        const user = response.data;

        localStorage.setItem('user', JSON.stringify(user));
        setToken(token);
        setUser(user);

        setStatus('success');

        setTimeout(() => {
          navigate(redirect || '/dashboard');
        }, 1500);
      } catch (err) {
        console.error('SSO callback error:', err);
        setStatus('error');
        setError('Failed to complete authentication');
        localStorage.removeItem('token');
      }
    };

    processCallback();
  }, [searchParams, navigate, setUser, setToken]);

  return (
    <div className="sso-callback-page">
      <div className="sso-callback-container">
        {status === 'processing' && (
          <>
            <div className="sso-spinner"></div>
            <h2>Completing Sign In...</h2>
            <p>Please wait while we authenticate your account</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="sso-success-icon">✓</div>
            <h2>Sign In Successful!</h2>
            <p>Redirecting to dashboard...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="sso-error-icon">✗</div>
            <h2>Sign In Failed</h2>
            <p className="error-message">{error}</p>
            <button className="btn btn-primary" onClick={() => navigate('/login')}>
              Return to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}
