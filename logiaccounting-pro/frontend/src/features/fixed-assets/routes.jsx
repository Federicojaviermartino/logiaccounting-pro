/**
 * Fixed Assets module routes.
 */
import { lazy } from 'react';
import { Navigate } from 'react-router-dom';

// Lazy load pages
const AssetRegister = lazy(() => import('./pages/AssetRegister'));
const DepreciationRun = lazy(() => import('./pages/DepreciationRun'));

// Placeholder components for future pages
const AssetDetail = () => <div className="p-6">Asset Detail - Coming Soon</div>;
const AssetForm = () => <div className="p-6">Asset Form - Coming Soon</div>;
const AssetCategories = () => <div className="p-6">Asset Categories - Coming Soon</div>;
const DepreciationSchedule = () => <div className="p-6">Depreciation Schedule - Coming Soon</div>;
const AssetMovements = () => <div className="p-6">Asset Movements - Coming Soon</div>;
const AssetDisposal = () => <div className="p-6">Asset Disposal - Coming Soon</div>;
const AssetReports = () => <div className="p-6">Asset Reports - Coming Soon</div>;
const AssetImport = () => <div className="p-6">Asset Import - Coming Soon</div>;

export const fixedAssetsRoutes = [
  {
    path: 'fixed-assets',
    children: [
      { index: true, element: <Navigate to="register" replace /> },

      // Asset Register
      { path: 'register', element: <AssetRegister /> },
      { path: 'new', element: <AssetForm /> },
      { path: ':id', element: <AssetDetail /> },
      { path: ':id/edit', element: <AssetForm /> },
      { path: 'import', element: <AssetImport /> },

      // Categories
      { path: 'categories', element: <AssetCategories /> },

      // Depreciation
      { path: 'depreciation', element: <DepreciationRun /> },
      { path: 'depreciation/schedule', element: <DepreciationSchedule /> },

      // Movements & Disposals
      { path: 'movements', element: <AssetMovements /> },
      { path: 'disposal', element: <AssetDisposal /> },
      { path: 'disposal/new', element: <AssetDisposal /> },

      // Reports
      { path: 'reports', element: <AssetReports /> },
    ],
  },
];

export default fixedAssetsRoutes;
