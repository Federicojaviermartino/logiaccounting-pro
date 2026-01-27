/**
 * Compliance Dashboard Page
 */
import { useState, useEffect } from 'react';
import { 
  Shield, AlertTriangle, CheckCircle, Clock, 
  FileText, TrendingUp, RefreshCw 
} from 'lucide-react';
import auditAPI from '../services/auditAPI';

export default function ComplianceDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await auditAPI.getDashboard();
      setDashboard(response.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-gray-500">Monitor compliance status and violations</p>
        </div>
        <button
          onClick={loadDashboard}
          className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Compliance Score */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-8">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle
                cx="64" cy="64" r="56"
                stroke="#e5e7eb" strokeWidth="12" fill="none"
              />
              <circle
                cx="64" cy="64" r="56"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${(dashboard?.compliance_score || 0) * 3.52} 352`}
                className={getScoreColor(dashboard?.compliance_score || 0)}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-3xl font-bold ${getScoreColor(dashboard?.compliance_score || 0)}`}>
                {Math.round(dashboard?.compliance_score || 0)}%
              </span>
            </div>
          </div>
          <div>
            <h3 className="text-xl font-semibold">Compliance Score</h3>
            <p className="text-gray-500 mt-1">
              Based on active rules and open violations
            </p>
            <div className="mt-4 flex gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="text-green-500" size={20} />
                <span>{dashboard?.active_rules || 0} Active Rules</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="text-red-500" size={20} />
                <span>{dashboard?.open_violations || 0} Open Violations</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Rules</p>
              <p className="text-2xl font-bold">{dashboard?.total_rules || 0}</p>
            </div>
            <Shield className="w-10 h-10 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Open Violations</p>
              <p className="text-2xl font-bold text-red-600">{dashboard?.open_violations || 0}</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-red-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Retention Policies</p>
              <p className="text-2xl font-bold">{dashboard?.retention_policies || 0}</p>
            </div>
            <FileText className="w-10 h-10 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Active Rules</p>
              <p className="text-2xl font-bold">{dashboard?.active_rules || 0}</p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
        </div>
      </div>

      {/* Violations by Severity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Violations by Severity</h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {['critical', 'high', 'medium', 'low'].map(severity => {
                const count = dashboard?.violations_by_severity?.[severity] || 0;
                const colors = {
                  critical: 'bg-red-500',
                  high: 'bg-orange-500',
                  medium: 'bg-yellow-500',
                  low: 'bg-gray-400'
                };
                return (
                  <div key={severity} className="flex items-center gap-4">
                    <span className="w-20 capitalize text-sm">{severity}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-4">
                      <div
                        className={`${colors[severity]} h-4 rounded-full`}
                        style={{ width: `${Math.min(count * 10, 100)}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-sm font-medium">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Violations by Standard</h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {Object.entries(dashboard?.violations_by_standard || {}).map(([standard, count]) => (
                <div key={standard} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="uppercase font-medium">{standard}</span>
                  <span className="text-red-600 font-bold">{count}</span>
                </div>
              ))}
              {Object.keys(dashboard?.violations_by_standard || {}).length === 0 && (
                <p className="text-gray-500 text-center py-4">No violations</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Violations */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h3 className="font-semibold">Recent Violations</h3>
        </div>
        <div className="divide-y">
          {(dashboard?.recent_violations || []).length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-2" />
              <p>No recent violations</p>
            </div>
          ) : (
            dashboard.recent_violations.map(violation => (
              <div key={violation.id} className="p-4 flex items-center gap-4">
                <AlertTriangle className={`w-5 h-5 ${
                  violation.severity === 'critical' ? 'text-red-600' :
                  violation.severity === 'high' ? 'text-orange-600' :
                  'text-yellow-600'
                }`} />
                <div className="flex-1">
                  <p className="font-medium">{violation.violation_type}</p>
                  <p className="text-sm text-gray-500">{violation.description}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  violation.status === 'open' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                }`}>
                  {violation.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
