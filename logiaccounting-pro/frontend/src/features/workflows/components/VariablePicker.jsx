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
