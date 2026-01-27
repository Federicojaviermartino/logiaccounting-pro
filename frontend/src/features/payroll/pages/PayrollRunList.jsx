import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import payrollAPI from '../services/payrollAPI';

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  calculating: 'bg-blue-100 text-blue-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  processing_payments: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  voided: 'bg-red-100 text-red-800',
};

const PayrollRunList = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: runsData, isLoading } = useQuery({
    queryKey: ['payrollRuns'],
    queryFn: () => payrollAPI.getPayrollRuns(),
  });

  const { data: periodsData } = useQuery({
    queryKey: ['payPeriods'],
    queryFn: () => payrollAPI.getPayPeriods({ status: 'open' }),
  });

  const createMutation = useMutation({
    mutationFn: (data) => payrollAPI.createPayrollRun(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['payrollRuns']);
      setShowCreateModal(false);
      navigate(`/payroll/runs/${response.data.id}`);
    },
  });

  const runs = runsData?.data?.items || [];
  const periods = periodsData?.data || [];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payroll Runs</h1>
          <p className="text-gray-600">Process and manage payroll</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + New Payroll Run
        </button>
      </div>

      {/* Payroll Runs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Run #</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Employees</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Gross Pay</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Net Pay</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Run Date</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {runs.map((run) => (
              <tr key={run.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium">{run.run_number}</td>
                <td className="px-6 py-4 capitalize">{run.run_type}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[run.status]}`}>
                    {run.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">{run.employee_count}</td>
                <td className="px-6 py-4 text-right">{formatCurrency(run.total_gross_pay)}</td>
                <td className="px-6 py-4 text-right font-medium">{formatCurrency(run.total_net_pay)}</td>
                <td className="px-6 py-4 text-gray-600">
                  {new Date(run.run_date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-right">
                  <Link
                    to={`/payroll/runs/${run.id}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {runs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No payroll runs found</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">New Payroll Run</h2>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target);
              createMutation.mutate({
                pay_period_id: formData.get('pay_period_id'),
                run_type: formData.get('run_type'),
              });
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Pay Period</label>
                  <select
                    name="pay_period_id"
                    required
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="">Select pay period...</option>
                    {periods.map(period => (
                      <option key={period.id} value={period.id}>
                        {period.frequency} #{period.period_number} ({period.start_date} - {period.end_date})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Run Type</label>
                  <select
                    name="run_type"
                    defaultValue="regular"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="regular">Regular</option>
                    <option value="bonus">Bonus</option>
                    <option value="correction">Correction</option>
                    <option value="final">Final</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollRunList;
