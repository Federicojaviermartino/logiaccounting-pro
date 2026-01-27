import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import budgetingAPI from '../services/budgetingAPI';

const BudgetForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    budget_type: 'annual',
    fiscal_year: new Date().getFullYear(),
    start_date: `${new Date().getFullYear()}-01-01`,
    end_date: `${new Date().getFullYear()}-12-31`,
    currency: 'USD',
    requires_approval: true,
    allow_overspend: false,
  });

  const [errors, setErrors] = useState({});

  // Load existing budget if editing
  useQuery({
    queryKey: ['budget', id],
    queryFn: () => budgetingAPI.getBudget(id),
    enabled: isEdit,
    onSuccess: (data) => {
      const budget = data.data;
      setFormData({
        name: budget.name,
        description: budget.description || '',
        budget_type: budget.budget_type,
        fiscal_year: budget.fiscal_year,
        start_date: budget.start_date,
        end_date: budget.end_date,
        currency: budget.currency,
        requires_approval: budget.requires_approval,
        allow_overspend: budget.allow_overspend,
      });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data) => budgetingAPI.createBudget(data),
    onSuccess: (response) => navigate(`/budgeting/${response.data.id}`),
    onError: (error) => setErrors({ submit: error.message }),
  });

  const updateMutation = useMutation({
    mutationFn: (data) => budgetingAPI.updateBudget(id, data),
    onSuccess: () => navigate(`/budgeting/${id}`),
    onError: (error) => setErrors({ submit: error.message }),
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    setErrors(prev => ({ ...prev, [name]: null }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.start_date) newErrors.start_date = 'Start date is required';
    if (!formData.end_date) newErrors.end_date = 'End date is required';
    if (formData.end_date <= formData.start_date) {
      newErrors.end_date = 'End date must be after start date';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    if (isEdit) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? 'Edit Budget' : 'Create New Budget'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-red-800">
            {errors.submit}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Budget Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`w-full border rounded-lg px-3 py-2 ${errors.name ? 'border-red-500' : 'border-gray-300'}`}
            placeholder="e.g., Annual Operating Budget 2025"
          />
          {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            placeholder="Optional description..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Budget Type
            </label>
            <select
              name="budget_type"
              value={formData.budget_type}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="annual">Annual</option>
              <option value="quarterly">Quarterly</option>
              <option value="monthly">Monthly</option>
              <option value="project">Project</option>
              <option value="departmental">Departmental</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fiscal Year
            </label>
            <select
              name="fiscal_year"
              value={formData.fiscal_year}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              {[2024, 2025, 2026, 2027].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date *
            </label>
            <input
              type="date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
              className={`w-full border rounded-lg px-3 py-2 ${errors.start_date ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date *
            </label>
            <input
              type="date"
              name="end_date"
              value={formData.end_date}
              onChange={handleChange}
              className={`w-full border rounded-lg px-3 py-2 ${errors.end_date ? 'border-red-500' : 'border-gray-300'}`}
            />
            {errors.end_date && <p className="text-red-500 text-sm mt-1">{errors.end_date}</p>}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Currency
          </label>
          <select
            name="currency"
            value={formData.currency}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="USD">USD - US Dollar</option>
            <option value="EUR">EUR - Euro</option>
            <option value="GBP">GBP - British Pound</option>
          </select>
        </div>

        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              name="requires_approval"
              checked={formData.requires_approval}
              onChange={handleChange}
              className="rounded border-gray-300 text-blue-600 mr-2"
            />
            <span className="text-sm text-gray-700">Requires approval workflow</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              name="allow_overspend"
              checked={formData.allow_overspend}
              onChange={handleChange}
              className="rounded border-gray-300 text-blue-600 mr-2"
            />
            <span className="text-sm text-gray-700">Allow overspending</span>
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Saving...' : (isEdit ? 'Update Budget' : 'Create Budget')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BudgetForm;
