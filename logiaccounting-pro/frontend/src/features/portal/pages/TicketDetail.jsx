/**
 * Ticket Detail - View and reply to a ticket
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Send, Clock, CheckCircle, AlertCircle,
  Star, RotateCcw, X, User, Bot,
} from 'lucide-react';

export default function TicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const [ticket, setTicket] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [replyText, setReplyText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  useEffect(() => {
    scrollToBottom();
  }, [ticket?.messages]);

  const loadTicket = async () => {
    try {
      // Simulated data - replace with API call
      setTicket({
        id: ticketId,
        ticket_number: 'TKT-123456',
        subject: 'Login issue with portal',
        description: 'I am unable to login to the customer portal. Getting error after entering credentials.',
        status: 'in_progress',
        priority: 'high',
        category: 'technical',
        created_at: new Date().toISOString(),
        satisfaction_rating: null,
        messages: [
          {
            id: '1',
            sender_type: 'customer',
            sender_name: 'John Doe',
            message: 'I am unable to login to the customer portal. Getting error after entering credentials.',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            attachments: [],
          },
          {
            id: '2',
            sender_type: 'agent',
            sender_name: 'Support Team',
            message: 'Thank you for reaching out. We are looking into this issue. Can you please clear your browser cache and try again?',
            created_at: new Date(Date.now() - 43200000).toISOString(),
            attachments: [],
          },
          {
            id: '3',
            sender_type: 'customer',
            sender_name: 'John Doe',
            message: 'I tried clearing cache but still having the same issue.',
            created_at: new Date().toISOString(),
            attachments: [],
          },
        ],
      });
    } catch (error) {
      console.error('Failed to load ticket:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendReply = async () => {
    if (!replyText.trim()) return;

    try {
      setIsSending(true);
      // API call would go here
      const newMessage = {
        id: Date.now().toString(),
        sender_type: 'customer',
        sender_name: 'You',
        message: replyText,
        created_at: new Date().toISOString(),
        attachments: [],
      };
      setTicket({ ...ticket, messages: [...ticket.messages, newMessage] });
      setReplyText('');
    } catch (error) {
      console.error('Failed to send reply:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleClose = async () => {
    if (!confirm('Are you sure you want to close this ticket?')) return;
    try {
      setTicket({ ...ticket, status: 'closed' });
    } catch (error) {
      console.error('Failed to close ticket:', error);
    }
  };

  const handleReopen = async () => {
    try {
      setTicket({ ...ticket, status: 'open' });
    } catch (error) {
      console.error('Failed to reopen ticket:', error);
    }
  };

  const handleRate = async () => {
    if (rating === 0) return;
    try {
      setTicket({ ...ticket, satisfaction_rating: rating });
      setShowRating(false);
    } catch (error) {
      console.error('Failed to rate ticket:', error);
    }
  };

  const getStatusInfo = (status) => {
    const info = {
      open: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Open' },
      in_progress: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'In Progress' },
      waiting_customer: { icon: AlertCircle, color: 'text-orange-600', bg: 'bg-orange-100', label: 'Waiting on You' },
      resolved: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Resolved' },
      closed: { icon: CheckCircle, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Closed' },
    };
    return info[status] || info.open;
  };

  if (isLoading) return <div className="loading">Loading...</div>;
  if (!ticket) return <div className="error">Ticket not found</div>;

  const statusInfo = getStatusInfo(ticket.status);
  const StatusIcon = statusInfo.icon;
  const canReply = !['closed'].includes(ticket.status);
  const canClose = ['open', 'in_progress', 'waiting_customer', 'resolved'].includes(ticket.status);
  const canReopen = ['resolved', 'closed'].includes(ticket.status);
  const canRate = ['resolved', 'closed'].includes(ticket.status) && !ticket.satisfaction_rating;

  return (
    <div className="ticket-detail">
      {/* Header */}
      <div className="ticket-header">
        <button className="back-btn" onClick={() => navigate('/portal/support')}>
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <div className="ticket-info">
          <div className="ticket-title-row">
            <span className="ticket-number">{ticket.ticket_number}</span>
            <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
              <StatusIcon className="w-4 h-4" />
              {statusInfo.label}
            </span>
          </div>
          <h1>{ticket.subject}</h1>
          <div className="ticket-meta">
            <span>Created {new Date(ticket.created_at).toLocaleDateString()}</span>
            <span>•</span>
            <span className="capitalize">{ticket.category}</span>
            <span>•</span>
            <span className="capitalize">{ticket.priority} priority</span>
          </div>
        </div>

        <div className="ticket-actions">
          {canClose && (
            <button className="btn-secondary" onClick={handleClose}>
              <X className="w-4 h-4" />
              Close
            </button>
          )}
          {canReopen && (
            <button className="btn-secondary" onClick={handleReopen}>
              <RotateCcw className="w-4 h-4" />
              Reopen
            </button>
          )}
          {canRate && (
            <button className="btn-primary" onClick={() => setShowRating(true)}>
              <Star className="w-4 h-4" />
              Rate
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {ticket.messages?.map((msg, i) => (
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
            <div className="message-content">
              <div className="message-header">
                <span className="sender-name">{msg.sender_name}</span>
                <span className="message-time">
                  {new Date(msg.created_at).toLocaleString()}
                </span>
              </div>
              <div className="message-text">{msg.message}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Reply Box */}
      {canReply && (
        <div className="reply-box">
          <textarea
            placeholder="Type your reply..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            rows={3}
          />
          <div className="reply-actions">
            <button
              className="send-btn"
              onClick={handleSendReply}
              disabled={!replyText.trim() || isSending}
            >
              <Send className="w-4 h-4" />
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      )}

      {/* Rating Modal */}
      {showRating && (
        <div className="modal-overlay" onClick={() => setShowRating(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Rate Your Experience</h2>
            <p>How satisfied are you with the support you received?</p>

            <div className="rating-stars">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  className={`star-btn ${star <= rating ? 'active' : ''}`}
                  onClick={() => setRating(star)}
                >
                  <Star className="w-8 h-8" fill={star <= rating ? '#f59e0b' : 'none'} />
                </button>
              ))}
            </div>

            <textarea
              placeholder="Additional comments (optional)"
              value={ratingComment}
              onChange={(e) => setRatingComment(e.target.value)}
              rows={3}
            />

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowRating(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleRate} disabled={rating === 0}>
                Submit Rating
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .ticket-detail {
          max-width: 900px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          height: calc(100vh - 140px);
        }

        .ticket-header {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 16px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #64748b;
          margin-bottom: 12px;
          background: none;
          border: none;
          cursor: pointer;
        }

        .ticket-title-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }

        .ticket-number {
          font-family: monospace;
          color: #64748b;
        }

        .status-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
        }

        .ticket-header h1 {
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 8px;
        }

        .ticket-meta {
          display: flex;
          gap: 8px;
          font-size: 13px;
          color: #64748b;
        }

        .ticket-actions {
          display: flex;
          gap: 10px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #e2e8f0;
        }

        .btn-secondary {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 14px;
          background: #ffffff;
          cursor: pointer;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-size: 14px;
          border: none;
          cursor: pointer;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          margin-bottom: 16px;
        }

        .message {
          display: flex;
          gap: 12px;
          margin-bottom: 20px;
        }

        .message.outgoing {
          flex-direction: row-reverse;
        }

        .message-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: #f8fafc;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .message.outgoing .message-avatar {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .message-content {
          max-width: 70%;
          background: #f8fafc;
          padding: 12px 16px;
          border-radius: 12px;
        }

        .message.outgoing .message-content {
          background: #3b82f6;
          color: white;
        }

        .message-header {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 6px;
        }

        .sender-name {
          font-weight: 600;
          font-size: 13px;
        }

        .message-time {
          font-size: 12px;
          opacity: 0.7;
        }

        .message-text {
          font-size: 14px;
          line-height: 1.5;
          white-space: pre-wrap;
        }

        .reply-box {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
        }

        .reply-box textarea {
          width: 100%;
          border: none;
          resize: none;
          font-size: 15px;
          outline: none;
        }

        .reply-actions {
          display: flex;
          justify-content: flex-end;
          margin-top: 12px;
        }

        .send-btn {
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

        .send-btn:disabled {
          opacity: 0.6;
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
          text-align: center;
        }

        .modal-content h2 {
          margin: 0 0 8px;
        }

        .modal-content p {
          color: #64748b;
          margin: 0 0 20px;
        }

        .rating-stars {
          display: flex;
          justify-content: center;
          gap: 8px;
          margin-bottom: 20px;
        }

        .star-btn {
          color: #d1d5db;
          transition: color 0.2s;
          background: none;
          border: none;
          cursor: pointer;
        }

        .star-btn.active,
        .star-btn:hover {
          color: #f59e0b;
        }

        .modal-content textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          margin-bottom: 20px;
          resize: none;
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
