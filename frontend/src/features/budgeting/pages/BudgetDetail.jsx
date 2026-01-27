import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import budgetingAPI from '../services/budgetingAPI';
import BudgetGrid from '../components/BudgetGrid';

const BudgetDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeVersionId, setActiveVersionId] = useState(null);

  const { data: budgetData, isLoading } = useQuery({
    queryKey: ['budget', id],
    queryFn: () => budgetingAPI.getBudget(id, true),
  });

  const budget = budgetData?.data;
  const versions = budget?.versions || [];

  const { data: linesData } = useQuery({
    queryKey: ['budgetLines', activeVersionId],
    queryFn: () => budgetingAPI.getLines(activeVersionId),
    enabled: !!activeVersionId,
  });

  const lines = linesData?.data || [];

  const submitMutation = useMutation({
    mutationFn: (versionId) => budgetingAPI.submitVersion(versionId),
    onSuccess: () => queryClient.invalidateQueries(['budget', id]),
  });

  const approveMutation = useMutation({
    mutationFn: (versionId) => budgetingAPI.approveVersion(versionId),
    onSuccess: () => queryClient.invalidateQueries(['budget', id]),
  });

  const activateMutation = useMutation({
    mutationFn: (versionId) => budgetingAPI.activateVersion(versionId),
    onSuccess: () => queryClient.invalidateQueries(['budget', id]),
  });

  // Set active version on load
  useState(() => {
    if (budget?.active_version_id) {
      setActiveVersionId(budget.active_version_id);
    } else if (versions.length > 0) {
      setActiveVersionId(versions[0].id);
    }
  }, [budget, versions]);

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

  if (!budget) {
    return <div className="text-center py-12">Budget not found</div>;
  }

  const currentVersion = versions.find(v => v.id === activeVersionId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{budget.name}</h1>
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
              {budget.status}
            </span>
          </div>
          <p className="text-gray-600">{budget.budget_code} | FY {budget.fiscal_year}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/budgeting')}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Back to List
          </button>
          {budget.status === 'draft' && (
            <button
              onClick={() => navigate(`/budgeting/${id}/edit`)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Edit Budget
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Total Revenue</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(budget.total_revenue)}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Total Expenses</p>
          <p className="text-2xl font-bold text-red-600">{formatCurrency(budget.total_expenses)}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Net Income</p>
          <p className="text-2xl font-bold text-blue-600">{formatCurrency(budget.total_net_income)}</p>
        </div>
      </div>

      {/* Version Selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Budget Versions</h2>
          <button
            onClick={() => navigate(`/budgeting/${id}/versions/new`)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            + New Version
          </button>
        </div>
        <div className="flex gap-2 flex-wrap">
          {versions.map((version) => (
            <button
              key={version.id}
              onClick={() => setActiveVersionId(version.id)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                activeVersionId === version.id
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
              }`}
            >
              <span className="font-medium">{version.version_name}</span>
              <span className="ml-2 text-xs opacity-75">v{version.version_number}</span>
              {version.is_active && <span className="ml-2 text-xs">★</span>}
            </button>
          ))}
        </div>

        {/* Version Actions */}
        {currentVersion && (
          <div className="mt-4 pt-4 border-t flex gap-2">
            {currentVersion.status === 'draft' && (
              <button
                onClick={() => submitMutation.mutate(currentVersion.id)}
                disabled={submitMutation.isPending}
                className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm"
              >
                Submit for Approval
              </button>
            )}
            {currentVersion.status === 'submitted' && (
              <button
                onClick={() => approveMutation.mutate(currentVersion.id)}
                disabled={approveMutation.isPending}
                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
              >
                Approve
              </button>
            )}
            {currentVersion.status === 'approved' && !currentVersion.is_active && (
              <button
                onClick={() => activateMutation.mutate(currentVersion.id)}
                disabled={activateMutation.isPending}
                className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
              >
                Activate Version
              </button>
            )}
          </div>
        )}
      </div>

      {/* Budget Grid */}
      {activeVersionId && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Budget Lines</h2>
          </div>
          <BudgetGrid
            versionId={activeVersionId}
            lines={lines}
            readOnly={currentVersion?.status !== 'draft'}
          />
        </div>
      )}
    </div>
  );
};

export default BudgetDetail;
