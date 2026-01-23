/**
 * ReportComponent - Draggable/resizable report component wrapper
 */

import React, { useState, useRef } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Trash2, Move, Settings } from 'lucide-react';

import { LineChart, BarChart, PieChart, KPICard, DataTable } from './charts';

export default function ReportComponent({
  component,
  isSelected,
  zoom,
  onClick,
  onResize,
  onDelete,
}) {
  const [isResizing, setIsResizing] = useState(false);
  const [resizeHandle, setResizeHandle] = useState(null);
  const startPosRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: component.id,
  });

  const style = {
    position: 'absolute',
    left: component.position.x * (zoom / 100),
    top: component.position.y * (zoom / 100),
    width: component.position.width * (zoom / 100),
    height: component.position.height * (zoom / 100),
    transform: CSS.Translate.toString(transform),
    zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
    opacity: isDragging ? 0.8 : 1,
  };

  const handleResizeStart = (e, handle) => {
    e.stopPropagation();
    setIsResizing(true);
    setResizeHandle(handle);
    startPosRef.current = {
      x: e.clientX,
      y: e.clientY,
      width: component.position.width,
      height: component.position.height,
    };

    document.addEventListener('mousemove', handleResizeMove);
    document.addEventListener('mouseup', handleResizeEnd);
  };

  const handleResizeMove = (e) => {
    if (!isResizing) return;

    const dx = (e.clientX - startPosRef.current.x) / (zoom / 100);
    const dy = (e.clientY - startPosRef.current.y) / (zoom / 100);

    let newWidth = startPosRef.current.width;
    let newHeight = startPosRef.current.height;

    if (resizeHandle.includes('e')) newWidth += dx;
    if (resizeHandle.includes('w')) newWidth -= dx;
    if (resizeHandle.includes('s')) newHeight += dy;
    if (resizeHandle.includes('n')) newHeight -= dy;

    onResize({
      width: Math.max(100, newWidth),
      height: Math.max(50, newHeight),
    });
  };

  const handleResizeEnd = () => {
    setIsResizing(false);
    setResizeHandle(null);
    document.removeEventListener('mousemove', handleResizeMove);
    document.removeEventListener('mouseup', handleResizeEnd);
  };

  const renderComponentContent = () => {
    switch (component.type) {
      case 'chart':
        return renderChart();
      case 'kpi':
        return (
          <KPICard
            title={component.config.title || 'KPI'}
            value={component.dataBinding?.value || 0}
            format={component.config.format}
          />
        );
      case 'table':
        return (
          <DataTable
            title={component.config.title}
            columns={component.dataBinding?.columns || []}
            data={component.dataBinding?.data || []}
            pageSize={component.config.pageSize}
          />
        );
      case 'text':
        return (
          <div
            className="text-component"
            style={{ fontSize: component.config.fontSize }}
          >
            {component.config.content}
          </div>
        );
      default:
        return <div>Unknown component type</div>;
    }
  };

  const renderChart = () => {
    const chartType = component.config.chartType || 'bar';
    const props = {
      title: component.config.title,
      data: component.dataBinding?.data,
      config: component.config,
    };

    switch (chartType) {
      case 'line':
        return <LineChart {...props} />;
      case 'bar':
        return <BarChart {...props} />;
      case 'pie':
      case 'donut':
        return <PieChart {...props} config={{ ...props.config, donut: chartType === 'donut' }} />;
      default:
        return <BarChart {...props} />;
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`report-component ${isSelected ? 'selected' : ''} ${isDragging ? 'dragging' : ''}`}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
    >
      {/* Drag Handle */}
      <div className="drag-handle" {...attributes} {...listeners}>
        <Move className="w-4 h-4" />
      </div>

      {/* Component Content */}
      <div className="component-content">
        {renderComponentContent()}
      </div>

      {/* Selection Overlay */}
      {isSelected && (
        <>
          <div className="selection-border" />

          {/* Action Buttons */}
          <div className="component-actions">
            <button className="action-btn" title="Settings">
              <Settings className="w-3 h-3" />
            </button>
            <button
              className="action-btn delete"
              title="Delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>

          {/* Resize Handles */}
          <div
            className="resize-handle nw"
            onMouseDown={(e) => handleResizeStart(e, 'nw')}
          />
          <div
            className="resize-handle ne"
            onMouseDown={(e) => handleResizeStart(e, 'ne')}
          />
          <div
            className="resize-handle sw"
            onMouseDown={(e) => handleResizeStart(e, 'sw')}
          />
          <div
            className="resize-handle se"
            onMouseDown={(e) => handleResizeStart(e, 'se')}
          />
          <div
            className="resize-handle n"
            onMouseDown={(e) => handleResizeStart(e, 'n')}
          />
          <div
            className="resize-handle s"
            onMouseDown={(e) => handleResizeStart(e, 's')}
          />
          <div
            className="resize-handle e"
            onMouseDown={(e) => handleResizeStart(e, 'e')}
          />
          <div
            className="resize-handle w"
            onMouseDown={(e) => handleResizeStart(e, 'w')}
          />
        </>
      )}

      <style jsx>{`
        .report-component {
          background: white;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          overflow: hidden;
          cursor: pointer;
        }

        .report-component.selected {
          cursor: default;
        }

        .report-component.dragging {
          cursor: grabbing;
        }

        .drag-handle {
          position: absolute;
          top: 4px;
          left: 4px;
          padding: 4px;
          background: rgba(255, 255, 255, 0.9);
          border-radius: 4px;
          cursor: grab;
          opacity: 0;
          transition: opacity 0.2s;
          z-index: 10;
        }

        .report-component:hover .drag-handle,
        .report-component.selected .drag-handle {
          opacity: 1;
        }

        .drag-handle:active {
          cursor: grabbing;
        }

        .component-content {
          width: 100%;
          height: 100%;
          overflow: hidden;
        }

        .selection-border {
          position: absolute;
          inset: -2px;
          border: 2px solid var(--primary);
          border-radius: 10px;
          pointer-events: none;
        }

        .component-actions {
          position: absolute;
          top: -32px;
          right: 0;
          display: flex;
          gap: 4px;
          background: white;
          padding: 4px;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        .action-btn {
          padding: 6px;
          border-radius: 4px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .action-btn.delete:hover {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .resize-handle {
          position: absolute;
          width: 10px;
          height: 10px;
          background: var(--primary);
          border: 2px solid white;
          border-radius: 50%;
          z-index: 20;
        }

        .resize-handle.nw { top: -5px; left: -5px; cursor: nwse-resize; }
        .resize-handle.ne { top: -5px; right: -5px; cursor: nesw-resize; }
        .resize-handle.sw { bottom: -5px; left: -5px; cursor: nesw-resize; }
        .resize-handle.se { bottom: -5px; right: -5px; cursor: nwse-resize; }
        .resize-handle.n { top: -5px; left: 50%; transform: translateX(-50%); cursor: ns-resize; }
        .resize-handle.s { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: ns-resize; }
        .resize-handle.e { top: 50%; right: -5px; transform: translateY(-50%); cursor: ew-resize; }
        .resize-handle.w { top: 50%; left: -5px; transform: translateY(-50%); cursor: ew-resize; }

        .text-component {
          padding: 12px;
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  );
}
