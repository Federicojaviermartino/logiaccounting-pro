import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function SupplierPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      const res = await api.get('/api/v1/portal/supplier/payments');
      setPayments(res.data.payments || []);
    } catch (err) {
      console.error('Failed to load payments:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPayments = filter === 'all'
    ? payments
    : payments.filter(p => p.status === filter);

  const getStatusBadge = (status) => {
    const styles = {
      paid: 'badge-success',
      pending: 'badge-warning',
      processing: 'badge-info',
      overdue: 'badge-danger'
    };
    return <span className={`badge ${styles[status] || 'badge-gray'}`}>{status}</span>;
  };

  const totalPending = payments
    .filter(p => p.status === 'pending')
    .reduce((sum, p) => sum + (p.amount || 0), 0);

  const totalPaid = payments
    .filter(p => p.status === 'paid')
    .reduce((sum, p) => sum + (p.amount || 0), 0);

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Payments</h2>

      {/* Summary Cards */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <div className="stat-icon">$</div>
          <div className="stat-content">
            <div className="stat-value">${totalPending.toLocaleString()}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">+</div>
          <div className="stat-content">
            <div className="stat-value">${totalPaid.toLocaleString()}</div>
            <div className="stat-label">Received</div>
          </div>
        </div>
      </div>

      <div className="section mb-4">
        <div className="flex gap-2">
          {['all', 'pending', 'paid'].map(f => (
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
        {filteredPayments.length === 0 ? (
          <div className="text-center text-muted">No payments found</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Order</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>Paid Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredPayments.map(payment => (
                  <tr key={payment.id}>
                    <td><code>{payment.reference || payment.id}</code></td>
                    <td>{payment.order_number || '-'}</td>
                    <td className="font-bold">${payment.amount?.toLocaleString()}</td>
                    <td>{payment.due_date || '-'}</td>
                    <td>{payment.paid_date || '-'}</td>
                    <td>{getStatusBadge(payment.status)}</td>
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
