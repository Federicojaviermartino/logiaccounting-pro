# Phase 31: AI/ML Features - Part 8: Frontend Components

## Overview
This part covers the reusable frontend components and API service for AI features.

---

## File 1: Forecast Chart Component
**Path:** `frontend/src/features/ai/components/ForecastChart.jsx`

```jsx
/**
 * Forecast Chart Component
 * Visualizes cash flow predictions with confidence intervals
 */

import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
);

const ForecastChart = ({ data, scenario }) => {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null;
    
    const labels = data.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    return {
      labels,
      datasets: [
        // Confidence interval (area)
        {
          label: 'Confidence Range',
          data: data.map(d => d.confidence_high),
          fill: '+1',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderColor: 'transparent',
          pointRadius: 0,
        },
        {
          label: 'Lower Bound',
          data: data.map(d => d.confidence_low),
          fill: false,
          backgroundColor: 'transparent',
          borderColor: 'transparent',
          pointRadius: 0,
        },
        // Main prediction line
        {
          label: 'Predicted Balance',
          data: data.map(d => d.predicted_balance),
          fill: false,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgb(59, 130, 246)',
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
        // Inflows
        {
          label: 'Inflows',
          data: data.map(d => d.predicted_inflows),
          fill: false,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgb(34, 197, 94)',
          borderWidth: 1,
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 0,
          yAxisID: 'y1',
        },
        // Outflows
        {
          label: 'Outflows',
          data: data.map(d => d.predicted_outflows),
          fill: false,
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgb(239, 68, 68)',
          borderWidth: 1,
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 0,
          yAxisID: 'y1',
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          filter: (item) => item.text !== 'Lower Bound' && item.text !== 'Confidence Range',
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.parsed.y;
            return `${context.dataset.label}: $${value.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Balance ($)',
        },
        ticks: {
          callback: (value) => `$${(value / 1000).toFixed(0)}K`,
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Daily Flow ($)',
        },
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          callback: (value) => `$${(value / 1000).toFixed(0)}K`,
        },
      },
    },
  };

  if (!chartData) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-500">
        No forecast data available
      </div>
    );
  }

  return (
    <div className="h-80">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default ForecastChart;
```

---

## File 2: Anomaly Card Component
**Path:** `frontend/src/features/ai/components/AnomalyCard.jsx`

```jsx
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
                  💡 {alert.recommended_action}
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
```

---

## File 3: Upload Zone Component
**Path:** `frontend/src/features/ai/components/UploadZone.jsx`

```jsx
/**
 * Upload Zone Component
 * Drag and drop file upload for documents
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

const UploadZone = ({
  onFilesSelected,
  accept = {
    'application/pdf': ['.pdf'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
  },
  maxSize = 10 * 1024 * 1024,
  maxFiles = 10,
  multiple = true,
}) => {
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle accepted files
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: 'pending',
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    onFilesSelected?.(acceptedFiles);
    
    // Handle rejected files
    const newErrors = rejectedFiles.map(({ file, errors }) => ({
      file: file.name,
      errors: errors.map(e => e.message),
    }));
    
    if (newErrors.length > 0) {
      setErrors(prev => [...prev, ...newErrors]);
    }
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles,
    multiple,
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearErrors = () => {
    setErrors([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragActive && !isDragReject ? 'border-blue-500 bg-blue-50' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
          ${!isDragActive ? 'border-gray-300 hover:border-gray-400 hover:bg-gray-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <Upload
          className={`mx-auto mb-4 ${
            isDragActive && !isDragReject ? 'text-blue-500' :
            isDragReject ? 'text-red-500' : 'text-gray-400'
          }`}
          size={48}
        />
        
        {isDragReject ? (
          <div>
            <div className="text-lg font-medium text-red-600">Invalid file type</div>
            <div className="text-sm text-red-500">Please upload PDF or image files</div>
          </div>
        ) : isDragActive ? (
          <div className="text-lg font-medium text-blue-600">Drop files here</div>
        ) : (
          <div>
            <div className="text-lg font-medium text-gray-700">
              Drag & drop files here
            </div>
            <div className="text-sm text-gray-500 mt-1">
              or click to browse
            </div>
            <div className="text-xs text-gray-400 mt-2">
              PDF, JPG, PNG up to {formatFileSize(maxSize)}
            </div>
          </div>
        )}
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-red-800 font-medium flex items-center gap-2">
              <AlertCircle size={18} />
              Upload Errors
            </span>
            <button
              onClick={clearErrors}
              className="text-red-600 hover:text-red-800"
            >
              <X size={18} />
            </button>
          </div>
          <ul className="text-sm text-red-700 space-y-1">
            {errors.map((error, i) => (
              <li key={i}>
                {error.file}: {error.errors.join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(({ file, id, status }) => (
            <div
              key={id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <File className="text-gray-400" size={20} />
                <div>
                  <div className="font-medium text-sm">{file.name}</div>
                  <div className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {status === 'pending' && (
                  <span className="text-xs text-gray-500">Pending</span>
                )}
                {status === 'processing' && (
                  <span className="text-xs text-blue-600">Processing...</span>
                )}
                {status === 'complete' && (
                  <CheckCircle className="text-green-500" size={18} />
                )}
                {status === 'error' && (
                  <AlertCircle className="text-red-500" size={18} />
                )}
                
                <button
                  onClick={() => removeFile(id)}
                  className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadZone;
```

---

## File 4: Recommendation Panel Component
**Path:** `frontend/src/features/ai/components/RecommendationPanel.jsx`

```jsx
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
```

---

## File 5: AI API Service
**Path:** `frontend/src/features/ai/services/aiAPI.js`

```javascript
/**
 * AI API Service
 * API calls for AI/ML features
 */

import api from '../../../services/api';

export const aiAPI = {
  // ==================== Cash Flow ====================
  
  async trainCashFlowModel(data) {
    const response = await api.post('/ai/cashflow/train', data);
    return response.data;
  },

  async getCashFlowForecast(params) {
    const response = await api.post('/ai/cashflow/forecast', params);
    return response.data;
  },

  async getCashFlowStatus() {
    const response = await api.get('/ai/cashflow/status');
    return response.data;
  },

  // ==================== OCR ====================
  
  async processDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/ai/ocr/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async batchProcessDocuments(files) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await api.post('/ai/ocr/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getProcessedDocuments(limit = 50) {
    const response = await api.get(`/ai/ocr/documents?limit=${limit}`);
    return response.data;
  },

  async getDocument(documentId) {
    const response = await api.get(`/ai/ocr/documents/${documentId}`);
    return response.data;
  },

  async updateDocument(documentId, updates) {
    const response = await api.put(`/ai/ocr/documents/${documentId}`, updates);
    return response.data;
  },

  async approveDocument(documentId) {
    const response = await api.post(`/ai/ocr/documents/${documentId}/approve`);
    return response.data;
  },

  // ==================== Assistant ====================
  
  async chatWithAssistant(params) {
    const response = await api.post('/ai/assistant/chat', params);
    return response.data;
  },

  async getQuickInsights() {
    const response = await api.get('/ai/assistant/insights');
    return response.data;
  },

  async analyzeEntity(params) {
    const response = await api.post('/ai/assistant/analyze', params);
    return response.data;
  },

  async getConversations(limit = 10) {
    const response = await api.get(`/ai/assistant/conversations?limit=${limit}`);
    return response.data;
  },

  async getConversation(conversationId) {
    const response = await api.get(`/ai/assistant/conversations/${conversationId}`);
    return response.data;
  },

  async deleteConversation(conversationId) {
    const response = await api.delete(`/ai/assistant/conversations/${conversationId}`);
    return response.data;
  },

  async getAssistantSuggestions(query) {
    const response = await api.get(`/ai/assistant/suggestions?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // ==================== Anomaly Detection ====================
  
  async trainAnomalyModels(data) {
    const response = await api.post('/ai/anomaly/train', data);
    return response.data;
  },

  async analyzeTransaction(transaction) {
    const response = await api.post('/ai/anomaly/analyze', { transaction });
    return response.data;
  },

  async batchAnalyzeTransactions(transactions) {
    const response = await api.post('/ai/anomaly/batch-analyze', transactions);
    return response.data;
  },

  async getAnomalyAlerts(params = {}) {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.severity) queryParams.append('severity', params.severity);
    if (params.limit) queryParams.append('limit', params.limit);
    
    const response = await api.get(`/ai/anomaly/alerts?${queryParams}`);
    return response.data;
  },

  async getAnomalySummary() {
    const response = await api.get('/ai/anomaly/alerts/summary');
    return response.data;
  },

  async acknowledgeAlert(alertId) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  async resolveAlert(alertId, params = {}) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/resolve`, params);
    return response.data;
  },

  async dismissAlert(alertId, params = {}) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/dismiss`, params);
    return response.data;
  },
};

export default aiAPI;
```

---

## File 6: AI Feature Index
**Path:** `frontend/src/features/ai/index.js`

```javascript
/**
 * AI Feature Module
 */

// Pages
export { default as CashFlowForecast } from './pages/CashFlowForecast';
export { default as DocumentScanner } from './pages/DocumentScanner';
export { default as AIAssistant } from './pages/AIAssistant';
export { default as AnomalyDashboard } from './pages/AnomalyDashboard';

// Components
export { default as ForecastChart } from './components/ForecastChart';
export { default as AnomalyCard } from './components/AnomalyCard';
export { default as UploadZone } from './components/UploadZone';
export { default as RecommendationPanel } from './components/RecommendationPanel';

// Services
export { aiAPI } from './services/aiAPI';

// Routes
export { default as AIRoutes } from './routes';
```

---

## Summary Part 8

| File | Description | Lines |
|------|-------------|-------|
| `components/ForecastChart.jsx` | Cash flow chart | ~150 |
| `components/AnomalyCard.jsx` | Anomaly alert card | ~170 |
| `components/UploadZone.jsx` | File upload component | ~180 |
| `components/RecommendationPanel.jsx` | Recommendations display | ~150 |
| `services/aiAPI.js` | AI API service | ~150 |
| `index.js` | Feature module exports | ~25 |
| **Total** | | **~825 lines** |

---

## Phase 31 Complete Summary

| Part | Content | Files | Lines |
|------|---------|-------|-------|
| Part 1 | AI Core Infrastructure | 5 | ~1,120 |
| Part 2 | Cash Flow Predictor | 5 | ~1,365 |
| Part 3 | Smart Invoice OCR | 5 | ~1,175 |
| Part 4 | AI Assistant / Chatbot | 5 | ~1,185 |
| Part 5 | Anomaly Detection | 5 | ~1,220 |
| Part 6 | API Routes & Service | 4 | ~890 |
| Part 7 | Frontend AI Dashboard | 5 | ~1,185 |
| Part 8 | Frontend Components | 6 | ~825 |
| **Total** | | **40 files** | **~8,965 lines** |
