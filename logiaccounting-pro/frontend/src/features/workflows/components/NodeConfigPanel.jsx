/**
 * Node Configuration Panel
 * Right sidebar for configuring selected node
 */

import React, { useState, useEffect } from 'react';
import { X, Trash2, Info, ChevronDown, ChevronRight } from 'lucide-react';
import ConditionBuilder from './ConditionBuilder';
import VariablePicker from './VariablePicker';
import { workflowAPI } from '../services/workflowAPI';

const NodeConfigPanel = ({ node, onUpdate, onDelete, onClose }) => {
  const [actionMetadata, setActionMetadata] = useState(null);
  const [expandedSections, setExpandedSections] = useState(['basic', 'config']);
  const [showVariablePicker, setShowVariablePicker] = useState(null);

  useEffect(() => {
    if (node.action) {
      loadActionMetadata(node.action);
    }
  }, [node.action]);

  const loadActionMetadata = async (actionId) => {
    try {
      const response = await workflowAPI.getActions();
      const action = response.actions?.find(a => a.id === actionId);
      setActionMetadata(action);
    } catch (error) {
      console.error('Failed to load action metadata:', error);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const handleConfigChange = (key, value) => {
    onUpdate({
      config: { ...node.config, [key]: value },
    });
  };

  const handleConditionChange = (condition) => {
    onUpdate({ condition });
  };

  const handleInsertVariable = (variable, targetField) => {
    const currentValue = node.config?.[targetField] || '';
    handleConfigChange(targetField, currentValue + `{{${variable}}}`);
    setShowVariablePicker(null);
  };

  const renderInputField = (input) => {
    const value = node.config?.[input.name] ?? input.default ?? '';

    switch (input.type) {
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleConfigChange(input.name, e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Select...</option>
            {input.options?.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        );

      case 'textarea':
      case 'template':
        return (
          <div className="relative">
            <textarea
              value={value}
              onChange={(e) => handleConfigChange(input.name, e.target.value)}
              placeholder={input.placeholder}
              rows={4}
              className="w-full px-3 py-2 border rounded-lg text-sm resize-none"
            />
            <button
              onClick={() => setShowVariablePicker(input.name)}
              className="absolute right-2 top-2 text-xs text-blue-600 hover:underline"
            >
              + Variable
            </button>
          </div>
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleConfigChange(input.name, parseFloat(e.target.value))}
            placeholder={input.placeholder}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />
        );

      case 'boolean':
        return (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value === true}
              onChange={(e) => handleConfigChange(input.name, e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">{input.label}</span>
          </label>
        );

      default:
        return (
          <div className="relative">
            <input
              type="text"
              value={value}
              onChange={(e) => handleConfigChange(input.name, e.target.value)}
              placeholder={input.placeholder}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            />
            {input.type === 'email' || input.type === 'string' ? (
              <button
                onClick={() => setShowVariablePicker(input.name)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-blue-600 hover:underline"
              >
                + Var
              </button>
            ) : null}
          </div>
        );
    }
  };

  return (
    <div className="w-80 bg-white border-l flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Configure Step</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {/* Basic Settings */}
        <div className="border-b">
          <button
            onClick={() => toggleSection('basic')}
            className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Basic Settings
            {expandedSections.includes('basic') ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
          {expandedSections.includes('basic') && (
            <div className="px-4 pb-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={node.name || ''}
                  onChange={(e) => onUpdate({ name: e.target.value })}
                  placeholder="Step name"
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={node.description || ''}
                  onChange={(e) => onUpdate({ description: e.target.value })}
                  placeholder="Optional description"
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
            </div>
          )}
        </div>

        {/* Condition Config */}
        {node.type === 'condition' && (
          <div className="border-b">
            <button
              onClick={() => toggleSection('condition')}
              className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Condition
              {expandedSections.includes('condition') ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {expandedSections.includes('condition') && (
              <div className="px-4 pb-4">
                <ConditionBuilder
                  condition={node.condition || {}}
                  onChange={handleConditionChange}
                />
              </div>
            )}
          </div>
        )}

        {/* Loop Config */}
        {node.type === 'loop' && (
          <div className="border-b">
            <button
              onClick={() => toggleSection('loop')}
              className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Loop Settings
              {expandedSections.includes('loop') ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {expandedSections.includes('loop') && (
              <div className="px-4 pb-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Collection
                  </label>
                  <input
                    type="text"
                    value={node.collection || ''}
                    onChange={(e) => onUpdate({ collection: e.target.value })}
                    placeholder="{{records}}"
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Variable containing the list to iterate
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Item Variable
                  </label>
                  <input
                    type="text"
                    value={node.item_variable || ''}
                    onChange={(e) => onUpdate({ item_variable: e.target.value })}
                    placeholder="item"
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Name for current item (use as {"{{item}}"})
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Config */}
        {node.type === 'action' && actionMetadata && (
          <div className="border-b">
            <button
              onClick={() => toggleSection('config')}
              className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Configuration
              {expandedSections.includes('config') ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {expandedSections.includes('config') && (
              <div className="px-4 pb-4 space-y-4">
                {actionMetadata.inputs?.map(input => (
                  <div key={input.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {input.label}
                      {input.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {renderInputField(input)}
                    {input.description && (
                      <p className="text-xs text-gray-500 mt-1">{input.description}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Outputs */}
        {actionMetadata?.outputs?.length > 0 && (
          <div className="border-b">
            <button
              onClick={() => toggleSection('outputs')}
              className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Outputs
              {expandedSections.includes('outputs') ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {expandedSections.includes('outputs') && (
              <div className="px-4 pb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  {actionMetadata.outputs.map(output => (
                    <div key={output.name} className="flex items-center gap-2 py-1">
                      <code className="text-xs bg-white px-2 py-1 rounded">
                        {`{{${output.name}}}`}
                      </code>
                      <span className="text-xs text-gray-500">{output.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t">
        <button
          onClick={onDelete}
          className="w-full px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 flex items-center justify-center gap-2"
        >
          <Trash2 size={16} />
          Delete Step
        </button>
      </div>

      {/* Variable Picker Modal */}
      {showVariablePicker && (
        <VariablePicker
          onSelect={(variable) => handleInsertVariable(variable, showVariablePicker)}
          onClose={() => setShowVariablePicker(null)}
        />
      )}
    </div>
  );
};

export default NodeConfigPanel;
