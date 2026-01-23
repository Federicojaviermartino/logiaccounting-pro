import React from 'react';
import { Routes, Route } from 'react-router-dom';

import WorkflowDashboard from './pages/WorkflowDashboard';
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowList from './pages/WorkflowList';
import ExecutionMonitor from './pages/ExecutionMonitor';
import ExecutionList from './pages/ExecutionList';
import TemplateMarketplace from './pages/TemplateMarketplace';
import DeadLetterQueue from './pages/DeadLetterQueue';
import WorkflowSettings from './pages/WorkflowSettings';

export default function WorkflowRoutes() {
  return (
    <Routes>
      <Route index element={<WorkflowDashboard />} />
      <Route path="dashboard" element={<WorkflowDashboard />} />
      <Route path="builder" element={<WorkflowBuilder />} />
      <Route path="builder/:workflowId" element={<WorkflowBuilder />} />
      <Route path="list" element={<WorkflowList />} />
      <Route path="executions" element={<ExecutionList />} />
      <Route path="executions/:executionId" element={<ExecutionMonitor />} />
      <Route path="templates" element={<TemplateMarketplace />} />
      <Route path="dead-letter" element={<DeadLetterQueue />} />
      <Route path="settings" element={<WorkflowSettings />} />
    </Routes>
  );
}
