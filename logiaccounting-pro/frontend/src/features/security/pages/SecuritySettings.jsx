import { useState, useEffect } from 'react';
import { Shield, Smartphone, Monitor, Key, AlertTriangle, CheckCircle } from 'lucide-react';
import { securityAPI } from '../services/securityAPI';
import MFAVerification from '../components/MFAVerification';
import SessionManager from '../components/SessionManager';

export default function SecuritySettings() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [securityStatus, setSecurityStatus] = useState(null);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield },
    { id: 'mfa', label: 'MFA', icon: Smartphone },
    { id: 'sessions', label: 'Sessions', icon: Monitor },
    { id: 'password', label: 'Password', icon: Key }
  ];

  useEffect(() => {
    loadSecurityStatus();
  }, []);

  const loadSecurityStatus = async () => {
    try {
      setLoading(true);
      const response = await securityAPI.getSecurityStatus();
      setSecurityStatus(response.data);
    } catch (error) {
      console.error('Failed to load security status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    try {
      setSaving(true);
      await securityAPI.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      setPasswordSuccess('Password changed successfully');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      setPasswordError(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const calculateSecurityScore = () => {
    if (!securityStatus) return 0;
    let score = 40;
    if (securityStatus.mfa_enabled) score += 30;
    if (securityStatus.password_strong) score += 15;
    if (securityStatus.recent_password_change) score += 15;
    return score;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const securityScore = calculateSecurityScore();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Security Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">Manage your account security and authentication settings</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Security Score</h2>
            <div className="flex items-center gap-6">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-gray-200 dark:text-gray-700"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeDasharray={`${(securityScore / 100) * 352} 352`}
                    className={getScoreBgColor(securityScore)}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-3xl font-bold ${getScoreColor(securityScore)}`}>
                    {securityScore}
                  </span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  {securityScore >= 80 ? 'Excellent Security' : securityScore >= 50 ? 'Good Security' : 'Needs Improvement'}
                </h3>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm">
                    {securityStatus?.mfa_enabled ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    )}
                    <span className="text-gray-600 dark:text-gray-400">
                      Two-factor authentication {securityStatus?.mfa_enabled ? 'enabled' : 'not enabled'}
                    </span>
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    {securityStatus?.password_strong ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    )}
                    <span className="text-gray-600 dark:text-gray-400">
                      Password strength: {securityStatus?.password_strong ? 'Strong' : 'Could be stronger'}
                    </span>
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    {securityStatus?.recent_password_change ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    )}
                    <span className="text-gray-600 dark:text-gray-400">
                      Last password change: {securityStatus?.last_password_change || 'Unknown'}
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-4">
                <Smartphone className="w-6 h-6 text-blue-600" />
                <h3 className="font-semibold text-gray-900 dark:text-white">Two-Factor Authentication</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                Add an extra layer of security to your account by requiring a verification code.
              </p>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                securityStatus?.mfa_enabled
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}>
                {securityStatus?.mfa_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-4">
                <Monitor className="w-6 h-6 text-blue-600" />
                <h3 className="font-semibold text-gray-900 dark:text-white">Active Sessions</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                Monitor and manage devices that are currently logged into your account.
              </p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                {securityStatus?.active_sessions || 0} active
              </span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'mfa' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Two-Factor Authentication</h2>
          <MFAVerification
            enabled={securityStatus?.mfa_enabled}
            onStatusChange={loadSecurityStatus}
          />
        </div>
      )}

      {activeTab === 'sessions' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Active Sessions</h2>
          <SessionManager />
        </div>
      )}

      {activeTab === 'password' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Change Password</h2>
          <form onSubmit={handlePasswordChange} className="max-w-md space-y-4">
            {passwordError && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded">
                {passwordError}
              </div>
            )}
            {passwordSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded">
                {passwordSuccess}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Current Password
              </label>
              <input
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                New Password
              </label>
              <input
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                required
                minLength={8}
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Minimum 8 characters
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                required
              />
            </div>
            <button
              type="submit"
              disabled={saving}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Changing Password...' : 'Change Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
