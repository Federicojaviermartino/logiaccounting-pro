# Phase 30: Workflow Automation - Part 6: Frontend Components & History

## Overview
This part covers additional frontend components including node palette, config panels, trigger configuration, and execution history.

---

## File 1: Node Palette
**Path:** `frontend/src/features/workflows/components/NodePalette.jsx`

```jsx
/**
 * Node Palette Component
 * Sidebar with draggable nodes for the workflow builder
 */

import React, { useState, useEffect } from 'react';
import {
  Search,
  GitBranch,
  Repeat,
  Clock,
  Mail,
  MessageSquare,
  Bell,
  Database,
  Globe,
  Calculator,
  FileText,
  Users,
  CreditCard,
  Zap,
  StopCircle,
  Variable,
  CheckSquare,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const NodePalette = ({ onAddNode }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState(['flow_control', 'communication']);
  const [actions, setActions] = useState([]);

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    try {
      const response = await workflowAPI.getActions();
      setActions(response.actions || []);
    } catch (error) {
      console.error('Failed to load actions:', error);
    }
  };

  // Built-in flow control nodes
  const flowControlNodes = [
    {
      type: 'condition',
      name: 'Condition',
      description: 'Branch based on condition',
      icon: GitBranch,
      color: 'bg-yellow-500',
    },
    {
      type: 'loop',
      name: 'Loop',
      description: 'Iterate over a list',
      icon: Repeat,
      color: 'bg-purple-500',
    },
    {
      type: 'delay',
      name: 'Delay',
      description: 'Wait for duration',
      icon: Clock,
      color: 'bg-orange-500',
      action: 'delay',
    },
    {
      type: 'action',
      name: 'Stop',
      description: 'End workflow execution',
      icon: StopCircle,
      color: 'bg-red-500',
      action: 'stop_workflow',
    },
    {
      type: 'action',
      name: 'Set Variable',
      description: 'Set a variable value',
      icon: Variable,
      color: 'bg-gray-500',
      action: 'set_variable',
    },
    {
      type: 'action',
      name: 'Request Approval',
      description: 'Pause for approval',
      icon: CheckSquare,
      color: 'bg-indigo-500',
      action: 'request_approval',
    },
  ];

  // Map action icons
  const actionIcons = {
    send_email: Mail,
    send_sms: MessageSquare,
    send_slack: MessageSquare,
    send_notification: Bell,
    send_push: Bell,
    query_records: Database,
    create_record: FileText,
    update_record: FileText,
    delete_record: FileText,
    http_request: Globe,
    calculate: Calculator,
    transform_data: FileText,
    sync_quickbooks: CreditCard,
    charge_stripe: CreditCard,
    trigger_zapier: Zap,
    generate_pdf: FileText,
  };

  // Group actions by category
  const groupedActions = actions.reduce((acc, action) => {
    const category = action.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(action);
    return acc;
  }, {});

  const categoryLabels = {
    flow_control: 'Flow Control',
    communication: 'Communication',
    data: 'Data Operations',
    integration: 'Integrations',
    utility: 'Utilities',
    other: 'Other',
  };

  const toggleCategory = (category) => {
    setExpandedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const handleDragStart = (e, node) => {
    e.dataTransfer.setData('application/json', JSON.stringify(node));
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleNodeClick = (node) => {
    onAddNode(node.type, {
      action: node.action || node.id,
      name: node.name,
      defaultConfig: {},
    });
  };

  const filterNodes = (nodes) => {
    if (!searchQuery) return nodes;
    const query = searchQuery.toLowerCase();
    return nodes.filter(node =>
      node.name.toLowerCase().includes(query) ||
      node.description?.toLowerCase().includes(query)
    );
  };

  const renderNode = (node, index) => {
    const IconComponent = node.icon || actionIcons[node.id] || actionIcons[node.action] || Zap;
    const color = node.color || 'bg-blue-500';

    return (
      <div
        key={node.id || `${node.type}-${index}`}
        className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
        draggable
        onDragStart={(e) => handleDragStart(e, node)}
        onClick={() => handleNodeClick(node)}
      >
        <div className={`${color} p-2 rounded-lg text-white`}>
          <IconComponent size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {node.name}
          </div>
          <div className="text-xs text-gray-500 truncate">
            {node.description}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-64 bg-white border-r flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="font-semibold text-gray-900 mb-3">Add Step</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg"
          />
        </div>
      </div>

      {/* Node List */}
      <div className="flex-1 overflow-auto p-2">
        {/* Flow Control */}
        <div className="mb-4">
          <button
            onClick={() => toggleCategory('flow_control')}
            className="flex items-center gap-2 w-full px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
          >
            {expandedCategories.includes('flow_control') ? (
              <ChevronDown size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
            Flow Control
          </button>
          {expandedCategories.includes('flow_control') && (
            <div className="mt-1 space-y-1">
              {filterNodes(flowControlNodes).map((node, index) => renderNode(node, index))}
            </div>
          )}
        </div>

        {/* Action Categories */}
        {Object.entries(groupedActions).map(([category, categoryActions]) => (
          <div key={category} className="mb-4">
            <button
              onClick={() => toggleCategory(category)}
              className="flex items-center gap-2 w-full px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
            >
              {expandedCategories.includes(category) ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
              {categoryLabels[category] || category}
            </button>
            {expandedCategories.includes(category) && (
              <div className="mt-1 space-y-1">
                {filterNodes(categoryActions).map((action, index) => renderNode({
                  type: 'action',
                  id: action.id,
                  action: action.id,
                  name: action.name,
                  description: action.description,
                  icon: actionIcons[action.id],
                }, index))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Help text */}
      <div className="p-4 border-t bg-gray-50">
        <p className="text-xs text-gray-500">
          Click or drag nodes to add them to your workflow
        </p>
      </div>
    </div>
  );
};

export default NodePalette;
```

---

## File 2: Node Config Panel
**Path:** `frontend/src/features/workflows/components/NodeConfigPanel.jsx`

```jsx
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
```

---

## File 3: Condition Builder
**Path:** `frontend/src/features/workflows/components/ConditionBuilder.jsx`

```jsx
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
```

---

## File 4: Trigger Config Modal
**Path:** `frontend/src/features/workflows/components/TriggerConfig.jsx`

```jsx
/**
 * Trigger Configuration Modal
 * Configure workflow trigger settings
 */

import React, { useState, useEffect } from 'react';
import { X, Zap, Calendar, MousePointer, Webhook, AlertCircle } from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const TriggerConfig = ({ trigger, onSave, onClose }) => {
  const [triggerType, setTriggerType] = useState(trigger?.type || 'manual');
  const [config, setConfig] = useState(trigger || {});
  const [events, setEvents] = useState({});
  const [cronPreview, setCronPreview] = useState([]);
  const [cronError, setCronError] = useState(null);

  useEffect(() => {
    loadTriggerMetadata();
  }, []);

  useEffect(() => {
    if (triggerType === 'schedule' && config.cron) {
      validateCron(config.cron);
    }
  }, [config.cron]);

  const loadTriggerMetadata = async () => {
    try {
      const response = await workflowAPI.getTriggers();
      setEvents(response.events || {});
    } catch (error) {
      console.error('Failed to load trigger metadata:', error);
    }
  };

  const validateCron = async (cron) => {
    try {
      const response = await workflowAPI.validateCron(cron);
      if (response.valid) {
        setCronPreview(response.next_runs || []);
        setCronError(null);
      } else {
        setCronError(response.message);
        setCronPreview([]);
      }
    } catch (error) {
      setCronError('Failed to validate');
    }
  };

  const handleSave = () => {
    onSave({
      type: triggerType,
      ...config,
    });
  };

  const triggerTypes = [
    { id: 'manual', name: 'Manual', icon: MousePointer, description: 'Trigger manually via button or API' },
    { id: 'event', name: 'Event', icon: Zap, description: 'Trigger when an event occurs' },
    { id: 'schedule', name: 'Schedule', icon: Calendar, description: 'Run on a schedule' },
    { id: 'webhook', name: 'Webhook', icon: Webhook, description: 'Trigger via external webhook' },
  ];

  const schedulePresets = [
    { label: 'Every hour', cron: '0 * * * *' },
    { label: 'Daily at 9 AM', cron: '0 9 * * *' },
    { label: 'Daily at 6 PM', cron: '0 18 * * *' },
    { label: 'Weekly Monday 9 AM', cron: '0 9 * * 1' },
    { label: 'Monthly on 1st', cron: '0 9 1 * *' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[80vh] overflow-auto">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">Configure Trigger</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Trigger Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trigger Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {triggerTypes.map(type => {
                const Icon = type.icon;
                const isSelected = triggerType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => {
                      setTriggerType(type.id);
                      setConfig({ type: type.id });
                    }}
                    className={`p-3 border rounded-lg text-left transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon size={18} className={isSelected ? 'text-blue-600' : 'text-gray-500'} />
                      <span className="font-medium text-sm">{type.name}</span>
                    </div>
                    <p className="text-xs text-gray-500">{type.description}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Event Configuration */}
          {triggerType === 'event' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Event
              </label>
              <select
                value={config.event || ''}
                onChange={(e) => setConfig({ ...config, event: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">Choose an event...</option>
                {Object.entries(events).map(([category, categoryEvents]) => (
                  <optgroup key={category} label={category.replace(/_/g, ' ').toUpperCase()}>
                    {categoryEvents.map(event => (
                      <option key={event.type} value={event.type}>
                        {event.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              {config.event && (
                <p className="text-xs text-gray-500 mt-2">
                  {Object.values(events).flat().find(e => e.type === config.event)?.description}
                </p>
              )}
            </div>
          )}

          {/* Schedule Configuration */}
          {triggerType === 'schedule' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schedule Presets
                </label>
                <div className="flex flex-wrap gap-2">
                  {schedulePresets.map(preset => (
                    <button
                      key={preset.cron}
                      onClick={() => setConfig({ ...config, cron: preset.cron })}
                      className={`px-3 py-1 text-sm rounded-full border ${
                        config.cron === preset.cron
                          ? 'bg-blue-100 border-blue-500 text-blue-700'
                          : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cron Expression
                </label>
                <input
                  type="text"
                  value={config.cron || ''}
                  onChange={(e) => setConfig({ ...config, cron: e.target.value })}
                  placeholder="0 9 * * *"
                  className="w-full px-3 py-2 border rounded-lg font-mono"
                />
                {cronError && (
                  <div className="flex items-center gap-1 text-red-600 text-xs mt-1">
                    <AlertCircle size={12} />
                    {cronError}
                  </div>
                )}
                {cronPreview.length > 0 && (
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                    <div className="font-medium mb-1">Next runs:</div>
                    {cronPreview.slice(0, 3).map((time, i) => (
                      <div key={i} className="text-gray-600">
                        {new Date(time).toLocaleString()}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Webhook Configuration */}
          {triggerType === 'webhook' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Webhook URL
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm break-all">
                  https://api.logiaccounting.com/webhooks/trigger/[workflow_id]
                </code>
                <p className="text-xs text-gray-500 mt-2">
                  The webhook URL will be generated after saving the workflow.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save Trigger
          </button>
        </div>
      </div>
    </div>
  );
};

export default TriggerConfig;
```

---

## File 5: Variable Picker
**Path:** `frontend/src/features/workflows/components/VariablePicker.jsx`

```jsx
/**
 * Variable Picker Component
 * Modal for selecting and inserting variables
 */

import React, { useState, useEffect } from 'react';
import { X, Search, ChevronRight } from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const VariablePicker = ({ onSelect, onClose }) => {
  const [variables, setVariables] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    loadVariables();
  }, []);

  const loadVariables = async () => {
    try {
      const response = await workflowAPI.getVariables();
      setVariables(response);
    } catch (error) {
      console.error('Failed to load variables:', error);
    }
  };

  const filterVariables = (vars) => {
    if (!searchQuery) return vars;
    const query = searchQuery.toLowerCase();
    return vars.filter(v =>
      v.name.toLowerCase().includes(query) ||
      v.description?.toLowerCase().includes(query)
    );
  };

  if (!variables) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[70vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="font-semibold">Insert Variable</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search variables..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {/* System Variables */}
          <div className="p-2">
            <div className="text-xs font-medium text-gray-500 uppercase px-2 py-1">
              System Variables
            </div>
            {filterVariables(variables.system_variables || []).map(v => (
              <button
                key={v.name}
                onClick={() => onSelect(v.name)}
                className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-100 rounded"
              >
                <div>
                  <code className="text-sm text-blue-600">{`{{${v.name}}}`}</code>
                  <div className="text-xs text-gray-500">{v.description}</div>
                </div>
                <ChevronRight size={16} className="text-gray-400" />
              </button>
            ))}
          </div>

          {/* Context Variables */}
          {variables.context_variables?.map(category => (
            <div key={category.category} className="p-2">
              <div className="text-xs font-medium text-gray-500 uppercase px-2 py-1">
                {category.category}
              </div>
              {filterVariables(category.variables || []).map(v => (
                <button
                  key={v.name}
                  onClick={() => onSelect(v.name)}
                  className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-100 rounded"
                >
                  <div>
                    <code className="text-sm text-blue-600">{`{{${v.name}}}`}</code>
                    <div className="text-xs text-gray-500">{v.description}</div>
                  </div>
                  <ChevronRight size={16} className="text-gray-400" />
                </button>
              ))}
            </div>
          ))}

          {/* Entity Variables */}
          {Object.entries(variables.entity_variables || {}).map(([entity, fields]) => (
            <div key={entity} className="p-2">
              <div className="text-xs font-medium text-gray-500 uppercase px-2 py-1">
                {entity}
              </div>
              <div className="flex flex-wrap gap-1 px-2">
                {filterVariables(fields.map(f => ({ name: `${entity}.${f}` }))).map(v => (
                  <button
                    key={v.name}
                    onClick={() => onSelect(v.name)}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    {v.name}
                  </button>
                ))}
              </div>
            </div>
          ))}

          {/* Pipe Functions */}
          <div className="p-2 border-t">
            <div className="text-xs font-medium text-gray-500 uppercase px-2 py-1">
              Formatting Functions
            </div>
            <div className="px-2 text-xs text-gray-600">
              <p className="mb-1">Add to any variable with |function:</p>
              <div className="flex flex-wrap gap-1">
                {variables.pipe_functions?.map(f => (
                  <span key={f.name} className="px-2 py-1 bg-gray-100 rounded" title={f.description}>
                    |{f.name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VariablePicker;
```

---

## File 6: Execution History Page
**Path:** `frontend/src/features/workflows/pages/WorkflowExecutions.jsx`

```jsx
/**
 * Workflow Executions Page
 * View execution history and details
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Play,
} from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const WorkflowExecutions = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [workflow, setWorkflow] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [workflowData, executionsData] = await Promise.all([
        workflowAPI.getWorkflow(id),
        workflowAPI.getExecutions(id, 50),
      ]);
      setWorkflow(workflowData);
      setExecutions(executionsData.executions || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutionDetails = async (executionId) => {
    try {
      const data = await workflowAPI.getExecution(id, executionId);
      setSelectedExecution(data);
    } catch (error) {
      console.error('Failed to load execution:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={18} />;
      case 'failed': return <XCircle className="text-red-500" size={18} />;
      case 'running': return <RefreshCw className="text-blue-500 animate-spin" size={18} />;
      default: return <Clock className="text-gray-500" size={18} />;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-yellow-100 text-yellow-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.pending}`}>
        {status}
      </span>
    );
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/workflows')}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {workflow?.name} - Executions
          </h1>
          <p className="text-gray-600">View execution history and details</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="flex gap-6">
        {/* Execution List */}
        <div className="w-1/2">
          <div className="bg-white rounded-lg border">
            <div className="p-4 border-b">
              <h2 className="font-semibold">Recent Executions</h2>
            </div>
            <div className="divide-y max-h-[600px] overflow-auto">
              {executions.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No executions yet
                </div>
              ) : (
                executions.map(execution => (
                  <div
                    key={execution.id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer ${
                      selectedExecution?.id === execution.id ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => loadExecutionDetails(execution.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(execution.status)}
                        <span className="font-medium">{execution.id.slice(0, 12)}</span>
                      </div>
                      {getStatusBadge(execution.status)}
                    </div>
                    <div className="text-sm text-gray-600">
                      <div>Started: {new Date(execution.started_at).toLocaleString()}</div>
                      <div>Duration: {formatDuration(execution.duration_ms)}</div>
                      <div>Steps: {execution.steps_completed}/{execution.steps_total}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Execution Details */}
        <div className="w-1/2">
          {selectedExecution ? (
            <div className="bg-white rounded-lg border">
              <div className="p-4 border-b">
                <h2 className="font-semibold">Execution Details</h2>
              </div>
              <div className="p-4">
                {/* Status */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(selectedExecution.status)}
                    <span className="font-medium text-lg">
                      {selectedExecution.status.charAt(0).toUpperCase() + selectedExecution.status.slice(1)}
                    </span>
                  </div>
                  {selectedExecution.error && (
                    <div className="bg-red-50 text-red-700 p-3 rounded text-sm">
                      {selectedExecution.error}
                    </div>
                  )}
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                  <div>
                    <div className="text-gray-500">Started</div>
                    <div>{new Date(selectedExecution.started_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Completed</div>
                    <div>
                      {selectedExecution.completed_at
                        ? new Date(selectedExecution.completed_at).toLocaleString()
                        : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500">Duration</div>
                    <div>{formatDuration(selectedExecution.duration_ms)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Trigger</div>
                    <div>{selectedExecution.trigger_type || 'Manual'}</div>
                  </div>
                </div>

                {/* Steps */}
                <div>
                  <h3 className="font-medium mb-2">Steps</h3>
                  <div className="space-y-2">
                    {selectedExecution.steps?.map((step, index) => (
                      <div key={step.id} className="border rounded p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(step.status)}
                            <span className="font-medium text-sm">{step.node_id}</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatDuration(step.duration_ms)}
                          </span>
                        </div>
                        {step.error && (
                          <div className="text-xs text-red-600 mt-1">{step.error}</div>
                        )}
                        {step.output_data && Object.keys(step.output_data).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer">
                              Output
                            </summary>
                            <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(step.output_data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-8 text-center text-gray-500">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowExecutions;
```

---

## File 7: Workflow Routes Config
**Path:** `frontend/src/features/workflows/routes.jsx`

```jsx
/**
 * Workflow Routes Configuration
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';

import WorkflowList from './pages/WorkflowList';
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowExecutions from './pages/WorkflowExecutions';

const WorkflowRoutes = () => {
  return (
    <Routes>
      <Route index element={<WorkflowList />} />
      <Route path="new" element={<WorkflowBuilder />} />
      <Route path=":id/edit" element={<WorkflowBuilder />} />
      <Route path=":id/executions" element={<WorkflowExecutions />} />
    </Routes>
  );
};

export default WorkflowRoutes;
```

---

## File 8: Workflows Index
**Path:** `frontend/src/features/workflows/index.js`

```javascript
/**
 * Workflows Feature Module
 */

// Pages
export { default as WorkflowList } from './pages/WorkflowList';
export { default as WorkflowBuilder } from './pages/WorkflowBuilder';
export { default as WorkflowExecutions } from './pages/WorkflowExecutions';

// Components
export { default as WorkflowCanvas } from './components/WorkflowCanvas';
export { default as WorkflowNode } from './components/WorkflowNode';
export { default as EdgeLine } from './components/EdgeLine';
export { default as NodePalette } from './components/NodePalette';
export { default as NodeConfigPanel } from './components/NodeConfigPanel';
export { default as ConditionBuilder } from './components/ConditionBuilder';
export { default as TriggerConfig } from './components/TriggerConfig';
export { default as VariablePicker } from './components/VariablePicker';

// Services
export { workflowAPI } from './services/workflowAPI';

// Routes
export { default as WorkflowRoutes } from './routes';
```

---

## Summary Part 6

| File | Description | Lines |
|------|-------------|-------|
| `components/NodePalette.jsx` | Node palette sidebar | ~240 |
| `components/NodeConfigPanel.jsx` | Node configuration panel | ~280 |
| `components/ConditionBuilder.jsx` | Condition builder | ~180 |
| `components/TriggerConfig.jsx` | Trigger configuration modal | ~260 |
| `components/VariablePicker.jsx` | Variable picker modal | ~180 |
| `pages/WorkflowExecutions.jsx` | Execution history page | ~240 |
| `routes.jsx` | Routes configuration | ~25 |
| `index.js` | Feature module exports | ~30 |
| **Total** | | **~1,435 lines** |
