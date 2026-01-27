/**
 * ComponentPalette - Draggable component library
 */

import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import {
  BarChart2,
  LineChart,
  PieChart,
  Table,
  Hash,
  Type,
  Image,
  Square,
} from 'lucide-react';

const COMPONENT_TYPES = [
  {
    type: 'chart',
    subtype: 'bar',
    label: 'Bar Chart',
    icon: BarChart2,
    description: 'Vertical or horizontal bar chart',
  },
  {
    type: 'chart',
    subtype: 'line',
    label: 'Line Chart',
    icon: LineChart,
    description: 'Trend visualization over time',
  },
  {
    type: 'chart',
    subtype: 'pie',
    label: 'Pie Chart',
    icon: PieChart,
    description: 'Part-of-whole visualization',
  },
  {
    type: 'table',
    label: 'Data Table',
    icon: Table,
    description: 'Tabular data with sorting',
  },
  {
    type: 'kpi',
    label: 'KPI Card',
    icon: Hash,
    description: 'Single metric display',
  },
  {
    type: 'text',
    label: 'Text Block',
    icon: Type,
    description: 'Static text or title',
  },
  {
    type: 'image',
    label: 'Image',
    icon: Image,
    description: 'Logo or static image',
  },
  {
    type: 'shape',
    label: 'Shape',
    icon: Square,
    description: 'Decorative shape',
  },
];

export default function ComponentPalette() {
  return (
    <div className="component-palette">
      <div className="palette-header">
        <span>Components</span>
      </div>

      <div className="palette-items">
        {COMPONENT_TYPES.map((item) => (
          <DraggablePaletteItem key={item.type + (item.subtype || '')} item={item} />
        ))}
      </div>

      <style jsx>{`
        .component-palette {
          width: 200px;
          background: var(--bg-primary);
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
        }

        .palette-header {
          padding: 12px 16px;
          font-weight: 600;
          font-size: 13px;
          border-bottom: 1px solid var(--border-color);
        }

        .palette-items {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
      `}</style>
    </div>
  );
}

function DraggablePaletteItem({ item }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `palette-${item.type}-${item.subtype || ''}`,
    data: {
      fromPalette: true,
      type: item.type,
      subtype: item.subtype,
    },
  });

  const Icon = item.icon;

  return (
    <div
      ref={setNodeRef}
      className={`palette-item ${isDragging ? 'dragging' : ''}`}
      {...attributes}
      {...listeners}
    >
      <div className="item-icon">
        <Icon className="w-5 h-5" />
      </div>
      <div className="item-info">
        <span className="item-label">{item.label}</span>
        <span className="item-desc">{item.description}</span>
      </div>

      <style jsx>{`
        .palette-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          cursor: grab;
          transition: all 0.2s;
        }

        .palette-item:hover {
          border-color: var(--primary);
          background: var(--primary-light);
        }

        .palette-item.dragging {
          opacity: 0.5;
        }

        .item-icon {
          padding: 8px;
          background: var(--bg-primary);
          border-radius: 6px;
          color: var(--primary);
        }

        .item-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .item-label {
          font-size: 13px;
          font-weight: 500;
        }

        .item-desc {
          font-size: 11px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
