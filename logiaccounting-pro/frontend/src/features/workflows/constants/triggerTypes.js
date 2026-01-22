/**
 * Workflow Trigger Types Configuration
 */

export const TRIGGER_TYPES = {
  ENTITY_EVENT: 'entity_event',
  SCHEDULE: 'schedule',
  WEBHOOK: 'webhook',
  MANUAL: 'manual',
};

export const TRIGGER_CONFIGS = {
  [TRIGGER_TYPES.ENTITY_EVENT]: {
    name: 'Entity Event',
    icon: 'Database',
    description: 'Trigger when an entity is created, updated, or deleted',
    fields: [
      { name: 'entity', label: 'Entity Type', type: 'select', required: true },
      { name: 'event', label: 'Event Type', type: 'select', required: true },
      { name: 'conditions', label: 'Conditions', type: 'conditions' },
    ],
  },
  [TRIGGER_TYPES.SCHEDULE]: {
    name: 'Schedule',
    icon: 'Calendar',
    description: 'Trigger on a schedule (cron expression)',
    fields: [
      { name: 'cron', label: 'Cron Expression', type: 'cron', required: true },
      { name: 'timezone', label: 'Timezone', type: 'timezone', default: 'UTC' },
    ],
  },
  [TRIGGER_TYPES.WEBHOOK]: {
    name: 'Webhook',
    icon: 'Link',
    description: 'Trigger via HTTP webhook',
    fields: [
      { name: 'webhook_path', label: 'Webhook Path', type: 'text', required: true },
      { name: 'method', label: 'HTTP Method', type: 'select', default: 'POST' },
    ],
  },
  [TRIGGER_TYPES.MANUAL]: {
    name: 'Manual',
    icon: 'Hand',
    description: 'Trigger manually by a user',
    fields: [
      { name: 'allowed_roles', label: 'Allowed Roles', type: 'multiselect' },
      { name: 'parameters', label: 'Input Parameters', type: 'parameters' },
    ],
  },
};

export const ENTITY_TYPES = [
  { value: 'invoice', label: 'Invoice' },
  { value: 'payment', label: 'Payment' },
  { value: 'project', label: 'Project' },
  { value: 'client', label: 'Client' },
  { value: 'expense', label: 'Expense' },
  { value: 'inventory', label: 'Inventory' },
  { value: 'employee', label: 'Employee' },
  { value: 'approval', label: 'Approval' },
];

export const EVENT_TYPES = [
  { value: 'created', label: 'Created' },
  { value: 'updated', label: 'Updated' },
  { value: 'deleted', label: 'Deleted' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
  { value: 'completed', label: 'Completed' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'low_stock', label: 'Low Stock' },
];

export const getTriggerConfig = (type) => TRIGGER_CONFIGS[type] || TRIGGER_CONFIGS[TRIGGER_TYPES.MANUAL];
