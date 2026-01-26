import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Search, FileText, Clock, CheckCircle, Truck, AlertCircle } from 'lucide-react';
import { purchasingAPI } from '../services/purchasingAPI';

const STATUS_CONFIG = {
  draft: { icon: FileText, color: 'text-gray-600 bg-gray-100' },
  pending_approval: { icon: Clock, color: 'text-yellow-600 bg-yellow-100' },
  approved: { icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  sent: { icon: Truck, color: 'text-blue-600 bg-blue-100' },
  partial: { icon: AlertCircle, color: 'text-orange-600 bg-orange-100' },
  received: { icon: CheckCircle, color: 'text-green-600 bg-green-100' },
  cancelled: { icon: AlertCircle, color: 'text-red-600 bg-red-100' },
};

export default function PurchaseOrders() {
  const [filters, setFilters] = useState({ search: '', status: '' });
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['purchase-orders', filters, page],
    queryFn: () => purchasingAPI.getOrders({ ...filters, page }),
  });

  const { data: dashboard } = useQuery({
    queryKey: ['po-dashboard'],
    queryFn: () => purchasingAPI.getDashboard(),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Purchase Orders</h1>
          <p className="text-gray-600 dark:text-gray-400">{data?.total || 0} orders</p>
        </div>
        <Link
          to="/purchasing/orders/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Order
        </Link>
      </div>

      {/* Dashboard Cards */}
      {dashboard && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Draft</p>
            <p className="text-2xl font-bold">{dashboard.total_draft}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Pending Approval</p>
            <p className="text-2xl font-bold text-yellow-600">{dashboard.total_pending_approval}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">Pending Receipt</p>
            <p className="text-2xl font-bold text-blue-600">{dashboard.total_pending_receipt}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">This Month</p>
            <p className="text-2xl font-bold">${dashboard.amount_this_month?.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search orders..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="pending_approval">Pending Approval</option>
          <option value="approved">Approved</option>
          <option value="sent">Sent</option>
          <option value="partial">Partially Received</option>
          <option value="received">Received</option>
        </select>
      </div>

      {/* Orders Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Supplier</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Lines</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {data?.orders?.map((order) => {
              const config = STATUS_CONFIG[order.status] || STATUS_CONFIG.draft;
              const Icon = config.icon;
              return (
                <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <Link to={`/purchasing/orders/${order.id}`} className="font-mono text-blue-600 hover:text-blue-800">
                      {order.order_number}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-medium">{order.supplier_name}</p>
                    <p className="text-sm text-gray-500">{order.supplier_code}</p>
                  </td>
                  <td className="px-6 py-4 text-sm">{new Date(order.order_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-right font-medium">
                    {order.currency} {order.total_amount?.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${config.color}`}>
                      <Icon className="w-3 h-3" />
                      {order.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center text-sm">{order.line_count}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
