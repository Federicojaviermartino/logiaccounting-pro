import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import payrollAPI from '../services/payrollAPI';

const PayrollRunDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['payrollRun', id],
    queryFn: () => payrollAPI.getPayrollRun(id),
  });

  const calculateMutation = useMutation({
    mutationFn: () => payrollAPI.calculatePayroll(id),
    onSuccess: () => queryClient.invalidateQueries(['payrollRun', id]),
  });

  const approveMutation = useMutation({
    mutationFn: () => payrollAPI.approvePayroll(id),
    onSuccess: () => queryClient.invalidateQueries(['payrollRun', id]),
  });

  const processMutation = useMutation({
    mutationFn: () => payrollAPI.processPayments(id),
    onSuccess: () => queryClient.invalidateQueries(['payrollRun', id]),
  });

  const run = data?.data;

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

  if (!run) {
    return <div className="text-center py-12">Payroll run not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{run.run_number}</h1>
          <p className="text-gray-600 capitalize">{run.run_type} Payroll Run</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/payroll/runs')}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Back to List
          </button>

          {run.status === 'draft' && (
            <button
              onClick={() => calculateMutation.mutate()}
              disabled={calculateMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {calculateMutation.isPending ? 'Calculating...' : 'Calculate Payroll'}
            </button>
          )}

          {run.status === 'pending_approval' && (
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {approveMutation.isPending ? 'Approving...' : 'Approve Payroll'}
            </button>
          )}

          {run.status === 'approved' && (
            <button
              onClick={() => processMutation.mutate()}
              disabled={processMutation.isPending}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {processMutation.isPending ? 'Processing...' : 'Process Payments'}
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Status</p>
          <p className="text-lg font-semibold capitalize">{run.status.replace('_', ' ')}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Employees</p>
          <p className="text-2xl font-bold text-blue-600">{run.employee_count}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Gross Pay</p>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(run.total_gross_pay)}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Deductions</p>
          <p className="text-2xl font-bold text-red-600">{formatCurrency(run.total_deductions)}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Net Pay</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(run.total_net_pay)}</p>
        </div>
      </div>

      {/* Employee Lines */}
      {run.payroll_lines && run.payroll_lines.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">Employee Payroll Details</h2>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Hours</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Gross</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Fed Tax</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">State Tax</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">SS/Medicare</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Deductions</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Net Pay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {run.payroll_lines.map((line) => (
                <tr key={line.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium">{line.employee_name}</div>
                    <div className="text-sm text-gray-500">{line.employee_number}</div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {parseFloat(line.regular_hours).toFixed(1)}
                    {parseFloat(line.overtime_hours) > 0 && (
                      <span className="text-orange-600 ml-1">+{parseFloat(line.overtime_hours).toFixed(1)} OT</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">{formatCurrency(line.gross_pay)}</td>
                  <td className="px-6 py-4 text-right text-red-600">{formatCurrency(line.federal_tax)}</td>
                  <td className="px-6 py-4 text-right text-red-600">{formatCurrency(line.state_tax)}</td>
                  <td className="px-6 py-4 text-right text-red-600">
                    {formatCurrency(parseFloat(line.social_security) + parseFloat(line.medicare))}
                  </td>
                  <td className="px-6 py-4 text-right text-red-600">{formatCurrency(line.total_deductions)}</td>
                  <td className="px-6 py-4 text-right font-semibold text-green-600">{formatCurrency(line.net_pay)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr className="font-semibold">
                <td className="px-6 py-3">TOTALS</td>
                <td className="px-6 py-3 text-right">-</td>
                <td className="px-6 py-3 text-right">{formatCurrency(run.total_gross_pay)}</td>
                <td className="px-6 py-3 text-right text-red-600">-</td>
                <td className="px-6 py-3 text-right text-red-600">-</td>
                <td className="px-6 py-3 text-right text-red-600">-</td>
                <td className="px-6 py-3 text-right text-red-600">{formatCurrency(run.total_deductions)}</td>
                <td className="px-6 py-3 text-right text-green-600">{formatCurrency(run.total_net_pay)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
};

export default PayrollRunDetail;
