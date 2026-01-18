import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const credentials = {
  admin: { email: 'admin@logiaccounting.demo', password: 'Demo2024!Admin' },
  client: { email: 'client@logiaccounting.demo', password: 'Demo2024!Client' },
  supplier: { email: 'supplier@logiaccounting.demo', password: 'Demo2024!Supplier' }
};

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

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
    setEmail(credentials[role].email);
    setPassword(credentials[role].password);
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-logo">📦</div>
        <h1 className="login-title">LogiAccounting Pro</h1>
        <p className="login-subtitle">Enterprise Logistics & Accounting</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              autoComplete="email"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>
          
          <button type="submit" className="btn btn-primary login-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="demo-section">
          <div className="demo-title">🎭 Demo Credentials - Click to autofill:</div>
          <div className="quick-login-btns">
            <button type="button" className="quick-btn" onClick={() => quickLogin('admin')}>
              👑 Admin
            </button>
            <button type="button" className="quick-btn" onClick={() => quickLogin('client')}>
              🧑‍💼 Client
            </button>
            <button type="button" className="quick-btn" onClick={() => quickLogin('supplier')}>
              🏭 Supplier
            </button>
          </div>
          <div className="credential-item">
            <strong>Admin:</strong> <code>admin@logiaccounting.demo</code> / <code>Demo2024!Admin</code>
          </div>
          <div className="credential-item">
            <strong>Client:</strong> <code>client@logiaccounting.demo</code> / <code>Demo2024!Client</code>
          </div>
          <div className="credential-item">
            <strong>Supplier:</strong> <code>supplier@logiaccounting.demo</code> / <code>Demo2024!Supplier</code>
          </div>
        </div>
      </div>
    </div>
  );
}
