/**
 * EndNode Component - Workflow end node
 */
import React, { memo } from 'react';
import { BaseNode } from './BaseNode';

export const EndNode = memo(({ data, selected }) => {
  return (
    <BaseNode
      data={data}
      selected={selected}
      type="end"
      showOutputHandle={false}
    >
      <div className="text-center py-2">
        <div className="text-xs text-gray-500">
          Workflow ends here
        </div>
      </div>
    </BaseNode>
  );
});

EndNode.displayName = 'EndNode';
