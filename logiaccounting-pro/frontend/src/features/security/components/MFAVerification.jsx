import { useState, useRef, useEffect } from 'react';
import { Shield, ShieldOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

export default function MFAVerification({ enabled, onStatusChange, onVerify, mode = 'settings' }) {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (mode === 'verify' && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [mode]);

  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value.slice(-1);
    setCode(newCode);
    setError('');

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (value && index === 5) {
      const fullCode = newCode.join('');
      if (fullCode.length === 6 && mode === 'verify' && onVerify) {
        handleVerify(fullCode);
      }
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...code];
    for (let i = 0; i < pastedData.length; i++) {
      newCode[i] = pastedData[i];
    }
    setCode(newCode);

    if (pastedData.length === 6) {
      inputRefs.current[5]?.focus();
      if (mode === 'verify' && onVerify) {
        setTimeout(() => handleVerify(pastedData), 100);
      }
    } else {
      inputRefs.current[pastedData.length]?.focus();
    }
  };

  const handleVerify = async (verificationCode) => {
    const codeToVerify = verificationCode || code.join('');
    if (codeToVerify.length !== 6) {
      setError('Please enter a complete 6-digit code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      if (onVerify) {
        await onVerify(codeToVerify);
      }
      setSuccess('Verification successful');
      setCode(['', '', '', '', '', '']);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code');
      setCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleDisableMFA = async () => {
    const disableCode = code.join('');
    if (disableCode.length !== 6) {
      setError('Please enter your verification code to disable MFA');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await securityAPI.mfa.disable(disableCode);
      setSuccess('Two-factor authentication has been disabled');
      setCode(['', '', '', '', '', '']);
      setShowDisableConfirm(false);
      if (onStatusChange) {
        onStatusChange();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disable MFA');
    } finally {
      setLoading(false);
    }
  };

  const renderCodeInputs = () => (
    <div className="flex justify-center gap-2" onPaste={handlePaste}>
      {code.map((digit, index) => (
        <input
          key={index}
          ref={(el) => (inputRefs.current[index] = el)}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleCodeChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 dark:bg-gray-700 dark:text-white transition-colors"
          disabled={loading}
        />
      ))}
    </div>
  );

  if (mode === 'verify') {
    return (
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Two-Factor Authentication
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Enter the 6-digit code from your authenticator app
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {renderCodeInputs()}

        <button
          onClick={() => handleVerify()}
          disabled={loading || code.join('').length !== 6}
          className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Verifying...
            </>
          ) : (
            'Verify'
          )}
        </button>
      </div>
    );
  }

  return (
    <div>
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-700 dark:text-green-400">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">{success}</span>
        </div>
      )}

      {enabled ? (
        <div>
          <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg mb-4">
            <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
            <div>
              <p className="font-medium text-green-800 dark:text-green-300">
                Two-factor authentication is enabled
              </p>
              <p className="text-sm text-green-600 dark:text-green-400">
                Your account is protected with an additional layer of security
              </p>
            </div>
          </div>

          {!showDisableConfirm ? (
            <button
              onClick={() => setShowDisableConfirm(true)}
              className="flex items-center gap-2 px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <ShieldOff className="w-4 h-4" />
              Disable Two-Factor Authentication
            </button>
          ) : (
            <div className="border border-red-200 dark:border-red-800 rounded-lg p-4">
              <h4 className="font-medium text-red-800 dark:text-red-300 mb-2">
                Confirm Disable MFA
              </h4>
              <p className="text-sm text-red-600 dark:text-red-400 mb-4">
                Enter your verification code to disable two-factor authentication.
                This will make your account less secure.
              </p>

              {renderCodeInputs()}

              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => {
                    setShowDisableConfirm(false);
                    setCode(['', '', '', '', '', '']);
                    setError('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDisableMFA}
                  disabled={loading || code.join('').length !== 6}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Disabling...
                    </>
                  ) : (
                    'Disable MFA'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg mb-4">
            <ShieldOff className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            <div>
              <p className="font-medium text-yellow-800 dark:text-yellow-300">
                Two-factor authentication is not enabled
              </p>
              <p className="text-sm text-yellow-600 dark:text-yellow-400">
                Enable MFA to add an extra layer of security to your account
              </p>
            </div>
          </div>

          <a
            href="/security/mfa/setup"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Shield className="w-4 h-4" />
            Enable Two-Factor Authentication
          </a>
        </div>
      )}
    </div>
  );
}
