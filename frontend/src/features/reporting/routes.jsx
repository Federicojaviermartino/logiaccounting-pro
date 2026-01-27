/**
 * Reporting module routes
 */
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import BalanceSheet from './pages/BalanceSheet';
import IncomeStatement from './pages/IncomeStatement';

export const reportingRoutes = [
  {
    path: '/reporting/dashboard',
    element: <ExecutiveDashboard />,
    title: 'Executive Dashboard'
  },
  {
    path: '/reporting/balance-sheet',
    element: <BalanceSheet />,
    title: 'Balance Sheet'
  },
  {
    path: '/reporting/income-statement',
    element: <IncomeStatement />,
    title: 'Income Statement'
  }
];
