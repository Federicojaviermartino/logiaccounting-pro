/**
 * Messages - Conversation and messaging center
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare, Search, Send, Plus, User, Bot,
  Paperclip, Image, MoreVertical, Archive, Trash2,
  Check, CheckCheck, Clock,
} from 'lucide-react';

export default function Messages() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messageText, setMessageText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMessageSubject, setNewMessageSubject] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [selectedConversation?.messages]);

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API calls
      setConversations([
        {
          id: '1',
          subject: 'Project Update - Website Redesign',
          participant: 'Jane Smith',
          participant_role: 'Project Manager',
          last_message: 'The design mockups are ready for your review.',
          last_message_at: new Date(Date.now() - 3600000).toISOString(),
          unread_count: 2,
          messages: [
            {
              id: 'm1',
              sender_type: 'agent',
              sender_name: 'Jane Smith',
              message: 'Hi! I wanted to give you an update on the website redesign project.',
              created_at: new Date(Date.now() - 86400000).toISOString(),
              read: true,
            },
            {
              id: 'm2',
              sender_type: 'customer',
              sender_name: 'You',
              message: 'Thanks for the update! How is the progress going?',
              created_at: new Date(Date.now() - 82800000).toISOString(),
              read: true,
            },
            {
              id: 'm3',
              sender_type: 'agent',
              sender_name: 'Jane Smith',
              message: 'We are on track! The design mockups are ready for your review. I will share the link shortly.',
              created_at: new Date(Date.now() - 7200000).toISOString(),
              read: true,
            },
            {
              id: 'm4',
              sender_type: 'agent',
              sender_name: 'Jane Smith',
              message: 'The design mockups are ready for your review.',
              created_at: new Date(Date.now() - 3600000).toISOString(),
              read: false,
            },
          ],
        },
        {
          id: '2',
          subject: 'Invoice Question',
          participant: 'Billing Team',
          participant_role: 'Finance',
          last_message: 'Thank you for your payment!',
          last_message_at: new Date(Date.now() - 172800000).toISOString(),
          unread_count: 0,
          messages: [
            {
              id: 'm1',
              sender_type: 'customer',
              sender_name: 'You',
              message: 'Hi, I have a question about invoice INV-2025-002.',
              created_at: new Date(Date.now() - 259200000).toISOString(),
              read: true,
            },
            {
              id: 'm2',
              sender_type: 'agent',
              sender_name: 'Billing Team',
              message: 'Of course! How can we help you with that invoice?',
              created_at: new Date(Date.now() - 252000000).toISOString(),
              read: true,
            },
            {
              id: 'm3',
              sender_type: 'customer',
              sender_name: 'You',
              message: 'I was wondering if I could split the payment.',
              created_at: new Date(Date.now() - 180000000).toISOString(),
              read: true,
            },
            {
              id: 'm4',
              sender_type: 'agent',
              sender_name: 'Billing Team',
              message: 'Yes, we can arrange a payment plan for you. Let me set that up.',
              created_at: new Date(Date.now() - 176400000).toISOString(),
              read: true,
            },
            {
              id: 'm5',
              sender_type: 'agent',
              sender_name: 'Billing Team',
              message: 'Thank you for your payment!',
              created_at: new Date(Date.now() - 172800000).toISOString(),
              read: true,
            },
          ],
        },
        {
          id: '3',
          subject: 'New Feature Request',
          participant: 'Support Team',
          participant_role: 'Support',
          last_message: 'We have logged your feature request.',
          last_message_at: new Date(Date.now() - 604800000).toISOString(),
          unread_count: 0,
          messages: [
            {
              id: 'm1',
              sender_type: 'customer',
              sender_name: 'You',
              message: 'I would like to request a new feature for the portal.',
              created_at: new Date(Date.now() - 691200000).toISOString(),
              read: true,
            },
            {
              id: 'm2',
              sender_type: 'agent',
              sender_name: 'Support Team',
              message: 'We have logged your feature request.',
              created_at: new Date(Date.now() - 604800000).toISOString(),
              read: true,
            },
          ],
        },
      ]);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!messageText.trim() || !selectedConversation) return;

    try {
      setIsSending(true);
      const newMessage = {
        id: Date.now().toString(),
        sender_type: 'customer',
        sender_name: 'You',
        message: messageText,
        created_at: new Date().toISOString(),
        read: true,
      };

      const updatedConversation = {
        ...selectedConversation,
        messages: [...selectedConversation.messages, newMessage],
        last_message: messageText,
        last_message_at: new Date().toISOString(),
      };

      setSelectedConversation(updatedConversation);
      setConversations(conversations.map(c =>
        c.id === selectedConversation.id ? updatedConversation : c
      ));
      setMessageText('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleNewConversation = async () => {
    if (!newMessageSubject.trim()) return;

    const newConversation = {
      id: Date.now().toString(),
      subject: newMessageSubject,
      participant: 'Support Team',
      participant_role: 'Support',
      last_message: '',
      last_message_at: new Date().toISOString(),
      unread_count: 0,
      messages: [],
    };

    setConversations([newConversation, ...conversations]);
    setSelectedConversation(newConversation);
    setShowNewMessage(false);
    setNewMessageSubject('');
  };

  const handleArchive = async (conversationId) => {
    setConversations(conversations.filter(c => c.id !== conversationId));
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(null);
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const filteredConversations = searchQuery
    ? conversations.filter(c =>
        c.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.participant.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : conversations;

  return (
    <div className="messages-page">
      <div className="conversations-sidebar">
        <div className="sidebar-header">
          <h2>Messages</h2>
          <button className="new-btn" onClick={() => setShowNewMessage(true)}>
            <Plus className="w-5 h-5" />
          </button>
        </div>

        <div className="search-box">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="conversations-list">
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : filteredConversations.length === 0 ? (
            <div className="empty-state">
              <MessageSquare className="w-10 h-10" />
              <p>No conversations</p>
            </div>
          ) : (
            filteredConversations.map((conversation) => (
              <button
                key={conversation.id}
                className={`conversation-item ${selectedConversation?.id === conversation.id ? 'active' : ''} ${conversation.unread_count > 0 ? 'unread' : ''}`}
                onClick={() => setSelectedConversation(conversation)}
              >
                <div className="avatar">
                  <User className="w-5 h-5" />
                </div>
                <div className="conversation-info">
                  <div className="conversation-header">
                    <span className="participant-name">{conversation.participant}</span>
                    <span className="timestamp">{formatTime(conversation.last_message_at)}</span>
                  </div>
                  <span className="subject">{conversation.subject}</span>
                  <p className="last-message">{conversation.last_message}</p>
                </div>
                {conversation.unread_count > 0 && (
                  <span className="unread-badge">{conversation.unread_count}</span>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="message-area">
        {selectedConversation ? (
          <>
            <div className="message-header">
              <div className="header-info">
                <h3>{selectedConversation.subject}</h3>
                <span className="participant">
                  {selectedConversation.participant} • {selectedConversation.participant_role}
                </span>
              </div>
              <div className="header-actions">
                <button className="action-btn" title="Archive" onClick={() => handleArchive(selectedConversation.id)}>
                  <Archive className="w-4 h-4" />
                </button>
                <button className="action-btn" title="More">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="messages-container">
              {selectedConversation.messages.length === 0 ? (
                <div className="empty-messages">
                  <MessageSquare className="w-12 h-12" />
                  <p>Start the conversation</p>
                </div>
              ) : (
                selectedConversation.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`message ${msg.sender_type === 'customer' ? 'outgoing' : 'incoming'}`}
                  >
                    <div className="message-avatar">
                      {msg.sender_type === 'customer' ? (
                        <User className="w-5 h-5" />
                      ) : (
                        <Bot className="w-5 h-5" />
                      )}
                    </div>
                    <div className="message-bubble">
                      <div className="message-content">{msg.message}</div>
                      <div className="message-meta">
                        <span className="time">{formatTime(msg.created_at)}</span>
                        {msg.sender_type === 'customer' && (
                          <span className="read-status">
                            {msg.read ? <CheckCheck className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="compose-area">
              <div className="compose-actions">
                <button className="attach-btn" title="Attach file">
                  <Paperclip className="w-5 h-5" />
                </button>
                <button className="attach-btn" title="Add image">
                  <Image className="w-5 h-5" />
                </button>
              </div>
              <div className="compose-input">
                <textarea
                  placeholder="Type your message..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  rows={1}
                />
                <button
                  className="send-btn"
                  onClick={handleSendMessage}
                  disabled={!messageText.trim() || isSending}
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="no-selection">
            <MessageSquare className="w-16 h-16" />
            <h3>Select a conversation</h3>
            <p>Choose a conversation from the list or start a new one</p>
            <button className="btn-primary" onClick={() => setShowNewMessage(true)}>
              <Plus className="w-4 h-4" />
              New Message
            </button>
          </div>
        )}
      </div>

      {/* New Message Modal */}
      {showNewMessage && (
        <div className="modal-overlay" onClick={() => setShowNewMessage(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>New Message</h2>
            <div className="form-group">
              <label>Subject</label>
              <input
                type="text"
                placeholder="What is this about?"
                value={newMessageSubject}
                onChange={(e) => setNewMessageSubject(e.target.value)}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowNewMessage(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleNewConversation}>
                Start Conversation
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .messages-page {
          display: flex;
          height: calc(100vh - 140px);
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          overflow: hidden;
        }

        .conversations-sidebar {
          width: 340px;
          border-right: 1px solid #e2e8f0;
          display: flex;
          flex-direction: column;
        }

        @media (max-width: 768px) {
          .conversations-sidebar {
            width: 100%;
            display: ${selectedConversation ? 'none' : 'flex'};
          }

          .message-area {
            display: ${selectedConversation ? 'flex' : 'none'};
          }
        }

        .sidebar-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e2e8f0;
        }

        .sidebar-header h2 {
          margin: 0;
          font-size: 18px;
        }

        .new-btn {
          width: 36px;
          height: 36px;
          background: #3b82f6;
          color: white;
          border-radius: 50%;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 20px;
          border-bottom: 1px solid #e2e8f0;
        }

        .search-box input {
          flex: 1;
          border: none;
          outline: none;
          font-size: 14px;
        }

        .conversations-list {
          flex: 1;
          overflow-y: auto;
        }

        .conversation-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 16px 20px;
          border-bottom: 1px solid #f1f5f9;
          cursor: pointer;
          width: 100%;
          text-align: left;
          background: white;
          border-left: 3px solid transparent;
          position: relative;
        }

        .conversation-item:hover {
          background: #f8fafc;
        }

        .conversation-item.active {
          background: #f1f5f9;
          border-left-color: #3b82f6;
        }

        .conversation-item.unread {
          background: rgba(59, 130, 246, 0.05);
        }

        .avatar {
          width: 40px;
          height: 40px;
          background: #f1f5f9;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          flex-shrink: 0;
        }

        .conversation-info {
          flex: 1;
          min-width: 0;
        }

        .conversation-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2px;
        }

        .participant-name {
          font-weight: 600;
          font-size: 14px;
        }

        .timestamp {
          font-size: 12px;
          color: #94a3b8;
        }

        .subject {
          font-size: 13px;
          color: #64748b;
          display: block;
          margin-bottom: 4px;
        }

        .last-message {
          font-size: 13px;
          color: #94a3b8;
          margin: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .unread-badge {
          position: absolute;
          right: 20px;
          top: 50%;
          transform: translateY(-50%);
          background: #3b82f6;
          color: white;
          font-size: 11px;
          font-weight: 600;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .message-area {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid #e2e8f0;
        }

        .header-info h3 {
          margin: 0 0 4px;
          font-size: 16px;
        }

        .participant {
          font-size: 13px;
          color: #64748b;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          width: 36px;
          height: 36px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: white;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          cursor: pointer;
        }

        .action-btn:hover {
          background: #f8fafc;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .message {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }

        .message.outgoing {
          flex-direction: row-reverse;
        }

        .message-avatar {
          width: 32px;
          height: 32px;
          background: #f1f5f9;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          flex-shrink: 0;
        }

        .message.outgoing .message-avatar {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .message-bubble {
          max-width: 70%;
          background: #f1f5f9;
          padding: 12px 16px;
          border-radius: 16px;
        }

        .message.outgoing .message-bubble {
          background: #3b82f6;
          color: white;
        }

        .message-content {
          font-size: 14px;
          line-height: 1.5;
        }

        .message-meta {
          display: flex;
          justify-content: flex-end;
          align-items: center;
          gap: 6px;
          margin-top: 6px;
        }

        .time {
          font-size: 11px;
          opacity: 0.7;
        }

        .read-status {
          opacity: 0.7;
        }

        .compose-area {
          padding: 16px 20px;
          border-top: 1px solid #e2e8f0;
        }

        .compose-actions {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }

        .attach-btn {
          width: 36px;
          height: 36px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: white;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          cursor: pointer;
        }

        .compose-input {
          display: flex;
          gap: 12px;
          align-items: flex-end;
        }

        .compose-input textarea {
          flex: 1;
          padding: 12px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          resize: none;
          font-size: 15px;
          max-height: 120px;
          outline: none;
        }

        .compose-input textarea:focus {
          border-color: #3b82f6;
        }

        .send-btn {
          width: 44px;
          height: 44px;
          background: #3b82f6;
          color: white;
          border-radius: 12px;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .no-selection {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #64748b;
          text-align: center;
        }

        .no-selection svg {
          color: #cbd5e1;
          margin-bottom: 16px;
        }

        .no-selection h3 {
          margin: 0 0 8px;
          color: #1e293b;
        }

        .no-selection p {
          margin: 0 0 20px;
        }

        .empty-state, .loading, .empty-messages {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px;
          color: #64748b;
          text-align: center;
          height: 100%;
        }

        .empty-state svg, .empty-messages svg {
          color: #cbd5e1;
          margin-bottom: 12px;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-weight: 500;
          border: none;
          cursor: pointer;
        }

        .btn-secondary {
          padding: 10px 20px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: white;
          cursor: pointer;
        }

        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
        }

        .modal-content {
          background: #ffffff;
          border-radius: 16px;
          padding: 24px;
          width: 100%;
          max-width: 400px;
        }

        .modal-content h2 {
          margin: 0 0 20px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 8px;
        }

        .form-group input {
          width: 100%;
          padding: 10px 14px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 15px;
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }
      `}</style>
    </div>
  );
}
