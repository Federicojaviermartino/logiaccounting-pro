/**
 * PivotTable - Interactive pivot table for data analysis
 */

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, Settings, Download } from 'lucide-react';

export default function PivotTable({
  title,
  data,
  rows,
  columns,
  values,
  aggregation = 'sum',
  showTotals = true,
  showSubtotals = true,
  onConfigChange,
}) {
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [showConfig, setShowConfig] = useState(false);

  // Aggregate data into pivot structure
  const pivotData = useMemo(() => {
    return aggregatePivotData(data, rows, columns, values, aggregation);
  }, [data, rows, columns, values, aggregation]);

  // Get unique column values
  const columnValues = useMemo(() => {
    return getUniqueValues(data, columns);
  }, [data, columns]);

  const toggleRow = (rowKey) => {
    setExpandedRows(prev => {
      const next = new Set(prev);
      if (next.has(rowKey)) {
        next.delete(rowKey);
      } else {
        next.add(rowKey);
      }
      return next;
    });
  };

  return (
    <div className="pivot-table">
      {/* Header */}
      <div className="pivot-header">
        {title && <h3 className="pivot-title">{title}</h3>}
        <div className="pivot-actions">
          <button className="action-btn" onClick={() => setShowConfig(!showConfig)}>
            <Settings className="w-4 h-4" />
          </button>
          <button className="action-btn" onClick={() => exportPivot(pivotData, columnValues)}>
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <PivotConfig
          rows={rows}
          columns={columns}
          values={values}
          aggregation={aggregation}
          availableFields={getAvailableFields(data)}
          onConfigChange={onConfigChange}
        />
      )}

      {/* Table */}
      <div className="pivot-container">
        <table>
          <thead>
            <tr>
              {/* Row headers */}
              {rows.map((row, i) => (
                <th key={`row-${i}`} className="row-header">
                  {row.label}
                </th>
              ))}

              {/* Column headers */}
              {columns.length > 0 ? (
                columnValues.flat().map((colValue, i) => (
                  <th key={`col-${i}`} className="value-header">
                    {colValue}
                  </th>
                ))
              ) : (
                values.map((val, i) => (
                  <th key={`val-${i}`} className="value-header">
                    {val.label}
                  </th>
                ))
              )}

              {/* Totals column */}
              {showTotals && <th className="total-header">Total</th>}
            </tr>
          </thead>

          <tbody>
            {renderPivotRows(pivotData, rows, columnValues, values, 0, expandedRows, toggleRow, showTotals)}

            {/* Grand Total Row */}
            {showTotals && (
              <tr className="grand-total-row">
                <td colSpan={rows.length} className="grand-total-label">
                  Grand Total
                </td>
                {columns.length > 0 ? (
                  columnValues.flat().map((_, i) => (
                    <td key={i} className="grand-total-value">
                      {formatValue(calculateColumnTotal(pivotData, i))}
                    </td>
                  ))
                ) : (
                  values.map((_, i) => (
                    <td key={i} className="grand-total-value">
                      {formatValue(calculateValueTotal(pivotData, i))}
                    </td>
                  ))
                )}
                <td className="grand-total-value">
                  {formatValue(calculateGrandTotal(pivotData))}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <style jsx>{`
        .pivot-table {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
        }

        .pivot-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .pivot-title {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .pivot-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          padding: 6px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .pivot-container {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th, td {
          padding: 10px 14px;
          border: 1px solid var(--border-color);
          font-size: 13px;
        }

        th {
          background: var(--bg-secondary);
          font-weight: 600;
          text-align: center;
        }

        .row-header {
          text-align: left;
        }

        .value-header {
          min-width: 100px;
        }

        .total-header {
          background: var(--bg-tertiary);
          font-weight: 700;
        }

        td {
          text-align: right;
        }

        .row-label {
          text-align: left;
          font-weight: 500;
        }

        .row-label.expandable {
          cursor: pointer;
        }

        .row-label.expandable:hover {
          background: var(--bg-secondary);
        }

        .expand-icon {
          display: inline-flex;
          margin-right: 8px;
        }

        .subtotal-row td {
          background: var(--bg-secondary);
          font-weight: 600;
        }

        .grand-total-row td {
          background: var(--bg-tertiary);
          font-weight: 700;
        }

        .level-1 { padding-left: 24px; }
        .level-2 { padding-left: 40px; }
        .level-3 { padding-left: 56px; }
      `}</style>
    </div>
  );
}

// Helper functions
function aggregatePivotData(data, rows, columns, values, aggregation) {
  if (!data || !Array.isArray(data)) return {};

  const result = {};

  data.forEach(item => {
    const rowKey = rows.map(r => item[r.field]).join('|');
    const colKey = columns.map(c => item[c.field]).join('|');

    if (!result[rowKey]) {
      result[rowKey] = { label: rows.map(r => item[r.field]), values: {}, total: 0 };
    }

    if (!result[rowKey].values[colKey]) {
      result[rowKey].values[colKey] = [];
    }

    values.forEach((v, i) => {
      const value = parseFloat(item[v.field]) || 0;
      if (!result[rowKey].values[colKey][i]) {
        result[rowKey].values[colKey][i] = [];
      }
      result[rowKey].values[colKey][i].push(value);
    });
  });

  // Apply aggregation
  Object.keys(result).forEach(rowKey => {
    let rowTotal = 0;
    Object.keys(result[rowKey].values).forEach(colKey => {
      result[rowKey].values[colKey] = result[rowKey].values[colKey].map(vals => {
        const aggregated = aggregate(vals, aggregation);
        rowTotal += aggregated;
        return aggregated;
      });
    });
    result[rowKey].total = rowTotal;
  });

  return result;
}

function aggregate(values, type) {
  if (!values || values.length === 0) return 0;

  switch (type) {
    case 'sum':
      return values.reduce((a, b) => a + b, 0);
    case 'avg':
      return values.reduce((a, b) => a + b, 0) / values.length;
    case 'count':
      return values.length;
    case 'min':
      return Math.min(...values);
    case 'max':
      return Math.max(...values);
    default:
      return values.reduce((a, b) => a + b, 0);
  }
}

function getUniqueValues(data, columns) {
  if (!data || !Array.isArray(data)) return [];

  const values = {};
  columns.forEach((col, i) => {
    values[i] = [...new Set(data.map(item => item[col.field]))].sort();
  });
  return columns.length > 0 ? values[0] : [];
}

function getAvailableFields(data) {
  if (!data || data.length === 0) return [];
  return Object.keys(data[0]).map(key => ({ field: key, label: key }));
}

function formatValue(value) {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

function renderPivotRows(pivotData, rows, columnValues, values, level, expandedRows, toggleRow, showTotals) {
  // Simplified row rendering
  return Object.entries(pivotData).map(([key, row]) => (
    <tr key={key}>
      <td className={`row-label level-${level}`}>
        {row.label.join(' - ')}
      </td>
      {Object.values(row.values).flat().map((val, i) => (
        <td key={i}>{formatValue(val)}</td>
      ))}
      {showTotals && <td className="row-total">{formatValue(row.total)}</td>}
    </tr>
  ));
}

function calculateColumnTotal(pivotData, colIndex) {
  return Object.values(pivotData).reduce((sum, row) => {
    const colValues = Object.values(row.values).flat();
    return sum + (colValues[colIndex] || 0);
  }, 0);
}

function calculateValueTotal(pivotData, valueIndex) {
  return Object.values(pivotData).reduce((sum, row) => {
    return sum + Object.values(row.values).reduce((s, vals) => s + (vals[valueIndex] || 0), 0);
  }, 0);
}

function calculateGrandTotal(pivotData) {
  return Object.values(pivotData).reduce((sum, row) => sum + row.total, 0);
}

function PivotConfig({ rows, columns, values, aggregation, availableFields, onConfigChange }) {
  return (
    <div className="pivot-config">
      <div className="config-section">
        <h4>Rows</h4>
        <select multiple>
          {availableFields.map(f => (
            <option key={f.field} value={f.field}>{f.label}</option>
          ))}
        </select>
      </div>
      <div className="config-section">
        <h4>Columns</h4>
        <select multiple>
          {availableFields.map(f => (
            <option key={f.field} value={f.field}>{f.label}</option>
          ))}
        </select>
      </div>
      <div className="config-section">
        <h4>Values</h4>
        <select multiple>
          {availableFields.map(f => (
            <option key={f.field} value={f.field}>{f.label}</option>
          ))}
        </select>
      </div>
      <div className="config-section">
        <h4>Aggregation</h4>
        <select value={aggregation} onChange={(e) => onConfigChange?.({ aggregation: e.target.value })}>
          <option value="sum">Sum</option>
          <option value="avg">Average</option>
          <option value="count">Count</option>
          <option value="min">Minimum</option>
          <option value="max">Maximum</option>
        </select>
      </div>

      <style jsx>{`
        .pivot-config {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          padding: 16px 20px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .config-section h4 {
          margin: 0 0 8px;
          font-size: 12px;
          color: var(--text-muted);
        }

        .config-section select {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
        }
      `}</style>
    </div>
  );
}

function exportPivot(pivotData, columnValues) {
  console.log('Export pivot data:', pivotData);
}
