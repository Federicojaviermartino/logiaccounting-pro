import { useState, useRef, useEffect } from 'react';
import DOMPurify from 'dompurify';
import { useTranslation } from 'react-i18next';
import { assistantAPI } from '../services/api';

export default function AIAssistant() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await assistantAPI.getHistory();
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await assistantAPI.chat(userMessage, i18n.language);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.message,
        suggestions: res.data.suggestions,
        data: res.data.data
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      await assistantAPI.clearHistory();
      setMessages([]);
    } catch (err) {
      console.error('Failed to clear:', err);
    }
  };

  const renderMessage = (msg, idx) => {
    const isUser = msg.role === 'user';

    return (
      <div key={idx} className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">
          {isUser ? '👤' : '🤖'}
        </div>
        <div className="message-content">
          <div
            className="message-text"
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(
                msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')
              )
            }}
          />
          {msg.suggestions && msg.suggestions.length > 0 && (
            <div className="message-suggestions">
              {msg.suggestions.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => handleSuggestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      <button
        className={`ai-assistant-fab ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="AI Assistant"
      >
        {isOpen ? '✕' : '🤖'}
      </button>

      {isOpen && (
        <div className="ai-assistant-window">
          <div className="ai-assistant-header">
            <div className="ai-assistant-title">
              <span>🤖</span>
              <span>AI Assistant</span>
            </div>
            <button className="ai-clear-btn" onClick={handleClear} title="Clear chat">
              🗑️
            </button>
          </div>

          <div className="ai-assistant-messages">
            {messages.length === 0 && (
              <div className="ai-welcome">
                <div className="ai-welcome-icon">🤖</div>
                <h4>Hi! I'm your AI Assistant</h4>
                <p>Ask me about sales, expenses, payments, inventory, or projects.</p>
                <div className="ai-quick-actions">
                  <button onClick={() => handleSuggestion('Sales this month')}>📊 Sales</button>
                  <button onClick={() => handleSuggestion('Overdue payments')}>💳 Payments</button>
                  <button onClick={() => handleSuggestion('Low stock')}>📦 Inventory</button>
                </div>
              </div>
            )}
            {messages.map(renderMessage)}
            {loading && (
              <div className="chat-message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="ai-assistant-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              disabled={loading}
            />
            <button onClick={handleSend} disabled={!input.trim() || loading}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}
