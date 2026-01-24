/**
 * Condition Builder Component
 * Visual builder for workflow conditions
 */

import React, { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const ConditionBuilder = ({ condition, onChange }) => {
  const [operators, setOperators] = useState({});
  const [presets, setPresets] = useState([]);

  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    try {
      const response = await workflowAPI.getConditions();
      setOperators(response.operators || {});
      setPresets(response.presets || []);
    } catch (error) {
      console.error('Failed to load condition metadata:', error);
    }
  };

  const isCompound = condition.type === 'and' || condition.type === 'or';
  const conditions = isCompound ? (condition.conditions || []) : [];

  const handleTypeChange = (type) => {
    if (type === 'simple') {
      onChange({ field: '', operator: 'equals', value: '' });
    } else {
      onChange({ type, conditions: [{ field: '', operator: 'equals', value: '' }] });
    }
  };

  const handleSimpleChange = (key, value) => {
    onChange({ ...condition, [key]: value });
  };

  const handleConditionChange = (index, updates) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    onChange({ ...condition, conditions: newConditions });
  };

  const addCondition = () => {
    onChange({
      ...condition,
      conditions: [...conditions, { field: '', operator: 'equals', value: '' }],
    });
  };

  const removeCondition = (index) => {
    onChange({
      ...condition,
      conditions: conditions.filter((_, i) => i !== index),
    });
  };

  const applyPreset = (presetId) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      onChange(preset.condition);
    }
  };

  const getOperatorsForType = (fieldType = 'string') => {
    return operators[fieldType] || operators.string || [];
  };

  const renderConditionRow = (cond, index = null) => {
    const isSimple = index === null;
    const handleChange = isSimple
      ? handleSimpleChange
      : (key, value) => handleConditionChange(index, { [key]: value });

    return (
      <div className="space-y-2">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Field</label>
          <input
            type="text"
            value={cond.field || ''}
            onChange={(e) => handleChange('field', e.target.value)}
            placeholder="invoice.amount"
            className="w-full px-3 py-2 border rounded text-sm"
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Operator</label>
            <select
              value={cond.operator || 'equals'}
              onChange={(e) => handleChange('operator', e.target.value)}
              className="w-full px-3 py-2 border rounded text-sm"
            >
              {getOperatorsForType('string').map(op => (
                <option key={op.value} value={op.value}>{op.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Value</label>
            <input
              type="text"
              value={cond.value ?? ''}
              onChange={(e) => handleChange('value', e.target.value)}
              placeholder="1000"
              className="w-full px-3 py-2 border rounded text-sm"
            />
          </div>
        </div>
        {!isSimple && (
          <button
            onClick={() => removeCondition(index)}
            className="text-xs text-red-600 hover:underline"
          >
            Remove
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Presets */}
      {presets.length > 0 && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Quick presets</label>
          <select
            onChange={(e) => e.target.value && applyPreset(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm"
            value=""
          >
            <option value="">Select a preset...</option>
            {presets.map(preset => (
              <option key={preset.id} value={preset.id}>{preset.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Type selector */}
      <div>
        <label className="block text-xs text-gray-500 mb-1">Condition type</label>
        <select
          value={isCompound ? condition.type : 'simple'}
          onChange={(e) => handleTypeChange(e.target.value)}
          className="w-full px-3 py-2 border rounded text-sm"
        >
          <option value="simple">Simple condition</option>
          <option value="and">All conditions (AND)</option>
          <option value="or">Any condition (OR)</option>
        </select>
      </div>

      {/* Conditions */}
      {isCompound ? (
        <div className="space-y-4">
          {conditions.map((cond, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-lg">
              {index > 0 && (
                <div className="text-xs font-medium text-gray-500 mb-2 uppercase">
                  {condition.type}
                </div>
              )}
              {renderConditionRow(cond, index)}
            </div>
          ))}
          <button
            onClick={addCondition}
            className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
          >
            <Plus size={14} />
            Add condition
          </button>
        </div>
      ) : (
        renderConditionRow(condition)
      )}
    </div>
  );
};

export default ConditionBuilder;
