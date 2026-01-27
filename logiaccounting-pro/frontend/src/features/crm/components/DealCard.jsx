/**
 * DealCard - Draggable deal card for pipeline board
 */

import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  GripVertical,
  Building2,
  User,
  Calendar,
  DollarSign,
} from 'lucide-react';

export default function DealCard({ deal, onClick }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: deal.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: deal.currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getDaysUntilClose = () => {
    if (!deal.expected_close_date) return null;
    const closeDate = new Date(deal.expected_close_date);
    const today = new Date();
    const diff = Math.ceil((closeDate - today) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const daysUntilClose = getDaysUntilClose();
  const isOverdue = daysUntilClose !== null && daysUntilClose < 0;
  const isClosingSoon = daysUntilClose !== null && daysUntilClose >= 0 && daysUntilClose <= 7;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`deal-card ${isDragging ? 'dragging' : ''}`}
      onClick={() => onClick?.(deal)}
    >
      <div className="card-header">
        <div
          className="drag-handle"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="w-4 h-4" />
        </div>
        <span className="deal-name">{deal.name}</span>
      </div>

      <div className="deal-amount">
        <DollarSign className="w-4 h-4" />
        {formatCurrency(deal.amount)}
      </div>

      <div className="deal-meta">
        {deal.company_name && (
          <div className="meta-item">
            <Building2 className="w-3 h-3" />
            <span>{deal.company_name}</span>
          </div>
        )}

        {deal.contact_name && (
          <div className="meta-item">
            <User className="w-3 h-3" />
            <span>{deal.contact_name}</span>
          </div>
        )}

        {deal.expected_close_date && (
          <div className={`meta-item ${isOverdue ? 'overdue' : ''} ${isClosingSoon ? 'closing-soon' : ''}`}>
            <Calendar className="w-3 h-3" />
            <span>{formatDate(deal.expected_close_date)}</span>
          </div>
        )}
      </div>

      {deal.probability !== undefined && (
        <div className="probability-bar">
          <div
            className="probability-fill"
            style={{ width: `${deal.probability}%` }}
          />
          <span className="probability-text">{deal.probability}%</span>
        </div>
      )}

      <style jsx>{`
        .deal-card {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .deal-card:hover {
          border-color: var(--primary);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .deal-card.dragging {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .card-header {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-bottom: 8px;
        }

        .drag-handle {
          color: var(--text-muted);
          cursor: grab;
          padding: 2px;
        }

        .drag-handle:active {
          cursor: grabbing;
        }

        .deal-name {
          flex: 1;
          font-weight: 500;
          font-size: 14px;
          line-height: 1.3;
        }

        .deal-amount {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 16px;
          font-weight: 600;
          color: var(--primary);
          margin-bottom: 8px;
        }

        .deal-meta {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 12px;
          color: var(--text-muted);
        }

        .meta-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .meta-item.overdue {
          color: #ef4444;
        }

        .meta-item.closing-soon {
          color: #f59e0b;
        }

        .probability-bar {
          position: relative;
          height: 4px;
          background: var(--bg-secondary);
          border-radius: 2px;
          margin-top: 8px;
          overflow: hidden;
        }

        .probability-fill {
          position: absolute;
          left: 0;
          top: 0;
          height: 100%;
          background: var(--primary);
          border-radius: 2px;
          transition: width 0.3s;
        }

        .probability-text {
          position: absolute;
          right: 0;
          top: -16px;
          font-size: 10px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
