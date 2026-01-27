/**
 * ReportCanvas - Visual report design surface
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  DndContext,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
  rectIntersection,
} from '@dnd-kit/core';
import { restrictToParentElement } from '@dnd-kit/modifiers';
import { ZoomIn, ZoomOut, Grid, Eye, Undo, Redo, Save } from 'lucide-react';

import { useReportDesigner } from '../context/ReportDesignerContext';
import ReportComponent from './ReportComponent';
import ComponentPalette from './ComponentPalette';
import PropertyPanel from './PropertyPanel';

const PAGE_SIZES = {
  a4: { width: 794, height: 1123 },
  letter: { width: 816, height: 1056 },
  legal: { width: 816, height: 1344 },
};

export default function ReportCanvas() {
  const { state, actions } = useReportDesigner();
  const { layout, designer, history } = state;

  const canvasRef = useRef(null);
  const [activeId, setActiveId] = useState(null);
  const [draggedItem, setDraggedItem] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  );

  const pageSize = PAGE_SIZES[layout.pageSize] || PAGE_SIZES.a4;
  const isLandscape = layout.orientation === 'landscape';
  const canvasWidth = isLandscape ? pageSize.height : pageSize.width;
  const canvasHeight = isLandscape ? pageSize.width : pageSize.height;

  const handleDragStart = (event) => {
    const { active } = event;
    setActiveId(active.id);

    // Check if dragging from palette (new component)
    if (active.data.current?.fromPalette) {
      setDraggedItem({
        type: active.data.current.type,
        isNew: true,
      });
    } else {
      // Dragging existing component
      const component = layout.components.find(c => c.id === active.id);
      setDraggedItem(component);
    }
  };

  const handleDragEnd = (event) => {
    const { active, over, delta } = event;

    if (active.data.current?.fromPalette && over) {
      // Adding new component from palette
      const type = active.data.current.type;
      const rect = canvasRef.current?.getBoundingClientRect();

      if (rect) {
        const x = Math.max(0, (event.activatorEvent.clientX - rect.left) / (designer.zoom / 100));
        const y = Math.max(0, (event.activatorEvent.clientY - rect.top) / (designer.zoom / 100));

        actions.addComponent({
          type,
          position: { x, y, width: getDefaultWidth(type), height: getDefaultHeight(type) },
          config: getDefaultConfig(type),
          dataBinding: {},
        });
      }
    } else if (delta && activeId) {
      // Moving existing component
      const component = layout.components.find(c => c.id === activeId);
      if (component) {
        const newX = Math.max(0, component.position.x + delta.x / (designer.zoom / 100));
        const newY = Math.max(0, component.position.y + delta.y / (designer.zoom / 100));

        actions.moveComponent(activeId, {
          ...component.position,
          x: designer.snapToGrid ? Math.round(newX / designer.gridSize) * designer.gridSize : newX,
          y: designer.snapToGrid ? Math.round(newY / designer.gridSize) * designer.gridSize : newY,
        });
      }
    }

    setActiveId(null);
    setDraggedItem(null);
  };

  const handleComponentClick = (componentId) => {
    actions.selectComponent(componentId);
  };

  const handleCanvasClick = (e) => {
    if (e.target === e.currentTarget || e.target.classList.contains('canvas-page')) {
      actions.selectComponent(null);
    }
  };

  const handleZoom = (delta) => {
    const newZoom = Math.max(25, Math.min(200, designer.zoom + delta));
    actions.setDesigner({ zoom: newZoom });
  };

  return (
    <div className="report-canvas-container">
      {/* Toolbar */}
      <div className="canvas-toolbar">
        <div className="toolbar-group">
          <button
            className="toolbar-btn"
            onClick={actions.undo}
            disabled={history.past.length === 0}
            title="Undo (Ctrl+Z)"
          >
            <Undo className="w-4 h-4" />
          </button>
          <button
            className="toolbar-btn"
            onClick={actions.redo}
            disabled={history.future.length === 0}
            title="Redo (Ctrl+Y)"
          >
            <Redo className="w-4 h-4" />
          </button>
        </div>

        <div className="toolbar-divider" />

        <div className="toolbar-group">
          <button
            className="toolbar-btn"
            onClick={() => handleZoom(-10)}
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="zoom-label">{designer.zoom}%</span>
          <button
            className="toolbar-btn"
            onClick={() => handleZoom(10)}
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>

        <div className="toolbar-divider" />

        <div className="toolbar-group">
          <button
            className={`toolbar-btn ${designer.showGrid ? 'active' : ''}`}
            onClick={() => actions.setDesigner({ showGrid: !designer.showGrid })}
            title="Toggle Grid"
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            className="toolbar-btn"
            title="Preview Report"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>

        <div className="toolbar-spacer" />

        <button className="save-btn">
          <Save className="w-4 h-4" />
          Save Report
        </button>
      </div>

      {/* Canvas Area */}
      <div className="canvas-wrapper">
        <ComponentPalette />

        <DndContext
          sensors={sensors}
          collisionDetection={rectIntersection}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          modifiers={[restrictToParentElement]}
        >
          <div
            className="canvas-scroll"
            onClick={handleCanvasClick}
          >
            <div
              ref={canvasRef}
              className="canvas-page"
              style={{
                width: canvasWidth * (designer.zoom / 100),
                height: canvasHeight * (designer.zoom / 100),
                backgroundSize: designer.showGrid
                  ? `${designer.gridSize * (designer.zoom / 100)}px ${designer.gridSize * (designer.zoom / 100)}px`
                  : 'none',
              }}
            >
              {/* Components */}
              {layout.components.map((component) => (
                <ReportComponent
                  key={component.id}
                  component={component}
                  isSelected={designer.selectedComponentId === component.id}
                  zoom={designer.zoom}
                  onClick={() => handleComponentClick(component.id)}
                  onResize={(size) => actions.updateComponent({ id: component.id, position: { ...component.position, ...size } })}
                  onDelete={() => actions.removeComponent(component.id)}
                />
              ))}
            </div>
          </div>

          <DragOverlay>
            {draggedItem && (
              <div className="drag-preview">
                {draggedItem.isNew ? draggedItem.type : 'Moving...'}
              </div>
            )}
          </DragOverlay>
        </DndContext>

        <PropertyPanel />
      </div>

      <style jsx>{`
        .report-canvas-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--bg-secondary);
        }

        .canvas-toolbar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--bg-primary);
          border-bottom: 1px solid var(--border-color);
        }

        .toolbar-group {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .toolbar-btn {
          padding: 8px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .toolbar-btn:hover:not(:disabled) {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .toolbar-btn:disabled {
          opacity: 0.4;
        }

        .toolbar-btn.active {
          background: var(--primary-light);
          color: var(--primary);
        }

        .toolbar-divider {
          width: 1px;
          height: 24px;
          background: var(--border-color);
          margin: 0 8px;
        }

        .zoom-label {
          min-width: 48px;
          text-align: center;
          font-size: 13px;
          color: var(--text-secondary);
        }

        .toolbar-spacer {
          flex: 1;
        }

        .save-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          font-weight: 500;
          transition: background 0.2s;
        }

        .save-btn:hover {
          background: var(--primary-dark);
        }

        .canvas-wrapper {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        .canvas-scroll {
          flex: 1;
          overflow: auto;
          padding: 40px;
          display: flex;
          justify-content: center;
        }

        .canvas-page {
          background: white;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          position: relative;
          background-image:
            linear-gradient(to right, #f0f0f0 1px, transparent 1px),
            linear-gradient(to bottom, #f0f0f0 1px, transparent 1px);
        }

        .drag-preview {
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          font-size: 13px;
          opacity: 0.8;
        }
      `}</style>
    </div>
  );
}

// Helper functions
function getDefaultWidth(type) {
  switch (type) {
    case 'kpi': return 200;
    case 'table': return 600;
    case 'chart': return 400;
    case 'text': return 300;
    default: return 200;
  }
}

function getDefaultHeight(type) {
  switch (type) {
    case 'kpi': return 120;
    case 'table': return 300;
    case 'chart': return 300;
    case 'text': return 100;
    default: return 100;
  }
}

function getDefaultConfig(type) {
  switch (type) {
    case 'chart':
      return { chartType: 'bar', showLegend: true };
    case 'table':
      return { pageSize: 10, showSearch: false };
    case 'kpi':
      return { format: 'number', showTrend: true };
    case 'text':
      return { content: 'Enter text...', fontSize: 14 };
    default:
      return {};
  }
}
