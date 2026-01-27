/**
 * Workflow Node Types Configuration
 */

export const NODE_TYPES = {
  TRIGGER: 'trigger',
  ACTION: 'action',
  CONDITION: 'condition',
  PARALLEL: 'parallel',
  DELAY: 'delay',
  LOOP: 'loop',
  END: 'end',
};

export const NODE_CONFIGS = {
  [NODE_TYPES.TRIGGER]: {
    name: 'Trigger',
    icon: 'Zap',
    color: '#10b981',
    description: 'Start point of the workflow',
    maxConnections: { inputs: 0, outputs: 1 },
  },
  [NODE_TYPES.ACTION]: {
    name: 'Action',
    icon: 'Play',
    color: '#3b82f6',
    description: 'Execute an action',
    maxConnections: { inputs: -1, outputs: 1 },
  },
  [NODE_TYPES.CONDITION]: {
    name: 'Condition',
    icon: 'GitBranch',
    color: '#f59e0b',
    description: 'Branch based on conditions',
    maxConnections: { inputs: -1, outputs: -1 },
  },
  [NODE_TYPES.PARALLEL]: {
    name: 'Parallel',
    icon: 'GitFork',
    color: '#8b5cf6',
    description: 'Execute branches in parallel',
    maxConnections: { inputs: 1, outputs: -1 },
  },
  [NODE_TYPES.DELAY]: {
    name: 'Delay',
    icon: 'Clock',
    color: '#6b7280',
    description: 'Wait for a specified duration',
    maxConnections: { inputs: -1, outputs: 1 },
  },
  [NODE_TYPES.LOOP]: {
    name: 'Loop',
    icon: 'RefreshCw',
    color: '#ec4899',
    description: 'Iterate over items',
    maxConnections: { inputs: -1, outputs: 2 },
  },
  [NODE_TYPES.END]: {
    name: 'End',
    icon: 'Square',
    color: '#ef4444',
    description: 'End point of the workflow',
    maxConnections: { inputs: -1, outputs: 0 },
  },
};

export const getNodeConfig = (type) => NODE_CONFIGS[type] || NODE_CONFIGS[NODE_TYPES.ACTION];
