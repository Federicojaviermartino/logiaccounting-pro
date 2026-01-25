import { useState, useEffect } from 'react';
import { Shield, Smartphone, Copy, CheckCircle, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

export default function MFASetup({ onComplete, onCancel }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [backupCodes, setBackupCodes] = useState([]);

  const steps = [
    { number: 1, title: 'Introduction' },
    { number: 2, title: 'Scan QR Code' },
    { number: 3, title: 'Verify Code' },
    { number: 4, title: 'Backup Codes' }
  ];

  const handleInitSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await securityAPI.mfa.setup();
      setSetupData(response.data);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize MFA setup');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newCode = [...verificationCode];
    newCode[index] = value.slice(-1);
    setVerificationCode(newCode);

    if (value && index < 5) {
      const nextInput = document.getElementById(`mfa-code-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !verificationCode[index] && index > 0) {
      const prevInput = document.getElementById(`mfa-code-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...verificationCode];
    for (let i = 0; i < pastedData.length; i++) {
      newCode[i] = pastedData[i];
    }
    setVerificationCode(newCode);
  };

  const handleVerify = async () => {
    const code = verificationCode.join('');
    if (code.length !== 6) {
      setError('Please enter a complete 6-digit code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await securityAPI.mfa.verifySetup(code);
      setBackupCodes(response.data.backup_codes || []);
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const copySecret = () => {
    navigator.clipboard.writeText(setupData?.secret || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const copyBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((s, index) => (
            <div key={s.number} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step > s.number
                  ? 'bg-green-500 text-white'
                  : step === s.number
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}>
                {step > s.number ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  s.number
                )}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-16 h-0.5 mx-2 ${
                  step > s.number ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
          {steps.map((s) => (
            <span key={s.number} className="w-16 text-center">{s.title}</span>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {step === 1 && (
        <div className="text-center">
          <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <Shield className="w-10 h-10 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Enable Two-Factor Authentication
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
            Two-factor authentication adds an extra layer of security to your account by requiring
            a verification code from your authenticator app in addition to your password.
          </p>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">What you will need:</h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li className="flex items-center gap-2">
                <Smartphone className="w-4 h-4" />
                An authenticator app (Google Authenticator, Authy, etc.)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Access to save backup codes securely
              </li>
            </ul>
          </div>
          <div className="flex justify-center gap-4">
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleInitSetup}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Get Started
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {step === 2 && setupData && (
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Scan QR Code
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Open your authenticator app and scan the QR code below.
          </p>
          <div className="bg-white dark:bg-gray-700 p-4 rounded-lg inline-block mb-4">
            <img
              src={setupData.qr_code}
              alt="MFA QR Code"
              className="w-48 h-48 mx-auto"
            />
          </div>
          <div className="mb-6">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              Cannot scan? Enter this code manually:
            </p>
            <div className="flex items-center justify-center gap-2">
              <code className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded font-mono text-sm text-gray-900 dark:text-white">
                {setupData.secret}
              </code>
              <button
                onClick={copySecret}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                title="Copy to clipboard"
              >
                {copied ? <CheckCircle className="w-5 h-5 text-green-500" /> : <Copy className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-2 px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Verify Setup
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Enter the 6-digit verification code from your authenticator app.
          </p>
          <div className="flex justify-center gap-2 mb-6" onPaste={handlePaste}>
            {verificationCode.map((digit, index) => (
              <input
                key={index}
                id={`mfa-code-${index}`}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleCodeChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 dark:bg-gray-700 dark:text-white"
                autoFocus={index === 0}
              />
            ))}
          </div>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-2 px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button
              onClick={handleVerify}
              disabled={loading || verificationCode.join('').length !== 6}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Verify
                  <CheckCircle className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Two-Factor Authentication Enabled
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Save these backup codes in a secure location. Each code can only be used once.
          </p>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-2 gap-2">
              {backupCodes.map((code, index) => (
                <code
                  key={index}
                  className="px-3 py-2 bg-white dark:bg-gray-700 rounded text-sm font-mono text-gray-900 dark:text-white"
                >
                  {code}
                </code>
              ))}
            </div>
          </div>
          <button
            onClick={copyBackupCodes}
            className="flex items-center gap-2 mx-auto mb-6 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            {copied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy all codes'}
          </button>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm text-yellow-800 dark:text-yellow-400">
              <strong>Important:</strong> These codes will not be shown again. If you lose access to your
              authenticator app and these backup codes, you will lose access to your account.
            </p>
          </div>
          <button
            onClick={handleComplete}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Done
          </button>
        </div>
      )}
    </div>
  );
}
