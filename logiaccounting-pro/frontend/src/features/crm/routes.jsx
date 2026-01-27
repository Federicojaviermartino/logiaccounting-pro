/**
 * CRM Module Routes
 */

import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import CRMLayout from './CRMLayout';

// Lazy load CRM pages
const CRMDashboard = lazy(() => import('./pages/CRMDashboard'));
const PipelineBoard = lazy(() => import('./components/PipelineBoard'));

// Placeholder components for pages not yet implemented
const PlaceholderPage = ({ title }) => (
  <div style={{ padding: '24px' }}>
    <h1>{title}</h1>
    <p style={{ color: 'var(--text-muted)' }}>This page is under construction.</p>
  </div>
);

const LeadsList = () => <PlaceholderPage title="Leads" />;
const LeadDetail = () => <PlaceholderPage title="Lead Detail" />;
const ContactsList = () => <PlaceholderPage title="Contacts" />;
const ContactDetail = () => <PlaceholderPage title="Contact Detail" />;
const CompaniesList = () => <PlaceholderPage title="Companies" />;
const CompanyDetail = () => <PlaceholderPage title="Company Detail" />;
const OpportunitiesList = () => <PlaceholderPage title="Opportunities" />;
const OpportunityDetail = () => <PlaceholderPage title="Opportunity Detail" />;
const ActivitiesList = () => <PlaceholderPage title="Activities" />;
const QuotesList = () => <PlaceholderPage title="Quotes" />;
const QuoteDetail = () => <PlaceholderPage title="Quote Detail" />;
const CRMSettings = () => <PlaceholderPage title="CRM Settings" />;
const CRMCalendar = () => <PlaceholderPage title="Calendar" />;

const LoadingFallback = () => (
  <div className="loading-fallback" style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: 'var(--text-muted)',
  }}>
    Loading...
  </div>
);

export default function CRMRoutes() {
  return (
    <Routes>
      <Route element={<CRMLayout />}>
        <Route
          index
          element={
            <Suspense fallback={<LoadingFallback />}>
              <CRMDashboard />
            </Suspense>
          }
        />

        <Route
          path="pipeline"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <PipelineBoard />
            </Suspense>
          }
        />

        {/* Leads */}
        <Route
          path="leads"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <LeadsList />
            </Suspense>
          }
        />
        <Route
          path="leads/:id"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <LeadDetail />
            </Suspense>
          }
        />

        {/* Contacts */}
        <Route
          path="contacts"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <ContactsList />
            </Suspense>
          }
        />
        <Route
          path="contacts/:id"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <ContactDetail />
            </Suspense>
          }
        />

        {/* Companies */}
        <Route
          path="companies"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <CompaniesList />
            </Suspense>
          }
        />
        <Route
          path="companies/:id"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <CompanyDetail />
            </Suspense>
          }
        />

        {/* Opportunities */}
        <Route
          path="opportunities"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <OpportunitiesList />
            </Suspense>
          }
        />
        <Route
          path="opportunities/:id"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <OpportunityDetail />
            </Suspense>
          }
        />

        {/* Activities */}
        <Route
          path="activities"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <ActivitiesList />
            </Suspense>
          }
        />

        {/* Calendar */}
        <Route
          path="calendar"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <CRMCalendar />
            </Suspense>
          }
        />

        {/* Quotes */}
        <Route
          path="quotes"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <QuotesList />
            </Suspense>
          }
        />
        <Route
          path="quotes/:id"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <QuoteDetail />
            </Suspense>
          }
        />

        {/* Settings */}
        <Route
          path="settings"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <CRMSettings />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}
