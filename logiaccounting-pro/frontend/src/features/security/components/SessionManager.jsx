import { useState, useEffect } from 'react';
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  MapPin,
  Clock,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  LogOut,
  Loader2
} from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

export default function SessionManager() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState(null);
  const [revokingAll, setRevokingAll] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await securityAPI.sessions.list();
      setSessions(response.data.sessions || []);
    } catch (err) {
      setError('Failed to load sessions');
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    try {
      setRevoking(sessionId);
      setError('');
      await securityAPI.sessions.revoke(sessionId);
      setSuccess('Session revoked successfully');
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to revoke session');
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAllOther = async () => {
    try {
      setRevokingAll(true);
      setError('');
      await securityAPI.sessions.revokeAllOther();
      setSuccess('All other sessions have been revoked');
      setSessions((prev) => prev.filter((s) => s.is_current));
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to revoke sessions');
    } finally {
      setRevokingAll(false);
    }
  };

  const getDeviceIcon = (deviceType) => {
    const type = (deviceType || '').toLowerCase();
    if (type.includes('mobile') || type.includes('phone')) {
      return <Smartphone className="w-5 h-5" />;
    }
    if (type.includes('tablet') || type.includes('ipad')) {
      return <Tablet className="w-5 h-5" />;
    }
    return <Monitor className="w-5 h-5" />;
  };

  const formatLastActive = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const formatCreatedAt = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600 dark:text-gray-400">Loading sessions...</span>
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

      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {sessions.length} active session{sessions.length !== 1 ? 's' : ''}
        </p>
        <div className="flex gap-2">
          <button
            onClick={loadSessions}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {sessions.filter((s) => !s.is_current).length > 0 && (
            <button
              onClick={handleRevokeAllOther}
              disabled={revokingAll}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {revokingAll ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogOut className="w-4 h-4" />
              )}
              Sign out all other sessions
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`border rounded-lg p-4 ${
              session.is_current
                ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                : 'border-gray-200 dark:border-gray-700'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${
                  session.is_current
                    ? 'bg-green-100 dark:bg-green-800 text-green-600 dark:text-green-300'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}>
                  {getDeviceIcon(session.device_type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {session.device_name || session.browser || 'Unknown Device'}
                    </h4>
                    {session.is_current && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200 rounded-full">
                        Current Session
                      </span>
                    )}
                  </div>
                  <div className="mt-1 space-y-1">
                    {session.browser && session.os && (
                      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                        <Globe className="w-3.5 h-3.5" />
                        <span>{session.browser} on {session.os}</span>
                      </div>
                    )}
                    {(session.location || session.ip_address) && (
                      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                        <MapPin className="w-3.5 h-3.5" />
                        <span>
                          {session.location || session.ip_address}
                          {session.location && session.ip_address && ` (${session.ip_address})`}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-500">
                      <Clock className="w-3.5 h-3.5" />
                      <span>
                        Last active: {formatLastActive(session.last_active)}
                        {session.created_at && (
                          <span className="ml-2 text-xs">
                            (Started: {formatCreatedAt(session.created_at)})
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              {!session.is_current && (
                <button
                  onClick={() => handleRevokeSession(session.id)}
                  disabled={revoking === session.id}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                  title="Revoke this session"
                >
                  {revoking === session.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  <span className="hidden sm:inline">Revoke</span>
                </button>
              )}
            </div>
          </div>
        ))}

        {sessions.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Monitor className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No active sessions found</p>
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Session Security Tips</h4>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>Regularly review your active sessions and revoke any you do not recognize</li>
          <li>If you see an unfamiliar location or device, change your password immediately</li>
          <li>Enable two-factor authentication for additional security</li>
        </ul>
      </div>
    </div>
  );
}
