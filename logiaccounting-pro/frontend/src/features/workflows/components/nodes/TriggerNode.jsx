/**
 * TriggerNode Component - Workflow trigger/start node
 */
import React, { memo } from 'react';
import { BaseNode } from './BaseNode';
import { TRIGGER_CONFIGS } from '../../constants/triggerTypes';

export const TriggerNode = memo(({ data, selected }) => {
  const triggerType = data.config?.type || 'manual';
  const triggerConfig = TRIGGER_CONFIGS[triggerType] || {};

  return (
    <BaseNode
      data={data}
      selected={selected}
      type="trigger"
      showInputHandle={false}
    >
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Type:
          </span>
          <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
            {triggerConfig.name || 'Manual'}
          </span>
        </div>

        {triggerType === 'entity_event' && data.config?.entity && (
          <div className="text-xs text-gray-500">
            On {data.config.entity} {data.config.event || 'event'}
          </div>
        )}

        {triggerType === 'schedule' && data.config?.cron && (
          <div className="text-xs text-gray-500">
            Schedule: {data.config.cron}
          </div>
        )}

        {triggerType === 'webhook' && data.config?.webhook_path && (
          <div className="text-xs text-gray-500 truncate">
            Path: {data.config.webhook_path}
          </div>
        )}
      </div>
    </BaseNode>
  );
});

TriggerNode.displayName = 'TriggerNode';
