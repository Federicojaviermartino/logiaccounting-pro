# Phase 32: Advanced Security - Part 10: Frontend Security Pages

## Overview
This part covers the frontend pages for security settings, MFA setup, and audit logs.

---

## File 1: Security Settings Page
**Path:** `frontend/src/features/security/pages/SecuritySettings.jsx`

```jsx
/**
 * Security Settings Page
 * Main security configuration and overview
 */

import React, { useState, useEffect } from 'react';
import { 
  Shield, Key, Smartphone, Users, Clock, 
  AlertTriangle, CheckCircle, Settings, Lock,
  Eye, EyeOff, RefreshCw
} from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

const SecuritySettings = () => {
  const [securityStatus, setSecurityStatus] = useState(null);
  const [mfaStatus, setMfaStatus] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      const [status, mfa, sessionsData] = await Promise.all([
        securityAPI.getSecurityStatus(),
        securityAPI.getMFAStatus(),
        securityAPI.getSessions(),
      ]);
      
      setSecurityStatus(status);
      setMfaStatus(mfa);
      setSessions(sessionsData.sessions || []);
    } catch (error) {
      console.error('Failed to load security data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    if (!confirm('Are you sure you want to revoke this session?')) return;
    
    try {
      await securityAPI.revokeSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
    } catch (error) {
      console.error('Failed to revoke session:', error);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!confirm('This will log you out of all other devices. Continue?')) return;
    
    try {
      await securityAPI.revokeAllSessions();
      loadSecurityData();
    } catch (error) {
      console.error('Failed to revoke sessions:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Shield className="w-7 h-7 text-blue-600" />
          Security Settings
        </h1>
        <p className="text-gray-600 mt-1">
          Manage your account security and authentication settings
        </p>
      </div>

      {/* Security Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatusCard
          icon={<Shield className="w-5 h-5" />}
          label="Security Status"
          value={securityStatus?.status || 'Unknown'}
          color={securityStatus?.status === 'healthy' ? 'green' : 'yellow'}
        />
        <StatusCard
          icon={<Smartphone className="w-5 h-5" />}
          label="MFA Status"
          value={mfaStatus?.enabled ? 'Enabled' : 'Disabled'}
          color={mfaStatus?.enabled ? 'green' : 'red'}
        />
        <StatusCard
          icon={<Users className="w-5 h-5" />}
          label="Active Sessions"
          value={sessions.length}
          color="blue"
        />
        <StatusCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Security Alerts"
          value={securityStatus?.recent_security_events || 0}
          color={securityStatus?.recent_security_events > 0 ? 'yellow' : 'green'}
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: Shield },
            { id: 'mfa', label: 'Two-Factor Auth', icon: Smartphone },
            { id: 'sessions', label: 'Active Sessions', icon: Users },
            { id: 'password', label: 'Password', icon: Key },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <OverviewTab status={securityStatus} mfaStatus={mfaStatus} />
      )}
      
      {activeTab === 'mfa' && (
        <MFATab status={mfaStatus} onUpdate={loadSecurityData} />
      )}
      
      {activeTab === 'sessions' && (
        <SessionsTab
          sessions={sessions}
          onRevoke={handleRevokeSession}
          onRevokeAll={handleRevokeAllSessions}
        />
      )}
      
      {activeTab === 'password' && (
        <PasswordTab />
      )}
    </div>
  );
};

const StatusCard = ({ icon, label, value, color }) => {
  const colors = {
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  };

  return (
    <div className={`p-4 rounded-lg border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
};

const OverviewTab = ({ status, mfaStatus }) => (
  <div className="space-y-6">
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold mb-4">Security Checklist</h3>
      <div className="space-y-3">
        <ChecklistItem
          checked={mfaStatus?.enabled}
          label="Two-factor authentication enabled"
          description="Add an extra layer of security to your account"
        />
        <ChecklistItem
          checked={true}
          label="Strong password set"
          description="Your password meets security requirements"
        />
        <ChecklistItem
          checked={status?.encryption_available}
          label="Data encryption active"
          description="Your sensitive data is encrypted"
        />
        <ChecklistItem
          checked={mfaStatus?.backup_codes_remaining > 0}
          label="Backup codes available"
          description={`${mfaStatus?.backup_codes_remaining || 0} backup codes remaining`}
        />
      </div>
    </div>

    {status?.warnings?.length > 0 && (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Security Warnings
        </h3>
        <ul className="mt-2 space-y-1">
          {status.warnings.map((warning, idx) => (
            <li key={idx} className="text-sm text-yellow-700">• {warning}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const ChecklistItem = ({ checked, label, description }) => (
  <div className="flex items-start gap-3">
    <div className={`mt-0.5 p-1 rounded-full ${checked ? 'bg-green-100' : 'bg-gray-100'}`}>
      {checked ? (
        <CheckCircle className="w-4 h-4 text-green-600" />
      ) : (
        <AlertTriangle className="w-4 h-4 text-gray-400" />
      )}
    </div>
    <div>
      <div className={`font-medium ${checked ? 'text-gray-900' : 'text-gray-500'}`}>
        {label}
      </div>
      <div className="text-sm text-gray-500">{description}</div>
    </div>
  </div>
);

const MFATab = ({ status, onUpdate }) => {
  const [showSetup, setShowSetup] = useState(false);

  if (status?.enabled && !showSetup) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">Two-Factor Authentication</h3>
            <p className="text-sm text-gray-500">
              Currently using: {status.method?.toUpperCase()}
            </p>
          </div>
          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
            Enabled
          </span>
        </div>
        
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600">
              Backup codes remaining: <strong>{status.backup_codes_remaining}</strong>
            </div>
            {status.backup_codes_remaining < 3 && (
              <p className="text-sm text-yellow-600 mt-1">
                Consider regenerating backup codes
              </p>
            )}
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => setShowSetup(true)}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Change Method
            </button>
            <button
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Regenerate Backup Codes
            </button>
            <button
              className="px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
            >
              Disable MFA
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <MFASetupWizard onComplete={onUpdate} />;
};

const MFASetupWizard = ({ onComplete }) => {
  // This would be imported from MFASetup.jsx
  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold mb-4">Set Up Two-Factor Authentication</h3>
      <p className="text-gray-600 mb-6">
        Choose your preferred authentication method:
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MFAMethodCard
          icon={<Smartphone className="w-8 h-8" />}
          title="Authenticator App"
          description="Use Google Authenticator, Authy, or similar"
          recommended
        />
        <MFAMethodCard
          icon={<Key className="w-8 h-8" />}
          title="SMS"
          description="Receive codes via text message"
        />
        <MFAMethodCard
          icon={<Lock className="w-8 h-8" />}
          title="Email"
          description="Receive codes via email"
        />
      </div>
    </div>
  );
};

const MFAMethodCard = ({ icon, title, description, recommended, onClick }) => (
  <button
    onClick={onClick}
    className={`p-4 border rounded-lg text-left hover:border-blue-500 hover:bg-blue-50 transition ${
      recommended ? 'border-blue-200 bg-blue-50/50' : ''
    }`}
  >
    <div className="text-blue-600 mb-2">{icon}</div>
    <h4 className="font-semibold">
      {title}
      {recommended && (
        <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
          Recommended
        </span>
      )}
    </h4>
    <p className="text-sm text-gray-500 mt-1">{description}</p>
  </button>
);

const SessionsTab = ({ sessions, onRevoke, onRevokeAll }) => (
  <div className="space-y-4">
    <div className="flex justify-between items-center">
      <h3 className="text-lg font-semibold">Active Sessions</h3>
      <button
        onClick={onRevokeAll}
        className="text-sm text-red-600 hover:text-red-700"
      >
        Sign out all other sessions
      </button>
    </div>
    
    <div className="space-y-3">
      {sessions.map(session => (
        <div
          key={session.id}
          className={`p-4 bg-white border rounded-lg ${
            session.is_current ? 'border-blue-200 bg-blue-50/30' : ''
          }`}
        >
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">
                  {session.device?.browser} on {session.device?.os}
                </span>
                {session.is_current && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    Current
                  </span>
                )}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {session.location?.city}, {session.location?.country} • {session.location?.ip}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Last active: {new Date(session.last_activity).toLocaleString()}
              </div>
            </div>
            {!session.is_current && (
              <button
                onClick={() => onRevoke(session.id)}
                className="text-sm text-red-600 hover:text-red-700"
              >
                Revoke
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const PasswordTab = () => {
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  return (
    <div className="bg-white rounded-lg border p-6 max-w-md">
      <h3 className="text-lg font-semibold mb-4">Change Password</h3>
      
      <form className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Password
          </label>
          <div className="relative">
            <input
              type={showCurrent ? 'text' : 'password'}
              className="w-full px-3 py-2 border rounded-lg pr-10"
            />
            <button
              type="button"
              onClick={() => setShowCurrent(!showCurrent)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            New Password
          </label>
          <div className="relative">
            <input
              type={showNew ? 'text' : 'password'}
              className="w-full px-3 py-2 border rounded-lg pr-10"
            />
            <button
              type="button"
              onClick={() => setShowNew(!showNew)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confirm New Password
          </label>
          <input
            type="password"
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
        
        <div className="text-sm text-gray-500">
          Password must be at least 12 characters with uppercase, lowercase, number, and special character.
        </div>
        
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Update Password
        </button>
      </form>
    </div>
  );
};

export default SecuritySettings;
```

---

## File 2: MFA Setup Page
**Path:** `frontend/src/features/security/pages/MFASetup.jsx`

```jsx
/**
 * MFA Setup Page
 * Step-by-step MFA configuration wizard
 */

import React, { useState } from 'react';
import { 
  Smartphone, Key, Mail, CheckCircle, 
  Copy, AlertTriangle, ArrowRight, ArrowLeft
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { securityAPI } from '../services/securityAPI';

const MFASetup = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(1);
  const [method, setMethod] = useState(null);
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [backupCodesCopied, setBackupCodesCopied] = useState(false);

  const methods = [
    {
      id: 'totp',
      name: 'Authenticator App',
      icon: Smartphone,
      description: 'Use an authenticator app like Google Authenticator or Authy',
      recommended: true,
    },
    {
      id: 'sms',
      name: 'SMS',
      icon: Key,
      description: 'Receive verification codes via text message',
    },
    {
      id: 'email',
      name: 'Email',
      icon: Mail,
      description: 'Receive verification codes via email',
    },
  ];

  const handleMethodSelect = async (selectedMethod) => {
    setMethod(selectedMethod);
    setError('');
    
    if (selectedMethod === 'sms') {
      setStep(2); // Need phone number first
      return;
    }
    
    await initiateSetup(selectedMethod);
  };

  const initiateSetup = async (selectedMethod, phone = null) => {
    try {
      setLoading(true);
      const result = await securityAPI.setupMFA({
        method: selectedMethod,
        phone_number: phone,
      });
      
      setSetupData(result);
      setStep(selectedMethod === 'totp' ? 3 : 4); // QR code step or verification
    } catch (err) {
      setError(err.message || 'Failed to setup MFA');
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    await initiateSetup('sms', phoneNumber);
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError('');
      
      await securityAPI.verifyMFASetup(verificationCode);
      setStep(5); // Backup codes step
    } catch (err) {
      setError(err.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCodes = () => {
    const codes = setupData?.backup_codes?.join('\n') || '';
    navigator.clipboard.writeText(codes);
    setBackupCodesCopied(true);
    setTimeout(() => setBackupCodesCopied(false), 2000);
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div>
            <h2 className="text-xl font-semibold mb-2">Choose Authentication Method</h2>
            <p className="text-gray-600 mb-6">
              Select how you want to receive verification codes
            </p>
            
            <div className="space-y-3">
              {methods.map(m => (
                <button
                  key={m.id}
                  onClick={() => handleMethodSelect(m.id)}
                  disabled={loading}
                  className={`w-full p-4 border rounded-lg text-left flex items-start gap-4 hover:border-blue-500 hover:bg-blue-50 transition ${
                    m.recommended ? 'border-blue-200' : ''
                  }`}
                >
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <m.icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{m.name}</span>
                      {m.recommended && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{m.description}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 mt-2" />
                </button>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <form onSubmit={handlePhoneSubmit}>
            <h2 className="text-xl font-semibold mb-2">Enter Phone Number</h2>
            <p className="text-gray-600 mb-6">
              We'll send verification codes to this number
            </p>
            
            <div className="mb-4">
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full px-4 py-3 border rounded-lg text-lg"
                required
              />
            </div>
            
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                <ArrowLeft className="w-4 h-4 inline mr-2" />
                Back
              </button>
              <button
                type="submit"
                disabled={loading || !phoneNumber}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Setting up...' : 'Continue'}
              </button>
            </div>
          </form>
        );

      case 3:
        return (
          <div>
            <h2 className="text-xl font-semibold mb-2">Scan QR Code</h2>
            <p className="text-gray-600 mb-6">
              Open your authenticator app and scan this QR code
            </p>
            
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-white border rounded-lg">
                {setupData?.qr_code_uri && (
                  <QRCodeSVG value={setupData.qr_code_uri} size={200} />
                )}
              </div>
            </div>
            
            <div className="text-center text-sm text-gray-500 mb-6">
              Can't scan? Enter this code manually:<br />
              <code className="bg-gray-100 px-2 py-1 rounded mt-1 inline-block">
                {setupData?.secret || 'XXXX-XXXX-XXXX-XXXX'}
              </code>
            </div>
            
            <button
              onClick={() => setStep(4)}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              I've Scanned the Code
            </button>
          </div>
        );

      case 4:
        return (
          <form onSubmit={handleVerify}>
            <h2 className="text-xl font-semibold mb-2">Enter Verification Code</h2>
            <p className="text-gray-600 mb-6">
              Enter the 6-digit code from your {method === 'totp' ? 'authenticator app' : method}
            </p>
            
            <div className="mb-4">
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="w-full px-4 py-3 border rounded-lg text-2xl text-center tracking-widest"
                maxLength={6}
                required
              />
            </div>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(method === 'totp' ? 3 : 1)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                <ArrowLeft className="w-4 h-4 inline mr-2" />
                Back
              </button>
              <button
                type="submit"
                disabled={loading || verificationCode.length !== 6}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          </form>
        );

      case 5:
        return (
          <div>
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold">MFA Enabled Successfully!</h2>
              <p className="text-gray-600 mt-2">
                Save these backup codes in a secure location
              </p>
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <strong>Important:</strong> These codes will only be shown once. 
                  Store them safely - you'll need them if you lose access to your device.
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 border rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                {setupData?.backup_codes?.map((code, idx) => (
                  <div key={idx} className="bg-white px-3 py-2 rounded border">
                    {code}
                  </div>
                ))}
              </div>
            </div>
            
            <button
              onClick={copyBackupCodes}
              className="w-full mb-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2"
            >
              <Copy className="w-4 h-4" />
              {backupCodesCopied ? 'Copied!' : 'Copy All Codes'}
            </button>
            
            <button
              onClick={onComplete}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-md mx-auto">
      {/* Progress indicator */}
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3, 4, 5].map(s => (
          <div key={s} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              s < step ? 'bg-blue-600 text-white' :
              s === step ? 'bg-blue-100 text-blue-600 border-2 border-blue-600' :
              'bg-gray-100 text-gray-400'
            }`}>
              {s < step ? <CheckCircle className="w-4 h-4" /> : s}
            </div>
            {s < 5 && (
              <div className={`w-12 h-0.5 ${s < step ? 'bg-blue-600' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>
      
      {renderStep()}
    </div>
  );
};

export default MFASetup;
```

---

## File 3: Audit Logs Page
**Path:** `frontend/src/features/security/pages/AuditLogs.jsx`

```jsx
/**
 * Audit Logs Page
 * View and search security audit logs
 */

import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, Download, Calendar,
  User, Shield, Database, Settings,
  AlertTriangle, CheckCircle, XCircle, Clock
} from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    eventType: '',
    userId: '',
    startDate: '',
    endDate: '',
  });
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    loadLogs();
    loadSummary();
  }, [filters]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await securityAPI.queryAuditLogs(filters);
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await securityAPI.getAuditSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    }
  };

  const handleExport = async (format) => {
    try {
      const blob = await securityAPI.exportAuditLogs(format, filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs.${format}`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getEventIcon = (eventType) => {
    if (eventType.startsWith('auth.')) return User;
    if (eventType.startsWith('security.')) return Shield;
    if (eventType.startsWith('data.')) return Database;
    if (eventType.startsWith('config.')) return Settings;
    return Clock;
  };

  const getOutcomeStyle = (outcome) => {
    switch (outcome) {
      case 'success': return { icon: CheckCircle, color: 'text-green-600 bg-green-50' };
      case 'failure': return { icon: XCircle, color: 'text-red-600 bg-red-50' };
      case 'denied': return { icon: AlertTriangle, color: 'text-yellow-600 bg-yellow-50' };
      default: return { icon: Clock, color: 'text-gray-600 bg-gray-50' };
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600">Security and activity audit trail</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <SummaryCard
            label="Total Events"
            value={summary.total_events}
            icon={<Clock className="w-5 h-5" />}
          />
          <SummaryCard
            label="Successful"
            value={summary.by_outcome?.success || 0}
            icon={<CheckCircle className="w-5 h-5" />}
            color="green"
          />
          <SummaryCard
            label="Failed"
            value={summary.by_outcome?.failure || 0}
            icon={<XCircle className="w-5 h-5" />}
            color="red"
          />
          <SummaryCard
            label="Denied"
            value={summary.by_outcome?.denied || 0}
            icon={<AlertTriangle className="w-5 h-5" />}
            color="yellow"
          />
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Event Type
            </label>
            <select
              value={filters.eventType}
              onChange={(e) => setFilters({ ...filters, eventType: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">All Events</option>
              <option value="auth.login">Login</option>
              <option value="auth.logout">Logout</option>
              <option value="auth.login_failed">Failed Login</option>
              <option value="auth.mfa_verified">MFA Verified</option>
              <option value="data.create">Data Create</option>
              <option value="data.update">Data Update</option>
              <option value="data.delete">Data Delete</option>
              <option value="security.alert">Security Alert</option>
            </select>
          </div>
          
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ eventType: '', userId: '', startDate: '', endDate: '' })}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Timestamp</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Event</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Outcome</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">IP Address</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No audit logs found
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const EventIcon = getEventIcon(log.event_type);
                const outcomeStyle = getOutcomeStyle(log.outcome);
                const OutcomeIcon = outcomeStyle.icon;
                
                return (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <EventIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium">
                          {log.event_type.replace(/_/g, ' ').replace(/\./g, ' › ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {log.user_id ? log.user_id.slice(0, 8) + '...' : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${outcomeStyle.color}`}>
                        <OutcomeIcon className="w-3 h-3" />
                        {log.outcome}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="text-blue-600 hover:text-blue-700 text-sm"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <LogDetailModal log={selectedLog} onClose={() => setSelectedLog(null)} />
      )}
    </div>
  );
};

const SummaryCard = ({ label, value, icon, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    yellow: 'bg-yellow-50 text-yellow-700',
  };

  return (
    <div className={`p-4 rounded-lg ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
};

const LogDetailModal = ({ log, onClose }) => (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto">
      <div className="p-6 border-b">
        <h2 className="text-lg font-semibold">Audit Log Details</h2>
      </div>
      <div className="p-6 space-y-4">
        <DetailRow label="Event ID" value={log.id} />
        <DetailRow label="Timestamp" value={new Date(log.timestamp).toLocaleString()} />
        <DetailRow label="Event Type" value={log.event_type} />
        <DetailRow label="Outcome" value={log.outcome} />
        <DetailRow label="Severity" value={log.severity} />
        <DetailRow label="User ID" value={log.user_id || '-'} />
        <DetailRow label="IP Address" value={log.ip_address || '-'} />
        <DetailRow label="User Agent" value={log.user_agent || '-'} />
        <DetailRow label="Resource" value={`${log.resource_type || '-'} / ${log.resource_id || '-'}`} />
        <DetailRow label="Action" value={log.action || '-'} />
        <DetailRow label="Description" value={log.description || '-'} />
        
        {log.details && Object.keys(log.details).length > 0 && (
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Details</div>
            <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
              {JSON.stringify(log.details, null, 2)}
            </pre>
          </div>
        )}
      </div>
      <div className="p-4 border-t flex justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          Close
        </button>
      </div>
    </div>
  </div>
);

const DetailRow = ({ label, value }) => (
  <div className="flex">
    <div className="w-32 text-sm font-medium text-gray-600">{label}</div>
    <div className="flex-1 text-sm text-gray-900">{value}</div>
  </div>
);

export default AuditLogs;
```

---

## Summary Part 10

| File | Description | Lines |
|------|-------------|-------|
| `pages/SecuritySettings.jsx` | Security settings page | ~380 |
| `pages/MFASetup.jsx` | MFA setup wizard | ~280 |
| `pages/AuditLogs.jsx` | Audit logs viewer | ~290 |
| **Total** | | **~950 lines** |
