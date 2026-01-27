/**
 * DataTable - Tabular data display with sorting and pagination
 */

import React, { useState, useMemo } from 'react';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Search,
} from 'lucide-react';

export default function DataTable({
  title,
  columns,
  data,
  pageSize = 10,
  showSearch = true,
  showPagination = true,
  showExport = true,
  onRowClick,
  isLoading,
  error,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [currentPage, setCurrentPage] = useState(1);

  // Filter data
  const filteredData = useMemo(() => {
    if (!searchTerm) return data || [];

    return (data || []).filter(row =>
      columns.some(col =>
        String(row[col.key] || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm, columns]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const comparison = String(aVal).localeCompare(String(bVal));
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortConfig]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleExport = () => {
    const csv = [
      columns.map(c => c.label).join(','),
      ...sortedData.map(row =>
        columns.map(c => `"${String(row[c.key] || '').replace(/"/g, '""')}"`).join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${title || 'data'}.csv`;
    link.click();
  };

  return (
    <div className="data-table">
      {/* Header */}
      <div className="table-header">
        {title && <h3 className="table-title">{title}</h3>}

        <div className="table-actions">
          {showSearch && (
            <div className="search-box">
              <Search className="w-4 h-4" />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
          )}

          {showExport && (
            <button className="action-btn" onClick={handleExport}>
              <Download className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="table-loading">
            <div className="spinner" />
            <span>Loading...</span>
          </div>
        ) : error ? (
          <div className="table-error">{error}</div>
        ) : (
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={column.sortable !== false ? 'sortable' : ''}
                    onClick={() => column.sortable !== false && handleSort(column.key)}
                    style={{
                      width: column.width,
                      textAlign: column.align || 'left',
                    }}
                  >
                    <div className="th-content">
                      <span>{column.label}</span>
                      {column.sortable !== false && (
                        <span className="sort-icon">
                          {sortConfig.key === column.key ? (
                            sortConfig.direction === 'asc' ? (
                              <ArrowUp className="w-4 h-4" />
                            ) : (
                              <ArrowDown className="w-4 h-4" />
                            )
                          ) : (
                            <ArrowUpDown className="w-4 h-4 opacity-30" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="empty-row">
                    No data available
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, rowIndex) => (
                  <tr
                    key={row.id || rowIndex}
                    className={onRowClick ? 'clickable' : ''}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        style={{ textAlign: column.align || 'left' }}
                      >
                        {column.render
                          ? column.render(row[column.key], row)
                          : formatCellValue(row[column.key], column.format)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="table-pagination">
          <div className="pagination-info">
            Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length}
          </div>

          <div className="pagination-controls">
            <button
              className="page-btn"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => p - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  className={`page-num ${currentPage === pageNum ? 'active' : ''}`}
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              className="page-btn"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(p => p + 1)}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .data-table {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
        }

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .table-title {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .table-actions {
          display: flex;
          gap: 12px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-secondary);
          border-radius: 8px;
          border: 1px solid var(--border-color);
        }

        .search-box input {
          border: none;
          background: transparent;
          outline: none;
          font-size: 13px;
          width: 150px;
        }

        .action-btn {
          padding: 8px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .table-container {
          overflow-x: auto;
          min-height: 200px;
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th, td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-color);
        }

        th {
          background: var(--bg-secondary);
          font-weight: 600;
          font-size: 12px;
          text-transform: uppercase;
          color: var(--text-muted);
          letter-spacing: 0.5px;
        }

        th.sortable {
          cursor: pointer;
          user-select: none;
        }

        th.sortable:hover {
          background: var(--bg-tertiary);
        }

        .th-content {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .sort-icon {
          display: flex;
        }

        td {
          font-size: 13px;
        }

        tr.clickable {
          cursor: pointer;
        }

        tbody tr:hover {
          background: var(--bg-secondary);
        }

        .empty-row {
          text-align: center;
          color: var(--text-muted);
          padding: 40px 16px;
        }

        .table-loading,
        .table-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
          min-height: 200px;
          color: var(--text-muted);
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 3px solid var(--border-color);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .table-pagination {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 20px;
          border-top: 1px solid var(--border-color);
        }

        .pagination-info {
          font-size: 13px;
          color: var(--text-muted);
        }

        .pagination-controls {
          display: flex;
          gap: 4px;
        }

        .page-btn,
        .page-num {
          padding: 6px 10px;
          border-radius: 6px;
          font-size: 13px;
          color: var(--text-secondary);
          transition: all 0.2s;
        }

        .page-btn:hover:not(:disabled),
        .page-num:hover {
          background: var(--bg-secondary);
        }

        .page-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .page-num.active {
          background: var(--primary);
          color: white;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

function formatCellValue(value, format) {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value);
    case 'percent':
      return `${Number(value).toFixed(1)}%`;
    case 'date':
      return new Date(value).toLocaleDateString();
    case 'datetime':
      return new Date(value).toLocaleString();
    default:
      return String(value);
  }
}
