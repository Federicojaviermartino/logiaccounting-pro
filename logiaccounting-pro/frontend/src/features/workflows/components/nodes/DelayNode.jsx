/**
 * DelayNode Component - Delay/wait node
 */
import React, { memo } from 'react';
import { BaseNode } from './BaseNode';

export const DelayNode = memo(({ data, selected }) => {
  const duration = data.config?.duration || 0;
  const unit = data.config?.unit || 'minutes';

  const formatDuration = () => {
    if (duration === 0) return 'No delay';
    if (duration === 1) return `${duration} ${unit.slice(0, -1)}`;
    return `${duration} ${unit}`;
  };

  return (
    <BaseNode data={data} selected={selected} type="delay">
      <div className="space-y-2">
        <div className="flex items-center justify-center gap-2 py-2">
          <span className="text-2xl font-bold text-gray-700 dark:text-gray-300">
            {duration}
          </span>
          <span className="text-sm text-gray-500">
            {unit}
          </span>
        </div>

        <div className="text-xs text-center text-gray-500">
          {formatDuration()}
        </div>
      </div>
    </BaseNode>
  );
});

DelayNode.displayName = 'DelayNode';
