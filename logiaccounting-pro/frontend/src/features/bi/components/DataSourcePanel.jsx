/**
 * DataSourcePanel - Select and configure data sources
 */

import React, { useState } from 'react';
import {
  Database,
  Table,
  Link,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Search,
} from 'lucide-react';
import { useReportDesigner } from '../context/ReportDesignerContext';

// Available data sources (internal tables)
const DATA_SOURCES = {
  invoices: {
    name: 'Invoices',
    icon: '📄',
    fields: [
      { name: 'id', type: 'string', label: 'Invoice ID' },
      { name: 'invoice_number', type: 'string', label: 'Invoice Number' },
      { name: 'client_id', type: 'string', label: 'Client ID' },
      { name: 'client_name', type: 'string', label: 'Client Name' },
      { name: 'status', type: 'string', label: 'Status' },
      { name: 'amount', type: 'number', label: 'Amount' },
      { name: 'tax_amount', type: 'number', label: 'Tax Amount' },
      { name: 'total', type: 'number', label: 'Total' },
      { name: 'currency', type: 'string', label: 'Currency' },
      { name: 'due_date', type: 'date', label: 'Due Date' },
      { name: 'issued_date', type: 'date', label: 'Issue Date' },
      { name: 'created_at', type: 'datetime', label: 'Created At' },
    ],
  },
  payments: {
    name: 'Payments',
    icon: '💰',
    fields: [
      { name: 'id', type: 'string', label: 'Payment ID' },
      { name: 'invoice_id', type: 'string', label: 'Invoice ID' },
      { name: 'amount', type: 'number', label: 'Amount' },
      { name: 'payment_method', type: 'string', label: 'Payment Method' },
      { name: 'status', type: 'string', label: 'Status' },
      { name: 'payment_date', type: 'date', label: 'Payment Date' },
      { name: 'reference', type: 'string', label: 'Reference' },
    ],
  },
  projects: {
    name: 'Projects',
    icon: '📁',
    fields: [
      { name: 'id', type: 'string', label: 'Project ID' },
      { name: 'name', type: 'string', label: 'Project Name' },
      { name: 'client_id', type: 'string', label: 'Client ID' },
      { name: 'status', type: 'string', label: 'Status' },
      { name: 'budget', type: 'number', label: 'Budget' },
      { name: 'spent', type: 'number', label: 'Spent' },
      { name: 'progress', type: 'number', label: 'Progress %' },
      { name: 'start_date', type: 'date', label: 'Start Date' },
      { name: 'end_date', type: 'date', label: 'End Date' },
    ],
  },
  transactions: {
    name: 'Transactions',
    icon: '📊',
    fields: [
      { name: 'id', type: 'string', label: 'Transaction ID' },
      { name: 'type', type: 'string', label: 'Type' },
      { name: 'category', type: 'string', label: 'Category' },
      { name: 'amount', type: 'number', label: 'Amount' },
      { name: 'description', type: 'string', label: 'Description' },
      { name: 'date', type: 'date', label: 'Date' },
      { name: 'project_id', type: 'string', label: 'Project ID' },
    ],
  },
  inventory: {
    name: 'Inventory',
    icon: '📦',
    fields: [
      { name: 'id', type: 'string', label: 'Item ID' },
      { name: 'sku', type: 'string', label: 'SKU' },
      { name: 'name', type: 'string', label: 'Name' },
      { name: 'category', type: 'string', label: 'Category' },
      { name: 'quantity', type: 'number', label: 'Quantity' },
      { name: 'min_stock', type: 'number', label: 'Min Stock' },
      { name: 'unit_cost', type: 'number', label: 'Unit Cost' },
      { name: 'unit_price', type: 'number', label: 'Unit Price' },
      { name: 'location', type: 'string', label: 'Location' },
    ],
  },
  clients: {
    name: 'Clients',
    icon: '👥',
    fields: [
      { name: 'id', type: 'string', label: 'Client ID' },
      { name: 'name', type: 'string', label: 'Name' },
      { name: 'email', type: 'string', label: 'Email' },
      { name: 'company', type: 'string', label: 'Company' },
      { name: 'phone', type: 'string', label: 'Phone' },
      { name: 'address', type: 'string', label: 'Address' },
      { name: 'created_at', type: 'datetime', label: 'Created At' },
    ],
  },
};

// Join suggestions based on common fields
const JOIN_SUGGESTIONS = {
  'invoices-payments': { left: 'id', right: 'invoice_id' },
  'invoices-clients': { left: 'client_id', right: 'id' },
  'projects-clients': { left: 'client_id', right: 'id' },
  'projects-transactions': { left: 'id', right: 'project_id' },
};

export default function DataSourcePanel() {
  const { state, actions } = useReportDesigner();
  const { dataSource } = state;

  const [searchTerm, setSearchTerm] = useState('');
  const [expandedTables, setExpandedTables] = useState({});
  const [showJoinModal, setShowJoinModal] = useState(false);

  // Filter data sources
  const filteredSources = Object.entries(DATA_SOURCES).filter(([key, source]) =>
    source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    source.fields.some(f => f.label.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  const handleAddTable = (tableName) => {
    if (!dataSource.tables.find(t => t.name === tableName)) {
      actions.addTable({
        name: tableName,
        alias: tableName.charAt(0),
        fields: DATA_SOURCES[tableName].fields,
      });
    }
  };

  const handleRemoveTable = (tableName) => {
    actions.removeTable(tableName);
  };

  const handleDragStart = (e, field, tableName) => {
    e.dataTransfer.setData('application/json', JSON.stringify({
      type: 'field',
      field: field.name,
      table: tableName,
      label: field.label,
      dataType: field.type,
    }));
  };

  return (
    <div className="data-source-panel">
      <div className="panel-header">
        <Database className="w-5 h-5" />
        <span>Data Sources</span>
      </div>

      {/* Search */}
      <div className="panel-search">
        <Search className="w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search tables & fields..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Selected Tables */}
      {dataSource.tables.length > 0 && (
        <div className="selected-tables">
          <div className="section-header">
            <span>Selected Tables</span>
            <button
              className="btn-icon"
              onClick={() => setShowJoinModal(true)}
              title="Add Join"
            >
              <Link className="w-4 h-4" />
            </button>
          </div>

          {dataSource.tables.map((table) => (
            <div key={table.name} className="selected-table">
              <div className="table-header" onClick={() => toggleTable(table.name)}>
                {expandedTables[table.name] ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
                <span className="table-icon">{DATA_SOURCES[table.name]?.icon}</span>
                <span className="table-name">{DATA_SOURCES[table.name]?.name}</span>
                <button
                  className="btn-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveTable(table.name);
                  }}
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>

              {expandedTables[table.name] && (
                <div className="table-fields">
                  {table.fields.map((field) => (
                    <div
                      key={field.name}
                      className="field-item"
                      draggable
                      onDragStart={(e) => handleDragStart(e, field, table.name)}
                    >
                      <span className={`field-type ${field.type}`}>
                        {field.type.charAt(0).toUpperCase()}
                      </span>
                      <span className="field-label">{field.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Joins */}
          {dataSource.joins.length > 0 && (
            <div className="joins-section">
              <div className="section-header">Joins</div>
              {dataSource.joins.map((join) => (
                <div key={join.id} className="join-item">
                  <Link className="w-3 h-3" />
                  <span>{join.leftTable}.{join.leftField}</span>
                  <span className="join-type">{join.type || 'INNER'}</span>
                  <span>{join.rightTable}.{join.rightField}</span>
                  <button
                    className="btn-remove"
                    onClick={() => actions.removeJoin(join.id)}
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Available Tables */}
      <div className="available-tables">
        <div className="section-header">Available Tables</div>

        {filteredSources.map(([key, source]) => {
          const isSelected = dataSource.tables.find(t => t.name === key);

          return (
            <div
              key={key}
              className={`table-item ${isSelected ? 'selected' : ''}`}
              onClick={() => !isSelected && handleAddTable(key)}
            >
              <span className="table-icon">{source.icon}</span>
              <span className="table-name">{source.name}</span>
              {!isSelected && <Plus className="w-4 h-4 add-icon" />}
            </div>
          );
        })}
      </div>

      {/* Join Modal */}
      {showJoinModal && (
        <JoinConfigModal
          tables={dataSource.tables}
          onClose={() => setShowJoinModal(false)}
          onSave={(join) => {
            actions.addJoin(join);
            setShowJoinModal(false);
          }}
        />
      )}

      <style jsx>{`
        .data-source-panel {
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

        .panel-search {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          border-bottom: 1px solid var(--border-color);
        }

        .panel-search input {
          flex: 1;
          border: none;
          background: transparent;
          outline: none;
          font-size: 13px;
        }

        .section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 16px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--text-muted);
        }

        .selected-tables {
          border-bottom: 1px solid var(--border-color);
        }

        .selected-table {
          border-bottom: 1px solid var(--border-color);
        }

        .table-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .table-header:hover {
          background: var(--bg-tertiary);
        }

        .table-icon {
          font-size: 14px;
        }

        .table-name {
          flex: 1;
          font-size: 13px;
        }

        .btn-remove {
          opacity: 0;
          padding: 4px;
          border-radius: 4px;
          transition: opacity 0.2s;
        }

        .table-header:hover .btn-remove,
        .join-item:hover .btn-remove {
          opacity: 1;
        }

        .btn-remove:hover {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .table-fields {
          padding: 0 16px 8px 32px;
        }

        .field-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 8px;
          border-radius: 4px;
          cursor: grab;
          transition: background 0.2s;
        }

        .field-item:hover {
          background: var(--bg-tertiary);
        }

        .field-type {
          width: 18px;
          height: 18px;
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

        .field-label {
          font-size: 12px;
        }

        .available-tables {
          flex: 1;
          overflow-y: auto;
        }

        .table-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .table-item:hover:not(.selected) {
          background: var(--bg-tertiary);
        }

        .table-item.selected {
          opacity: 0.5;
          cursor: default;
        }

        .add-icon {
          margin-left: auto;
          opacity: 0;
          transition: opacity 0.2s;
        }

        .table-item:hover .add-icon {
          opacity: 1;
        }

        .joins-section {
          padding: 8px 0;
        }

        .join-item {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 16px;
          font-size: 12px;
        }

        .join-type {
          padding: 2px 6px;
          background: var(--bg-tertiary);
          border-radius: 4px;
          font-size: 10px;
        }

        .btn-icon {
          padding: 4px;
          border-radius: 4px;
          transition: background 0.2s;
        }

        .btn-icon:hover {
          background: var(--bg-tertiary);
        }
      `}</style>
    </div>
  );
}

// Join Configuration Modal
function JoinConfigModal({ tables, onClose, onSave }) {
  const [leftTable, setLeftTable] = useState(tables[0]?.name || '');
  const [rightTable, setRightTable] = useState(tables[1]?.name || '');
  const [leftField, setLeftField] = useState('');
  const [rightField, setRightField] = useState('');
  const [joinType, setJoinType] = useState('inner');

  const leftFields = DATA_SOURCES[leftTable]?.fields || [];
  const rightFields = DATA_SOURCES[rightTable]?.fields || [];

  const handleSave = () => {
    if (leftTable && rightTable && leftField && rightField) {
      onSave({
        leftTable,
        rightTable,
        leftField,
        rightField,
        type: joinType,
      });
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Configure Join</h3>

        <div className="join-config">
          <div className="join-side">
            <label>Left Table</label>
            <select value={leftTable} onChange={(e) => setLeftTable(e.target.value)}>
              {tables.map((t) => (
                <option key={t.name} value={t.name}>
                  {DATA_SOURCES[t.name]?.name}
                </option>
              ))}
            </select>

            <label>Left Field</label>
            <select value={leftField} onChange={(e) => setLeftField(e.target.value)}>
              <option value="">Select field...</option>
              {leftFields.map((f) => (
                <option key={f.name} value={f.name}>{f.label}</option>
              ))}
            </select>
          </div>

          <div className="join-type">
            <select value={joinType} onChange={(e) => setJoinType(e.target.value)}>
              <option value="inner">INNER</option>
              <option value="left">LEFT</option>
              <option value="right">RIGHT</option>
            </select>
          </div>

          <div className="join-side">
            <label>Right Table</label>
            <select value={rightTable} onChange={(e) => setRightTable(e.target.value)}>
              {tables.map((t) => (
                <option key={t.name} value={t.name}>
                  {DATA_SOURCES[t.name]?.name}
                </option>
              ))}
            </select>

            <label>Right Field</label>
            <select value={rightField} onChange={(e) => setRightField(e.target.value)}>
              <option value="">Select field...</option>
              {rightFields.map((f) => (
                <option key={f.name} value={f.name}>{f.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>Add Join</button>
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: var(--bg-primary);
          border-radius: 12px;
          padding: 24px;
          width: 500px;
          max-width: 90vw;
        }

        h3 {
          margin: 0 0 20px;
        }

        .join-config {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .join-side {
          flex: 1;
        }

        .join-side label {
          display: block;
          font-size: 12px;
          font-weight: 500;
          margin-bottom: 4px;
          color: var(--text-muted);
        }

        .join-side select {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          margin-bottom: 12px;
        }

        .join-type select {
          padding: 6px 12px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 12px;
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 24px;
        }

        .btn-secondary {
          padding: 8px 16px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          background: transparent;
        }

        .btn-primary {
          padding: 8px 16px;
          background: var(--primary);
          color: white;
          border-radius: 6px;
          border: none;
        }
      `}</style>
    </div>
  );
}
