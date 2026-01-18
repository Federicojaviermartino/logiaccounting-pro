import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Projects from './pages/Projects';
import Movements from './pages/Movements';
import Transactions from './pages/Transactions';
import Payments from './pages/Payments';
import Users from './pages/Users';
import Reports from './pages/Reports';
import Layout from './components/Layout';

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

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      
      <Route path="/dashboard" element={
        <PrivateRoute>
          <Layout><Dashboard /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/inventory" element={
        <PrivateRoute roles={['admin', 'supplier']}>
          <Layout><Inventory /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/projects" element={
        <PrivateRoute roles={['admin', 'client']}>
          <Layout><Projects /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/movements" element={
        <PrivateRoute roles={['admin', 'supplier']}>
          <Layout><Movements /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/transactions" element={
        <PrivateRoute>
          <Layout><Transactions /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/payments" element={
        <PrivateRoute>
          <Layout><Payments /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/users" element={
        <PrivateRoute roles={['admin']}>
          <Layout><Users /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="/reports" element={
        <PrivateRoute roles={['admin']}>
          <Layout><Reports /></Layout>
        </PrivateRoute>
      } />
      
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
