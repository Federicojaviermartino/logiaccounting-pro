/**
 * Recommendation Panel Component
 * Displays AI-generated business recommendations
 */

import React from 'react';
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Users,
  FileText,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

const RecommendationPanel = ({ recommendations, onActionClick }) => {
  const getTypeIcon = (type) => {
    const icons = {
      invoice_reminder: FileText,
      payment_schedule: DollarSign,
      cash_flow: TrendingUp,
      expense_optimization: DollarSign,
      customer_risk: Users,
      project_health: TrendingUp,
      pricing: DollarSign,
    };
    return icons[type] || Lightbulb;
  };

  const getPriorityStyles = (priority) => {
    if (priority === 'critical') {
      return {
        border: 'border-l-red-500',
        bg: 'bg-red-50',
        text: 'text-red-700',
        badge: 'bg-red-100 text-red-800',
      };
    }
    if (priority === 'high') {
      return {
        border: 'border-l-orange-500',
        bg: 'bg-orange-50',
        text: 'text-orange-700',
        badge: 'bg-orange-100 text-orange-800',
      };
    }
    if (priority === 'medium') {
      return {
        border: 'border-l-yellow-500',
        bg: 'bg-yellow-50',
        text: 'text-yellow-700',
        badge: 'bg-yellow-100 text-yellow-800',
      };
    }
    return {
      border: 'border-l-blue-500',
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      badge: 'bg-blue-100 text-blue-800',
    };
  };

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-white rounded-lg border p-6 text-center">
        <Sparkles className="mx-auto text-gray-400 mb-3" size={32} />
        <div className="text-gray-600">No recommendations at this time</div>
        <div className="text-sm text-gray-400 mt-1">
          We'll notify you when we have suggestions
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border">
      <div className="p-4 border-b flex items-center gap-2">
        <Lightbulb className="text-yellow-500" size={20} />
        <h2 className="font-semibold">AI Recommendations</h2>
      </div>

      <div className="divide-y">
        {recommendations.map((rec, index) => {
          const Icon = getTypeIcon(rec.type);
          const styles = getPriorityStyles(rec.priority);

          return (
            <div
              key={index}
              className={`p-4 border-l-4 ${styles.border} hover:bg-gray-50 transition-colors`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-full ${styles.bg}`}>
                  <Icon className={styles.text} size={18} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles.badge}`}>
                      {rec.priority.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      {rec.type.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <h3 className="font-medium text-gray-900">{rec.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{rec.description}</p>

                  {rec.potential_impact && (
                    <div className="mt-2 text-sm text-green-600 flex items-center gap-1">
                      <TrendingUp size={14} />
                      Impact: {rec.potential_impact}
                    </div>
                  )}

                  {rec.actions && rec.actions.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {rec.actions.map((action, i) => (
                        <button
                          key={i}
                          onClick={() => onActionClick?.(action)}
                          className="px-3 py-1 text-sm bg-white border rounded-full hover:bg-gray-50 flex items-center gap-1"
                        >
                          {action.action?.replace(/_/g, ' ') || 'Take Action'}
                          <ChevronRight size={12} />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RecommendationPanel;
