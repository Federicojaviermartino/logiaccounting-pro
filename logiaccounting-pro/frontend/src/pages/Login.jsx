import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ssoAPI } from '../services/ssoApi';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

const credentials = DEMO_MODE ? {
  admin: { email: import.meta.env.VITE_DEMO_ADMIN_EMAIL || '', password: import.meta.env.VITE_DEMO_ADMIN_PASS || '' },
  client: { email: import.meta.env.VITE_DEMO_CLIENT_EMAIL || '', password: import.meta.env.VITE_DEMO_CLIENT_PASS || '' },
  supplier: { email: import.meta.env.VITE_DEMO_SUPPLIER_EMAIL || '', password: import.meta.env.VITE_DEMO_SUPPLIER_PASS || '' }
} : null;

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [ssoConnection, setSsoConnection] = useState(null);
  const [checkingSSO, setCheckingSSO] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const checkSSODomain = useCallback(async (emailValue) => {
    if (!emailValue || !emailValue.includes('@')) {
      setSsoConnection(null);
      return;
    }

    setCheckingSSO(true);
    try {
      const response = await ssoAPI.discoverSSO(emailValue);
      if (response.data.sso_enabled) {
        setSsoConnection(response.data);
      } else {
        setSsoConnection(null);
      }
    } catch (err) {
      setSsoConnection(null);
    } finally {
      setCheckingSSO(false);
    }
  }, []);

  const handleEmailBlur = () => {
    checkSSODomain(email);
  };

  const handleSSOLogin = async () => {
    if (!ssoConnection) return;

    setLoading(true);
    setError('');

    try {
      const response = await ssoAPI.initiateSSOLogin({
        connection_id: ssoConnection.connection_id,
        email: email,
      });

      window.location.href = response.data.redirect_url;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initiate SSO login');
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = (role) => {
    if (!credentials?.[role]) return;
    setEmail(credentials[role].email);
    setPassword(credentials[role].password);
    setSsoConnection(null);
  };

  return (
    <div className="login-page" role="main">
      <div className="login-container">
        <div className="login-logo" aria-hidden="true">📦</div>
        <h1 className="login-title">LogiAccounting Pro</h1>
        <p className="login-subtitle">Enterprise Logistics & Accounting</p>

        {error && <div className="error-message" role="alert" aria-live="assertive">{error}</div>}

        <form className="login-form" onSubmit={handleSubmit} aria-label="Sign in">
          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={handleEmailBlur}
              placeholder="your@email.com"
              required
              autoComplete="email"
              aria-describedby={checkingSSO ? 'sso-hint' : undefined}
            />
            {checkingSSO && (
              <small className="form-hint" id="sso-hint" aria-live="polite">Checking for SSO...</small>
            )}
          </div>

          {ssoConnection && (
            <div className="sso-detected">
              <div className="sso-badge">
                🔐 SSO Available
              </div>
              <p>
                Your organization ({ssoConnection.connection_name}) uses Single Sign-On
              </p>
              <button
                type="button"
                className="btn btn-primary sso-btn"
                onClick={handleSSOLogin}
                disabled={loading}
              >
                {loading ? 'Redirecting...' : `Sign in with ${ssoConnection.provider_type || 'SSO'}`}
              </button>
              <div className="sso-divider">
                <span>or continue with password</span>
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required={!ssoConnection}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary login-btn"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {DEMO_MODE && credentials && (
          <div className="demo-section">
            <div className="demo-title">Demo Credentials - Click to autofill:</div>
            <div className="quick-login-btns">
              <button type="button" className="quick-btn" onClick={() => quickLogin('admin')}>
                Admin
              </button>
              <button type="button" className="quick-btn" onClick={() => quickLogin('client')}>
                Client
              </button>
              <button type="button" className="quick-btn" onClick={() => quickLogin('supplier')}>
                Supplier
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
