/**
 * AI Feature Routes
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';

import CashFlowForecast from './pages/CashFlowForecast';
import DocumentScanner from './pages/DocumentScanner';
import AIAssistant from './pages/AIAssistant';
import AnomalyDashboard from './pages/AnomalyDashboard';

const AIRoutes = () => {
  return (
    <Routes>
      <Route path="cashflow" element={<CashFlowForecast />} />
      <Route path="scanner" element={<DocumentScanner />} />
      <Route path="assistant" element={<AIAssistant />} />
      <Route path="anomalies" element={<AnomalyDashboard />} />
    </Routes>
  );
};

export default AIRoutes;
