/**
 * ParallelNode Component - Parallel execution node
 */
import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { BaseNode } from './BaseNode';

export const ParallelNode = memo(({ data, selected }) => {
  const branches = data.config?.branches || [];
  const waitAll = data.config?.wait_all !== false;

  return (
    <BaseNode
      data={data}
      selected={selected}
      type="parallel"
      showOutputHandle={false}
    >
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Branches:
          </span>
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
            {branches.length || 0}
          </span>
        </div>

        <div className="text-xs text-gray-500">
          {waitAll ? 'Wait for all branches' : 'Continue after first completion'}
        </div>

        {branches.map((branch, index) => (
          <div
            key={branch.id || index}
            className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded border border-purple-200"
          >
            {branch.name || `Branch ${index + 1}`}
          </div>
        ))}
      </div>

      {branches.map((branch, index) => (
        <Handle
          key={branch.id || index}
          type="source"
          position={Position.Bottom}
          id={branch.id || `parallel-${index}`}
          className="w-3 h-3 !bg-purple-400 border-2 border-white"
          style={{ left: `${((index + 1) / (branches.length + 1)) * 100}%` }}
        />
      ))}
    </BaseNode>
  );
});

ParallelNode.displayName = 'ParallelNode';
