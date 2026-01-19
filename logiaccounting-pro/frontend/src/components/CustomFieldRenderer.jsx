import { useState, useEffect } from 'react';

export default function CustomFieldRenderer({ field, value, onChange, readonly = false }) {
  const renderField = () => {
    switch (field.type) {
      case 'text':
      case 'url':
      case 'email':
      case 'phone':
        return (
          <input
            type={field.type === 'email' ? 'email' : field.type === 'url' ? 'url' : 'text'}
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            disabled={readonly}
          />
        );

      case 'textarea':
        return (
          <textarea
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            rows={3}
            disabled={readonly}
          />
        );

      case 'number':
      case 'currency':
        return (
          <input
            type="number"
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
            placeholder={field.placeholder}
            min={field.validation?.min}
            max={field.validation?.max}
            step={field.type === 'currency' ? '0.01' : '1'}
            disabled={readonly}
          />
        );

      case 'date':
        return (
          <input
            type="date"
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={readonly}
          />
        );

      case 'datetime':
        return (
          <input
            type="datetime-local"
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={readonly}
          />
        );

      case 'dropdown':
        return (
          <select
            className="form-select"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={readonly}
          >
            <option value="">Select...</option>
            {field.options?.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );

      case 'multiselect':
        return (
          <div className="multiselect">
            {field.options?.map(opt => (
              <label key={opt} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={(value || []).includes(opt)}
                  onChange={(e) => {
                    const current = value || [];
                    if (e.target.checked) {
                      onChange([...current, opt]);
                    } else {
                      onChange(current.filter(v => v !== opt));
                    }
                  }}
                  disabled={readonly}
                />
                {opt}
              </label>
            ))}
          </div>
        );

      case 'checkbox':
        return (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={!!value}
              onChange={(e) => onChange(e.target.checked)}
              disabled={readonly}
            />
            {field.label}
          </label>
        );

      default:
        return (
          <input
            type="text"
            className="form-input"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={readonly}
          />
        );
    }
  };

  return (
    <div className="custom-field">
      {field.type !== 'checkbox' && (
        <label className="form-label">
          {field.label}
          {field.required && <span className="required">*</span>}
        </label>
      )}
      {renderField()}
      {field.help_text && <div className="form-help">{field.help_text}</div>}
    </div>
  );
}
