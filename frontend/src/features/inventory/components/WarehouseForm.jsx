import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';

export default function WarehouseForm({ warehouse, onClose, onSuccess }) {
  const [form, setForm] = useState({
    code: warehouse?.code || '',
    name: warehouse?.name || '',
    address: {
      line1: warehouse?.address?.line1 || '',
      city: warehouse?.address?.city || '',
      state: warehouse?.address?.state || '',
      postal_code: warehouse?.address?.postal_code || '',
      country: warehouse?.address?.country || '',
    },
    phone: warehouse?.phone || '',
    email: warehouse?.email || '',
  });

  const mutation = useMutation({
    mutationFn: (data) => inventoryAPI.createWarehouse(data),
    onSuccess,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{warehouse ? 'Edit Warehouse' : 'Add Warehouse'}</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Code *</label>
              <input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value})}
                required className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
                required className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Address</label>
            <input type="text" value={form.address.line1}
              onChange={(e) => setForm({...form, address: {...form.address, line1: e.target.value}})}
              placeholder="Street address"
              className="w-full px-3 py-2 border rounded-lg" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">City</label>
              <input type="text" value={form.address.city}
                onChange={(e) => setForm({...form, address: {...form.address, city: e.target.value}})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">State</label>
              <input type="text" value={form.address.state}
                onChange={(e) => setForm({...form, address: {...form.address, state: e.target.value}})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Postal Code</label>
              <input type="text" value={form.address.postal_code}
                onChange={(e) => setForm({...form, address: {...form.address, postal_code: e.target.value}})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Country</label>
              <input type="text" value={form.address.country}
                onChange={(e) => setForm({...form, address: {...form.address, country: e.target.value}})}
                maxLength={2} placeholder="US"
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input type="tel" value={form.phone}
                onChange={(e) => setForm({...form, phone: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input type="email" value={form.email}
                onChange={(e) => setForm({...form, email: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
            <button type="submit" disabled={mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {mutation.isPending ? 'Saving...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
