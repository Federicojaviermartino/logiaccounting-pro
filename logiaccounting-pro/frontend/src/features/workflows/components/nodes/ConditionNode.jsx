/**
 * ConditionNode Component - Workflow condition/branching node
 */
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { BaseNode } from './BaseNode';

export const ConditionNode = memo(({ data, selected }) => {
  const conditions = data.config?.conditions || [];

  return (
    <BaseNode
      data={data}
      selected={selected}
      type="condition"
      showOutputHandle={false}
    >
      <div className="space-y-2">
        {conditions.length > 0 ? (
          conditions.map((condition, index) => (
            <div
              key={condition.id || index}
              className="text-xs bg-amber-50 text-amber-800 px-2 py-1 rounded border border-amber-200"
            >
              {condition.label || `Branch ${index + 1}`}
            </div>
          ))
        ) : (
          <div className="text-xs text-gray-500">
            No conditions defined
          </div>
        )}

        {data.config?.default && (
          <div className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
            Default branch
          </div>
        )}
      </div>

      {conditions.map((condition, index) => (
        <Handle
          key={condition.id || index}
          type="source"
          position={Position.Bottom}
          id={condition.id || `branch-${index}`}
          className="w-3 h-3 !bg-amber-400 border-2 border-white"
          style={{ left: `${((index + 1) / (conditions.length + 1)) * 100}%` }}
        />
      ))}

      {data.config?.default && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="default"
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
          style={{ left: '90%' }}
        />
      )}
    </BaseNode>
  );
});

ConditionNode.displayName = 'ConditionNode';
