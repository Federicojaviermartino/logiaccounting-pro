import { lazy } from 'react';

const EmployeeList = lazy(() => import('./pages/EmployeeList'));
const PayrollRunList = lazy(() => import('./pages/PayrollRunList'));
const PayrollRunDetail = lazy(() => import('./pages/PayrollRunDetail'));

export const payrollRoutes = [
  {
    path: '/payroll/employees',
    element: <EmployeeList />,
  },
  {
    path: '/payroll/runs',
    element: <PayrollRunList />,
  },
  {
    path: '/payroll/runs/:id',
    element: <PayrollRunDetail />,
  },
];

export default payrollRoutes;
