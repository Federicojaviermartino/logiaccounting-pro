import { lazy } from 'react';

const BudgetList = lazy(() => import('./pages/BudgetList'));
const BudgetDetail = lazy(() => import('./pages/BudgetDetail'));
const BudgetForm = lazy(() => import('./pages/BudgetForm'));
const VarianceAnalysis = lazy(() => import('./pages/VarianceAnalysis'));

export const budgetingRoutes = [
  {
    path: '/budgeting',
    element: <BudgetList />,
  },
  {
    path: '/budgeting/new',
    element: <BudgetForm />,
  },
  {
    path: '/budgeting/:id',
    element: <BudgetDetail />,
  },
  {
    path: '/budgeting/:id/edit',
    element: <BudgetForm />,
  },
  {
    path: '/budgeting/:budgetId/variance',
    element: <VarianceAnalysis />,
  },
];

export default budgetingRoutes;
