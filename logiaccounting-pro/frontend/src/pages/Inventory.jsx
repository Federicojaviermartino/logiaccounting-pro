import { useState, useEffect } from 'react';
import { inventoryAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

export default function Inventory() {
  const { user } = useAuth();
  const [materials, setMaterials] = useState([]);
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [filters, setFilters] = useState({ search: '', category_id: '', state: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [filters]);

  const loadData = async () => {
    try {
      const [matRes, catRes, locRes] = await Promise.all([
        inventoryAPI.getMaterials(filters),
        inventoryAPI.getCategories('material'),
        inventoryAPI.getLocations()
      ]);
      setMaterials(matRes.data.materials || []);
      setCategories(catRes.data || []);
      setLocations(locRes.data || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (item = null) => {
    setEditItem(item);
    setFormData(item || {
      reference: '', name: '', description: '', category_id: '', location_id: '',
      quantity: 0, min_stock: 0, unit: 'units', unit_cost: 0, state: 'available'
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editItem) {
        await inventoryAPI.updateMaterial(editItem.id, formData);
      } else {
        await inventoryAPI.createMaterial(formData);
      }
      setModalOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save material');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this material?')) return;
    try {
      await inventoryAPI.deleteMaterial(id);
      loadData();
    } catch (error) {
      toast.error('Failed to delete material');
    }
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="toolbar">
        <input
          type="text"
          className="form-input"
          placeholder="Search materials..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <select
          className="form-select"
          value={filters.category_id}
          onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}
        >
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select
          className="form-select"
          value={filters.state}
          onChange={(e) => setFilters({ ...filters, state: e.target.value })}
        >
          <option value="">All States</option>
          <option value="available">Available</option>
          <option value="reserved">Reserved</option>
          <option value="damaged">Damaged</option>
        </select>
        <button className="btn btn-primary" onClick={() => openModal()}>+ Add Material</button>
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Name</th>
                <th>Category</th>
                <th>Location</th>
                <th>Quantity</th>
                <th>Unit Cost</th>
                <th>State</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {materials.length === 0 ? (
                <tr className="empty-row"><td colSpan="8">No materials found</td></tr>
              ) : materials.map(m => (
                <tr key={m.id}>
                  <td className="font-mono">{m.reference}</td>
                  <td className="font-bold">{m.name}</td>
                  <td>{m.category_name || '-'}</td>
                  <td>{m.location_name || '-'}</td>
                  <td className={m.is_low_stock ? 'text-danger font-bold' : ''}>{m.quantity} {m.unit}</td>
                  <td className="font-mono">${(m.unit_cost || 0).toFixed(2)}</td>
                  <td>
                    <span className={`badge badge-${m.state === 'available' ? 'success' : m.state === 'reserved' ? 'warning' : 'danger'}`}>
                      {m.state}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => openModal(m)}>Edit</button>
                    {user?.role === 'admin' && (
                      <button className="btn btn-danger btn-sm ml-2" onClick={() => handleDelete(m.id)}>Delete</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editItem ? 'Edit Material' : 'Add Material'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Reference *</label>
                  <input className="form-input" value={formData.reference || ''} onChange={(e) => setFormData({ ...formData, reference: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input className="form-input" value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-textarea" rows="2" value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <select className="form-select" value={formData.category_id || ''} onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}>
                      <option value="">Select</option>
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Location</label>
                    <select className="form-select" value={formData.location_id || ''} onChange={(e) => setFormData({ ...formData, location_id: e.target.value })}>
                      <option value="">Select</option>
                      {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid-3">
                  <div className="form-group">
                    <label className="form-label">Quantity</label>
                    <input type="number" className="form-input" value={formData.quantity || 0} onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Min Stock</label>
                    <input type="number" className="form-input" value={formData.min_stock || 0} onChange={(e) => setFormData({ ...formData, min_stock: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Unit</label>
                    <input className="form-input" value={formData.unit || 'units'} onChange={(e) => setFormData({ ...formData, unit: e.target.value })} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Unit Cost ($)</label>
                    <input type="number" step="0.01" className="form-input" value={formData.unit_cost || 0} onChange={(e) => setFormData({ ...formData, unit_cost: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">State</label>
                    <select className="form-select" value={formData.state || 'available'} onChange={(e) => setFormData({ ...formData, state: e.target.value })}>
                      <option value="available">Available</option>
                      <option value="reserved">Reserved</option>
                      <option value="damaged">Damaged</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
