import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function AccountForm({
  account,
  accountTypes,
  accounts,
  onSubmit,
  onClose,
  isLoading,
}) {
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    account_type_id: '',
    parent_id: '',
    description: '',
    is_header: false,
    opening_balance: '0',
    currency: 'USD',
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (account) {
      setFormData({
        code: account.code || '',
        name: account.name || '',
        account_type_id: account.account_type?.id || '',
        parent_id: account.parent_id || '',
        description: account.description || '',
        is_header: account.is_header || false,
        opening_balance: account.opening_balance?.toString() || '0',
        currency: account.currency || 'USD',
      });
    }
  }, [account]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.code.trim()) newErrors.code = 'Account code is required';
    else if (!/^\d{4}$/.test(formData.code)) newErrors.code = 'Code must be 4 digits';
    if (!formData.name.trim()) newErrors.name = 'Account name is required';
    if (!formData.account_type_id) newErrors.account_type_id = 'Account type is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      ...formData,
      opening_balance: parseFloat(formData.opening_balance) || 0,
      parent_id: formData.parent_id || null,
    });
  };

  const parentOptions = accounts?.filter((a) =>
    a.is_header && a.account_type?.id === formData.account_type_id && a.id !== account?.id
  ) || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {account ? 'Edit Account' : 'Create Account'}
            </h2>
            <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Account Code *</label>
                <input type="text" name="code" value={formData.code} onChange={handleChange}
                  placeholder="1100" maxLength={4}
                  className={`w-full px-3 py-2 border rounded-lg ${errors.code ? 'border-red-500' : 'border-gray-300'}`} />
                {errors.code && <p className="mt-1 text-xs text-red-500">{errors.code}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Currency</label>
                <select name="currency" value={formData.currency} onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Name *</label>
              <input type="text" name="name" value={formData.name} onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg ${errors.name ? 'border-red-500' : 'border-gray-300'}`} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Type *</label>
              <select name="account_type_id" value={formData.account_type_id} onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg ${errors.account_type_id ? 'border-red-500' : 'border-gray-300'}`}>
                <option value="">Select type...</option>
                {accountTypes?.map((type) => (
                  <option key={type.id} value={type.id}>{type.display_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Parent Account</label>
              <select name="parent_id" value={formData.parent_id} onChange={handleChange}
                disabled={!formData.account_type_id}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50">
                <option value="">None (Top Level)</option>
                {parentOptions.map((p) => (
                  <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Opening Balance</label>
                <input type="number" step="0.01" name="opening_balance" value={formData.opening_balance}
                  onChange={handleChange} disabled={formData.is_header}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50" />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2">
                  <input type="checkbox" name="is_header" checked={formData.is_header}
                    onChange={handleChange} className="rounded border-gray-300" />
                  <span className="text-sm">Header account</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button type="button" onClick={onClose}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                {isLoading ? 'Saving...' : account ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
