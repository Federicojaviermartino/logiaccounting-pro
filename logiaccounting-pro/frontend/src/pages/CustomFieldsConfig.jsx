import { useState, useEffect } from 'react';
import { customFieldsAPI } from '../services/api';

export default function CustomFieldsConfig() {
  const [fields, setFields] = useState([]);
  const [entities, setEntities] = useState([]);
  const [fieldTypes, setFieldTypes] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState('materials');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingField, setEditingField] = useState(null);

  const [formData, setFormData] = useState({
    entity: 'materials',
    name: '',
    label: '',
    type: 'text',
    required: false,
    default_value: '',
    options: '',
    placeholder: '',
    help_text: '',
    position: 0,
    searchable: false,
    show_in_list: false
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadFields();
  }, [selectedEntity]);

  const loadInitialData = async () => {
    try {
      const [entitiesRes, typesRes] = await Promise.all([
        customFieldsAPI.getEntities(),
        customFieldsAPI.getTypes()
      ]);
      setEntities(entitiesRes.data.entities);
      setFieldTypes(typesRes.data.types);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const loadFields = async () => {
    setLoading(true);
    try {
      const res = await customFieldsAPI.getEntityFields(selectedEntity, false);
      setFields(res.data.fields);
    } catch (err) {
      console.error('Failed to load fields:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        options: formData.options ? formData.options.split(',').map(o => o.trim()) : []
      };

      if (editingField) {
        await customFieldsAPI.update(editingField.id, data);
      } else {
        await customFieldsAPI.create(data);
      }

      setShowForm(false);
      setEditingField(null);
      resetForm();
      loadFields();
    } catch (err) {
      alert('Failed to save field');
    }
  };

  const resetForm = () => {
    setFormData({
      entity: selectedEntity,
      name: '',
      label: '',
      type: 'text',
      required: false,
      default_value: '',
      options: '',
      placeholder: '',
      help_text: '',
      position: fields.length,
      searchable: false,
      show_in_list: false
    });
  };

  const handleEdit = (field) => {
    setEditingField(field);
    setFormData({
      ...field,
      options: field.options?.join(', ') || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (field) => {
    if (!confirm(`Delete field "${field.label}"? This will remove all values.`)) return;
    try {
      await customFieldsAPI.delete(field.id);
      loadFields();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleToggleActive = async (field) => {
    try {
      await customFieldsAPI.update(field.id, { active: !field.active });
      loadFields();
    } catch (err) {
      alert('Failed to toggle');
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      text: 'T', textarea: '=', number: '#', currency: '$',
      date: 'D', datetime: 'DT', dropdown: 'v', multiselect: '[]',
      checkbox: '[x]', url: '@', email: '@', phone: '#', formula: 'fx'
    };
    return icons[type] || 'T';
  };

  return (
    <>
      <div className="info-banner mb-6">
        Define custom fields to extend your data without code changes.
      </div>

      {/* Entity Tabs */}
      <div className="entity-tabs mb-6">
        {entities.map(entity => (
          <button
            key={entity}
            className={`tab ${selectedEntity === entity ? 'active' : ''}`}
            onClick={() => setSelectedEntity(entity)}
          >
            {entity.charAt(0).toUpperCase() + entity.slice(1)}
          </button>
        ))}
      </div>

      {/* Fields List */}
      <div className="section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>
            Custom Fields for {selectedEntity}
          </h3>
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
            + Add Field
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : fields.length === 0 ? (
          <div className="text-center text-muted">No custom fields defined</div>
        ) : (
          <div className="fields-list">
            {fields.map(field => (
              <div key={field.id} className={`field-card ${!field.active ? 'inactive' : ''}`}>
                <div className="field-icon">{getTypeIcon(field.type)}</div>
                <div className="field-info">
                  <div className="field-label">
                    {field.label}
                    {field.required && <span className="required">*</span>}
                  </div>
                  <div className="field-meta">
                    <code>{field.name}</code>
                    <span className="badge badge-info">{field.type}</span>
                    {field.searchable && <span className="badge badge-gray">Searchable</span>}
                    {field.show_in_list && <span className="badge badge-gray">In List</span>}
                  </div>
                  {field.help_text && <div className="field-help">{field.help_text}</div>}
                </div>
                <div className="field-actions">
                  <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(field)}>
                    Edit
                  </button>
                  <button
                    className={`btn btn-sm ${field.active ? 'btn-warning' : 'btn-success'}`}
                    onClick={() => handleToggleActive(field)}
                  >
                    {field.active ? 'Disable' : 'Enable'}
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(field)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingField ? 'Edit Field' : 'Add Custom Field'}</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Field Name (code) *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                    placeholder="warranty_months"
                    disabled={!!editingField}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Label *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.label}
                    onChange={(e) => setFormData({ ...formData, label: e.target.value })}
                    placeholder="Warranty (Months)"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Type *</label>
                  <select
                    className="form-select"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    disabled={!!editingField}
                  >
                    {fieldTypes.map(t => (
                      <option key={t} value={t}>{getTypeIcon(t)} {t}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Default Value</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.default_value || ''}
                    onChange={(e) => setFormData({ ...formData, default_value: e.target.value })}
                  />
                </div>
                {(formData.type === 'dropdown' || formData.type === 'multiselect') && (
                  <div className="form-group full-width">
                    <label className="form-label">Options (comma separated)</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.options}
                      onChange={(e) => setFormData({ ...formData, options: e.target.value })}
                      placeholder="Option 1, Option 2, Option 3"
                    />
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Placeholder</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.placeholder}
                    onChange={(e) => setFormData({ ...formData, placeholder: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Position</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div className="form-group full-width">
                  <label className="form-label">Help Text</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.help_text}
                    onChange={(e) => setFormData({ ...formData, help_text: e.target.value })}
                    placeholder="Additional information about this field"
                  />
                </div>
              </div>
              <div className="checkbox-group mt-4">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.required}
                    onChange={(e) => setFormData({ ...formData, required: e.target.checked })}
                  />
                  Required
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.searchable}
                    onChange={(e) => setFormData({ ...formData, searchable: e.target.checked })}
                  />
                  Searchable
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.show_in_list}
                    onChange={(e) => setFormData({ ...formData, show_in_list: e.target.checked })}
                  />
                  Show in List
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={!formData.name || !formData.label}
              >
                {editingField ? 'Update' : 'Create'} Field
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
