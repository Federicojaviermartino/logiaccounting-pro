import { useState } from 'react';
import { twoFactorAPI } from '../services/api';

export default function TwoFactorVerify({ email, onSuccess, onCancel }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await twoFactorAPI.verifyLogin(email, code);
      onSuccess(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && code.length === 6) {
      handleVerify();
    }
  };

  return (
    <div className="two-factor-verify">
      <div className="verify-icon">🔐</div>
      <h3>Two-Factor Authentication</h3>
      <p className="text-muted mb-4">Enter the 6-digit code from your authenticator app</p>

      {error && <div className="error-message mb-4">{error}</div>}

      <input
        type="text"
        className="form-input verify-input"
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
        onKeyPress={handleKeyPress}
        placeholder="000000"
        maxLength={6}
        autoFocus
      />

      <p className="text-sm text-muted mt-2">Or use a backup code</p>

      <div className="flex gap-3 mt-6">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button
          className="btn btn-primary"
          onClick={handleVerify}
          disabled={loading || code.length < 6}
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </div>
    </div>
  );
}
