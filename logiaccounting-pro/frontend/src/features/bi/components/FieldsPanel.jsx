/**
 * FieldsPanel - Select and configure report fields
 */

import React, { useState } from 'react';
import {
  Columns,
  GripVertical,
  Settings,
  Trash2,
  ChevronDown,
  Calculator,
  Filter,
  ArrowUpDown,
} from 'lucide-react';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useReportDesigner } from '../context/ReportDesignerContext';

const AGGREGATIONS = [
  { value: '', label: 'None' },
  { value: 'sum', label: 'Sum' },
  { value: 'avg', label: 'Average' },
  { value: 'count', label: 'Count' },
  { value: 'count_distinct', label: 'Count Distinct' },
  { value: 'min', label: 'Minimum' },
  { value: 'max', label: 'Maximum' },
];

export default function FieldsPanel() {
  const { state, actions } = useReportDesigner();
  const { query, dataSource } = state;

  const [editingFieldId, setEditingFieldId] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  );

  const handleDrop = (e) => {
    e.preventDefault();

    try {
      const data = JSON.parse(e.dataTransfer.getData('application/json'));

      if (data.type === 'field') {
        actions.addField({
          field: `${data.table}.${data.field}`,
          alias: data.label,
          label: data.label,
          table: data.table,
          dataType: data.dataType,
          aggregation: null,
          format: null,
        });
      }
    } catch (err) {
      console.error('Drop error:', err);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = query.fields.findIndex(f => f.id === active.id);
      const newIndex = query.fields.findIndex(f => f.id === over.id);

      const newFields = arrayMove(query.fields, oldIndex, newIndex);
      // Update state with reordered fields
      actions.setQuery({ ...query, fields: newFields });
    }
  };

  return (
    <div className="fields-panel">
      <div className="panel-header">
        <Columns className="w-5 h-5" />
        <span>Report Fields</span>
      </div>

      {/* Selected Fields */}
      <div
        className="selected-fields"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {query.fields.length === 0 ? (
          <div className="empty-state">
            <p>Drag fields here to add them to your report</p>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={query.fields.map(f => f.id)}
              strategy={verticalListSortingStrategy}
            >
              {query.fields.map((field) => (
                <SortableFieldItem
                  key={field.id}
                  field={field}
                  isEditing={editingFieldId === field.id}
                  onEdit={() => setEditingFieldId(field.id)}
                  onClose={() => setEditingFieldId(null)}
                  onUpdate={(updates) => actions.updateField({ ...field, ...updates })}
                  onRemove={() => actions.removeField(field.id)}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {/* Add Calculated Field */}
      <div className="panel-actions">
        <button
          className="add-calculated-btn"
          onClick={() => {
            actions.addField({
              field: 'calculated',
              alias: 'Calculated Field',
              label: 'Calculated Field',
              isCalculated: true,
              formula: '',
              dataType: 'number',
            });
          }}
        >
          <Calculator className="w-4 h-4" />
          Add Calculated Field
        </button>
      </div>

      <style jsx>{`
        .fields-panel {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-color);
        }

        .panel-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 16px;
          font-weight: 600;
          border-bottom: 1px solid var(--border-color);
        }

        .selected-fields {
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          min-height: 200px;
        }

        .empty-state {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          padding: 24px;
          text-align: center;
          color: var(--text-muted);
          font-size: 13px;
          border: 2px dashed var(--border-color);
          border-radius: 8px;
        }

        .panel-actions {
          padding: 12px;
          border-top: 1px solid var(--border-color);
        }

        .add-calculated-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 10px 16px;
          border: 1px dashed var(--border-color);
          border-radius: 8px;
          background: transparent;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s;
        }

        .add-calculated-btn:hover {
          border-color: var(--primary);
          color: var(--primary);
        }
      `}</style>
    </div>
  );
}

// Sortable Field Item
function SortableFieldItem({ field, isEditing, onEdit, onClose, onUpdate, onRemove }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: field.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="field-item">
      <div className="field-row">
        <button className="drag-handle" {...attributes} {...listeners}>
          <GripVertical className="w-4 h-4" />
        </button>

        <span className={`field-type ${field.dataType}`}>
          {field.dataType?.charAt(0).toUpperCase()}
        </span>

        <div className="field-info">
          <span className="field-label">{field.alias || field.label}</span>
          {field.aggregation && (
            <span className="field-agg">{field.aggregation.toUpperCase()}</span>
          )}
        </div>

        <button className="btn-icon" onClick={onEdit}>
          <Settings className="w-4 h-4" />
        </button>

        <button className="btn-icon btn-remove" onClick={onRemove}>
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Expanded Settings */}
      {isEditing && (
        <FieldSettings
          field={field}
          onUpdate={onUpdate}
          onClose={onClose}
        />
      )}

      <style jsx>{`
        .field-item {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          margin-bottom: 8px;
        }

        .field-row {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
        }

        .drag-handle {
          cursor: grab;
          color: var(--text-muted);
        }

        .drag-handle:active {
          cursor: grabbing;
        }

        .field-type {
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 600;
          border-radius: 4px;
          background: var(--primary-light);
          color: var(--primary);
        }

        .field-type.number {
          background: #dbeafe;
          color: #2563eb;
        }

        .field-type.date, .field-type.datetime {
          background: #fef3c7;
          color: #d97706;
        }

        .field-info {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .field-label {
          font-size: 13px;
        }

        .field-agg {
          font-size: 10px;
          padding: 2px 6px;
          background: var(--bg-tertiary);
          border-radius: 4px;
          color: var(--text-muted);
        }

        .btn-icon {
          padding: 4px;
          border-radius: 4px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .btn-remove:hover {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }
      `}</style>
    </div>
  );
}

// Field Settings Component
function FieldSettings({ field, onUpdate, onClose }) {
  const [alias, setAlias] = useState(field.alias || '');
  const [aggregation, setAggregation] = useState(field.aggregation || '');
  const [format, setFormat] = useState(field.format || '');

  const handleSave = () => {
    onUpdate({ alias, aggregation, format });
    onClose();
  };

  return (
    <div className="field-settings">
      <div className="setting-row">
        <label>Display Name</label>
        <input
          type="text"
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
          placeholder="Field alias..."
        />
      </div>

      {field.dataType === 'number' && (
        <>
          <div className="setting-row">
            <label>Aggregation</label>
            <select
              value={aggregation}
              onChange={(e) => setAggregation(e.target.value)}
            >
              {AGGREGATIONS.map((agg) => (
                <option key={agg.value} value={agg.value}>
                  {agg.label}
                </option>
              ))}
            </select>
          </div>

          <div className="setting-row">
            <label>Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
            >
              <option value="">Default</option>
              <option value="currency">Currency ($1,234.56)</option>
              <option value="percent">Percentage (12.34%)</option>
              <option value="decimal">Decimal (1,234.56)</option>
              <option value="integer">Integer (1,234)</option>
            </select>
          </div>
        </>
      )}

      {(field.dataType === 'date' || field.dataType === 'datetime') && (
        <div className="setting-row">
          <label>Date Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
          >
            <option value="">Default</option>
            <option value="MM/DD/YYYY">MM/DD/YYYY</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            <option value="MMM D, YYYY">Jan 1, 2024</option>
          </select>
        </div>
      )}

      {field.isCalculated && (
        <div className="setting-row">
          <label>Formula</label>
          <textarea
            value={field.formula}
            onChange={(e) => onUpdate({ formula: e.target.value })}
            placeholder="e.g., [Amount] * [Quantity]"
            rows={3}
          />
        </div>
      )}

      <div className="setting-actions">
        <button className="btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn-primary" onClick={handleSave}>Apply</button>
      </div>

      <style jsx>{`
        .field-settings {
          padding: 12px;
          border-top: 1px solid var(--border-color);
          background: var(--bg-secondary);
        }

        .setting-row {
          margin-bottom: 12px;
        }

        .setting-row label {
          display: block;
          font-size: 11px;
          font-weight: 500;
          color: var(--text-muted);
          margin-bottom: 4px;
        }

        .setting-row input,
        .setting-row select,
        .setting-row textarea {
          width: 100%;
          padding: 8px 10px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
        }

        .setting-row textarea {
          resize: vertical;
          font-family: monospace;
        }

        .setting-actions {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          margin-top: 16px;
        }

        .btn-secondary {
          padding: 6px 12px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          background: transparent;
          font-size: 13px;
        }

        .btn-primary {
          padding: 6px 12px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          border: none;
          font-size: 13px;
        }
      `}</style>
    </div>
  );
}
