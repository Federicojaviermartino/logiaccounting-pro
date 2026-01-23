/**
 * FilterBuilder - Configure report filters
 */

import React, { useState } from 'react';
import { Filter, Plus, Trash2, X } from 'lucide-react';
import { useReportDesigner } from '../context/ReportDesignerContext';

const OPERATORS = {
  string: [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'not_contains', label: 'Does Not Contain' },
    { value: 'starts_with', label: 'Starts With' },
    { value: 'ends_with', label: 'Ends With' },
    { value: 'in', label: 'In List' },
    { value: 'not_in', label: 'Not In List' },
    { value: 'is_null', label: 'Is Empty' },
    { value: 'is_not_null', label: 'Is Not Empty' },
  ],
  number: [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'gt', label: 'Greater Than' },
    { value: 'gte', label: 'Greater Than or Equal' },
    { value: 'lt', label: 'Less Than' },
    { value: 'lte', label: 'Less Than or Equal' },
    { value: 'between', label: 'Between' },
    { value: 'is_null', label: 'Is Empty' },
    { value: 'is_not_null', label: 'Is Not Empty' },
  ],
  date: [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'gt', label: 'After' },
    { value: 'gte', label: 'On or After' },
    { value: 'lt', label: 'Before' },
    { value: 'lte', label: 'On or Before' },
    { value: 'between', label: 'Between' },
    { value: 'is_null', label: 'Is Empty' },
    { value: 'is_not_null', label: 'Is Not Empty' },
  ],
};

const UNARY_OPERATORS = ['is_null', 'is_not_null'];
const RANGE_OPERATORS = ['between'];
const MULTI_VALUE_OPERATORS = ['in', 'not_in'];

export default function FilterBuilder() {
  const { state, actions } = useReportDesigner();
  const { query, dataSource } = state;

  // Get all available fields from selected tables
  const availableFields = dataSource.tables.flatMap(table =>
    table.fields.map(field => ({
      ...field,
      fullName: `${table.name}.${field.name}`,
      tableName: table.name,
    }))
  );

  const handleAddFilter = () => {
    actions.addFilter({
      field: availableFields[0]?.fullName || '',
      operator: 'eq',
      value: '',
      logic: 'AND',
    });
  };

  return (
    <div className="filter-builder">
      <div className="panel-header">
        <Filter className="w-5 h-5" />
        <span>Filters</span>
        <button className="add-btn" onClick={handleAddFilter}>
          <Plus className="w-4 h-4" />
        </button>
      </div>

      <div className="filters-list">
        {query.filters.length === 0 ? (
          <div className="empty-state">
            <p>No filters applied</p>
            <button onClick={handleAddFilter}>Add Filter</button>
          </div>
        ) : (
          query.filters.map((filter, index) => (
            <FilterRow
              key={filter.id}
              filter={filter}
              index={index}
              availableFields={availableFields}
              onUpdate={(updates) => actions.updateFilter({ ...filter, ...updates })}
              onRemove={() => actions.removeFilter(filter.id)}
            />
          ))
        )}
      </div>

      <style jsx>{`
        .filter-builder {
          background: var(--bg-secondary);
          border-radius: 8px;
          border: 1px solid var(--border-color);
        }

        .panel-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          font-weight: 600;
          border-bottom: 1px solid var(--border-color);
        }

        .add-btn {
          margin-left: auto;
          padding: 4px;
          border-radius: 4px;
          transition: background 0.2s;
        }

        .add-btn:hover {
          background: var(--bg-tertiary);
        }

        .filters-list {
          padding: 12px;
        }

        .empty-state {
          text-align: center;
          padding: 24px;
          color: var(--text-muted);
        }

        .empty-state button {
          margin-top: 12px;
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          font-size: 13px;
        }
      `}</style>
    </div>
  );
}

// Filter Row Component
function FilterRow({ filter, index, availableFields, onUpdate, onRemove }) {
  const selectedField = availableFields.find(f => f.fullName === filter.field);
  const fieldType = selectedField?.type || 'string';
  const operators = OPERATORS[fieldType] || OPERATORS.string;

  const isUnary = UNARY_OPERATORS.includes(filter.operator);
  const isRange = RANGE_OPERATORS.includes(filter.operator);
  const isMultiValue = MULTI_VALUE_OPERATORS.includes(filter.operator);

  return (
    <div className="filter-row">
      {/* Logic Connector */}
      {index > 0 && (
        <select
          className="logic-select"
          value={filter.logic}
          onChange={(e) => onUpdate({ logic: e.target.value })}
        >
          <option value="AND">AND</option>
          <option value="OR">OR</option>
        </select>
      )}

      <div className="filter-controls">
        {/* Field Select */}
        <select
          className="field-select"
          value={filter.field}
          onChange={(e) => onUpdate({ field: e.target.value, value: '' })}
        >
          <option value="">Select field...</option>
          {availableFields.map((field) => (
            <option key={field.fullName} value={field.fullName}>
              {field.label} ({field.tableName})
            </option>
          ))}
        </select>

        {/* Operator Select */}
        <select
          className="operator-select"
          value={filter.operator}
          onChange={(e) => onUpdate({ operator: e.target.value })}
        >
          {operators.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>

        {/* Value Input */}
        {!isUnary && (
          <FilterValueInput
            filter={filter}
            fieldType={fieldType}
            isRange={isRange}
            isMultiValue={isMultiValue}
            onUpdate={onUpdate}
          />
        )}

        {/* Remove Button */}
        <button className="remove-btn" onClick={onRemove}>
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <style jsx>{`
        .filter-row {
          margin-bottom: 12px;
        }

        .logic-select {
          display: block;
          width: 80px;
          padding: 4px 8px;
          margin-bottom: 8px;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          font-size: 11px;
          background: var(--bg-primary);
        }

        .filter-controls {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .field-select {
          flex: 1;
          padding: 8px 10px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
        }

        .operator-select {
          width: 160px;
          padding: 8px 10px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
        }

        .remove-btn {
          padding: 8px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .remove-btn:hover {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }
      `}</style>
    </div>
  );
}

// Filter Value Input
function FilterValueInput({ filter, fieldType, isRange, isMultiValue, onUpdate }) {
  if (isRange) {
    const [from, to] = Array.isArray(filter.value) ? filter.value : ['', ''];

    return (
      <div className="range-inputs">
        <input
          type={fieldType === 'date' ? 'date' : 'text'}
          placeholder="From"
          value={from}
          onChange={(e) => onUpdate({ value: [e.target.value, to] })}
        />
        <span>to</span>
        <input
          type={fieldType === 'date' ? 'date' : 'text'}
          placeholder="To"
          value={to}
          onChange={(e) => onUpdate({ value: [from, e.target.value] })}
        />

        <style jsx>{`
          .range-inputs {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
          }

          .range-inputs input {
            flex: 1;
            padding: 8px 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 13px;
          }

          .range-inputs span {
            color: var(--text-muted);
            font-size: 12px;
          }
        `}</style>
      </div>
    );
  }

  if (isMultiValue) {
    const values = Array.isArray(filter.value) ? filter.value : [];

    return (
      <div className="multi-value-input">
        <div className="tags">
          {values.map((val, idx) => (
            <span key={idx} className="tag">
              {val}
              <button
                onClick={() => {
                  const newValues = values.filter((_, i) => i !== idx);
                  onUpdate({ value: newValues });
                }}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
        <input
          type="text"
          placeholder="Add value and press Enter"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.target.value) {
              onUpdate({ value: [...values, e.target.value] });
              e.target.value = '';
            }
          }}
        />

        <style jsx>{`
          .multi-value-input {
            flex: 1;
            min-width: 200px;
          }

          .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 4px;
          }

          .tag {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            background: var(--primary-light);
            color: var(--primary);
            border-radius: 4px;
            font-size: 12px;
          }

          .tag button {
            display: flex;
            padding: 2px;
            border-radius: 2px;
          }

          .tag button:hover {
            background: rgba(0, 0, 0, 0.1);
          }

          .multi-value-input input {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 13px;
          }
        `}</style>
      </div>
    );
  }

  // Default single value input
  return (
    <input
      type={fieldType === 'date' ? 'date' : fieldType === 'number' ? 'number' : 'text'}
      className="value-input"
      placeholder="Value..."
      value={filter.value || ''}
      onChange={(e) => onUpdate({ value: e.target.value })}
      style={{
        flex: 1,
        padding: '8px 10px',
        border: '1px solid var(--border-color)',
        borderRadius: '6px',
        fontSize: '13px',
      }}
    />
  );
}
