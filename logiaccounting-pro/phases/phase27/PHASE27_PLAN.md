# Phase 27: Customer Portal v2 - Self-Service Hub
## Enterprise Customer Experience Platform

---

## Executive Summary

**Phase 27** transforms the basic client portal into a comprehensive **Customer Self-Service Hub** that integrates CRM, support ticketing, knowledge base, communication center, and collaboration tools. This positions LogiAccounting Pro as a complete customer experience platform competing with Zendesk, HubSpot Service Hub, and Salesforce Experience Cloud.

### Strategic Value

| Metric | Target |
|--------|--------|
| Support Ticket Deflection | 40% via self-service |
| Customer Satisfaction | +25% CSAT improvement |
| Admin Time Saved | 15 hours/week |
| Customer Engagement | 3x portal visits |
| Quote Acceptance Rate | +20% faster |

### Competitive Advantages

| vs Zendesk | vs HubSpot | vs Salesforce |
|------------|------------|---------------|
| ✅ Integrated accounting | ✅ Native CRM integration | ✅ Simpler setup |
| ✅ Project visibility | ✅ No per-seat cost | ✅ Lower cost |
| ✅ Quote acceptance | ✅ Invoice payments | ✅ Unified platform |
| ✅ Knowledge base | ✅ Workflow automation | ✅ White-label ready |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER PORTAL V2 ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     CUSTOMER PORTAL FRONTEND                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │Dashboard │ │ Support  │ │ Projects │ │ Payments │            │  │
│  │  │   Hub    │ │ Center   │ │  & Docs  │ │& Invoices│            │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │Knowledge │ │  Quote   │ │ Messages │ │ Account  │            │  │
│  │  │  Base    │ │ Manager  │ │  Center  │ │ Settings │            │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     PORTAL API GATEWAY                            │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │  │
│  │  │Auth & Token │ │ Rate Limit  │ │ Portal Scope│                 │  │
│  │  │  Middleware │ │  Per Tenant │ │ Enforcement │                 │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     PORTAL SERVICES                               │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │  │
│  │  │  Ticket   │ │ Knowledge │ │  Message  │ │   Quote   │        │  │
│  │  │  Service  │ │  Service  │ │  Service  │ │  Service  │        │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │  │
│  │  │  Project  │ │  Payment  │ │  Document │ │  Account  │        │  │
│  │  │ Visibility│ │  Portal   │ │  Manager  │ │  Manager  │        │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     CORE PLATFORM INTEGRATION                     │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │  │
│  │  │    CRM    │ │ Invoices  │ │  Projects │ │ Workflows │        │  │
│  │  │  Module   │ │  Module   │ │   Module  │ │  Engine   │        │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Feature Catalog (96 Features)

### Category 1: Customer Hub Dashboard (12 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 1.1 | Personalized welcome dashboard | P0 | 8 |
| 1.2 | Recent activity feed | P0 | 6 |
| 1.3 | Quick action cards | P0 | 4 |
| 1.4 | Open ticket summary | P0 | 4 |
| 1.5 | Pending invoice widget | P0 | 4 |
| 1.6 | Active projects overview | P1 | 6 |
| 1.7 | Upcoming payments calendar | P1 | 6 |
| 1.8 | Quote status tracker | P1 | 4 |
| 1.9 | Unread messages badge | P1 | 3 |
| 1.10 | Announcements banner | P2 | 4 |
| 1.11 | Custom widget placement | P2 | 8 |
| 1.12 | Dashboard analytics | P2 | 6 |
| | **Subtotal** | | **63h** |

### Category 2: Support Ticketing System (16 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 2.1 | Create support ticket | P0 | 8 |
| 2.2 | Ticket categories & priorities | P0 | 6 |
| 2.3 | Ticket detail view | P0 | 6 |
| 2.4 | Reply to ticket | P0 | 6 |
| 2.5 | File attachments on tickets | P0 | 6 |
| 2.6 | Ticket status tracking | P0 | 4 |
| 2.7 | Ticket history timeline | P1 | 6 |
| 2.8 | Ticket satisfaction rating | P1 | 4 |
| 2.9 | Reopen closed ticket | P1 | 3 |
| 2.10 | Related tickets | P1 | 4 |
| 2.11 | Escalation request | P1 | 4 |
| 2.12 | SLA visibility | P2 | 6 |
| 2.13 | Ticket export (PDF) | P2 | 4 |
| 2.14 | Canned responses (customer) | P2 | 4 |
| 2.15 | Ticket search & filters | P1 | 6 |
| 2.16 | Email notifications | P0 | 6 |
| | **Subtotal** | | **83h** |

### Category 3: Knowledge Base (14 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 3.1 | Article categories | P0 | 6 |
| 3.2 | Article display | P0 | 6 |
| 3.3 | Search articles | P0 | 8 |
| 3.4 | Popular articles section | P0 | 4 |
| 3.5 | Recently viewed articles | P1 | 3 |
| 3.6 | Article helpfulness voting | P1 | 4 |
| 3.7 | Related articles | P1 | 4 |
| 3.8 | Article sharing | P2 | 3 |
| 3.9 | Print article | P2 | 2 |
| 3.10 | Video tutorials | P1 | 6 |
| 3.11 | Step-by-step guides | P1 | 8 |
| 3.12 | FAQ section | P0 | 6 |
| 3.13 | Search suggestions | P2 | 6 |
| 3.14 | Article feedback form | P2 | 4 |
| | **Subtotal** | | **70h** |

### Category 4: Communication Center (12 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 4.1 | Conversation threads | P0 | 10 |
| 4.2 | Send message to team | P0 | 6 |
| 4.3 | Message attachments | P0 | 6 |
| 4.4 | Real-time message delivery | P0 | 8 |
| 4.5 | Read receipts | P1 | 4 |
| 4.6 | Typing indicators | P2 | 4 |
| 4.7 | Message search | P1 | 6 |
| 4.8 | Pin important messages | P2 | 3 |
| 4.9 | Message reactions | P2 | 4 |
| 4.10 | Conversation archive | P1 | 4 |
| 4.11 | Email fallback notifications | P0 | 6 |
| 4.12 | Message templates | P2 | 4 |
| | **Subtotal** | | **65h** |

### Category 5: Project Visibility (10 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 5.1 | Project list view | P0 | 6 |
| 5.2 | Project detail page | P0 | 8 |
| 5.3 | Project timeline/Gantt | P1 | 12 |
| 5.4 | Milestone tracking | P0 | 6 |
| 5.5 | Project status updates | P0 | 4 |
| 5.6 | Project documents access | P0 | 6 |
| 5.7 | Project budget visibility | P1 | 6 |
| 5.8 | Deliverable approvals | P1 | 8 |
| 5.9 | Project comments/feedback | P1 | 6 |
| 5.10 | Project notifications | P0 | 4 |
| | **Subtotal** | | **66h** |

### Category 6: Quote & Contract Management (10 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 6.1 | Quote list view | P0 | 6 |
| 6.2 | Quote detail display | P0 | 8 |
| 6.3 | Accept quote online | P0 | 8 |
| 6.4 | Decline with reason | P0 | 4 |
| 6.5 | Request quote revision | P1 | 6 |
| 6.6 | E-signature for quotes | P0 | 12 |
| 6.7 | Quote PDF download | P0 | 4 |
| 6.8 | Contract document viewer | P1 | 8 |
| 6.9 | Contract e-signature | P1 | 12 |
| 6.10 | Quote comparison | P2 | 8 |
| | **Subtotal** | | **76h** |

### Category 7: Payment Portal (12 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 7.1 | Invoice list & filters | P0 | 6 |
| 7.2 | Invoice detail view | P0 | 6 |
| 7.3 | Pay invoice online | P0 | 12 |
| 7.4 | Multiple payment methods | P0 | 8 |
| 7.5 | Payment history | P0 | 6 |
| 7.6 | Payment receipt download | P0 | 4 |
| 7.7 | Auto-pay setup | P1 | 10 |
| 7.8 | Payment reminders settings | P1 | 6 |
| 7.9 | Partial payments | P1 | 8 |
| 7.10 | Payment dispute | P2 | 8 |
| 7.11 | Saved payment methods | P1 | 8 |
| 7.12 | Statement download | P0 | 6 |
| | **Subtotal** | | **88h** |

### Category 8: Document Management (10 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 8.1 | Document library view | P0 | 6 |
| 8.2 | Document categories | P0 | 4 |
| 8.3 | Document upload | P0 | 6 |
| 8.4 | Document preview | P0 | 8 |
| 8.5 | Document download | P0 | 3 |
| 8.6 | Document sharing | P1 | 6 |
| 8.7 | Version history | P1 | 6 |
| 8.8 | Digital signature requests | P1 | 10 |
| 8.9 | Document expiry alerts | P2 | 4 |
| 8.10 | Bulk download | P2 | 4 |
| | **Subtotal** | | **57h** |

### Category 9: Account Management (10 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 9.1 | Profile settings | P0 | 6 |
| 9.2 | Password change | P0 | 4 |
| 9.3 | Two-factor authentication | P0 | 8 |
| 9.4 | Notification preferences | P0 | 6 |
| 9.5 | Contact information update | P0 | 4 |
| 9.6 | User preferences (theme) | P1 | 4 |
| 9.7 | Language selection | P1 | 3 |
| 9.8 | Session management | P1 | 4 |
| 9.9 | API access (read-only) | P2 | 8 |
| 9.10 | Data export request | P2 | 6 |
| | **Subtotal** | | **53h** |

### Category 10: Portal Customization (10 features)

| ID | Feature | Priority | Hours |
|----|---------|----------|-------|
| 10.1 | Custom branding (logo, colors) | P0 | 8 |
| 10.2 | Custom domain support | P1 | 12 |
| 10.3 | Welcome message customization | P0 | 3 |
| 10.4 | Feature toggles per tenant | P0 | 6 |
| 10.5 | Custom CSS injection | P2 | 6 |
| 10.6 | Portal analytics dashboard | P1 | 10 |
| 10.7 | Customer segments | P2 | 8 |
| 10.8 | Onboarding wizard | P1 | 12 |
| 10.9 | Custom fields visibility | P1 | 6 |
| 10.10 | Multi-language content | P2 | 10 |
| | **Subtotal** | | **81h** |

---

## Total Estimation

| Category | Features | Hours |
|----------|----------|-------|
| Customer Hub Dashboard | 12 | 63h |
| Support Ticketing | 16 | 83h |
| Knowledge Base | 14 | 70h |
| Communication Center | 12 | 65h |
| Project Visibility | 10 | 66h |
| Quote & Contract | 10 | 76h |
| Payment Portal | 12 | 88h |
| Document Management | 10 | 57h |
| Account Management | 10 | 53h |
| Portal Customization | 10 | 81h |
| **TOTAL** | **96** | **702h** |

**Timeline: ~17-18 weeks** (assuming 40h/week)

---

## Database Schema

### Support Tickets

```sql
CREATE TABLE portal_tickets (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,  -- Links to CRM contact/company
    
    -- Ticket Info
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- billing, technical, general, feature_request
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'open',  -- open, in_progress, waiting_customer, resolved, closed
    
    -- Assignment
    assigned_to VARCHAR(36),  -- Internal user ID
    
    -- SLA
    sla_due_at TIMESTAMP,
    first_response_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Satisfaction
    satisfaction_rating INTEGER,  -- 1-5
    satisfaction_comment TEXT,
    
    -- Metadata
    source VARCHAR(20) DEFAULT 'portal',  -- portal, email, api
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_ticket_messages (
    id VARCHAR(36) PRIMARY KEY,
    ticket_id VARCHAR(36) NOT NULL REFERENCES portal_tickets(id),
    
    sender_type VARCHAR(20) NOT NULL,  -- customer, agent, system
    sender_id VARCHAR(36) NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    
    is_internal BOOLEAN DEFAULT FALSE,  -- Internal notes
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tickets_tenant ON portal_tickets(tenant_id);
CREATE INDEX idx_tickets_customer ON portal_tickets(customer_id);
CREATE INDEX idx_tickets_status ON portal_tickets(status);
```

### Knowledge Base

```sql
CREATE TABLE portal_kb_categories (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    
    parent_id VARCHAR(36),
    sort_order INTEGER DEFAULT 0,
    
    is_public BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_kb_articles (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) REFERENCES portal_kb_categories(id),
    
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,  -- Markdown or HTML
    excerpt TEXT,
    
    status VARCHAR(20) DEFAULT 'published',  -- draft, published, archived
    
    -- Metadata
    author_id VARCHAR(36),
    tags JSONB DEFAULT '[]',
    
    -- Stats
    view_count INTEGER DEFAULT 0,
    helpful_yes INTEGER DEFAULT 0,
    helpful_no INTEGER DEFAULT 0,
    
    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kb_articles_tenant ON portal_kb_articles(tenant_id);
CREATE INDEX idx_kb_articles_category ON portal_kb_articles(category_id);
CREATE INDEX idx_kb_articles_status ON portal_kb_articles(status);
```

### Messages

```sql
CREATE TABLE portal_conversations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,
    
    subject VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',  -- active, archived
    
    last_message_at TIMESTAMP,
    last_message_preview TEXT,
    
    unread_customer INTEGER DEFAULT 0,
    unread_agent INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES portal_conversations(id),
    
    sender_type VARCHAR(20) NOT NULL,  -- customer, agent
    sender_id VARCHAR(36) NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    
    read_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON portal_messages(conversation_id);
```

---

## API Endpoints

### Support Tickets

```
POST   /api/v1/portal/tickets                    - Create ticket
GET    /api/v1/portal/tickets                    - List my tickets
GET    /api/v1/portal/tickets/{id}               - Get ticket detail
POST   /api/v1/portal/tickets/{id}/reply         - Reply to ticket
POST   /api/v1/portal/tickets/{id}/close         - Close ticket
POST   /api/v1/portal/tickets/{id}/reopen        - Reopen ticket
POST   /api/v1/portal/tickets/{id}/rate          - Rate satisfaction
GET    /api/v1/portal/tickets/categories         - Get categories
```

### Knowledge Base

```
GET    /api/v1/portal/kb/categories              - List categories
GET    /api/v1/portal/kb/articles                - List articles
GET    /api/v1/portal/kb/articles/{slug}         - Get article
GET    /api/v1/portal/kb/articles/popular        - Popular articles
GET    /api/v1/portal/kb/articles/recent         - Recently viewed
POST   /api/v1/portal/kb/articles/{id}/helpful   - Vote helpful
GET    /api/v1/portal/kb/search                  - Search articles
GET    /api/v1/portal/kb/faq                     - FAQ section
```

### Messages

```
GET    /api/v1/portal/conversations              - List conversations
POST   /api/v1/portal/conversations              - Start conversation
GET    /api/v1/portal/conversations/{id}         - Get messages
POST   /api/v1/portal/conversations/{id}/messages - Send message
POST   /api/v1/portal/conversations/{id}/read    - Mark as read
POST   /api/v1/portal/conversations/{id}/archive - Archive
```

### Quotes & Contracts

```
GET    /api/v1/portal/quotes                     - List quotes
GET    /api/v1/portal/quotes/{id}                - Get quote detail
POST   /api/v1/portal/quotes/{id}/accept         - Accept quote
POST   /api/v1/portal/quotes/{id}/decline        - Decline quote
POST   /api/v1/portal/quotes/{id}/request-revision - Request changes
GET    /api/v1/portal/quotes/{id}/pdf            - Download PDF
GET    /api/v1/portal/contracts                  - List contracts
GET    /api/v1/portal/contracts/{id}             - Get contract
POST   /api/v1/portal/contracts/{id}/sign        - Sign contract
```

### Payments

```
GET    /api/v1/portal/invoices                   - List invoices
GET    /api/v1/portal/invoices/{id}              - Get invoice detail
POST   /api/v1/portal/invoices/{id}/pay          - Pay invoice
GET    /api/v1/portal/payments                   - Payment history
GET    /api/v1/portal/payments/{id}/receipt      - Download receipt
GET    /api/v1/portal/statements                 - Account statements
POST   /api/v1/portal/payment-methods            - Add payment method
DELETE /api/v1/portal/payment-methods/{id}       - Remove method
POST   /api/v1/portal/auto-pay                   - Setup auto-pay
```

### Projects

```
GET    /api/v1/portal/projects                   - List projects
GET    /api/v1/portal/projects/{id}              - Get project detail
GET    /api/v1/portal/projects/{id}/timeline     - Project timeline
GET    /api/v1/portal/projects/{id}/documents    - Project documents
POST   /api/v1/portal/projects/{id}/feedback     - Submit feedback
POST   /api/v1/portal/projects/{id}/approve/{deliverable_id} - Approve deliverable
```

### Documents

```
GET    /api/v1/portal/documents                  - List documents
GET    /api/v1/portal/documents/{id}             - Get document
GET    /api/v1/portal/documents/{id}/download    - Download
POST   /api/v1/portal/documents                  - Upload document
GET    /api/v1/portal/documents/categories       - Categories
```

### Account

```
GET    /api/v1/portal/profile                    - Get profile
PUT    /api/v1/portal/profile                    - Update profile
PUT    /api/v1/portal/password                   - Change password
GET    /api/v1/portal/2fa                        - Get 2FA status
POST   /api/v1/portal/2fa/enable                 - Enable 2FA
DELETE /api/v1/portal/2fa                        - Disable 2FA
GET    /api/v1/portal/notifications/settings     - Notification prefs
PUT    /api/v1/portal/notifications/settings     - Update prefs
GET    /api/v1/portal/sessions                   - Active sessions
DELETE /api/v1/portal/sessions/{id}              - Revoke session
```

---

## Implementation Timeline

### Sprint 1-2: Foundation (Weeks 1-4)
- Portal authentication & authorization
- Customer Hub dashboard
- Basic navigation & layout
- Profile & account settings

### Sprint 3-4: Support Ticketing (Weeks 5-8)
- Ticket creation & management
- Ticket messaging
- File attachments
- Email notifications

### Sprint 5-6: Knowledge Base (Weeks 9-12)
- Article categories & display
- Search functionality
- Helpful voting
- FAQ section

### Sprint 7-8: Communication (Weeks 13-16)
- Conversation threads
- Real-time messaging
- Read receipts
- Message search

### Sprint 9-10: Projects & Quotes (Weeks 17-20)
- Project visibility
- Quote acceptance flow
- E-signature integration
- Contract management

### Sprint 11-12: Payments (Weeks 21-24)
- Invoice management
- Online payments
- Payment history
- Auto-pay setup

### Sprint 13-14: Documents & Polish (Weeks 25-28)
- Document library
- Customization options
- Analytics dashboard
- Performance optimization

---

## UI/UX Design Principles

### Portal Design System

```
Colors:
- Primary: Brand color (configurable)
- Background: #F8FAFC (light) / #0F172A (dark)
- Card: #FFFFFF / #1E293B
- Text: #1E293B / #F1F5F9
- Accent: #3B82F6 (blue for actions)
- Success: #10B981
- Warning: #F59E0B
- Error: #EF4444

Typography:
- Font: Inter, system-ui
- Headings: 600-700 weight
- Body: 400 weight
- Size scale: 12/14/16/18/24/32px

Spacing:
- Base unit: 4px
- Component padding: 16-24px
- Section gaps: 24-32px
- Card radius: 12px
```

### Navigation Structure

```
┌─────────────────────────────────────────┐
│  Logo    [Dashboard] [Support] [Projects] [Payments] [Profile] │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       PAGE CONTENT              │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Quick Actions:                 │   │
│  │  [New Ticket] [Pay Invoice]     │   │
│  │  [Send Message] [View Docs]     │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Ticket Volume | 100/week | 60/week | Jira/Zendesk |
| Self-Service Rate | 0% | 40% | KB views vs tickets |
| Quote Response Time | 3 days | 1 day | Quote analytics |
| Payment on Time | 70% | 90% | Invoice reports |
| Portal Adoption | 0% | 80% | Active users |
| Customer Satisfaction | N/A | 4.5/5 | Survey |
| Support Response Time | 24h | 4h | Ticket SLA |
| Document Uploads | 0/month | 50/month | Document stats |

---

## Security Considerations

### Authentication
- JWT tokens with short expiry (15 min)
- Refresh token rotation
- 2FA support (TOTP)
- Session management with device tracking

### Authorization
- Customer-scoped data access only
- Rate limiting per customer
- IP-based anomaly detection
- Audit logging of all actions

### Data Protection
- TLS 1.3 for all connections
- Data encryption at rest
- PCI compliance for payments
- GDPR data export capability

---

## Integration Points

### CRM Integration (Phase 25)
- Customer links to CRM contacts/companies
- Ticket creation triggers CRM activities
- Quote acceptance updates opportunities
- Communication logged as CRM activities

### Workflow Engine (Phase 26)
- Ticket creation workflow triggers
- Quote accepted workflow automation
- Payment received notifications
- Document upload workflows

### Notification System
- Email notifications for all events
- In-app notification center
- Push notifications (PWA)
- SMS notifications (optional)

---

## Next: Part 1 Implementation

Part 1 will cover:
- Portal authentication service
- Customer Hub dashboard
- Basic navigation & layout
- Profile & account management
- Notification preferences
