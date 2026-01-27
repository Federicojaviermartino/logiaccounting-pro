/**
 * Income Statement (P&L) Report Page
 */
import { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, RefreshCw, Calendar } from 'lucide-react';
import reportingAPI from '../services/reportingAPI';

export default function IncomeStatement() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  
  const [startDate, setStartDate] = useState(firstDay.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0]);
  const [comparePrior, setComparePrior] = useState(false);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await reportingAPI.getIncomeStatement({
        startDate,
        endDate,
        comparePriorPeriod: comparePrior
      });
      setData(response.data);
    } catch (err) {
      setError('Failed to load income statement');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  const handleExportExcel = async () => {
    try {
      const response = await reportingAPI.exportIncomeStatementExcel({
        startDate,
        endDate,
        comparePriorPeriod: comparePrior
      });
      reportingAPI.downloadBlob(response.data, `income_statement_${startDate}_${endDate}.xlsx`);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleExportPDF = async () => {
    try {
      const response = await reportingAPI.exportIncomeStatementPDF({
        startDate,
        endDate,
        comparePriorPeriod: comparePrior
      });
      reportingAPI.downloadBlob(response.data, `income_statement_${startDate}_${endDate}.pdf`);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '';
    return `${Number(value).toFixed(1)}%`;
  };

  const renderLineItem = (line) => (
    <tr key={line.code} className={line.bold ? 'font-semibold' : ''}>
      <td className={`py-2 pl-${(line.indent_level || 0) * 4 + 4}`}>
        {line.label}
      </td>
      <td className={`py-2 text-right ${line.underline ? 'border-b' : ''}`}>
        {formatCurrency(line.current_period)}
      </td>
      <td className="py-2 text-right text-gray-500 text-sm"></td>
    </tr>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Income Statement</h1>
          <p className="text-gray-500">Profit & Loss Statement</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportExcel}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            <FileSpreadsheet size={16} />
            Excel
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            <FileText size={16} />
            PDF
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            />
          </div>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={comparePrior}
              onChange={(e) => setComparePrior(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Compare Prior Period</span>
          </label>

          <button
            onClick={loadReport}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Generate
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg">{error}</div>
      )}

      {data && (
        <div className="bg-white rounded-lg shadow">
          {/* Report Header */}
          <div className="p-6 border-b text-center">
            <h2 className="text-xl font-bold">{data.company_name}</h2>
            <h3 className="text-lg text-gray-600">Income Statement</h3>
            <p className="text-gray-500">
              {new Date(data.period_start).toLocaleDateString()} - {new Date(data.period_end).toLocaleDateString()}
            </p>
          </div>

          {/* Report Body */}
          <div className="p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2">
                  <th className="text-left py-2">Account</th>
                  <th className="text-right py-2">Amount</th>
                  <th className="text-right py-2 text-sm">% of Revenue</th>
                </tr>
              </thead>
              <tbody>
                {/* Revenue */}
                <tr className="bg-gray-50">
                  <td colSpan={3} className="py-3 font-bold text-lg">REVENUE</td>
                </tr>
                {data.revenue?.map(renderLineItem)}
                <tr className="font-bold border-t">
                  <td className="py-2">Total Revenue</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_revenue)}</td>
                  <td className="py-2 text-right text-gray-500">100.0%</td>
                </tr>

                <tr><td colSpan={3} className="py-3"></td></tr>

                {/* Cost of Sales */}
                <tr className="bg-gray-50">
                  <td colSpan={3} className="py-3 font-bold text-lg">COST OF SALES</td>
                </tr>
                {data.cost_of_sales?.map(renderLineItem)}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Cost of Sales</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_cost_of_sales)}</td>
                  <td></td>
                </tr>

                <tr><td colSpan={3} className="py-3"></td></tr>

                {/* Gross Profit */}
                <tr className="font-bold text-lg bg-blue-50">
                  <td className="py-3">GROSS PROFIT</td>
                  <td className="py-3 text-right">{formatCurrency(data.gross_profit)}</td>
                  <td className="py-3 text-right text-blue-600">{formatPercent(data.gross_margin_percent)}</td>
                </tr>

                <tr><td colSpan={3} className="py-3"></td></tr>

                {/* Operating Expenses */}
                <tr className="bg-gray-50">
                  <td colSpan={3} className="py-3 font-bold text-lg">OPERATING EXPENSES</td>
                </tr>
                {data.operating_expenses?.map(renderLineItem)}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Operating Expenses</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_operating_expenses)}</td>
                  <td></td>
                </tr>

                <tr><td colSpan={3} className="py-3"></td></tr>

                {/* Operating Income */}
                <tr className="font-bold text-lg bg-blue-50">
                  <td className="py-3">OPERATING INCOME</td>
                  <td className="py-3 text-right">{formatCurrency(data.operating_income)}</td>
                  <td className="py-3 text-right text-blue-600">{formatPercent(data.operating_margin_percent)}</td>
                </tr>

                <tr><td colSpan={3} className="py-3"></td></tr>

                {/* Net Income */}
                <tr className={`font-bold text-xl ${Number(data.net_income) >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <td className="py-4">NET INCOME</td>
                  <td className={`py-4 text-right border-b-4 border-double ${Number(data.net_income) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(data.net_income)}
                  </td>
                  <td className={`py-4 text-right ${Number(data.net_income) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(data.net_margin_percent)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
