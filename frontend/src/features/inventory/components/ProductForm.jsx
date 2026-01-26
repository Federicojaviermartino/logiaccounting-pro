import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';

export default function ProductForm({ product, onClose, onSuccess }) {
  const [form, setForm] = useState({
    sku: '', name: '', description: '', category_id: '',
    uom_id: '', list_price: '0', standard_cost: '0',
    track_inventory: true, track_lots: false, track_serials: false,
    reorder_point: '0', reorder_quantity: '0',
  });

  useEffect(() => {
    if (product) {
      setForm({
        sku: product.sku || '',
        name: product.name || '',
        description: product.description || '',
        category_id: product.category_id || '',
        uom_id: product.uom_id || '',
        list_price: product.list_price?.toString() || '0',
        standard_cost: product.standard_cost?.toString() || '0',
        track_inventory: product.track_inventory ?? true,
        track_lots: product.track_lots ?? false,
        track_serials: product.track_serials ?? false,
        reorder_point: product.reorder_point?.toString() || '0',
        reorder_quantity: product.reorder_quantity?.toString() || '0',
      });
    }
  }, [product]);

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => inventoryAPI.getCategories(),
  });

  const { data: uoms } = useQuery({
    queryKey: ['uoms'],
    queryFn: () => inventoryAPI.getUOMs(),
  });

  const mutation = useMutation({
    mutationFn: (data) => product
      ? inventoryAPI.updateProduct(product.id, data)
      : inventoryAPI.createProduct(data),
    onSuccess,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate({
      ...form,
      list_price: parseFloat(form.list_price) || 0,
      standard_cost: parseFloat(form.standard_cost) || 0,
      reorder_point: parseFloat(form.reorder_point) || 0,
      reorder_quantity: parseFloat(form.reorder_quantity) || 0,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{product ? 'Edit Product' : 'Add Product'}</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">SKU *</label>
              <input type="text" value={form.sku} onChange={(e) => setForm({...form, sku: e.target.value})}
                required disabled={!!product}
                className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">UOM *</label>
              <select value={form.uom_id} onChange={(e) => setForm({...form, uom_id: e.target.value})}
                required className="w-full px-3 py-2 border rounded-lg">
                <option value="">Select...</option>
                {uoms?.map((u) => <option key={u.id} value={u.id}>{u.code} - {u.name}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name *</label>
            <input type="text" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
              required className="w-full px-3 py-2 border rounded-lg" />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select value={form.category_id} onChange={(e) => setForm({...form, category_id: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg">
              <option value="">None</option>
              {categories?.categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">List Price</label>
              <input type="number" step="0.01" value={form.list_price}
                onChange={(e) => setForm({...form, list_price: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Standard Cost</label>
              <input type="number" step="0.01" value={form.standard_cost}
                onChange={(e) => setForm({...form, standard_cost: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={form.track_inventory}
                onChange={(e) => setForm({...form, track_inventory: e.target.checked})} />
              <span className="text-sm">Track Inventory</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={form.track_lots}
                onChange={(e) => setForm({...form, track_lots: e.target.checked})} />
              <span className="text-sm">Track Lots</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={form.track_serials}
                onChange={(e) => setForm({...form, track_serials: e.target.checked})} />
              <span className="text-sm">Track Serials</span>
            </label>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Reorder Point</label>
              <input type="number" value={form.reorder_point}
                onChange={(e) => setForm({...form, reorder_point: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Reorder Quantity</label>
              <input type="number" value={form.reorder_quantity}
                onChange={(e) => setForm({...form, reorder_quantity: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
            <button type="submit" disabled={mutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50">
              {mutation.isPending ? 'Saving...' : product ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
