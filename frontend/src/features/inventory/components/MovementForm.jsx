import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';

export default function MovementForm({ type, onClose, onSuccess }) {
  const [form, setForm] = useState({
    product_id: '',
    warehouse_id: '',
    location_id: '',
    quantity: '',
    unit_cost: '0',
    source_warehouse_id: '',
    source_location_id: '',
    dest_warehouse_id: '',
    dest_location_id: '',
    reason: '',
    notes: '',
  });

  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: () => inventoryAPI.getProducts({ page_size: 100 }),
  });

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => inventoryAPI.getWarehouses(),
  });

  const { data: locations } = useQuery({
    queryKey: ['locations', form.warehouse_id || form.source_warehouse_id],
    queryFn: () => inventoryAPI.getLocations(form.warehouse_id || form.source_warehouse_id),
    enabled: !!(form.warehouse_id || form.source_warehouse_id),
  });

  const { data: destLocations } = useQuery({
    queryKey: ['locations', form.dest_warehouse_id],
    queryFn: () => inventoryAPI.getLocations(form.dest_warehouse_id),
    enabled: !!form.dest_warehouse_id,
  });

  const mutation = useMutation({
    mutationFn: (data) => {
      switch (type) {
        case 'receipt': return inventoryAPI.createReceipt(data);
        case 'issue': return inventoryAPI.createIssue(data);
        case 'transfer': return inventoryAPI.createTransfer(data);
        default: return Promise.reject('Unknown type');
      }
    },
    onSuccess,
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    const data = {
      product_id: form.product_id,
      quantity: parseFloat(form.quantity),
      notes: form.notes,
    };

    if (type === 'receipt') {
      data.warehouse_id = form.warehouse_id;
      data.location_id = form.location_id;
      data.unit_cost = parseFloat(form.unit_cost) || 0;
    } else if (type === 'issue') {
      data.warehouse_id = form.warehouse_id;
      data.location_id = form.location_id;
      data.reason = form.reason;
    } else if (type === 'transfer') {
      data.source_warehouse_id = form.source_warehouse_id;
      data.source_location_id = form.source_location_id;
      data.dest_warehouse_id = form.dest_warehouse_id;
      data.dest_location_id = form.dest_location_id;
      data.reason = form.reason;
    }

    mutation.mutate(data);
  };

  const titles = {
    receipt: 'New Receipt',
    issue: 'New Issue',
    transfer: 'New Transfer',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{titles[type]}</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Product *</label>
            <select value={form.product_id} onChange={(e) => setForm({...form, product_id: e.target.value})}
              required className="w-full px-3 py-2 border rounded-lg">
              <option value="">Select product...</option>
              {products?.products?.map((p) => (
                <option key={p.id} value={p.id}>{p.sku} - {p.name}</option>
              ))}
            </select>
          </div>

          {type === 'transfer' ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Source Warehouse *</label>
                  <select value={form.source_warehouse_id}
                    onChange={(e) => setForm({...form, source_warehouse_id: e.target.value, source_location_id: ''})}
                    required className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Select...</option>
                    {warehouses?.warehouses?.map((w) => (
                      <option key={w.id} value={w.id}>{w.code} - {w.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Source Location *</label>
                  <select value={form.source_location_id}
                    onChange={(e) => setForm({...form, source_location_id: e.target.value})}
                    required disabled={!form.source_warehouse_id} className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Select...</option>
                    {locations?.locations?.map((l) => (
                      <option key={l.id} value={l.id}>{l.code}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Dest Warehouse *</label>
                  <select value={form.dest_warehouse_id}
                    onChange={(e) => setForm({...form, dest_warehouse_id: e.target.value, dest_location_id: ''})}
                    required className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Select...</option>
                    {warehouses?.warehouses?.map((w) => (
                      <option key={w.id} value={w.id}>{w.code} - {w.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Dest Location *</label>
                  <select value={form.dest_location_id}
                    onChange={(e) => setForm({...form, dest_location_id: e.target.value})}
                    required disabled={!form.dest_warehouse_id} className="w-full px-3 py-2 border rounded-lg">
                    <option value="">Select...</option>
                    {destLocations?.locations?.map((l) => (
                      <option key={l.id} value={l.id}>{l.code}</option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Warehouse *</label>
                <select value={form.warehouse_id}
                  onChange={(e) => setForm({...form, warehouse_id: e.target.value, location_id: ''})}
                  required className="w-full px-3 py-2 border rounded-lg">
                  <option value="">Select...</option>
                  {warehouses?.warehouses?.map((w) => (
                    <option key={w.id} value={w.id}>{w.code} - {w.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Location *</label>
                <select value={form.location_id}
                  onChange={(e) => setForm({...form, location_id: e.target.value})}
                  required disabled={!form.warehouse_id} className="w-full px-3 py-2 border rounded-lg">
                  <option value="">Select...</option>
                  {locations?.locations?.map((l) => (
                    <option key={l.id} value={l.id}>{l.code}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Quantity *</label>
              <input type="number" step="0.01" value={form.quantity}
                onChange={(e) => setForm({...form, quantity: e.target.value})}
                required className="w-full px-3 py-2 border rounded-lg" />
            </div>
            {type === 'receipt' && (
              <div>
                <label className="block text-sm font-medium mb-1">Unit Cost</label>
                <input type="number" step="0.01" value={form.unit_cost}
                  onChange={(e) => setForm({...form, unit_cost: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg" />
              </div>
            )}
          </div>

          {(type === 'issue' || type === 'transfer') && (
            <div>
              <label className="block text-sm font-medium mb-1">Reason</label>
              <input type="text" value={form.reason}
                onChange={(e) => setForm({...form, reason: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})}
              rows={2} className="w-full px-3 py-2 border rounded-lg" />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
            <button type="submit" disabled={mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {mutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
