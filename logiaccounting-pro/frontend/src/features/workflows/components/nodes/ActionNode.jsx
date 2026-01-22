/**
 * ActionNode Component - Workflow action node
 */
import React, { memo } from 'react';
import { BaseNode } from './BaseNode';
import { ACTION_CONFIGS } from '../../constants/actionTypes';

export const ActionNode = memo(({ data, selected }) => {
  const actionType = data.config?.action_type || 'log';
  const actionConfig = ACTION_CONFIGS[actionType] || {};

  return (
    <BaseNode data={data} selected={selected} type="action">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Action:
          </span>
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
            {actionConfig.name || 'Log'}
          </span>
        </div>

        {actionType === 'send_email' && data.config?.template && (
          <div className="text-xs text-gray-500">
            Template: {data.config.template}
          </div>
        )}

        {actionType === 'notification' && data.config?.title && (
          <div className="text-xs text-gray-500 truncate">
            "{data.config.title}"
          </div>
        )}

        {actionType === 'webhook' && data.config?.url && (
          <div className="text-xs text-gray-500 truncate">
            {data.config.method || 'POST'} {data.config.url}
          </div>
        )}

        {actionType === 'update_entity' && data.config?.entity && (
          <div className="text-xs text-gray-500">
            Update {data.config.entity}
          </div>
        )}

        {actionType === 'approval' && (
          <div className="text-xs text-gray-500">
            Requires approval
          </div>
        )}
      </div>
    </BaseNode>
  );
});

ActionNode.displayName = 'ActionNode';
