import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function ClientPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/payments');
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
    const styles = { paid: 'badge-success', pending: 'badge-warning', overdue: 'badge-danger' };
    return <span className={`badge ${styles[status] || 'badge-gray'}`}>{status}</span>;
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Payments</h2>

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
                  <th>Project</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredPayments.map(payment => (
                  <tr key={payment.id}>
                    <td><code>{payment.reference || payment.id}</code></td>
                    <td>{payment.project_name}</td>
                    <td className="font-bold">${payment.amount?.toLocaleString()}</td>
                    <td>{payment.due_date}</td>
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
