# Phase 30: Workflow Automation

## Overview

Build a comprehensive Workflow Automation system that enables users to automate repetitive business processes with visual workflow builder, triggers, conditions, and actions.

---

## Roadmap Update

| Phase | Feature | Status |
|-------|---------|--------|
| 28 | Mobile API & PWA | ✅ Complete |
| 29 | Integration Hub | ✅ Complete |
| 30 | Workflow Automation | 🚧 Current |
| 31 | AI/ML Features | 📋 Planned |
| 32 | Advanced Security | 📋 Planned |
| 33 | Performance & Scaling | 📋 Planned |

---

## Phase 30 Features

### 1. Workflow Engine

#### 1.1 Core Components
- **Workflow Definition**: JSON-based workflow schema
- **Execution Engine**: Async workflow runner
- **State Machine**: Track workflow/step states
- **Variable System**: Dynamic data passing between steps
- **Error Handling**: Retry, fallback, and error recovery

#### 1.2 Workflow States
```
┌─────────┐    ┌─────────┐    ┌───────────┐    ┌───────────┐
│  Draft  │───>│ Active  │───>│  Running  │───>│ Completed │
└─────────┘    └─────────┘    └───────────┘    └───────────┘
                    │              │                  │
                    │              v                  │
                    │         ┌─────────┐            │
                    └────────>│  Failed │<───────────┘
                              └─────────┘
                                   │
                                   v
                              ┌─────────┐
                              │ Retrying│
                              └─────────┘
```

### 2. Trigger System

#### 2.1 Event Triggers
| Trigger | Description |
|---------|-------------|
| `invoice.created` | New invoice created |
| `invoice.sent` | Invoice sent to customer |
| `invoice.overdue` | Invoice past due date |
| `payment.received` | Payment received |
| `customer.created` | New customer added |
| `project.status_changed` | Project status updated |
| `ticket.created` | Support ticket created |
| `ticket.escalated` | Ticket priority increased |

#### 2.2 Schedule Triggers
| Type | Example |
|------|---------|
| Cron | `0 9 * * 1` (Every Monday 9am) |
| Interval | Every 4 hours |
| Daily | At specific time |
| Weekly | Specific day/time |
| Monthly | Specific date/time |

#### 2.3 Manual Triggers
- Button click from UI
- API call
- Webhook received

### 3. Action System

#### 3.1 Communication Actions
- Send Email
- Send SMS (via Twilio)
- Send Slack Message
- Send Push Notification
- Create In-App Notification

#### 3.2 Data Actions
- Create Record (Invoice, Customer, Project, Ticket)
- Update Record
- Delete Record
- Calculate Value
- Transform Data

#### 3.3 Integration Actions
- Sync to QuickBooks
- Charge via Stripe
- Create Zapier Event
- Call External API (HTTP Request)

#### 3.4 Flow Control Actions
- Condition (If/Else)
- Switch (Multiple branches)
- Loop (For Each)
- Delay (Wait)
- Parallel (Run simultaneously)
- Stop Workflow

### 4. Condition Builder

#### 4.1 Operators
| Type | Operators |
|------|-----------|
| Comparison | `equals`, `not_equals`, `greater_than`, `less_than`, `contains`, `starts_with`, `ends_with` |
| Logical | `and`, `or`, `not` |
| Existence | `is_empty`, `is_not_empty`, `exists`, `not_exists` |
| Date | `before`, `after`, `between`, `days_ago`, `days_from_now` |

#### 4.2 Example Condition
```json
{
  "type": "and",
  "conditions": [
    {
      "field": "invoice.amount",
      "operator": "greater_than",
      "value": 1000
    },
    {
      "field": "customer.type",
      "operator": "equals",
      "value": "enterprise"
    }
  ]
}
```

### 5. Visual Workflow Builder

#### 5.1 Features
- Drag-and-drop interface
- Node-based editor
- Real-time validation
- Test execution mode
- Version history
- Import/Export workflows

#### 5.2 Node Types
- **Trigger Node**: Starting point (green)
- **Action Node**: Performs action (blue)
- **Condition Node**: Decision point (yellow)
- **End Node**: Workflow completion (red)

---

## Technical Architecture

### Backend Structure
```
backend/app/
├── workflows/
│   ├── __init__.py
│   ├── engine.py           # Workflow execution engine
│   ├── triggers.py         # Trigger definitions & handlers
│   ├── actions.py          # Action definitions & handlers
│   ├── conditions.py       # Condition evaluator
│   ├── scheduler.py        # Cron/schedule manager
│   ├── variables.py        # Variable resolution
│   └── templates.py        # Workflow templates
├── routes/
│   └── workflows.py        # Workflow API routes
├── services/
│   └── workflow_service.py # Workflow business logic
├── models/
│   └── workflow.py         # Workflow data models
```

### Frontend Structure
```
frontend/src/
├── features/
│   └── workflows/
│       ├── pages/
│       │   ├── WorkflowList.jsx
│       │   ├── WorkflowBuilder.jsx
│       │   ├── WorkflowDetail.jsx
│       │   └── WorkflowHistory.jsx
│       ├── components/
│       │   ├── WorkflowCanvas.jsx
│       │   ├── NodePalette.jsx
│       │   ├── TriggerNode.jsx
│       │   ├── ActionNode.jsx
│       │   ├── ConditionNode.jsx
│       │   ├── NodeEditor.jsx
│       │   ├── ConditionBuilder.jsx
│       │   ├── VariablePicker.jsx
│       │   └── ExecutionLog.jsx
│       └── services/
│           └── workflowAPI.js
```

---

## Implementation Parts

| Part | Content | Files |
|------|---------|-------|
| Part 1 | Workflow Engine Core | 6 files |
| Part 2 | Triggers & Scheduler | 5 files |
| Part 3 | Actions Library | 5 files |
| Part 4 | Backend Routes & Service | 4 files |
| Part 5 | Frontend Workflow Builder | 8 files |
| Part 6 | Frontend Components & History | 6 files |

---

## Workflow Schema

### Workflow Definition
```json
{
  "id": "wf_001",
  "name": "Invoice Reminder Workflow",
  "description": "Send reminders for overdue invoices",
  "version": 1,
  "status": "active",
  "trigger": {
    "type": "schedule",
    "config": {
      "cron": "0 9 * * *"
    }
  },
  "nodes": [
    {
      "id": "node_1",
      "type": "action",
      "action": "query_records",
      "config": {
        "entity": "invoices",
        "filter": {
          "status": "overdue",
          "days_overdue": { "$gte": 7 }
        }
      },
      "outputs": ["invoices"]
    },
    {
      "id": "node_2",
      "type": "loop",
      "collection": "{{invoices}}",
      "item_variable": "invoice",
      "body": ["node_3", "node_4"]
    },
    {
      "id": "node_3",
      "type": "condition",
      "condition": {
        "field": "{{invoice.reminder_count}}",
        "operator": "less_than",
        "value": 3
      },
      "true_branch": ["node_4"],
      "false_branch": ["node_5"]
    },
    {
      "id": "node_4",
      "type": "action",
      "action": "send_email",
      "config": {
        "to": "{{invoice.customer.email}}",
        "template": "invoice_reminder",
        "variables": {
          "invoice_number": "{{invoice.number}}",
          "amount": "{{invoice.amount}}",
          "due_date": "{{invoice.due_date}}"
        }
      }
    },
    {
      "id": "node_5",
      "type": "action",
      "action": "create_ticket",
      "config": {
        "subject": "Escalate: Invoice {{invoice.number}} severely overdue",
        "priority": "high",
        "assign_to": "collections_team"
      }
    }
  ],
  "edges": [
    { "from": "trigger", "to": "node_1" },
    { "from": "node_1", "to": "node_2" },
    { "from": "node_2", "to": "node_3" },
    { "from": "node_3", "to": "node_4", "condition": "true" },
    { "from": "node_3", "to": "node_5", "condition": "false" }
  ]
}
```

---

## API Specifications

### GET /api/workflows
List all workflows.

**Response:**
```json
{
  "workflows": [
    {
      "id": "wf_001",
      "name": "Invoice Reminder",
      "status": "active",
      "trigger_type": "schedule",
      "last_run": "2024-01-15T09:00:00Z",
      "run_count": 45,
      "success_rate": 98.5
    }
  ],
  "total": 12,
  "page": 1
}
```

### POST /api/workflows
Create new workflow.

**Request:**
```json
{
  "name": "New Customer Welcome",
  "trigger": {
    "type": "event",
    "event": "customer.created"
  },
  "nodes": [...],
  "edges": [...]
}
```

### POST /api/workflows/{id}/execute
Manually execute workflow.

**Request:**
```json
{
  "input_data": {
    "customer_id": "cust_001"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_001",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/workflows/{id}/executions
Get workflow execution history.

**Response:**
```json
{
  "executions": [
    {
      "id": "exec_001",
      "status": "completed",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:05Z",
      "duration_ms": 5230,
      "steps_completed": 5,
      "steps_total": 5
    }
  ]
}
```

---

## Workflow Templates

### 1. Invoice Reminder
Automatically send reminders for overdue invoices.

### 2. Welcome Email Sequence
Send series of onboarding emails to new customers.

### 3. Payment Thank You
Send thank you email after payment received.

### 4. Project Status Update
Notify stakeholders when project status changes.

### 5. Ticket Escalation
Escalate tickets not responded within SLA.

### 6. Weekly Report
Generate and send weekly business summary.

### 7. Lead Qualification
Score and route new leads based on criteria.

### 8. Contract Renewal
Remind customers before contract expiration.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Workflow Creation Time | < 10 min |
| Execution Success Rate | > 99% |
| Average Execution Time | < 30s |
| User Adoption | > 40% |
| Automation Hours Saved | > 100h/month |
