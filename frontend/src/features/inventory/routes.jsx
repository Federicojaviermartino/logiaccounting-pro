import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

const Products = lazy(() => import('./pages/Products'));
const Warehouses = lazy(() => import('./pages/Warehouses'));
const StockLevels = lazy(() => import('./pages/StockLevels'));
const StockMovements = lazy(() => import('./pages/StockMovements'));

const Wrapper = ({ children }) => (
  <Suspense fallback={<div className="flex justify-center p-12"><div className="animate-spin h-8 w-8 border-2 border-blue-600 rounded-full border-t-transparent" /></div>}>
    {children}
  </Suspense>
);

export default function InventoryRoutes() {
  return (
    <Routes>
      <Route path="products" element={<Wrapper><Products /></Wrapper>} />
      <Route path="warehouses" element={<Wrapper><Warehouses /></Wrapper>} />
      <Route path="stock" element={<Wrapper><StockLevels /></Wrapper>} />
      <Route path="movements" element={<Wrapper><StockMovements /></Wrapper>} />
      <Route path="" element={<Navigate to="products" replace />} />
    </Routes>
  );
}

export const INVENTORY_PATHS = {
  ROOT: '/inventory',
  PRODUCTS: '/inventory/products',
  WAREHOUSES: '/inventory/warehouses',
  STOCK: '/inventory/stock',
  MOVEMENTS: '/inventory/movements',
};
