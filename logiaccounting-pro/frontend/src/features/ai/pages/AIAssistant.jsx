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
