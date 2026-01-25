# Phase 31: AI/ML Features - Part 7: Frontend AI Dashboard

## Overview
This part covers the frontend pages for AI features including cash flow forecast, document scanner, AI assistant, and anomaly dashboard.

---

## File 1: Cash Flow Forecast Page
**Path:** `frontend/src/features/ai/pages/CashFlowForecast.jsx`

```jsx
/**
 * Cash Flow Forecast Page
 * AI-powered cash flow predictions and analysis
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Calendar,
  RefreshCw,
  Download,
  ChevronDown,
} from 'lucide-react';
import ForecastChart from '../components/ForecastChart';
import { aiAPI } from '../services/aiAPI';

const CashFlowForecast = () => {
  const { t } = useTranslation();
  
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [horizonDays, setHorizonDays] = useState(30);
  const [scenario, setScenario] = useState('expected');
  const [modelStatus, setModelStatus] = useState(null);

  useEffect(() => {
    loadForecast();
    loadModelStatus();
  }, [horizonDays, scenario]);

  const loadForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await aiAPI.getCashFlowForecast({
        horizon_days: horizonDays,
        scenario,
        include_pending: true,
        include_recurring: true,
      });
      setForecast(data);
    } catch (err) {
      setError('Failed to load forecast');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadModelStatus = async () => {
    try {
      const status = await aiAPI.getCashFlowStatus();
      setModelStatus(status);
    } catch (err) {
      console.error('Failed to load model status:', err);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="text-green-500" size={20} />;
    if (trend === 'decreasing') return <TrendingDown className="text-red-500" size={20} />;
    return <span className="text-gray-500">→</span>;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return colors[severity] || colors.info;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cash Flow Forecast</h1>
          <p className="text-gray-600">AI-powered predictions for your cash position</p>
        </div>
        <div className="flex gap-3">
          <select
            value={horizonDays}
            onChange={(e) => setHorizonDays(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={7}>7 Days</option>
            <option value={14}>14 Days</option>
            <option value={30}>30 Days</option>
            <option value={60}>60 Days</option>
            <option value={90}>90 Days</option>
          </select>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="expected">Expected</option>
            <option value="optimistic">Optimistic</option>
            <option value="pessimistic">Pessimistic</option>
          </select>
          <button
            onClick={loadForecast}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Model Status */}
      {modelStatus && !modelStatus.trained && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <span className="text-yellow-800">
              Cash flow model is not trained yet. Predictions may be less accurate.
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="animate-spin text-gray-400" size={32} />
        </div>
      ) : forecast ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Current Balance</span>
                <DollarSign className="text-gray-400" size={18} />
              </div>
              <div className="text-2xl font-bold">
                {formatCurrency(forecast.summary?.starting_balance || 0)}
              </div>
            </div>
            
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Forecast ({horizonDays}d)</span>
                {getTrendIcon(forecast.summary?.trend)}
              </div>
              <div className="text-2xl font-bold">
                {formatCurrency(forecast.summary?.ending_balance || 0)}
              </div>
              <div className={`text-sm ${forecast.summary?.net_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {forecast.summary?.net_change >= 0 ? '+' : ''}
                {formatCurrency(forecast.summary?.net_change || 0)}
              </div>
            </div>
            
            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-600 mb-2">Lowest Point</div>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(forecast.summary?.lowest_point?.balance || 0)}
              </div>
              <div className="text-sm text-gray-500">
                {forecast.summary?.lowest_point?.date}
              </div>
            </div>
            
            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-600 mb-2">Total Inflows</div>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(forecast.summary?.total_inflows || 0)}
              </div>
              <div className="text-sm text-gray-500">
                Outflows: {formatCurrency(forecast.summary?.total_outflows || 0)}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-lg border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Forecast Timeline</h2>
            <ForecastChart
              data={forecast.forecast}
              scenario={scenario}
            />
          </div>

          {/* Alerts */}
          {forecast.alerts && forecast.alerts.length > 0 && (
            <div className="bg-white rounded-lg border p-6 mb-6">
              <h2 className="text-lg font-semibold mb-4">Alerts & Warnings</h2>
              <div className="space-y-3">
                {forecast.alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle size={16} />
                      <span className="font-medium">{alert.type.replace(/_/g, ' ').toUpperCase()}</span>
                      <span className="text-sm opacity-75">• {alert.date}</span>
                    </div>
                    <div className="text-sm">{alert.message}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Forecast Table */}
          <div className="bg-white rounded-lg border overflow-hidden">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Daily Forecast</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Inflows</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Outflows</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {forecast.forecast?.slice(0, 14).map((day, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{day.date}</td>
                      <td className="px-4 py-3 text-sm text-right text-green-600">
                        +{formatCurrency(day.predicted_inflows)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-red-600">
                        -{formatCurrency(day.predicted_outflows)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium">
                        {formatCurrency(day.predicted_balance)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          day.confidence_level === 'high' ? 'bg-green-100 text-green-800' :
                          day.confidence_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {day.confidence_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default CashFlowForecast;
```

---

## File 2: Document Scanner Page
**Path:** `frontend/src/features/ai/pages/DocumentScanner.jsx`

```jsx
/**
 * Document Scanner Page
 * AI-powered invoice and receipt OCR
 */

import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Edit2,
  Eye,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { aiAPI } from '../services/aiAPI';

const DocumentScanner = () => {
  const { t } = useTranslation();
  
  const [documents, setDocuments] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});

  const onDrop = useCallback(async (acceptedFiles) => {
    setProcessing(true);
    
    for (const file of acceptedFiles) {
      try {
        const result = await aiAPI.processDocument(file);
        setDocuments(prev => [{
          ...result,
          filename: file.name,
          uploadedAt: new Date().toISOString(),
        }, ...prev]);
      } catch (error) {
        console.error('Processing failed:', error);
        setDocuments(prev => [{
          document_id: `error_${Date.now()}`,
          filename: file.name,
          status: 'failed',
          error: error.message,
          uploadedAt: new Date().toISOString(),
        }, ...prev]);
      }
    }
    
    setProcessing(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleApprove = async (docId) => {
    try {
      await aiAPI.approveDocument(docId);
      setDocuments(prev => prev.map(doc =>
        doc.document_id === docId ? { ...doc, status: 'completed' } : doc
      ));
    } catch (error) {
      console.error('Approve failed:', error);
    }
  };

  const handleEdit = (doc) => {
    setSelectedDoc(doc);
    setEditData(doc.extracted_data || {});
    setEditMode(true);
  };

  const handleSaveEdit = async () => {
    try {
      await aiAPI.updateDocument(selectedDoc.document_id, { updates: editData });
      setDocuments(prev => prev.map(doc =>
        doc.document_id === selectedDoc.document_id
          ? { ...doc, extracted_data: editData }
          : doc
      ));
      setEditMode(false);
      setSelectedDoc(null);
    } catch (error) {
      console.error('Update failed:', error);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={18} />;
      case 'failed': return <XCircle className="text-red-500" size={18} />;
      case 'needs_review': return <AlertTriangle className="text-yellow-500" size={18} />;
      default: return <Clock className="text-gray-500" size={18} />;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Document Scanner</h1>
        <p className="text-gray-600">Upload invoices and receipts for AI-powered data extraction</p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 mb-6 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`mx-auto mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} size={48} />
        {processing ? (
          <div>
            <div className="text-lg font-medium text-gray-700">Processing...</div>
            <div className="text-sm text-gray-500">Extracting data from documents</div>
          </div>
        ) : isDragActive ? (
          <div className="text-lg font-medium text-blue-600">Drop files here</div>
        ) : (
          <div>
            <div className="text-lg font-medium text-gray-700">Drag & drop files here</div>
            <div className="text-sm text-gray-500">or click to browse (PDF, JPG, PNG up to 10MB)</div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h2 className="font-semibold">Processed Documents</h2>
        </div>
        
        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents processed yet. Upload your first document above.
          </div>
        ) : (
          <div className="divide-y">
            {documents.map((doc) => (
              <div key={doc.document_id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <FileText className="text-gray-400 mt-1" size={24} />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{doc.filename}</span>
                        {getStatusIcon(doc.status)}
                      </div>
                      {doc.extracted_data && (
                        <div className="mt-1 text-sm text-gray-600">
                          <span className="font-medium">{doc.extracted_data.vendor?.name || 'Unknown Vendor'}</span>
                          {' • '}
                          <span>{doc.extracted_data.invoice_number || 'No Number'}</span>
                          {' • '}
                          <span className="font-medium">{formatCurrency(doc.extracted_data.total)}</span>
                        </div>
                      )}
                      {doc.error && (
                        <div className="mt-1 text-sm text-red-600">{doc.error}</div>
                      )}
                      {doc.confidence && (
                        <div className="mt-1 text-xs text-gray-500">
                          Confidence: {(doc.confidence * 100).toFixed(0)}%
                          {doc.suggested_category && ` • Category: ${doc.suggested_category}`}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    {doc.status === 'needs_review' && (
                      <button
                        onClick={() => handleApprove(doc.document_id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Approve
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedDoc(doc)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="View Details"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(doc)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedDoc && !editMode && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Document Details</h2>
              <button onClick={() => setSelectedDoc(null)} className="text-gray-500 hover:text-gray-700">
                <XCircle size={24} />
              </button>
            </div>
            
            {selectedDoc.extracted_data && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Vendor</label>
                    <div className="font-medium">{selectedDoc.extracted_data.vendor?.name || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Invoice Number</label>
                    <div className="font-medium">{selectedDoc.extracted_data.invoice_number || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Invoice Date</label>
                    <div className="font-medium">{selectedDoc.extracted_data.invoice_date || '-'}</div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Due Date</label>
                    <div className="font-medium">{selectedDoc.extracted_data.due_date || '-'}</div>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">Line Items</h3>
                  {selectedDoc.extracted_data.line_items?.map((item, i) => (
                    <div key={i} className="flex justify-between py-2 border-b">
                      <span>{item.description}</span>
                      <span>{formatCurrency(item.amount)}</span>
                    </div>
                  ))}
                </div>
                
                <div className="border-t pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.tax_amount)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg">
                    <span>Total</span>
                    <span>{formatCurrency(selectedDoc.extracted_data.total)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentScanner;
```

---

## File 3: AI Assistant Page
**Path:** `frontend/src/features/ai/pages/AIAssistant.jsx`

```jsx
/**
 * AI Assistant Page
 * Conversational AI for business insights
 */

import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Send,
  Bot,
  User,
  Sparkles,
  RefreshCw,
  Trash2,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { aiAPI } from '../services/aiAPI';

const AIAssistant = () => {
  const { t } = useTranslation();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    // Add welcome message
    setMessages([{
      role: 'assistant',
      content: "Hello! I'm your AI business assistant. I can help you analyze your financial data, answer questions about your business, and provide insights. What would you like to know?",
      timestamp: new Date().toISOString(),
    }]);
    
    loadSuggestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSuggestions = async () => {
    try {
      const data = await aiAPI.getAssistantSuggestions('');
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await aiAPI.chatWithAssistant({
        message: userMessage.content,
        conversation_id: conversationId,
        context: { current_page: 'assistant' },
      });
      
      setConversationId(response.conversation_id);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        data: response.data,
        suggested_actions: response.suggested_actions,
        timestamp: new Date().toISOString(),
      }]);
    } catch (error) {
      console.error('Chat failed:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I apologize, but I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
        isError: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearConversation = () => {
    setMessages([{
      role: 'assistant',
      content: "Conversation cleared. How can I help you?",
      timestamp: new Date().toISOString(),
    }]);
    setConversationId(null);
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';
    
    return (
      <div
        key={index}
        className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
      >
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
        }`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        
        <div className={`max-w-[70%] ${isUser ? 'text-right' : ''}`}>
          <div className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white'
              : message.isError
                ? 'bg-red-50 text-red-800'
                : 'bg-gray-100 text-gray-800'
          }`}>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
          
          {/* Data visualization */}
          {message.data && (
            <div className="mt-2 p-3 bg-white border rounded-lg text-sm">
              <pre className="overflow-auto max-h-40">
                {JSON.stringify(message.data, null, 2)}
              </pre>
            </div>
          )}
          
          {/* Suggested actions */}
          {message.suggested_actions?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {message.suggested_actions.map((action, i) => (
                <button
                  key={i}
                  className="px-3 py-1 text-sm bg-white border rounded-full hover:bg-gray-50 flex items-center gap-1"
                >
                  {action.action.replace(/_/g, ' ')}
                  <ExternalLink size={12} />
                </button>
              ))}
            </div>
          )}
          
          <div className="text-xs text-gray-400 mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Sparkles className="text-white" size={20} />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">AI Assistant</h1>
            <p className="text-sm text-gray-500">Ask questions about your business data</p>
          </div>
        </div>
        <button
          onClick={clearConversation}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          title="Clear Conversation"
        >
          <Trash2 size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, i) => renderMessage(msg, i))}
        
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <Bot size={16} className="text-gray-600" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <RefreshCw className="animate-spin text-gray-400" size={16} />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && suggestions.length > 0 && (
        <div className="px-4 py-2 bg-white border-t">
          <div className="text-xs text-gray-500 mb-2">Suggested questions:</div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full flex items-center gap-1"
              >
                {suggestion}
                <ChevronRight size={12} />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 bg-white border-t">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your business..."
            rows={1}
            className="flex-1 px-4 py-2 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
```

---

## File 4: Anomaly Dashboard Page
**Path:** `frontend/src/features/ai/pages/AnomalyDashboard.jsx`

```jsx
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
```

---

## File 5: AI Routes Config
**Path:** `frontend/src/features/ai/routes.jsx`

```jsx
/**
 * AI Feature Routes
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';

import CashFlowForecast from './pages/CashFlowForecast';
import DocumentScanner from './pages/DocumentScanner';
import AIAssistant from './pages/AIAssistant';
import AnomalyDashboard from './pages/AnomalyDashboard';

const AIRoutes = () => {
  return (
    <Routes>
      <Route path="cashflow" element={<CashFlowForecast />} />
      <Route path="scanner" element={<DocumentScanner />} />
      <Route path="assistant" element={<AIAssistant />} />
      <Route path="anomalies" element={<AnomalyDashboard />} />
    </Routes>
  );
};

export default AIRoutes;
```

---

## Summary Part 7

| File | Description | Lines |
|------|-------------|-------|
| `pages/CashFlowForecast.jsx` | Cash flow prediction page | ~320 |
| `pages/DocumentScanner.jsx` | OCR document scanner page | ~280 |
| `pages/AIAssistant.jsx` | AI chatbot interface | ~280 |
| `pages/AnomalyDashboard.jsx` | Anomaly monitoring page | ~280 |
| `routes.jsx` | AI routes configuration | ~25 |
| **Total** | | **~1,185 lines** |
