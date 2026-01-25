/**
 * Anomaly Dashboard Page
 * View and manage detected anomalies and alerts
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AlertTriangle,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  ChevronRight,
  Filter,
  RefreshCw,
} from 'lucide-react';
import AnomalyCard from '../components/AnomalyCard';
import { aiAPI } from '../services/aiAPI';

const AnomalyDashboard = () => {
  const { t } = useTranslation();

  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [severityFilter, setSeverityFilter] = useState('all');

  useEffect(() => {
    loadData();
  }, [statusFilter, severityFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertsData, summaryData] = await Promise.all([
        aiAPI.getAnomalyAlerts({
          status: statusFilter === 'all' ? null : statusFilter,
          severity: severityFilter === 'all' ? null : severityFilter,
        }),
        aiAPI.getAnomalySummary(),
      ]);

      setAlerts(alertsData.alerts || []);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load anomaly data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await aiAPI.acknowledgeAlert(alertId);
      loadData();
    } catch (error) {
      console.error('Acknowledge failed:', error);
    }
  };

  const handleResolve = async (alertId, notes) => {
    try {
      await aiAPI.resolveAlert(alertId, { notes });
      loadData();
      setSelectedAlert(null);
    } catch (error) {
      console.error('Resolve failed:', error);
    }
  };

  const handleDismiss = async (alertId, reason) => {
    try {
      await aiAPI.dismissAlert(alertId, { reason });
      loadData();
      setSelectedAlert(null);
    } catch (error) {
      console.error('Dismiss failed:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-yellow-500',
      low: 'bg-blue-500',
    };
    return colors[severity] || 'bg-gray-500';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="text-gray-500" size={16} />;
      case 'acknowledged': return <Eye className="text-blue-500" size={16} />;
      case 'investigating': return <AlertTriangle className="text-yellow-500" size={16} />;
      case 'resolved': return <CheckCircle className="text-green-500" size={16} />;
      case 'dismissed': return <XCircle className="text-gray-400" size={16} />;
      default: return null;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Anomaly Detection</h1>
          <p className="text-gray-600">Monitor and investigate unusual activities</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="text-blue-500" size={20} />
              <span className="text-sm text-gray-600">Total Alerts</span>
            </div>
            <div className="text-2xl font-bold">{summary.total}</div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="text-yellow-500" size={20} />
              <span className="text-sm text-gray-600">Pending</span>
            </div>
            <div className="text-2xl font-bold">{summary.pending}</div>
          </div>

          <div className="bg-white rounded-lg border p-4 border-red-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="text-red-500" size={20} />
              <span className="text-sm text-gray-600">Critical</span>
            </div>
            <div className="text-2xl font-bold text-red-600">{summary.critical_pending}</div>
          </div>

          <div className="bg-white rounded-lg border p-4 border-orange-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="text-orange-500" size={20} />
              <span className="text-sm text-gray-600">High</span>
            </div>
            <div className="text-2xl font-bold text-orange-600">{summary.high_pending}</div>
          </div>

          <div className="bg-white rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="text-green-500" size={20} />
              <span className="text-sm text-gray-600">Resolved</span>
            </div>
            <div className="text-2xl font-bold text-green-600">
              {summary.by_status?.resolved || 0}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Filter size={18} className="text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 border rounded-lg"
        >
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="animate-spin text-gray-400" size={32} />
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-white rounded-lg border p-8 text-center">
          <Shield className="mx-auto text-green-500 mb-4" size={48} />
          <div className="text-lg font-medium text-gray-700">All Clear</div>
          <div className="text-gray-500">No anomalies detected matching your filters</div>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <AnomalyCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onView={() => setSelectedAlert(alert)}
            />
          ))}
        </div>
      )}

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className={`inline-block px-2 py-1 text-xs font-medium text-white rounded ${getSeverityColor(selectedAlert.severity)}`}>
                  {selectedAlert.severity.toUpperCase()}
                </div>
                <h2 className="text-xl font-bold mt-2">{selectedAlert.title}</h2>
              </div>
              <button onClick={() => setSelectedAlert(null)} className="text-gray-500">
                <XCircle size={24} />
              </button>
            </div>

            <p className="text-gray-600 mb-4">{selectedAlert.description}</p>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <h3 className="font-medium mb-2">Details</h3>
              <pre className="text-sm text-gray-600 overflow-auto">
                {JSON.stringify(selectedAlert.details, null, 2)}
              </pre>
            </div>

            <div className="flex gap-3">
              {selectedAlert.status === 'pending' && (
                <button
                  onClick={() => handleAcknowledge(selectedAlert.id)}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Acknowledge
                </button>
              )}
              <button
                onClick={() => handleResolve(selectedAlert.id, 'Reviewed and resolved')}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Resolve
              </button>
              <button
                onClick={() => handleDismiss(selectedAlert.id, 'False positive')}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnomalyDashboard;
