import { useState, useEffect } from 'react';
import { movementsAPI, inventoryAPI, projectsAPI } from '../services/api';

export default function Movements() {
  const [movements, setMovements] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [projects, setProjects] = useState([]);
  const [filters, setFilters] = useState({ type: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({ type: 'entry', material_id: '', quantity: '', project_id: '', notes: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [filters]);

  const loadData = async () => {
    try {
      const [movRes, matRes, projRes] = await Promise.all([
        movementsAPI.getMovements(filters),
        inventoryAPI.getMaterials({}),
        projectsAPI.getProjects({})
      ]);
      setMovements(movRes.data.movements || []);
      setMaterials(matRes.data.materials || []);
      setProjects(projRes.data.projects || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (type) => {
    setFormData({ type, material_id: '', quantity: '', project_id: '', notes: '' });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await movementsAPI.createMovement({ ...formData, quantity: parseFloat(formData.quantity) });
      setModalOpen(false);
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save movement');
    }
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="toolbar">
        <select
          className="form-select"
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
        >
          <option value="">All Types</option>
          <option value="entry">Entry</option>
          <option value="exit">Exit</option>
        </select>
        <button className="btn btn-success" onClick={() => openModal('entry')}>📥 Stock Entry</button>
        <button className="btn btn-danger" onClick={() => openModal('exit')}>📤 Stock Exit</button>
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Material</th>
                <th>Reference</th>
                <th>Quantity</th>
                <th>Project</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {movements.length === 0 ? (
                <tr className="empty-row"><td colSpan="7">No movements found</td></tr>
              ) : movements.map(m => (
                <tr key={m.id}>
                  <td>{new Date(m.created_at).toLocaleString()}</td>
                  <td>
                    <span className={`badge badge-${m.type === 'entry' ? 'success' : 'danger'}`}>
                      {m.type}
                    </span>
                  </td>
                  <td className="font-bold">{m.material_name}</td>
                  <td className="font-mono">{m.material_reference}</td>
                  <td className={`font-bold ${m.type === 'entry' ? 'text-success' : 'text-danger'}`}>
                    {m.type === 'entry' ? '+' : '-'}{m.quantity}
                  </td>
                  <td>{m.project_code || '-'}</td>
                  <td>{m.notes || '-'}</td>
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
              <h3 className="modal-title">Stock {formData.type === 'entry' ? 'Entry' : 'Exit'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Material *</label>
                  <select className="form-select" value={formData.material_id} onChange={(e) => setFormData({ ...formData, material_id: e.target.value })} required>
                    <option value="">Select material</option>
                    {materials.map(m => <option key={m.id} value={m.id}>{m.name} (Stock: {m.quantity} {m.unit})</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity *</label>
                  <input type="number" className="form-input" min="1" value={formData.quantity} onChange={(e) => setFormData({ ...formData, quantity: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Project (Optional)</label>
                  <select className="form-select" value={formData.project_id} onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}>
                    <option value="">None</option>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Notes</label>
                  <textarea className="form-textarea" rows="2" value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Movement</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
