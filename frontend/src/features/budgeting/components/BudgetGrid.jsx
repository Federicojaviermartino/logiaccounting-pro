import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import budgetingAPI from '../services/budgetingAPI';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const BudgetGrid = ({ versionId, lines, readOnly = false }) => {
  const queryClient = useQueryClient();
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [expandedLines, setExpandedLines] = useState(new Set());

  const updatePeriodMutation = useMutation({
    mutationFn: ({ periodId, amount }) => budgetingAPI.updatePeriod(periodId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries(['budgetLines', versionId]);
      setEditingCell(null);
    },
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const parseCurrency = (value) => {
    return parseFloat(value.replace(/[^0-9.-]/g, '')) || 0;
  };

  const handleCellClick = (lineId, periodId, currentValue) => {
    if (readOnly) return;
    setEditingCell({ lineId, periodId });
    setEditValue(currentValue.toString());
  };

  const handleCellBlur = () => {
    if (editingCell) {
      const amount = parseCurrency(editValue);
      updatePeriodMutation.mutate({ periodId: editingCell.periodId, amount });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleCellBlur();
    } else if (e.key === 'Escape') {
      setEditingCell(null);
    }
  };

  const toggleExpand = (lineId) => {
    setExpandedLines(prev => {
      const next = new Set(prev);
      if (next.has(lineId)) {
        next.delete(lineId);
      } else {
        next.add(lineId);
      }
      return next;
    });
  };

  // Group lines by account type
  const groupedLines = useMemo(() => {
    const groups = { revenue: [], expense: [] };
    lines.forEach(line => {
      if (line.account_type === 'revenue' || line.account_type === 'income') {
        groups.revenue.push(line);
      } else {
        groups.expense.push(line);
      }
    });
    return groups;
  }, [lines]);

  const renderLineRow = (line) => {
    const isExpanded = expandedLines.has(line.id);
    const periods = line.periods || [];

    return (
      <>
        <tr key={line.id} className="hover:bg-gray-50">
          <td className="px-4 py-2 border-r sticky left-0 bg-white">
            <div className="flex items-center">
              <button
                onClick={() => toggleExpand(line.id)}
                className="mr-2 text-gray-400 hover:text-gray-600"
              >
                {isExpanded ? '▼' : '▶'}
              </button>
              <div>
                <div className="font-medium text-sm">{line.account_code}</div>
                <div className="text-xs text-gray-500">{line.account_name}</div>
              </div>
            </div>
          </td>
          {MONTHS.map((_, monthIndex) => {
            const period = periods.find(p => p.period_month === monthIndex + 1);
            const isEditing = editingCell?.lineId === line.id && editingCell?.periodId === period?.id;

            return (
              <td
                key={monthIndex}
                className="px-2 py-2 text-right border-r cursor-pointer hover:bg-blue-50"
                onClick={() => period && handleCellClick(line.id, period.id, period.budgeted_amount)}
              >
                {isEditing ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={handleCellBlur}
                    onKeyDown={handleKeyDown}
                    className="w-full text-right border rounded px-1 py-0.5 text-sm"
                    autoFocus
                  />
                ) : (
                  <span className="text-sm">
                    {period ? formatCurrency(period.budgeted_amount) : '-'}
                  </span>
                )}
              </td>
            );
          })}
          <td className="px-4 py-2 text-right font-medium bg-gray-50">
            {formatCurrency(line.annual_amount)}
          </td>
        </tr>
        {isExpanded && (
          <tr className="bg-gray-50">
            <td colSpan={14} className="px-8 py-2 text-sm text-gray-600">
              <div className="flex gap-6">
                <span>YTD Actual: {formatCurrency(line.ytd_actual)}</span>
                <span>YTD Variance: {formatCurrency(line.ytd_variance)}</span>
                <span>Distribution: {line.distribution_method}</span>
              </div>
            </td>
          </tr>
        )}
      </>
    );
  };

  const renderSection = (title, sectionLines, colorClass) => {
    const total = sectionLines.reduce((sum, line) => sum + parseFloat(line.annual_amount || 0), 0);

    return (
      <>
        <tr className={`${colorClass} font-semibold`}>
          <td className="px-4 py-2 border-r sticky left-0" style={{ backgroundColor: 'inherit' }}>
            {title}
          </td>
          {MONTHS.map((_, i) => (
            <td key={i} className="px-2 py-2 border-r"></td>
          ))}
          <td className="px-4 py-2 text-right">{formatCurrency(total)}</td>
        </tr>
        {sectionLines.map(renderLineRow)}
      </>
    );
  };

  if (lines.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No budget lines yet</p>
        {!readOnly && (
          <button className="mt-2 text-blue-600 hover:text-blue-800">
            + Add budget line
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase border-r sticky left-0 bg-gray-100 min-w-[200px]">
              Account
            </th>
            {MONTHS.map(month => (
              <th key={month} className="px-2 py-3 text-right text-xs font-medium text-gray-500 uppercase border-r min-w-[80px]">
                {month}
              </th>
            ))}
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase min-w-[100px]">
              Total
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {renderSection('Revenue', groupedLines.revenue, 'bg-green-50')}
          {renderSection('Expenses', groupedLines.expense, 'bg-red-50')}
          <tr className="bg-blue-100 font-bold">
            <td className="px-4 py-3 border-r sticky left-0 bg-blue-100">
              Net Income
            </td>
            {MONTHS.map((_, i) => (
              <td key={i} className="px-2 py-3 border-r"></td>
            ))}
            <td className="px-4 py-3 text-right">
              {formatCurrency(
                groupedLines.revenue.reduce((s, l) => s + parseFloat(l.annual_amount || 0), 0) -
                groupedLines.expense.reduce((s, l) => s + parseFloat(l.annual_amount || 0), 0)
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default BudgetGrid;
