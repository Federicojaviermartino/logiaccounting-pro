import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Critical pages - loaded immediately
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Layout from './components/Layout';

// PWA Components
import PWAInstallBanner from './components/PWAInstallBanner';
import OfflineIndicator from './components/OfflineIndicator';

// Lazy-loaded pages - code split for better performance
const Inventory = lazy(() => import('./pages/Inventory'));
const Projects = lazy(() => import('./pages/Projects'));
const Movements = lazy(() => import('./pages/Movements'));
const Transactions = lazy(() => import('./pages/Transactions'));
const Payments = lazy(() => import('./pages/Payments'));
const Users = lazy(() => import('./pages/Users'));
const Reports = lazy(() => import('./pages/Reports'));

// AI-Powered Pages - lazy loaded due to larger bundle size
const AIDashboard = lazy(() => import('./pages/AIDashboard'));
const InvoiceOCR = lazy(() => import('./pages/InvoiceOCR'));
const Assistant = lazy(() => import('./pages/Assistant'));

// Admin Pages
const Settings = lazy(() => import('./pages/Settings'));
const ActivityLog = lazy(() => import('./pages/ActivityLog'));
const BulkOperations = lazy(() => import('./pages/BulkOperations'));
const ReportBuilder = lazy(() => import('./pages/ReportBuilder'));
const BackupRestore = lazy(() => import('./pages/BackupRestore'));
const Webhooks = lazy(() => import('./pages/Webhooks'));
const HelpCenter = lazy(() => import('./pages/HelpCenter'));

// Phase 5 - Enterprise Features
const Approvals = lazy(() => import('./pages/Approvals'));
const RecurringItems = lazy(() => import('./pages/RecurringItems'));
const Budgets = lazy(() => import('./pages/Budgets'));
const APIKeys = lazy(() => import('./pages/APIKeys'));

// Phase 6 - Ultimate Enterprise Features
const DashboardBuilder = lazy(() => import('./pages/DashboardBuilder'));
const BankReconciliation = lazy(() => import('./pages/BankReconciliation'));
const ScheduledReports = lazy(() => import('./pages/ScheduledReports'));
const CurrencySettings = lazy(() => import('./pages/CurrencySettings'));

// Portal Pages
const ClientDashboard = lazy(() => import('./pages/portal/ClientDashboard'));
const ClientProjects = lazy(() => import('./pages/portal/ClientProjects'));
const ClientPayments = lazy(() => import('./pages/portal/ClientPayments'));
const SupplierDashboard = lazy(() => import('./pages/portal/SupplierDashboard'));
const SupplierOrders = lazy(() => import('./pages/portal/SupplierOrders'));
const SupplierPayments = lazy(() => import('./pages/portal/SupplierPayments'));

// Loading fallback component
function PageLoader() {
  return (
    <div className="page-loader">
      <div className="loading-spinner"></div>
      <p>Loading...</p>
    </div>
  );
}

function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

// Wrapper for lazy loaded routes
function LazyRoute({ children, roles }) {
  return (
    <PrivateRoute roles={roles}>
      <Layout>
        <Suspense fallback={<PageLoader />}>
          {children}
        </Suspense>
      </Layout>
    </PrivateRoute>
  );
}

function App() {
  return (
    <>
      <OfflineIndicator />
      <PWAInstallBanner />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        <Route path="/dashboard" element={
          <PrivateRoute>
            <Layout><Dashboard /></Layout>
          </PrivateRoute>
        } />

        <Route path="/inventory" element={
          <LazyRoute roles={['admin', 'supplier']}>
            <Inventory />
          </LazyRoute>
        } />

        <Route path="/projects" element={
          <LazyRoute roles={['admin', 'client']}>
            <Projects />
          </LazyRoute>
        } />

        <Route path="/movements" element={
          <LazyRoute roles={['admin', 'supplier']}>
            <Movements />
          </LazyRoute>
        } />

        <Route path="/transactions" element={
          <LazyRoute>
            <Transactions />
          </LazyRoute>
        } />

        <Route path="/payments" element={
          <LazyRoute>
            <Payments />
          </LazyRoute>
        } />

        <Route path="/users" element={
          <LazyRoute roles={['admin']}>
            <Users />
          </LazyRoute>
        } />

        <Route path="/reports" element={
          <LazyRoute roles={['admin']}>
            <Reports />
          </LazyRoute>
        } />

        {/* AI-Powered Routes */}
        <Route path="/ai-dashboard" element={
          <LazyRoute roles={['admin']}>
            <AIDashboard />
          </LazyRoute>
        } />

        <Route path="/invoice-ocr" element={
          <LazyRoute roles={['admin', 'supplier']}>
            <InvoiceOCR />
          </LazyRoute>
        } />

        <Route path="/assistant" element={
          <LazyRoute roles={['admin']}>
            <Assistant />
          </LazyRoute>
        } />

        <Route path="/settings" element={
          <LazyRoute>
            <Settings />
          </LazyRoute>
        } />

        {/* Admin Tools */}
        <Route path="/activity-log" element={
          <LazyRoute roles={['admin']}>
            <ActivityLog />
          </LazyRoute>
        } />

        <Route path="/bulk-operations" element={
          <LazyRoute roles={['admin']}>
            <BulkOperations />
          </LazyRoute>
        } />

        <Route path="/report-builder" element={
          <LazyRoute roles={['admin']}>
            <ReportBuilder />
          </LazyRoute>
        } />

        <Route path="/backup" element={
          <LazyRoute roles={['admin']}>
            <BackupRestore />
          </LazyRoute>
        } />

        <Route path="/webhooks" element={
          <LazyRoute roles={['admin']}>
            <Webhooks />
          </LazyRoute>
        } />

        <Route path="/help" element={
          <LazyRoute>
            <HelpCenter />
          </LazyRoute>
        } />

        {/* Phase 5 - Enterprise Features Routes */}
        <Route path="/approvals" element={
          <LazyRoute roles={['admin', 'manager']}>
            <Approvals />
          </LazyRoute>
        } />

        <Route path="/recurring" element={
          <LazyRoute roles={['admin']}>
            <RecurringItems />
          </LazyRoute>
        } />

        <Route path="/budgets" element={
          <LazyRoute roles={['admin']}>
            <Budgets />
          </LazyRoute>
        } />

        <Route path="/api-keys" element={
          <LazyRoute roles={['admin']}>
            <APIKeys />
          </LazyRoute>
        } />

        {/* Phase 6 - Ultimate Enterprise Features Routes */}
        <Route path="/dashboard-builder" element={
          <LazyRoute roles={['admin']}>
            <DashboardBuilder />
          </LazyRoute>
        } />

        <Route path="/reconciliation" element={
          <LazyRoute roles={['admin']}>
            <BankReconciliation />
          </LazyRoute>
        } />

        <Route path="/scheduled-reports" element={
          <LazyRoute roles={['admin']}>
            <ScheduledReports />
          </LazyRoute>
        } />

        <Route path="/currencies" element={
          <LazyRoute roles={['admin']}>
            <CurrencySettings />
          </LazyRoute>
        } />

        {/* Client Portal Routes */}
        <Route path="/portal/client" element={
          <LazyRoute roles={['client']}>
            <ClientDashboard />
          </LazyRoute>
        } />

        <Route path="/portal/client/projects" element={
          <LazyRoute roles={['client']}>
            <ClientProjects />
          </LazyRoute>
        } />

        <Route path="/portal/client/payments" element={
          <LazyRoute roles={['client']}>
            <ClientPayments />
          </LazyRoute>
        } />

        {/* Supplier Portal Routes */}
        <Route path="/portal/supplier" element={
          <LazyRoute roles={['supplier']}>
            <SupplierDashboard />
          </LazyRoute>
        } />

        <Route path="/portal/supplier/orders" element={
          <LazyRoute roles={['supplier']}>
            <SupplierOrders />
          </LazyRoute>
        } />

        <Route path="/portal/supplier/payments" element={
          <LazyRoute roles={['supplier']}>
            <SupplierPayments />
          </LazyRoute>
        } />

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App;
