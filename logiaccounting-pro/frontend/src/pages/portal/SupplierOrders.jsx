import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function SupplierOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const res = await api.get('/api/v1/portal/supplier/orders');
      setOrders(res.data.orders || []);
    } catch (err) {
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (orderId, newStatus) => {
    try {
      await api.put(`/api/v1/portal/supplier/orders/${orderId}/status`, { status: newStatus });
      loadOrders();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const filteredOrders = filter === 'all'
    ? orders
    : orders.filter(o => o.status === filter);

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'badge-warning',
      confirmed: 'badge-info',
      shipped: 'badge-primary',
      delivered: 'badge-success',
      cancelled: 'badge-danger'
    };
    return <span className={`badge ${styles[status] || 'badge-gray'}`}>{status}</span>;
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Orders</h2>

      <div className="section mb-4">
        <div className="flex gap-2 flex-wrap">
          {['all', 'pending', 'confirmed', 'shipped', 'delivered'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="section">
        {filteredOrders.length === 0 ? (
          <div className="text-center text-muted">No orders found</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order #</th>
                  <th>Date</th>
                  <th>Items</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map(order => (
                  <tr key={order.id}>
                    <td><code>{order.order_number || order.id}</code></td>
                    <td>{order.date}</td>
                    <td>{order.items_count || 0} items</td>
                    <td className="font-bold">${order.total?.toLocaleString()}</td>
                    <td>{getStatusBadge(order.status)}</td>
                    <td>
                      {order.status === 'pending' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => updateStatus(order.id, 'confirmed')}
                        >
                          Confirm
                        </button>
                      )}
                      {order.status === 'confirmed' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => updateStatus(order.id, 'shipped')}
                        >
                          Ship
                        </button>
                      )}
                      {order.status === 'shipped' && (
                        <button
                          className="btn btn-sm btn-success"
                          onClick={() => updateStatus(order.id, 'delivered')}
                        >
                          Delivered
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
