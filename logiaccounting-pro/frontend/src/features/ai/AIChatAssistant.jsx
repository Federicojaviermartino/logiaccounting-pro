/**
 * AI Chat Assistant Component
 * Enhanced profitability assistant with conversation history
 */

import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const API_BASE = '/api/v1/ai/assistant';

export default function AIChatAssistant({ embedded = false }) {
  const { t } = useTranslation();
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API_BASE}/conversations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await res.json();
      setConversations(data);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
    }
  };

  const loadConversation = async (conversationId) => {
    try {
      const res = await fetch(`${API_BASE}/conversations/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await res.json();
      setCurrentConversation(data);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: currentConversation?.id,
        }),
      });

      const data = await res.json();
      setCurrentConversation({ id: data.conversation_id });
      setMessages(prev => [...prev, {
        id: data.message_id,
        role: 'assistant',
        content: data.content,
        tool_calls: data.tool_calls,
      }]);

      // Refresh conversations list
      fetchConversations();
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const provideFeedback = async (messageId, feedback) => {
    try {
      await fetch(`${API_BASE}/messages/${messageId}/feedback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback }),
      });
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const startNewConversation = () => {
    setCurrentConversation(null);
    setMessages([]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    { icon: '📊', text: 'How is my revenue this month?' },
    { icon: '💰', text: 'What are my top expenses?' },
    { icon: '📈', text: 'Show me profitability metrics' },
    { icon: '💳', text: 'Any overdue payments?' },
  ];

  return (
    <div className={`ai-chat-assistant ${embedded ? 'embedded' : ''}`}>
      {!embedded && (
        <div className="chat-sidebar">
          <button className="new-chat-btn" onClick={startNewConversation}>
            + New Chat
          </button>
          <div className="conversation-list">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`conversation-item ${currentConversation?.id === conv.id ? 'active' : ''}`}
                onClick={() => loadConversation(conv.id)}
              >
                <span className="conv-title">{conv.title}</span>
                <span className="conv-date">
                  {new Date(conv.updated_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-welcome">
              <div className="welcome-icon">🤖</div>
              <h3>AI Profitability Assistant</h3>
              <p>Ask me anything about your financial data</p>
              <div className="quick-questions">
                {quickQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    className="quick-question"
                    onClick={() => setInput(q.text)}
                  >
                    <span>{q.icon}</span>
                    <span>{q.text}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-body">
                  <div className="message-content">{msg.content}</div>
                  {msg.tool_calls && msg.tool_calls.length > 0 && (
                    <div className="tool-calls">
                      {msg.tool_calls.map((tool, tidx) => (
                        <span key={tidx} className="tool-badge">
                          📊 {tool.name}
                        </span>
                      ))}
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.id && (
                    <div className="message-feedback">
                      <button onClick={() => provideFeedback(msg.id, 'positive')}>👍</button>
                      <button onClick={() => provideFeedback(msg.id, 'negative')}>👎</button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="chat-message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-body">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about revenue, expenses, profitability..."
            rows={1}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}
