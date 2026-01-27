/**
 * BaseNode Component - Base wrapper for all workflow nodes
 */
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { NODE_CONFIGS } from '../../constants/nodeTypes';

export const BaseNode = memo(({
  data,
  selected,
  type,
  showInputHandle = true,
  showOutputHandle = true,
  children
}) => {
  const config = NODE_CONFIGS[type] || {};
  const { color = '#3b82f6' } = config;

  return (
    <div
      className={`
        relative min-w-[180px] rounded-lg shadow-md border-2 transition-all
        ${selected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
        bg-white dark:bg-gray-800
      `}
      style={{ borderColor: color }}
    >
      {showInputHandle && type !== 'trigger' && (
        <Handle
          type="target"
          position={Position.Top}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}

      <div
        className="px-3 py-2 rounded-t-md text-white text-sm font-medium"
        style={{ backgroundColor: color }}
      >
        {data.name || config.name || 'Node'}
      </div>

      <div className="p-3">
        {children}
        {data.description && (
          <p className="text-xs text-gray-500 mt-2">{data.description}</p>
        )}
      </div>

      {showOutputHandle && type !== 'end' && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-3 h-3 !bg-gray-400 border-2 border-white"
        />
      )}
    </div>
  );
});

BaseNode.displayName = 'BaseNode';
