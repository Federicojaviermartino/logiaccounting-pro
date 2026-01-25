import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Download, Printer, Calendar, ArrowRight } from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';
import StatementViewer from '../components/StatementViewer';

const STATEMENT_TYPES = [
  { id: 'balance-sheet', name: 'Balance Sheet', description: 'Financial position at a point in time' },
  { id: 'income-statement', name: 'Income Statement', description: 'Revenue and expenses over a period' },
  { id: 'cash-flow', name: 'Cash Flow Statement', description: 'Cash movements over a period' },
];

export default function FinancialStatements() {
  const [selectedStatement, setSelectedStatement] = useState('balance-sheet');
  const [dateParams, setDateParams] = useState({
    asOfDate: new Date().toISOString().split('T')[0],
    startDate: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    comparativeDate: '',
  });

  const { data: balanceSheet, isLoading: bsLoading } = useQuery({
    queryKey: ['balanceSheet', dateParams.asOfDate, dateParams.comparativeDate],
    queryFn: () =>
      accountingAPI.getBalanceSheet({
        asOfDate: dateParams.asOfDate,
        comparativeDate: dateParams.comparativeDate || undefined,
      }),
    enabled: selectedStatement === 'balance-sheet',
  });

  const { data: incomeStatement, isLoading: isLoading } = useQuery({
    queryKey: ['incomeStatement', dateParams.startDate, dateParams.endDate],
    queryFn: () =>
      accountingAPI.getIncomeStatement({
        startDate: dateParams.startDate,
        endDate: dateParams.endDate,
      }),
    enabled: selectedStatement === 'income-statement',
  });

  const { data: cashFlow, isLoading: cfLoading } = useQuery({
    queryKey: ['cashFlow', dateParams.startDate, dateParams.endDate],
    queryFn: () =>
      accountingAPI.getCashFlow({
        startDate: dateParams.startDate,
        endDate: dateParams.endDate,
      }),
    enabled: selectedStatement === 'cash-flow',
  });

  const loading = bsLoading || isLoading || cfLoading;
  const currentData =
    selectedStatement === 'balance-sheet'
      ? balanceSheet
      : selectedStatement === 'income-statement'
      ? incomeStatement
      : cashFlow;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Financial Statements
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Generate and view financial reports
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <Printer className="w-4 h-4" />
                Print
              </button>
              <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <Download className="w-4 h-4" />
                Export PDF
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                Select Statement
              </h3>

              <div className="space-y-2">
                {STATEMENT_TYPES.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setSelectedStatement(type.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedStatement === type.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className={`w-5 h-5 ${
                        selectedStatement === type.id
                          ? 'text-blue-600'
                          : 'text-gray-400'
                      }`} />
                      <div>
                        <p className={`text-sm font-medium ${
                          selectedStatement === type.id
                            ? 'text-blue-600'
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {type.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {type.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
                  Date Parameters
                </h3>

                {selectedStatement === 'balance-sheet' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
                        As of Date
                      </label>
                      <input
                        type="date"
                        value={dateParams.asOfDate}
                        onChange={(e) =>
                          setDateParams({ ...dateParams, asOfDate: e.target.value })
                        }
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
                        Comparative Date (optional)
                      </label>
                      <input
                        type="date"
                        value={dateParams.comparativeDate}
                        onChange={(e) =>
                          setDateParams({ ...dateParams, comparativeDate: e.target.value })
                        }
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={dateParams.startDate}
                        onChange={(e) =>
                          setDateParams({ ...dateParams, startDate: e.target.value })
                        }
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={dateParams.endDate}
                        onChange={(e) =>
                          setDateParams({ ...dateParams, endDate: e.target.value })
                        }
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="col-span-9">
            {loading ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : currentData ? (
              <StatementViewer
                type={selectedStatement}
                data={currentData}
              />
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Select date parameters and click generate to view statement
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
