import { useState } from 'react';

export default function AdvancedFilters({
  filters,
  onFiltersChange,
  filterConfig,
  onSavePreset,
  savedPresets = [],
  onLoadPreset,
  onDeletePreset
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [showPresetModal, setShowPresetModal] = useState(false);

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    const clearedFilters = {};
    Object.keys(filters).forEach(key => {
      clearedFilters[key] = '';
    });
    onFiltersChange(clearedFilters);
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      onSavePreset({ name: presetName, filters: { ...filters } });
      setPresetName('');
      setShowPresetModal(false);
    }
  };

  const activeFilterCount = Object.values(filters).filter(v => v !== '' && v !== null && v !== undefined).length;

  return (
    <div className="advanced-filters">
      {/* Filter Header */}
      <div className="filter-header">
        <button
          className="btn btn-secondary"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          Filters {activeFilterCount > 0 && <span className="filter-badge">{activeFilterCount}</span>}
        </button>

        {activeFilterCount > 0 && (
          <button className="btn btn-sm btn-secondary" onClick={clearFilters}>
            Clear All
          </button>
        )}

        {savedPresets.length > 0 && (
          <div className="preset-dropdown">
            <select
              className="form-select form-select-sm"
              onChange={(e) => e.target.value && onLoadPreset(e.target.value)}
              value=""
            >
              <option value="">Load Preset...</option>
              {savedPresets.map(preset => (
                <option key={preset.id} value={preset.id}>{preset.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="filter-panel">
          <div className="filter-grid">
            {filterConfig.map(config => (
              <div key={config.key} className="filter-item">
                <label className="filter-label">{config.label}</label>

                {config.type === 'select' && (
                  <select
                    className="form-select form-select-sm"
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  >
                    <option value="">All</option>
                    {config.options.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}

                {config.type === 'text' && (
                  <input
                    type="text"
                    className="form-input form-input-sm"
                    placeholder={config.placeholder || ''}
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  />
                )}

                {config.type === 'date' && (
                  <input
                    type="date"
                    className="form-input form-input-sm"
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  />
                )}

                {config.type === 'dateRange' && (
                  <div className="date-range">
                    <input
                      type="date"
                      className="form-input form-input-sm"
                      value={filters[`${config.key}_from`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_from`, e.target.value)}
                    />
                    <span>to</span>
                    <input
                      type="date"
                      className="form-input form-input-sm"
                      value={filters[`${config.key}_to`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_to`, e.target.value)}
                    />
                  </div>
                )}

                {config.type === 'amountRange' && (
                  <div className="amount-range">
                    <input
                      type="number"
                      className="form-input form-input-sm"
                      placeholder="Min"
                      value={filters[`${config.key}_min`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_min`, e.target.value)}
                    />
                    <span>-</span>
                    <input
                      type="number"
                      className="form-input form-input-sm"
                      placeholder="Max"
                      value={filters[`${config.key}_max`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_max`, e.target.value)}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Filter Actions */}
          {onSavePreset && (
            <div className="filter-actions">
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setShowPresetModal(true)}
              >
                Save as Preset
              </button>
            </div>
          )}
        </div>
      )}

      {/* Quick Filter Chips */}
      {activeFilterCount > 0 && (
        <div className="filter-chips">
          {Object.entries(filters).map(([key, value]) => {
            if (!value) return null;
            const config = filterConfig.find(c => c.key === key || c.key + '_from' === key || c.key + '_to' === key || c.key + '_min' === key || c.key + '_max' === key);
            const label = config?.label || key;
            return (
              <span key={key} className="filter-chip">
                {label}: {value}
                <button onClick={() => handleFilterChange(key, '')}>x</button>
              </span>
            );
          })}
        </div>
      )}

      {/* Save Preset Modal */}
      {showPresetModal && (
        <div className="modal-overlay" onClick={() => setShowPresetModal(false)}>
          <div className="modal-content modal-sm" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Save Filter Preset</h3>
              <button className="modal-close" onClick={() => setShowPresetModal(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Preset Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="e.g., Monthly Expenses"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowPresetModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSavePreset}>Save Preset</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
