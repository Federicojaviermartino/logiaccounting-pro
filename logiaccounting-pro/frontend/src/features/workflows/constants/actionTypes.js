/**
 * Workflow Action Types Configuration
 */

export const ACTION_TYPES = {
  SEND_EMAIL: 'send_email',
  NOTIFICATION: 'notification',
  WEBHOOK: 'webhook',
  UPDATE_ENTITY: 'update_entity',
  CREATE_ENTITY: 'create_entity',
  DELETE_ENTITY: 'delete_entity',
  APPROVAL: 'approval',
  DELAY: 'delay',
  SCRIPT: 'script',
  ASSIGN: 'assign',
  LOG: 'log',
};

export const ACTION_CONFIGS = {
  [ACTION_TYPES.SEND_EMAIL]: {
    name: 'Send Email',
    icon: 'Mail',
    category: 'communication',
    description: 'Send an email to recipients',
    fields: [
      { name: 'template', label: 'Email Template', type: 'select' },
      { name: 'recipients', label: 'Recipients', type: 'recipients', required: true },
      { name: 'subject', label: 'Subject', type: 'text' },
      { name: 'body', label: 'Body', type: 'richtext' },
      { name: 'cc', label: 'CC', type: 'recipients' },
    ],
  },
  [ACTION_TYPES.NOTIFICATION]: {
    name: 'Send Notification',
    icon: 'Bell',
    category: 'communication',
    description: 'Create in-app notification',
    fields: [
      { name: 'recipients', label: 'Recipients', type: 'recipients', required: true },
      { name: 'title', label: 'Title', type: 'text', required: true },
      { name: 'message', label: 'Message', type: 'textarea', required: true },
      { name: 'priority', label: 'Priority', type: 'select', default: 'normal' },
      { name: 'link', label: 'Link URL', type: 'text' },
    ],
  },
  [ACTION_TYPES.WEBHOOK]: {
    name: 'HTTP Request',
    icon: 'Globe',
    category: 'integration',
    description: 'Make an HTTP request to external service',
    fields: [
      { name: 'url', label: 'URL', type: 'text', required: true },
      { name: 'method', label: 'Method', type: 'select', default: 'POST' },
      { name: 'headers', label: 'Headers', type: 'keyvalue' },
      { name: 'body', label: 'Request Body', type: 'json' },
      { name: 'expected_status', label: 'Expected Status', type: 'number', default: 200 },
    ],
  },
  [ACTION_TYPES.UPDATE_ENTITY]: {
    name: 'Update Entity',
    icon: 'Edit',
    category: 'data',
    description: 'Update an existing entity',
    fields: [
      { name: 'entity', label: 'Entity Type', type: 'select', required: true },
      { name: 'id', label: 'Entity ID', type: 'expression', required: true },
      { name: 'updates', label: 'Field Updates', type: 'keyvalue', required: true },
    ],
  },
  [ACTION_TYPES.CREATE_ENTITY]: {
    name: 'Create Entity',
    icon: 'PlusCircle',
    category: 'data',
    description: 'Create a new entity',
    fields: [
      { name: 'entity', label: 'Entity Type', type: 'select', required: true },
      { name: 'data', label: 'Entity Data', type: 'keyvalue', required: true },
    ],
  },
  [ACTION_TYPES.DELETE_ENTITY]: {
    name: 'Delete Entity',
    icon: 'Trash',
    category: 'data',
    description: 'Delete an entity',
    fields: [
      { name: 'entity', label: 'Entity Type', type: 'select', required: true },
      { name: 'id', label: 'Entity ID', type: 'expression', required: true },
      { name: 'soft_delete', label: 'Soft Delete', type: 'boolean', default: true },
    ],
  },
  [ACTION_TYPES.APPROVAL]: {
    name: 'Request Approval',
    icon: 'CheckSquare',
    category: 'workflow',
    description: 'Request approval from users',
    fields: [
      { name: 'approvers', label: 'Approvers', type: 'recipients' },
      { name: 'approver_role', label: 'Approver Role', type: 'select' },
      { name: 'title', label: 'Title', type: 'text', required: true },
      { name: 'description', label: 'Description', type: 'textarea' },
      { name: 'timeout_hours', label: 'Timeout (hours)', type: 'number', default: 24 },
      { name: 'require_all', label: 'Require All Approvers', type: 'boolean', default: false },
    ],
  },
  [ACTION_TYPES.DELAY]: {
    name: 'Delay',
    icon: 'Clock',
    category: 'workflow',
    description: 'Wait for a specified duration',
    fields: [
      { name: 'duration', label: 'Duration', type: 'number', required: true },
      { name: 'unit', label: 'Unit', type: 'select', default: 'minutes' },
    ],
  },
  [ACTION_TYPES.SCRIPT]: {
    name: 'Run Script',
    icon: 'Code',
    category: 'advanced',
    description: 'Execute custom script',
    fields: [
      { name: 'language', label: 'Language', type: 'select', default: 'javascript' },
      { name: 'code', label: 'Code', type: 'code', required: true },
      { name: 'timeout', label: 'Timeout (seconds)', type: 'number', default: 30 },
    ],
  },
  [ACTION_TYPES.ASSIGN]: {
    name: 'Set Variable',
    icon: 'Variable',
    category: 'workflow',
    description: 'Set a workflow variable',
    fields: [
      { name: 'variable', label: 'Variable Name', type: 'text', required: true },
      { name: 'value', label: 'Value', type: 'expression', required: true },
    ],
  },
  [ACTION_TYPES.LOG]: {
    name: 'Log Message',
    icon: 'FileText',
    category: 'debugging',
    description: 'Log a message for debugging',
    fields: [
      { name: 'level', label: 'Level', type: 'select', default: 'info' },
      { name: 'message', label: 'Message', type: 'textarea', required: true },
    ],
  },
};

export const ACTION_CATEGORIES = [
  { id: 'communication', name: 'Communication', icon: 'MessageCircle' },
  { id: 'data', name: 'Data Operations', icon: 'Database' },
  { id: 'workflow', name: 'Workflow Control', icon: 'GitBranch' },
  { id: 'integration', name: 'Integrations', icon: 'Globe' },
  { id: 'advanced', name: 'Advanced', icon: 'Settings' },
  { id: 'debugging', name: 'Debugging', icon: 'Bug' },
];

export const getActionConfig = (type) => ACTION_CONFIGS[type] || ACTION_CONFIGS[ACTION_TYPES.LOG];

export const getActionsByCategory = (category) => {
  return Object.entries(ACTION_CONFIGS)
    .filter(([_, config]) => config.category === category)
    .map(([type, config]) => ({ type, ...config }));
};
