import AuditLogs from './pages/AuditLogs';
import ComplianceDashboard from './pages/ComplianceDashboard';

export const auditRoutes = [
  { path: '/audit/logs', element: <AuditLogs />, title: 'Audit Logs' },
  { path: '/audit/compliance', element: <ComplianceDashboard />, title: 'Compliance' }
];
