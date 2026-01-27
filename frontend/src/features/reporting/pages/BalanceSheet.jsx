/**
 * Balance Sheet Report Page
 */
import { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, RefreshCw, Calendar } from 'lucide-react';
import reportingAPI from '../services/reportingAPI';

export default function BalanceSheet() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [comparePrior, setComparePrior] = useState(false);
  const [showZero, setShowZero] = useState(false);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await reportingAPI.getBalanceSheet({
        asOfDate,
        comparePriorPeriod: comparePrior,
        showZeroBalances: showZero
      });
      setData(response.data);
    } catch (err) {
      setError('Failed to load balance sheet');
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
      const response = await reportingAPI.exportBalanceSheetExcel({
        asOfDate,
        comparePriorPeriod: comparePrior
      });
      reportingAPI.downloadBlob(response.data, `balance_sheet_${asOfDate}.xlsx`);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleExportPDF = async () => {
    try {
      const response = await reportingAPI.exportBalanceSheetPDF({
        asOfDate,
        comparePriorPeriod: comparePrior
      });
      reportingAPI.downloadBlob(response.data, `balance_sheet_${asOfDate}.pdf`);
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

  const renderLineItem = (line, showPrior = false) => (
    <tr key={line.code} className={line.bold ? 'font-semibold' : ''}>
      <td className={`py-2 ${line.indent_level > 0 ? `pl-${line.indent_level * 4}` : ''}`}>
        {line.label}
      </td>
      <td className={`py-2 text-right ${line.underline ? 'border-b' : ''} ${line.double_underline ? 'border-b-2' : ''}`}>
        {formatCurrency(line.current_period)}
      </td>
      {showPrior && line.prior_period !== null && (
        <>
          <td className="py-2 text-right">{formatCurrency(line.prior_period)}</td>
          <td className={`py-2 text-right ${line.variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(line.variance)}
          </td>
        </>
      )}
    </tr>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Balance Sheet</h1>
          <p className="text-gray-500">Statement of Financial Position</p>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">As of Date</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
                className="pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
          </div>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={comparePrior}
              onChange={(e) => setComparePrior(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Compare Prior Year</span>
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showZero}
              onChange={(e) => setShowZero(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Show Zero Balances</span>
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
            <h3 className="text-lg text-gray-600">Balance Sheet</h3>
            <p className="text-gray-500">
              As of {new Date(data.report_date).toLocaleDateString('en-US', { 
                year: 'numeric', month: 'long', day: 'numeric' 
              })}
            </p>
          </div>

          {/* Report Body */}
          <div className="p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2">
                  <th className="text-left py-2">Account</th>
                  <th className="text-right py-2">Current Period</th>
                  {comparePrior && data.prior_period_date && (
                    <>
                      <th className="text-right py-2">Prior Period</th>
                      <th className="text-right py-2">Variance</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {/* ASSETS */}
                <tr className="bg-gray-50">
                  <td colSpan={comparePrior ? 4 : 2} className="py-3 font-bold text-lg">ASSETS</td>
                </tr>
                
                <tr className="font-semibold">
                  <td className="py-2">Current Assets</td>
                  <td></td>
                </tr>
                {data.current_assets?.map(line => renderLineItem(line, comparePrior))}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Current Assets</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_current_assets)}</td>
                </tr>

                <tr><td colSpan={4} className="py-2"></td></tr>

                <tr className="font-semibold">
                  <td className="py-2">Non-Current Assets</td>
                  <td></td>
                </tr>
                {data.non_current_assets?.map(line => renderLineItem(line, comparePrior))}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Non-Current Assets</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_non_current_assets)}</td>
                </tr>

                <tr className="font-bold text-lg border-t-2">
                  <td className="py-3">TOTAL ASSETS</td>
                  <td className="py-3 text-right border-b-4 border-double">{formatCurrency(data.total_assets)}</td>
                </tr>

                <tr><td colSpan={4} className="py-4"></td></tr>

                {/* LIABILITIES */}
                <tr className="bg-gray-50">
                  <td colSpan={comparePrior ? 4 : 2} className="py-3 font-bold text-lg">LIABILITIES</td>
                </tr>

                <tr className="font-semibold">
                  <td className="py-2">Current Liabilities</td>
                  <td></td>
                </tr>
                {data.current_liabilities?.map(line => renderLineItem(line, comparePrior))}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Current Liabilities</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_current_liabilities)}</td>
                </tr>

                <tr><td colSpan={4} className="py-2"></td></tr>

                <tr className="font-semibold">
                  <td className="py-2">Non-Current Liabilities</td>
                  <td></td>
                </tr>
                {data.non_current_liabilities?.map(line => renderLineItem(line, comparePrior))}
                <tr className="font-semibold border-t">
                  <td className="py-2">Total Non-Current Liabilities</td>
                  <td className="py-2 text-right border-b">{formatCurrency(data.total_non_current_liabilities)}</td>
                </tr>

                <tr className="font-bold border-t">
                  <td className="py-3">TOTAL LIABILITIES</td>
                  <td className="py-3 text-right border-b">{formatCurrency(data.total_liabilities)}</td>
                </tr>

                <tr><td colSpan={4} className="py-4"></td></tr>

                {/* EQUITY */}
                <tr className="bg-gray-50">
                  <td colSpan={comparePrior ? 4 : 2} className="py-3 font-bold text-lg">EQUITY</td>
                </tr>
                {data.equity?.map(line => renderLineItem(line, comparePrior))}
                <tr className="font-bold border-t">
                  <td className="py-3">TOTAL EQUITY</td>
                  <td className="py-3 text-right border-b">{formatCurrency(data.total_equity)}</td>
                </tr>

                <tr><td colSpan={4} className="py-2"></td></tr>

                <tr className="font-bold text-lg border-t-2">
                  <td className="py-3">TOTAL LIABILITIES & EQUITY</td>
                  <td className="py-3 text-right border-b-4 border-double">{formatCurrency(data.total_liabilities_and_equity)}</td>
                </tr>
              </tbody>
            </table>

            {/* Balance Check */}
            <div className={`mt-4 p-3 rounded-lg text-center ${data.is_balanced ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {data.is_balanced ? '✓ Balance Sheet is balanced' : '⚠ Balance Sheet is out of balance'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
