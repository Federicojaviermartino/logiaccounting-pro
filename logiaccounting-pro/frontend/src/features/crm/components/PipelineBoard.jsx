/**
 * PipelineBoard - Kanban board for sales pipeline
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import {
  Plus,
  Filter,
  RefreshCw,
  Settings,
  ChevronDown,
} from 'lucide-react';
import StageColumn from './StageColumn';
import DealCard from './DealCard';
import DealModal from './DealModal';
import { crmAPI } from '../../../services/api/crm';

export default function PipelineBoard() {
  const [boardData, setBoardData] = useState(null);
  const [activeDeal, setActiveDeal] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [showDealModal, setShowDealModal] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [selectedStageId, setSelectedStageId] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 10,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    loadPipelines();
  }, []);

  useEffect(() => {
    if (selectedPipeline) {
      loadBoard();
    }
  }, [selectedPipeline]);

  const loadPipelines = async () => {
    try {
      const res = await crmAPI.pipelines.list();
      setPipelines(res.data || []);
      if (res.data?.length > 0) {
        setSelectedPipeline(res.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load pipelines:', error);
    }
  };

  const loadBoard = async () => {
    try {
      setIsLoading(true);
      const res = await crmAPI.opportunities.getBoard(selectedPipeline);
      setBoardData(res.data);
    } catch (error) {
      console.error('Failed to load board:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragStart = (event) => {
    const { active } = event;
    const deal = findDealById(active.id);
    setActiveDeal(deal);
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setActiveDeal(null);

    if (!over) return;

    const dealId = active.id;
    const newStageId = over.id;

    // Find current stage of the deal
    const currentStage = boardData.stages.find((stage) =>
      stage.opportunities.some((opp) => opp.id === dealId)
    );

    if (currentStage?.id === newStageId) return;

    // Optimistically update UI
    const updatedStages = boardData.stages.map((stage) => {
      // Remove from current stage
      if (stage.id === currentStage?.id) {
        return {
          ...stage,
          opportunities: stage.opportunities.filter((o) => o.id !== dealId),
          count: stage.count - 1,
        };
      }
      // Add to new stage
      if (stage.id === newStageId) {
        const deal = findDealById(dealId);
        return {
          ...stage,
          opportunities: [...stage.opportunities, deal],
          count: stage.count + 1,
        };
      }
      return stage;
    });

    setBoardData({ ...boardData, stages: updatedStages });

    // Call API
    try {
      await crmAPI.opportunities.moveStage(dealId, newStageId);
    } catch (error) {
      console.error('Failed to move deal:', error);
      loadBoard(); // Reload on error
    }
  };

  const findDealById = (dealId) => {
    for (const stage of boardData?.stages || []) {
      const deal = stage.opportunities.find((o) => o.id === dealId);
      if (deal) return deal;
    }
    return null;
  };

  const handleAddDeal = (stageId) => {
    setSelectedStageId(stageId);
    setSelectedDeal(null);
    setShowDealModal(true);
  };

  const handleDealClick = (deal) => {
    setSelectedDeal(deal);
    setSelectedStageId(null);
    setShowDealModal(true);
  };

  const handleDealSaved = () => {
    setShowDealModal(false);
    loadBoard();
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  if (isLoading) {
    return <div className="loading">Loading pipeline...</div>;
  }

  return (
    <div className="pipeline-board">
      {/* Header */}
      <div className="board-header">
        <div className="header-left">
          <div className="pipeline-selector">
            <select
              value={selectedPipeline || ''}
              onChange={(e) => setSelectedPipeline(e.target.value)}
            >
              {pipelines.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>

        <div className="header-center">
          {boardData && (
            <div className="pipeline-stats">
              <div className="stat">
                <span className="stat-value">{boardData.totals.count}</span>
                <span className="stat-label">Deals</span>
              </div>
              <div className="stat">
                <span className="stat-value">{formatCurrency(boardData.totals.value)}</span>
                <span className="stat-label">Pipeline</span>
              </div>
              <div className="stat">
                <span className="stat-value">{formatCurrency(boardData.totals.weighted_value)}</span>
                <span className="stat-label">Weighted</span>
              </div>
            </div>
          )}
        </div>

        <div className="header-right">
          <button className="btn-icon" onClick={loadBoard}>
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="btn-icon">
            <Filter className="w-4 h-4" />
          </button>
          <button className="btn-primary" onClick={() => handleAddDeal(null)}>
            <Plus className="w-4 h-4" />
            New Deal
          </button>
        </div>
      </div>

      {/* Board */}
      <div className="board-container">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="stages-container">
            {boardData?.stages.map((stage) => (
              <StageColumn
                key={stage.id}
                stage={stage}
                opportunities={stage.opportunities || []}
                onAddDeal={handleAddDeal}
                onDealClick={handleDealClick}
              />
            ))}
          </div>

          <DragOverlay>
            {activeDeal ? <DealCard deal={activeDeal} /> : null}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Deal Modal */}
      {showDealModal && (
        <DealModal
          deal={selectedDeal}
          stageId={selectedStageId}
          pipelineId={selectedPipeline}
          onClose={() => setShowDealModal(false)}
          onSaved={handleDealSaved}
        />
      )}

      <style jsx>{`
        .pipeline-board {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--bg-primary);
        }

        .board-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          border-bottom: 1px solid var(--border-color);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .pipeline-selector {
          position: relative;
          display: flex;
          align-items: center;
        }

        .pipeline-selector select {
          appearance: none;
          padding: 8px 32px 8px 12px;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          background: transparent;
          cursor: pointer;
        }

        .pipeline-selector svg {
          position: absolute;
          right: 12px;
          pointer-events: none;
          color: var(--text-muted);
        }

        .header-center {
          flex: 1;
          display: flex;
          justify-content: center;
        }

        .pipeline-stats {
          display: flex;
          gap: 32px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-value {
          font-size: 18px;
          font-weight: 600;
        }

        .stat-label {
          font-size: 12px;
          color: var(--text-muted);
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .btn-icon {
          padding: 8px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          font-weight: 500;
        }

        .board-container {
          flex: 1;
          overflow-x: auto;
          padding: 16px;
        }

        .stages-container {
          display: flex;
          gap: 16px;
          height: 100%;
          min-height: 500px;
        }

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
