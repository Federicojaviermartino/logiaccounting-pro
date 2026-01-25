import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, AlertCircle } from 'lucide-react';
import AccountPicker from './AccountPicker';

export default function JournalEntryForm({ entry, onSubmit, onClose, isLoading }) {
  const [formData, setFormData] = useState({
    entry_date: new Date().toISOString().split('T')[0],
    entry_type: 'standard',
    description: '',
    reference: '',
    lines: [
      { account_id: '', debit_amount: '', credit_amount: '', description: '' },
      { account_id: '', debit_amount: '', credit_amount: '', description: '' },
    ],
  });

  const totalDebit = formData.lines.reduce((sum, l) => sum + (parseFloat(l.debit_amount) || 0), 0);
  const totalCredit = formData.lines.reduce((sum, l) => sum + (parseFloat(l.credit_amount) || 0), 0);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  useEffect(() => {
    if (entry) {
      setFormData({
        entry_date: entry.entry_date,
        entry_type: entry.entry_type,
        description: entry.description || '',
        reference: entry.reference || '',
        lines: entry.lines.map((l) => ({
          account_id: l.account_id,
          debit_amount: l.debit_amount > 0 ? l.debit_amount.toString() : '',
          credit_amount: l.credit_amount > 0 ? l.credit_amount.toString() : '',
          description: l.description || '',
        })),
      });
    }
  }, [entry]);

  const handleLineChange = (index, field, value) => {
    setFormData((prev) => {
      const newLines = [...prev.lines];
      newLines[index] = { ...newLines[index], [field]: value };
      if (field === 'debit_amount' && value) newLines[index].credit_amount = '';
      else if (field === 'credit_amount' && value) newLines[index].debit_amount = '';
      return { ...prev, lines: newLines };
    });
  };

  const addLine = () => {
    setFormData((prev) => ({
      ...prev,
      lines: [...prev.lines, { account_id: '', debit_amount: '', credit_amount: '', description: '' }],
    }));
  };

  const removeLine = (index) => {
    if (formData.lines.length <= 2) return;
    setFormData((prev) => ({ ...prev, lines: prev.lines.filter((_, i) => i !== index) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isBalanced) return;
    onSubmit({
      ...formData,
      lines: formData.lines.map((l) => ({
        account_id: l.account_id,
        debit_amount: parseFloat(l.debit_amount) || 0,
        credit_amount: parseFloat(l.credit_amount) || 0,
        description: l.description,
      })),
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl">
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">{entry ? 'Edit Journal Entry' : 'New Journal Entry'}</h2>
            <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
          </div>
          <form onSubmit={handleSubmit} className="p-6">
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-1">Date *</label>
                <input type="date" name="entry_date" value={formData.entry_date}
                  onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select name="entry_type" value={formData.entry_type}
                  onChange={(e) => setFormData({ ...formData, entry_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg">
                  <option value="standard">Standard</option>
                  <option value="adjustment">Adjustment</option>
                  <option value="closing">Closing</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium mb-1">Reference</label>
                <input type="text" value={formData.reference}
                  onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg" />
              </div>
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium mb-1">Description *</label>
              <input type="text" value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Entry Lines</label>
                <button type="button" onClick={addLine} className="flex items-center gap-1 text-sm text-blue-600">
                  <Plus className="w-4 h-4" /> Add Line
                </button>
              </div>
              <div className="border rounded-lg overflow-hidden">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 w-1/3">Account</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Description</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 w-32">Debit</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 w-32">Credit</th>
                      <th className="px-4 py-2 w-10"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {formData.lines.map((line, i) => (
                      <tr key={i}>
                        <td className="px-2 py-2">
                          <AccountPicker value={line.account_id}
                            onChange={(acc) => handleLineChange(i, 'account_id', acc?.id || '')} compact />
                        </td>
                        <td className="px-2 py-2">
                          <input type="text" value={line.description}
                            onChange={(e) => handleLineChange(i, 'description', e.target.value)}
                            className="w-full px-2 py-1 text-sm border rounded" />
                        </td>
                        <td className="px-2 py-2">
                          <input type="number" step="0.01" min="0" value={line.debit_amount}
                            onChange={(e) => handleLineChange(i, 'debit_amount', e.target.value)}
                            className="w-full px-2 py-1 text-sm text-right border rounded" />
                        </td>
                        <td className="px-2 py-2">
                          <input type="number" step="0.01" min="0" value={line.credit_amount}
                            onChange={(e) => handleLineChange(i, 'credit_amount', e.target.value)}
                            className="w-full px-2 py-1 text-sm text-right border rounded" />
                        </td>
                        <td className="px-2 py-2">
                          <button type="button" onClick={() => removeLine(i)}
                            disabled={formData.lines.length <= 2}
                            className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-30">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr className="font-medium">
                      <td colSpan={2} className="px-4 py-2 text-right text-sm">Totals</td>
                      <td className="px-4 py-2 text-right text-sm font-mono">${totalDebit.toFixed(2)}</td>
                      <td className="px-4 py-2 text-right text-sm font-mono">${totalCredit.toFixed(2)}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              {!isBalanced && (
                <div className="mt-2 flex items-center gap-2 text-sm text-red-600">
                  <AlertCircle className="w-4 h-4" />
                  Out of balance by ${Math.abs(totalDebit - totalCredit).toFixed(2)}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" disabled={isLoading || !isBalanced}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
                {isLoading ? 'Saving...' : entry ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
