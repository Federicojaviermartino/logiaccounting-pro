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

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App;
