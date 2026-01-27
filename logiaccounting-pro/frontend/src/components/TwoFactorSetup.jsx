import { useState } from 'react';
import { twoFactorAPI } from '../services/api';

export default function TwoFactorSetup({ onComplete, onCancel }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [error, setError] = useState('');

  const handleSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await twoFactorAPI.setup();
      setSetupData(res.data);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      await twoFactorAPI.verifySetup(verifyCode);
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="two-factor-setup">
      {step === 1 && (
        <div className="setup-step">
          <div className="step-icon">🔐</div>
          <h3>Enable Two-Factor Authentication</h3>
          <p className="text-muted">
            Add an extra layer of security to your account using an
            authenticator app like Google Authenticator or Authy.
          </p>
          <div className="flex gap-3 mt-6">
            <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSetup} disabled={loading}>
              {loading ? 'Setting up...' : 'Begin Setup'}
            </button>
          </div>
        </div>
      )}

      {step === 2 && setupData && (
        <div className="setup-step">
          <h3>Scan QR Code</h3>
          <p className="text-muted mb-4">Scan this QR code with your authenticator app:</p>
          <div className="qr-container">
            <img src={setupData.qr_code} alt="2FA QR Code" />
          </div>
          <div className="manual-entry mt-4">
            <p className="text-sm text-muted">Can't scan? Enter this code manually:</p>
            <code className="secret-code">{setupData.secret}</code>
          </div>
          <button className="btn btn-primary mt-4" onClick={() => setStep(3)}>Continue</button>
        </div>
      )}

      {step === 3 && (
        <div className="setup-step">
          <h3>Verify Setup</h3>
          <p className="text-muted mb-4">Enter the 6-digit code from your authenticator app:</p>
          {error && <div className="error-message mb-4">{error}</div>}
          <input
            type="text"
            className="form-input verify-input"
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            maxLength={6}
            autoFocus
          />
          <div className="flex gap-3 mt-6">
            <button className="btn btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button
              className="btn btn-primary"
              onClick={handleVerify}
              disabled={loading || verifyCode.length !== 6}
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </div>
        </div>
      )}

      {step === 4 && setupData && (
        <div className="setup-step">
          <div className="step-icon success">✅</div>
          <h3>2FA Enabled Successfully!</h3>
          <p className="text-muted mb-4">
            Save these backup codes in a secure place. Each can only be used once.
          </p>
          <div className="backup-codes">
            {setupData.backup_codes.map((code, i) => (
              <code key={i} className="backup-code">{code}</code>
            ))}
          </div>
          <div className="warning-box mt-4">
            These codes will not be shown again!
          </div>
          <button className="btn btn-primary mt-6" onClick={onComplete}>Done</button>
        </div>
      )}
    </div>
  );
}
