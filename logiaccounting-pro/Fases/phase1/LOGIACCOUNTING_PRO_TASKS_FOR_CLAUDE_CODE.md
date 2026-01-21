# LogiAccounting Pro - Task List for Claude Code VSC

## INSTRUCTIONS FOR CLAUDE CODE

Copy this entire file into your Claude Code session in VSC. Execute tasks in order.

---

## TASK 1: FIX GIT HISTORY (CRITICAL)

**Context:** The git repository shows "claude" as a contributor. This must be fixed before any other work.

**Execute:**
```bash
# First, check current git authors
git log --format='%an <%ae>' | sort -u

# If "claude" appears, run this script to rewrite history:
git filter-branch -f --env-filter '
CORRECT_NAME="Federico Javier Martino"
CORRECT_EMAIL="your-actual-email@example.com"

export GIT_COMMITTER_NAME="$CORRECT_NAME"
export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
export GIT_AUTHOR_NAME="$CORRECT_NAME"
export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
' --tag-name-filter cat -- --branches --tags

# Force push (CAREFUL - this rewrites history)
git push --force origin main

# Clean up
rm -rf .git/refs/original/
git gc --prune=now
```

---

## TASK 2: ADD AI API SERVICES TO FRONTEND

**File:** `frontend/src/services/api.js`

**Action:** Add these exports at the end of the file (before the final export if any):

```javascript
// ============================================
// AI-POWERED FEATURES API
// ============================================

// OCR API - Smart Invoice Processing
export const ocrAPI = {
  processInvoice: (file, autoCreate = false) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/ocr/process?auto_create=${autoCreate}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getCategorySuggestions: (vendorName) => 
    api.get('/api/v1/ocr/categories/suggestions', { params: { vendor_name: vendorName } }),
  getStatus: () => api.get('/api/v1/ocr/status')
};

// Cash Flow Predictor API
export const cashflowAPI = {
  predict: (days = 90, includePending = true) => 
    api.get('/api/v1/cashflow/predict', { 
      params: { days, include_pending: includePending } 
    }),
  getSummary: () => api.get('/api/v1/cashflow/summary')
};

// Anomaly Detection API
export const anomalyAPI = {
  runScan: () => api.get('/api/v1/anomaly/scan'),
  getSummary: () => api.get('/api/v1/anomaly/summary'),
  checkTransaction: (data) => api.post('/api/v1/anomaly/check', data),
  checkDuplicates: (invoiceNumber) => 
    api.get('/api/v1/anomaly/duplicates', { params: { invoice_number: invoiceNumber } }),
  analyzeVendor: (vendorId) => api.get(`/api/v1/anomaly/vendor/${vendorId}/analysis`),
  getStatus: () => api.get('/api/v1/anomaly/status')
};

// Payment Scheduler API
export const schedulerAPI = {
  optimize: (availableCash, optimizeFor = 'balanced') => 
    api.get('/api/v1/scheduler/optimize', { 
      params: { available_cash: availableCash, optimize_for: optimizeFor } 
    }),
  getDailySchedule: (startDate, endDate) => 
    api.get('/api/v1/scheduler/daily', { 
      params: { start_date: startDate, end_date: endDate } 
    }),
  getRecommendations: () => api.get('/api/v1/scheduler/recommendations')
};

// Profitability Assistant API
export const assistantAPI = {
  query: (userQuery) => api.post('/api/v1/assistant/query', { query: userQuery }),
  getSuggestions: () => api.get('/api/v1/assistant/suggestions'),
  getStatus: () => api.get('/api/v1/assistant/status')
};
```

---

## TASK 3: CREATE AI DASHBOARD PAGE

**File:** `frontend/src/pages/AIDashboard.jsx`

**Action:** Create new file with this content:

```jsx
import { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { cashflowAPI, anomalyAPI, schedulerAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

export default function AIDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('cashflow');
  const [cashflow, setCashflow] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [predictionDays, setPredictionDays] = useState(90);

  useEffect(() => {
    loadData();
  }, [predictionDays]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cfRes, anomRes, schedRes] = await Promise.all([
        cashflowAPI.predict(predictionDays),
        anomalyAPI.getSummary(),
        schedulerAPI.optimize(50000, 'balanced')
      ]);
      setCashflow(cfRes.data);
      setAnomalies(anomRes.data);
      setSchedule(schedRes.data);
    } catch (error) {
      console.error('Failed to load AI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAnomalyScan = async () => {
    try {
      const res = await anomalyAPI.runScan();
      setAnomalies(res.data);
    } catch (error) {
      alert('Scan failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  // Cash Flow Chart Data
  const cashflowChartData = {
    labels: cashflow?.predictions?.slice(0, 30).map(p => 
      new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ) || [],
    datasets: [
      {
        label: 'Predicted Income',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_income) || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Predicted Expenses',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_expenses) || [],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Net Cash Flow',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_net) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  // Anomaly Severity Chart
  const anomalyChartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        anomalies?.critical_count || 0,
        anomalies?.high_count || 0,
        anomalies?.medium_count || 0,
        anomalies?.low_count || 0
      ],
      backgroundColor: ['#dc2626', '#f97316', '#eab308', '#22c55e'],
      borderWidth: 0
    }]
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading AI Analytics...</p>
      </div>
    );
  }

  return (
    <>
      {/* Stats Overview */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <span className="stat-icon">📈</span>
          <div className="stat-content">
            <div className="stat-label">Predicted Net ({predictionDays}d)</div>
            <div className={`stat-value ${cashflow?.summary?.total_net >= 0 ? 'success' : 'danger'}`}>
              {formatCurrency(cashflow?.summary?.total_net)}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⚠️</span>
          <div className="stat-content">
            <div className="stat-label">Anomalies Detected</div>
            <div className={`stat-value ${anomalies?.total_anomalies > 0 ? 'warning' : 'success'}`}>
              {anomalies?.total_anomalies || 0}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">💰</span>
          <div className="stat-content">
            <div className="stat-label">Potential Savings</div>
            <div className="stat-value success">
              {formatCurrency(schedule?.total_potential_savings)}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📊</span>
          <div className="stat-content">
            <div className="stat-label">Risk Score</div>
            <div className={`stat-value ${anomalies?.risk_score > 0.5 ? 'danger' : 'success'}`}>
              {((anomalies?.risk_score || 0) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2 mb-4">
          <button 
            className={`btn ${activeTab === 'cashflow' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('cashflow')}
          >
            Cash Flow Predictor
          </button>
          <button 
            className={`btn ${activeTab === 'anomaly' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('anomaly')}
          >
            Anomaly Detection
          </button>
          <button 
            className={`btn ${activeTab === 'scheduler' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('scheduler')}
          >
            Payment Optimizer
          </button>
        </div>

        {/* Cash Flow Tab */}
        {activeTab === 'cashflow' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Cash Flow Prediction</h3>
              <div className="flex gap-2">
                {[30, 60, 90].map(days => (
                  <button
                    key={days}
                    className={`btn btn-sm ${predictionDays === days ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setPredictionDays(days)}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>
            <div className="chart-container" style={{ height: '400px' }}>
              <Line 
                data={cashflowChartData} 
                options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'top' }
                  }
                }} 
              />
            </div>
            {cashflow?.risk_alerts?.length > 0 && (
              <div className="mt-4">
                <h4 className="font-bold mb-2">Risk Alerts</h4>
                {cashflow.risk_alerts.map((alert, i) => (
                  <div key={i} className="info-banner" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' }}>
                    ⚠️ {alert}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Anomaly Tab */}
        {activeTab === 'anomaly' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Anomaly Detection</h3>
              <button className="btn btn-primary" onClick={runAnomalyScan}>
                🔍 Run Full Scan
              </button>
            </div>
            <div className="grid-2">
              <div>
                <div className="chart-container" style={{ height: '300px' }}>
                  <Doughnut 
                    data={anomalyChartData}
                    options={{ responsive: true, maintainAspectRatio: false }}
                  />
                </div>
              </div>
              <div>
                <h4 className="font-bold mb-2">Summary</h4>
                <p className="text-muted mb-4">{anomalies?.summary}</p>
                <div className="info-banner">
                  ML Detection: {anomalies?.ml_detection_enabled ? '✅ Enabled' : '❌ Disabled'}
                </div>
              </div>
            </div>
            {anomalies?.anomalies?.length > 0 && (
              <div className="table-container mt-4">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Severity</th>
                      <th>Description</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.anomalies.slice(0, 10).map((a, i) => (
                      <tr key={i}>
                        <td>{a.type}</td>
                        <td>
                          <span className={`badge badge-${
                            a.severity === 'critical' ? 'danger' : 
                            a.severity === 'high' ? 'warning' : 'gray'
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td>{a.title}</td>
                        <td>{(a.confidence * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {/* Scheduler Tab */}
        {activeTab === 'scheduler' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Payment Optimization</h3>
            </div>
            <div className="stats-grid mb-4">
              <div className="stat-card">
                <span className="stat-icon">💵</span>
                <div className="stat-content">
                  <div className="stat-label">Cash Required (7d)</div>
                  <div className="stat-value">{formatCurrency(schedule?.cash_required_7_days)}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">📅</span>
                <div className="stat-content">
                  <div className="stat-label">Cash Required (30d)</div>
                  <div className="stat-value">{formatCurrency(schedule?.cash_required_30_days)}</div>
                </div>
              </div>
            </div>
            {schedule?.recommendations?.length > 0 && (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Reference</th>
                      <th>Amount</th>
                      <th>Due Date</th>
                      <th>Recommended</th>
                      <th>Action</th>
                      <th>Savings</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedule.recommendations.slice(0, 10).map((r, i) => (
                      <tr key={i}>
                        <td className="font-mono">{r.reference}</td>
                        <td className="font-bold">{formatCurrency(r.amount)}</td>
                        <td>{new Date(r.original_due_date).toLocaleDateString()}</td>
                        <td>{new Date(r.recommended_date).toLocaleDateString()}</td>
                        <td>
                          <span className={`badge badge-${
                            r.action === 'pay_now' ? 'danger' :
                            r.action === 'pay_early' ? 'success' : 'gray'
                          }`}>
                            {r.action.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="text-success">{formatCurrency(r.potential_savings)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
```

---

## TASK 4: CREATE INVOICE OCR PAGE

**File:** `frontend/src/pages/InvoiceOCR.jsx`

**Action:** Create new file with this content:

```jsx
import { useState, useRef } from 'react';
import { ocrAPI, transactionsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function InvoiceOCR() {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [ocrStatus, setOcrStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);
      
      // Create preview for images
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result);
        reader.readAsDataURL(selectedFile);
      } else {
        setPreview(null);
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setResult(null);
      setError(null);
    }
  };

  const processInvoice = async (autoCreate = false) => {
    if (!file) return;
    
    setProcessing(true);
    setError(null);
    
    try {
      const res = await ocrAPI.processInvoice(file, autoCreate);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const createTransaction = async () => {
    if (!result?.invoice) return;
    
    try {
      await transactionsAPI.createTransaction({
        type: 'expense',
        amount: result.invoice.total_amount,
        description: `Invoice from ${result.invoice.vendor_name}`,
        vendor_name: result.invoice.vendor_name,
        invoice_number: result.invoice.invoice_number,
        date: result.invoice.date,
        category_id: result.suggested_category?.id
      });
      alert('Transaction created successfully!');
    } catch (err) {
      alert('Failed to create transaction: ' + (err.response?.data?.detail || err.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  return (
    <>
      <div className="info-banner mb-6">
        📄 Upload invoices (PDF, JPG, PNG) to automatically extract data and create transactions.
        Supports Tesseract OCR {ocrStatus?.openai_vision_available && '+ OpenAI Vision'}.
      </div>

      <div className="grid-2">
        {/* Upload Section */}
        <div className="section">
          <h3 className="section-title">Upload Invoice</h3>
          
          <div 
            className="upload-zone"
            style={{
              border: '2px dashed var(--gray-300)',
              borderRadius: '12px',
              padding: '40px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              background: file ? 'var(--gray-50)' : 'white'
            }}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {preview ? (
              <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px' }} />
            ) : (
              <>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📄</div>
                <p className="font-bold">Drop invoice here or click to browse</p>
                <p className="text-muted">Supports PDF, JPG, PNG up to 10MB</p>
              </>
            )}
            
            {file && (
              <div className="mt-4">
                <span className="badge badge-primary">{file.name}</span>
                <span className="text-muted ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-4">
            <button 
              className="btn btn-primary"
              onClick={() => processInvoice(false)}
              disabled={!file || processing}
            >
              {processing ? 'Processing...' : '🔍 Extract Data'}
            </button>
            <button 
              className="btn btn-success"
              onClick={() => processInvoice(true)}
              disabled={!file || processing}
            >
              {processing ? 'Processing...' : '⚡ Extract & Create'}
            </button>
          </div>

          {error && (
            <div className="info-banner mt-4" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' }}>
              ❌ {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="section">
          <h3 className="section-title">Extracted Data</h3>
          
          {result?.invoice ? (
            <>
              <div className="grid-2 mb-4">
                <div className="form-group">
                  <label className="form-label">Vendor</label>
                  <input className="form-input" value={result.invoice.vendor_name || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice #</label>
                  <input className="form-input" value={result.invoice.invoice_number || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input className="form-input" value={result.invoice.date || ''} readOnly />
                </div>
                <div className="form-group">
                  <label className="form-label">Total Amount</label>
                  <input className="form-input font-bold" value={formatCurrency(result.invoice.total_amount)} readOnly />
                </div>
              </div>

              {result.invoice.line_items?.length > 0 && (
                <>
                  <h4 className="font-bold mb-2">Line Items</h4>
                  <div className="table-container mb-4">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Description</th>
                          <th>Qty</th>
                          <th>Unit Price</th>
                          <th>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.invoice.line_items.map((item, i) => (
                          <tr key={i}>
                            <td>{item.description}</td>
                            <td>{item.quantity}</td>
                            <td>{formatCurrency(item.unit_price)}</td>
                            <td className="font-bold">{formatCurrency(item.total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {result.suggested_category && (
                <div className="info-banner">
                  💡 Suggested Category: <strong>{result.suggested_category.name}</strong>
                </div>
              )}

              <button className="btn btn-success mt-4" onClick={createTransaction}>
                ✅ Create Transaction
              </button>
            </>
          ) : (
            <div className="text-center text-muted" style={{ padding: '60px 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📋</div>
              <p>Upload and process an invoice to see extracted data</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
```

---

## TASK 5: CREATE ASSISTANT PAGE

**File:** `frontend/src/pages/Assistant.jsx`

**Action:** Create new file with this content:

```jsx
import { useState, useEffect, useRef } from 'react';
import { assistantAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Assistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSuggestions();
    // Welcome message
    setMessages([{
      role: 'assistant',
      content: 'Hello! I\'m your Profitability Assistant. Ask me anything about your projects, finances, or business metrics. For example:\n\n• "What projects are over budget?"\n• "Show me the most profitable projects"\n• "Which suppliers have the highest expenses?"'
    }]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSuggestions = async () => {
    try {
      const res = await assistantAPI.getSuggestions();
      setSuggestions(res.data.suggestions || []);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const sendQuery = async (query = input) => {
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await assistantAPI.query(query);
      const assistantMessage = {
        role: 'assistant',
        content: res.data.answer,
        data: res.data.data,
        charts: res.data.charts,
        suggestions: res.data.suggestions
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  return (
    <div style={{ display: 'flex', gap: '24px', height: 'calc(100vh - 160px)' }}>
      {/* Chat Area */}
      <div className="section" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <h3 className="section-title">Chat</h3>
        
        {/* Messages */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px',
          background: 'var(--gray-50)',
          borderRadius: '8px',
          marginBottom: '16px'
        }}>
          {messages.map((msg, i) => (
            <div 
              key={i} 
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '16px'
              }}
            >
              <div style={{
                maxWidth: '80%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: msg.role === 'user' ? 'var(--primary)' : 'white',
                color: msg.role === 'user' ? 'white' : 'var(--gray-800)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                
                {/* Data Table */}
                {msg.data && Object.keys(msg.data).length > 0 && (
                  <div className="table-container mt-2" style={{ fontSize: '0.85rem' }}>
                    <table className="data-table">
                      <tbody>
                        {Object.entries(msg.data).map(([key, value]) => (
                          <tr key={key}>
                            <td className="font-bold">{key.replace(/_/g, ' ')}</td>
                            <td>{typeof value === 'number' ? formatCurrency(value) : String(value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Follow-up Suggestions */}
                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {msg.suggestions.map((s, j) => (
                      <button
                        key={j}
                        className="btn btn-sm btn-secondary"
                        onClick={() => sendQuery(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
              <div style={{
                padding: '12px 16px',
                borderRadius: '12px',
                background: 'white',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div className="loading-spinner" style={{ width: '20px', height: '20px' }}></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Ask about projects, finances, or metrics..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button 
            className="btn btn-primary"
            onClick={() => sendQuery()}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>

      {/* Suggestions Sidebar */}
      <div className="section" style={{ width: '280px' }}>
        <h3 className="section-title">Quick Questions</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {suggestions.map((s, i) => (
            <button
              key={i}
              className="btn btn-secondary"
              style={{ textAlign: 'left', whiteSpace: 'normal', height: 'auto', padding: '12px' }}
              onClick={() => sendQuery(s)}
              disabled={loading}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## TASK 6: UPDATE LAYOUT NAVIGATION

**File:** `frontend/src/components/Layout.jsx`

**Action:** Replace the `navItems` array with this:

```javascript
const navItems = [
  { path: '/dashboard', icon: '📊', label: 'Dashboard', roles: ['admin', 'client', 'supplier'] },
  
  { section: 'Logistics', roles: ['admin', 'supplier'] },
  { path: '/inventory', icon: '📦', label: 'Inventory', roles: ['admin', 'supplier'] },
  { path: '/movements', icon: '🔄', label: 'Movements', roles: ['admin', 'supplier'] },
  
  { section: 'Projects', roles: ['admin', 'client'] },
  { path: '/projects', icon: '📁', label: 'Projects', roles: ['admin', 'client'] },
  
  { section: 'Finance', roles: ['admin', 'client', 'supplier'] },
  { path: '/transactions', icon: '💰', label: 'Transactions', roles: ['admin', 'client', 'supplier'] },
  { path: '/payments', icon: '💳', label: 'Payments', roles: ['admin', 'client', 'supplier'] },
  
  { section: 'AI Tools', roles: ['admin'] },
  { path: '/ai-dashboard', icon: '🤖', label: 'AI Dashboard', roles: ['admin'] },
  { path: '/invoice-ocr', icon: '📄', label: 'Invoice OCR', roles: ['admin', 'supplier'] },
  { path: '/assistant', icon: '💬', label: 'Assistant', roles: ['admin'] },
  
  { section: 'Administration', roles: ['admin'] },
  { path: '/users', icon: '👥', label: 'Users', roles: ['admin'] },
  { path: '/reports', icon: '📈', label: 'Reports', roles: ['admin'] }
];

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/inventory': 'Inventory Management',
  '/projects': 'Projects',
  '/movements': 'Stock Movements',
  '/transactions': 'Transactions',
  '/payments': 'Payments',
  '/users': 'User Management',
  '/reports': 'Reports & Analytics',
  '/ai-dashboard': 'AI Analytics Dashboard',
  '/invoice-ocr': 'Smart Invoice Processing',
  '/assistant': 'Profitability Assistant'
};
```

---

## TASK 7: UPDATE APP ROUTES

**File:** `frontend/src/App.jsx`

**Action:** Add these imports at the top:

```javascript
import AIDashboard from './pages/AIDashboard';
import InvoiceOCR from './pages/InvoiceOCR';
import Assistant from './pages/Assistant';
```

**Action:** Add these routes inside `<Routes>` (before the catch-all route):

```jsx
<Route path="/ai-dashboard" element={
  <PrivateRoute roles={['admin']}>
    <Layout><AIDashboard /></Layout>
  </PrivateRoute>
} />

<Route path="/invoice-ocr" element={
  <PrivateRoute roles={['admin', 'supplier']}>
    <Layout><InvoiceOCR /></Layout>
  </PrivateRoute>
} />

<Route path="/assistant" element={
  <PrivateRoute roles={['admin']}>
    <Layout><Assistant /></Layout>
  </PrivateRoute>
} />
```

---

## TASK 8: TEST THE IMPLEMENTATION

**Execute these commands:**

```bash
# Start backend
cd backend
uvicorn app.main:app --reload --port 5000

# In another terminal, start frontend
cd frontend
npm run dev

# Test login
# Open http://localhost:5173
# Login with: admin@logiaccounting.demo / Demo2024!Admin

# Navigate to AI Dashboard, Invoice OCR, and Assistant pages
```

---

## TASK 9: FINAL BUILD AND DEPLOY

```bash
# Build frontend
cd frontend
npm run build

# Test production build locally
npm run preview

# Commit changes (with YOUR name)
git add .
git commit -m "Add AI features frontend integration"

# Push to GitHub
git push origin main

# Deploy to Render
# - Go to render.com
# - Connect repository
# - Use render.yaml blueprint
# - Deploy
```

---

## COMPLETION CHECKLIST

- [ ] Git history cleaned (no AI traces)
- [ ] AI API services added to api.js
- [ ] AIDashboard page created
- [ ] InvoiceOCR page created
- [ ] Assistant page created
- [ ] Navigation updated with AI Tools section
- [ ] Routes added to App.jsx
- [ ] All pages tested locally
- [ ] Production build successful
- [ ] Deployed to Render

---

**END OF TASK LIST**
