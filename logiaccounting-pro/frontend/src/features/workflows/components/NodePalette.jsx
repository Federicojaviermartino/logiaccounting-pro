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
