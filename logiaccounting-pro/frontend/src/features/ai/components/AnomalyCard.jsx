/**
 * Anomaly Card Component
 * Displays individual anomaly alert
 */

import React from 'react';
import {
  AlertTriangle,
  Clock,
  Eye,
  CheckCircle,
  ChevronRight,
  DollarSign,
  User,
  FileText,
} from 'lucide-react';

const AnomalyCard = ({ alert, onAcknowledge, onView }) => {
  const getSeverityStyles = (severity) => {
    const styles = {
      critical: {
        border: 'border-red-500',
        bg: 'bg-red-50',
        badge: 'bg-red-500 text-white',
        icon: 'text-red-500',
      },
      high: {
        border: 'border-orange-400',
        bg: 'bg-orange-50',
        badge: 'bg-orange-500 text-white',
        icon: 'text-orange-500',
      },
      medium: {
        border: 'border-yellow-400',
        bg: 'bg-yellow-50',
        badge: 'bg-yellow-500 text-white',
        icon: 'text-yellow-500',
      },
      low: {
        border: 'border-blue-300',
        bg: 'bg-blue-50',
        badge: 'bg-blue-500 text-white',
        icon: 'text-blue-500',
      },
    };
    return styles[severity] || styles.low;
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { bg: 'bg-gray-100 text-gray-700', icon: Clock },
      acknowledged: { bg: 'bg-blue-100 text-blue-700', icon: Eye },
      investigating: { bg: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle },
      resolved: { bg: 'bg-green-100 text-green-700', icon: CheckCircle },
      dismissed: { bg: 'bg-gray-100 text-gray-500', icon: CheckCircle },
    };
    return badges[status] || badges.pending;
  };

  const getEntityIcon = (entityType) => {
    switch (entityType) {
      case 'transaction':
      case 'payment': return DollarSign;
      case 'invoice': return FileText;
      case 'customer':
      case 'vendor': return User;
      default: return AlertTriangle;
    }
  };

  const styles = getSeverityStyles(alert.severity);
  const statusBadge = getStatusBadge(alert.status);
  const StatusIcon = statusBadge.icon;
  const EntityIcon = getEntityIcon(alert.entity_type);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`bg-white rounded-lg border-l-4 ${styles.border} shadow-sm hover:shadow-md transition-shadow`}>
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {/* Severity Icon */}
            <div className={`p-2 rounded-full ${styles.bg}`}>
              <AlertTriangle className={styles.icon} size={20} />
            </div>

            {/* Content */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles.badge}`}>
                  {alert.severity.toUpperCase()}
                </span>
                <span className={`px-2 py-0.5 text-xs font-medium rounded flex items-center gap-1 ${statusBadge.bg}`}>
                  <StatusIcon size={12} />
                  {alert.status}
                </span>
              </div>

              <h3 className="font-semibold text-gray-900">{alert.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{alert.description}</p>

              {/* Meta info */}
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <EntityIcon size={12} />
                  {alert.entity_type}: {alert.entity_id}
                </span>
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {formatDate(alert.created_at)}
                </span>
              </div>

              {/* Recommended action */}
              {alert.recommended_action && (
                <div className="mt-2 text-sm text-blue-600">
                  {alert.recommended_action}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {alert.status === 'pending' && (
              <button
                onClick={() => onAcknowledge(alert.id)}
                className="px-3 py-1 text-sm border border-blue-500 text-blue-600 rounded hover:bg-blue-50"
              >
                Acknowledge
              </button>
            )}
            <button
              onClick={() => onView(alert)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            >
              <ChevronRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnomalyCard;
