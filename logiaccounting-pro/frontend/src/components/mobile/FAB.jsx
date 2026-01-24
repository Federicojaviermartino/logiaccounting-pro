/**
 * Floating Action Button (FAB) - Quick actions menu
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  X,
  CreditCard,
  TicketIcon,
  MessageCircle,
  FileText,
} from 'lucide-react';

const defaultActions = [
  { id: 'pay', label: 'Pay Invoice', icon: CreditCard, color: '#10b981', path: '/portal/payments' },
  { id: 'ticket', label: 'New Ticket', icon: TicketIcon, color: '#3b82f6', path: '/portal/support/new' },
  { id: 'message', label: 'Message', icon: MessageCircle, color: '#8b5cf6', path: '/portal/messages/new' },
  { id: 'quote', label: 'View Quotes', icon: FileText, color: '#f59e0b', path: '/portal/quotes' },
];

export default function FAB({ actions = defaultActions, onAction }) {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const handleAction = (action) => {
    setIsOpen(false);
    if (onAction) {
      onAction(action);
    } else if (action.path) {
      navigate(action.path);
    }
  };

  return (
    <div className="fab-container">
      {/* Backdrop */}
      {isOpen && (
        <div className="fab-backdrop" onClick={() => setIsOpen(false)} />
      )}

      {/* Action items */}
      <div className={`fab-actions ${isOpen ? 'open' : ''}`}>
        {actions.map((action, index) => (
          <button
            key={action.id}
            className="fab-action"
            style={{
              '--action-color': action.color,
              '--delay': `${index * 50}ms`,
            }}
            onClick={() => handleAction(action)}
          >
            <span className="action-label">{action.label}</span>
            <span className="action-icon" style={{ background: action.color }}>
              <action.icon className="icon" />
            </span>
          </button>
        ))}
      </div>

      {/* Main FAB button */}
      <button
        className={`fab-main ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close menu' : 'Open quick actions'}
      >
        {isOpen ? <X className="icon" /> : <Plus className="icon" />}
      </button>

      <style jsx>{`
        .fab-container {
          position: fixed;
          bottom: calc(80px + env(safe-area-inset-bottom));
          right: 16px;
          z-index: 90;
        }

        @media (min-width: 769px) {
          .fab-container {
            bottom: 24px;
            right: 24px;
          }
        }

        .fab-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.3);
          z-index: -1;
        }

        .fab-main {
          width: 56px;
          height: 56px;
          border-radius: 16px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
          transition: transform 0.3s, box-shadow 0.3s;
        }

        .fab-main:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 24px rgba(59, 130, 246, 0.5);
        }

        .fab-main.open {
          transform: rotate(45deg);
          background: var(--text-secondary);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .fab-main .icon {
          width: 24px;
          height: 24px;
          transition: transform 0.3s;
        }

        .fab-actions {
          position: absolute;
          bottom: 70px;
          right: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
          opacity: 0;
          pointer-events: none;
          transform: translateY(20px);
          transition: opacity 0.3s, transform 0.3s;
        }

        .fab-actions.open {
          opacity: 1;
          pointer-events: all;
          transform: translateY(0);
        }

        .fab-action {
          display: flex;
          align-items: center;
          gap: 12px;
          opacity: 0;
          transform: translateY(10px) scale(0.9);
          transition: opacity 0.2s var(--delay), transform 0.2s var(--delay);
        }

        .fab-actions.open .fab-action {
          opacity: 1;
          transform: translateY(0) scale(1);
        }

        .action-label {
          padding: 8px 16px;
          background: var(--bg-primary);
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          white-space: nowrap;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }

        .action-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
        }

        .action-icon .icon {
          width: 20px;
          height: 20px;
        }
      `}</style>
    </div>
  );
}
