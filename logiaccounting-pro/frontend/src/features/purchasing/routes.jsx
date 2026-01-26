import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

const Suppliers = lazy(() => import('./pages/Suppliers'));
const PurchaseOrders = lazy(() => import('./pages/PurchaseOrders'));

const Wrapper = ({ children }) => (
  <Suspense fallback={<div className="flex justify-center p-12"><div className="animate-spin h-8 w-8 border-2 border-blue-600 rounded-full border-t-transparent" /></div>}>
    {children}
  </Suspense>
);

export default function PurchasingRoutes() {
  return (
    <Routes>
      <Route path="suppliers" element={<Wrapper><Suppliers /></Wrapper>} />
      <Route path="orders" element={<Wrapper><PurchaseOrders /></Wrapper>} />
      <Route path="" element={<Navigate to="orders" replace />} />
    </Routes>
  );
}

export const PURCHASING_PATHS = {
  ROOT: '/purchasing',
  SUPPLIERS: '/purchasing/suppliers',
  ORDERS: '/purchasing/orders',
  RECEIPTS: '/purchasing/receipts',
  INVOICES: '/purchasing/invoices',
};
