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
      // Set default suggestions if API fails
      setSuggestions([
        "What projects are over budget?",
        "Show me the most profitable projects",
        "Which suppliers have the highest expenses?",
        "What's our monthly revenue trend?",
        "Which projects are at risk?",
        "Compare expenses by category",
        "What payments are due this week?",
        "Show low stock materials"
      ]);
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
        suggestions: res.data.suggestions,
        queryType: res.data.query_type,
        confidence: res.data.confidence
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

  const formatValue = (key, value) => {
    if (typeof value === 'number') {
      if (key.toLowerCase().includes('percent') || key.toLowerCase().includes('margin')) {
        return `${value.toFixed(1)}%`;
      }
      if (key.toLowerCase().includes('count') || key.toLowerCase().includes('num')) {
        return value.toString();
      }
      return formatCurrency(value);
    }
    if (Array.isArray(value)) {
      return value.length + ' items';
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return String(value);
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
                background: msg.role === 'user' ? 'var(--primary)' : msg.error ? '#fef2f2' : 'white',
                color: msg.role === 'user' ? 'white' : msg.error ? '#dc2626' : 'var(--gray-800)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                {/* Query Type Badge */}
                {msg.queryType && (
                  <div className="mt-2">
                    <span className="badge badge-primary">{msg.queryType}</span>
                    {msg.confidence && (
                      <span className="badge badge-gray ml-2">
                        {(msg.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                )}

                {/* Data Table */}
                {msg.data && typeof msg.data === 'object' && !Array.isArray(msg.data) && Object.keys(msg.data).length > 0 && (
                  <div className="table-container mt-3" style={{ fontSize: '0.85rem' }}>
                    <table className="data-table">
                      <tbody>
                        {Object.entries(msg.data).map(([key, value]) => (
                          <tr key={key}>
                            <td className="font-bold" style={{ textTransform: 'capitalize' }}>
                              {key.replace(/_/g, ' ')}
                            </td>
                            <td>{formatValue(key, value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Array Data */}
                {msg.data && Array.isArray(msg.data) && msg.data.length > 0 && (
                  <div className="table-container mt-3" style={{ fontSize: '0.85rem', maxHeight: '200px', overflowY: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          {Object.keys(msg.data[0]).map(key => (
                            <th key={key} style={{ textTransform: 'capitalize' }}>
                              {key.replace(/_/g, ' ')}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.slice(0, 5).map((item, idx) => (
                          <tr key={idx}>
                            {Object.entries(item).map(([key, value]) => (
                              <td key={key}>{formatValue(key, value)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Follow-up Suggestions */}
                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {msg.suggestions.slice(0, 3).map((s, j) => (
                      <button
                        key={j}
                        className="btn btn-sm btn-secondary"
                        onClick={() => sendQuery(s)}
                        disabled={loading}
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
      <div className="section" style={{ width: '280px', flexShrink: 0 }}>
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
