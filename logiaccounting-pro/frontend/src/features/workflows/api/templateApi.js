/**
 * Template API - Workflow template library
 */

const API_BASE = '/api/v1';

const BUILTIN_TEMPLATES = [
  {
    id: 'invoice-reminder',
    name: 'Invoice Payment Reminder',
    description: 'Automatically send payment reminders for overdue invoices',
    category: 'invoicing',
    trigger: {
      type: 'schedule',
      cron: '0 9 * * *',
    },
    nodes: [
      {
        id: 'trigger-1',
        type: 'trigger',
        name: 'Daily Check',
        position: { x: 100, y: 100 },
      },
      {
        id: 'condition-1',
        type: 'condition',
        name: 'Check Overdue',
        config: {
          conditions: [
            { expression: '{{invoice.days_overdue}} > 7' }
          ]
        },
        position: { x: 300, y: 100 },
      },
      {
        id: 'action-1',
        type: 'action',
        name: 'Send Reminder',
        config: {
          action_type: 'send_email',
          template: 'payment_reminder',
        },
        position: { x: 500, y: 100 },
      },
    ],
  },
  {
    id: 'low-stock-alert',
    name: 'Low Stock Alert',
    description: 'Send notifications when inventory falls below threshold',
    category: 'inventory',
    trigger: {
      type: 'entity_event',
      entity: 'inventory',
      event: 'low_stock',
    },
    nodes: [
      {
        id: 'trigger-1',
        type: 'trigger',
        name: 'Stock Event',
        position: { x: 100, y: 100 },
      },
      {
        id: 'action-1',
        type: 'action',
        name: 'Notify Manager',
        config: {
          action_type: 'notification',
          template: 'low_stock_alert',
        },
        position: { x: 300, y: 100 },
      },
    ],
  },
  {
    id: 'expense-approval',
    name: 'Expense Approval Workflow',
    description: 'Route expense requests for approval based on amount',
    category: 'approvals',
    trigger: {
      type: 'entity_event',
      entity: 'expense',
      event: 'created',
    },
    nodes: [
      {
        id: 'trigger-1',
        type: 'trigger',
        name: 'New Expense',
        position: { x: 100, y: 100 },
      },
      {
        id: 'condition-1',
        type: 'condition',
        name: 'Check Amount',
        config: {
          conditions: [
            { id: 'high', expression: '{{expense.amount}} > 1000', next: 'action-approval' },
            { id: 'low', expression: '{{expense.amount}} <= 1000', next: 'action-auto' }
          ]
        },
        position: { x: 300, y: 100 },
      },
      {
        id: 'action-approval',
        type: 'action',
        name: 'Request Approval',
        config: {
          action_type: 'approval',
          approver_role: 'finance_manager',
        },
        position: { x: 500, y: 50 },
      },
      {
        id: 'action-auto',
        type: 'action',
        name: 'Auto Approve',
        config: {
          action_type: 'update_entity',
          updates: { status: 'approved' },
        },
        position: { x: 500, y: 150 },
      },
    ],
  },
  {
    id: 'new-client-onboarding',
    name: 'New Client Onboarding',
    description: 'Welcome sequence for new clients',
    category: 'clients',
    trigger: {
      type: 'entity_event',
      entity: 'client',
      event: 'created',
    },
    nodes: [
      {
        id: 'trigger-1',
        type: 'trigger',
        name: 'New Client',
        position: { x: 100, y: 100 },
      },
      {
        id: 'action-1',
        type: 'action',
        name: 'Send Welcome Email',
        config: {
          action_type: 'send_email',
          template: 'client_welcome',
        },
        position: { x: 300, y: 100 },
      },
      {
        id: 'delay-1',
        type: 'delay',
        name: 'Wait 3 Days',
        config: {
          duration: 3,
          unit: 'days',
        },
        position: { x: 500, y: 100 },
      },
      {
        id: 'action-2',
        type: 'action',
        name: 'Follow-up Email',
        config: {
          action_type: 'send_email',
          template: 'client_followup',
        },
        position: { x: 700, y: 100 },
      },
    ],
  },
];

export async function getTemplates(params = {}) {
  let templates = [...BUILTIN_TEMPLATES];

  if (params.category) {
    templates = templates.filter(t => t.category === params.category);
  }

  if (params.search) {
    const search = params.search.toLowerCase();
    templates = templates.filter(t =>
      t.name.toLowerCase().includes(search) ||
      t.description.toLowerCase().includes(search)
    );
  }

  return templates;
}

export async function getTemplate(templateId) {
  const template = BUILTIN_TEMPLATES.find(t => t.id === templateId);

  if (!template) {
    throw new Error('Template not found');
  }

  return template;
}

export async function getTemplateCategories() {
  const categories = [...new Set(BUILTIN_TEMPLATES.map(t => t.category))];
  return categories.map(c => ({
    id: c,
    name: c.charAt(0).toUpperCase() + c.slice(1),
  }));
}

export async function createFromTemplate(templateId, customizations = {}) {
  const template = await getTemplate(templateId);

  const workflowData = {
    name: customizations.name || template.name,
    description: customizations.description || template.description,
    trigger: { ...template.trigger, ...customizations.trigger },
    nodes: template.nodes.map(node => ({
      ...node,
      id: `${node.id}-${Date.now()}`,
    })),
    tags: ['from-template', template.category],
    category: template.category,
  };

  return workflowData;
}
