/**
 * CRMLayout - Main CRM module layout
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import CRMSidebar from './components/CRMSidebar';

export default function CRMLayout() {
  return (
    <div className="crm-layout">
      <CRMSidebar />
      <main className="crm-content">
        <Outlet />
      </main>

      <style jsx>{`
        .crm-layout {
          display: flex;
          height: calc(100vh - 64px);
          background: var(--bg-secondary);
        }

        .crm-content {
          flex: 1;
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
}
