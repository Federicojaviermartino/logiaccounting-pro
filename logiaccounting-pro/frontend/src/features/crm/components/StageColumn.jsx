/**
 * StageColumn - Pipeline stage column for Kanban board
 */

import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Plus, MoreVertical } from 'lucide-react';
import DealCard from './DealCard';

export default function StageColumn({
  stage,
  opportunities,
  onAddDeal,
  onDealClick,
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: stage.id,
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  return (
    <div
      className={`stage-column ${isOver ? 'drag-over' : ''}`}
      style={{ '--stage-color': stage.color || '#6366f1' }}
    >
      <div className="column-header">
        <div className="header-left">
          <div className="stage-indicator" />
          <h3 className="stage-name">{stage.name}</h3>
          <span className="deal-count">{opportunities.length}</span>
        </div>
        <div className="header-right">
          <span className="stage-value">{formatCurrency(stage.value)}</span>
          <button className="add-btn" onClick={() => onAddDeal?.(stage.id)}>
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {stage.probability !== undefined && (
        <div className="stage-probability">
          {stage.probability}% probability
        </div>
      )}

      <div ref={setNodeRef} className="deals-container">
        <SortableContext
          items={opportunities.map((o) => o.id)}
          strategy={verticalListSortingStrategy}
        >
          {opportunities.map((opp) => (
            <DealCard
              key={opp.id}
              deal={opp}
              onClick={onDealClick}
            />
          ))}
        </SortableContext>

        {opportunities.length === 0 && (
          <div className="empty-state">
            <p>No deals in this stage</p>
            <button className="add-deal-btn" onClick={() => onAddDeal?.(stage.id)}>
              <Plus className="w-4 h-4" />
              Add Deal
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .stage-column {
          min-width: 300px;
          max-width: 300px;
          background: var(--bg-secondary);
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          max-height: 100%;
        }

        .stage-column.drag-over {
          background: rgba(99, 102, 241, 0.05);
          border: 2px dashed var(--primary);
        }

        .column-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid var(--border-color);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stage-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: var(--stage-color);
        }

        .stage-name {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
        }

        .deal-count {
          background: var(--bg-tertiary, #e5e7eb);
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .stage-value {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .add-btn {
          padding: 4px;
          border-radius: 4px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .add-btn:hover {
          background: var(--bg-tertiary);
          color: var(--primary);
        }

        .stage-probability {
          font-size: 11px;
          color: var(--text-muted);
          padding: 4px 16px 8px;
        }

        .deals-container {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 16px;
          color: var(--text-muted);
          text-align: center;
        }

        .empty-state p {
          margin: 0 0 12px;
          font-size: 13px;
        }

        .add-deal-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
        }

        .add-deal-btn:hover {
          opacity: 0.9;
        }
      `}</style>
    </div>
  );
}
