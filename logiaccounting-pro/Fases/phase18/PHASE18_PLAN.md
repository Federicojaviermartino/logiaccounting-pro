# LogiAccounting Pro - Phase 18: Real-Time Collaboration

## WebSocket-Based Real-Time Features

---

## 📋 EXECUTIVE SUMMARY

Phase 18 implements comprehensive real-time collaboration features using WebSockets, enabling users to work together seamlessly with live updates, presence awareness, collaborative editing, and instant notifications. This transforms LogiAccounting Pro from a traditional request-response application into a modern real-time platform.

### Business Value

| Benefit | Impact |
|---------|--------|
| **Team Productivity** | Work together without refresh delays |
| **Instant Updates** | See changes as they happen |
| **User Awareness** | Know who's online and what they're doing |
| **Conflict Prevention** | Avoid overwriting each other's work |
| **Engagement** | Push notifications keep users informed |
| **Modern UX** | Competes with top SaaS applications |

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **WebSocket Server** | Persistent bidirectional connections |
| **User Presence** | Online status, activity indicators |
| **Live Cursors** | See collaborators' cursor positions |
| **Real-Time Sync** | Instant data updates across clients |
| **Collaborative Editing** | Multiple users editing same document |
| **Push Notifications** | Browser & mobile notifications |
| **Activity Feed** | Live activity stream |

---

## 🏗️ ARCHITECTURE OVERVIEW

### Real-Time Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     REAL-TIME COLLABORATION ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────────────────┘

                              CLIENTS
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Browser    │  │   Browser    │  │   Mobile     │                  │
│  │   User A     │  │   User B     │  │   User C     │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         │    WebSocket    │    WebSocket    │    WebSocket              │
│         │   Connection    │   Connection    │   Connection              │
│         │                 │                 │                           │
└─────────┼─────────────────┼─────────────────┼───────────────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBSOCKET GATEWAY                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CONNECTION MANAGER                            │   │
│  │  • Authenticate connections (JWT)                               │   │
│  │  • Track active connections per user                            │   │
│  │  • Handle reconnection & heartbeat                              │   │
│  │  • Rate limiting per connection                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ROOM MANAGER                                  │   │
│  │  • Create/manage collaboration rooms                            │   │
│  │  • Subscribe users to rooms (documents, projects)               │   │
│  │  • Broadcast messages to room participants                      │   │
│  │  • Track room membership                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MESSAGE ROUTER                                │   │
│  │  • Route messages to appropriate handlers                       │   │
│  │  • Validate message schemas                                      │   │
│  │  • Queue messages for persistence                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        REDIS PUB/SUB                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Channel    │  │   Channel    │  │   Channel    │                  │
│  │  presence:*  │  │  document:*  │  │  notify:*    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  Purpose: Enable horizontal scaling - multiple WebSocket servers        │
│  can share state and broadcast messages across all connected clients    │
│                                                                          │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FEATURE HANDLERS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Presence    │  │ Collaboration│  │ Notifications│  │  Activity  │ │
│  │  Handler     │  │   Handler    │  │   Handler    │  │   Feed     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Cursors    │  │    Sync      │  │    Chat      │                  │
│  │   Handler    │  │   Handler    │  │   Handler    │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Message Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE FLOW EXAMPLES                             │
└─────────────────────────────────────────────────────────────────────────┘

  1. USER PRESENCE UPDATE
  ═══════════════════════

  User A comes online
        │
        ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Client A   │────▶│   WebSocket  │────▶│    Redis     │
  │  {type:      │     │    Server    │     │   Pub/Sub    │
  │   'presence',│     │              │     │              │
  │   status:    │     └──────────────┘     └──────┬───────┘
  │   'online'}  │                                 │
  └──────────────┘                                 │
                                                   ▼
                       ┌───────────────────────────────────────┐
                       │  Broadcast to all tenant connections  │
                       └───────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
             ┌────────────┐       ┌────────────┐       ┌────────────┐
             │  Client B  │       │  Client C  │       │  Client D  │
             │  (online)  │       │  (online)  │       │  (online)  │
             └────────────┘       └────────────┘       └────────────┘


  2. COLLABORATIVE DOCUMENT EDITING
  ══════════════════════════════════

  User A edits Invoice #1234
        │
        ▼
  ┌──────────────┐
  │  Client A    │
  │  {type:      │
  │   'doc.edit',│
  │   doc_id:    │
  │   'inv_1234',│
  │   changes:   │──────────────────────────────────────────────┐
  │   [...]}     │                                              │
  └──────────────┘                                              │
                                                                ▼
                                                   ┌──────────────────┐
                                                   │  Validate &      │
                                                   │  Transform       │
                                                   │  (OT/CRDT)       │
                                                   └────────┬─────────┘
                                                            │
                       ┌────────────────────────────────────┤
                       │                                    │
                       ▼                                    ▼
              ┌──────────────┐                    ┌──────────────┐
              │   Persist    │                    │  Broadcast   │
              │   to DB      │                    │  to Room     │
              └──────────────┘                    │  'doc:1234'  │
                                                  └──────┬───────┘
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    ▼                    ▼                    ▼
                             ┌────────────┐       ┌────────────┐       ┌────────────┐
                             │  Client B  │       │  Client C  │       │  Client A  │
                             │  (viewing  │       │  (viewing  │       │    (ack)   │
                             │  doc_1234) │       │  doc_1234) │       │            │
                             └────────────┘       └────────────┘       └────────────┘


  3. REAL-TIME NOTIFICATION
  ═════════════════════════

  Payment received for User B's invoice
        │
        ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Backend    │────▶│   Publish    │────▶│    Redis     │
  │   Event      │     │   Event      │     │   Channel    │
  │              │     │              │     │  notify:B    │
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                                                   ▼
                                          ┌──────────────┐
                                          │  Find B's    │
                                          │  Connections │
                                          └──────┬───────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                             ┌────────────┐            ┌────────────┐
                             │  Browser   │            │   Mobile   │
                             │  Tab 1     │            │    App     │
                             └────────────┘            └────────────┘
                                    │                         │
                                    ▼                         ▼
                             ┌────────────┐            ┌────────────┐
                             │   Toast    │            │    Push    │
                             │   Notif    │            │   Notif    │
                             └────────────┘            └────────────┘
```

### Presence States

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER PRESENCE STATES                              │
└─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                      │
  │    ●  ONLINE      User is active, connection is healthy             │
  │                                                                      │
  │    ◐  AWAY        User is idle (no activity for 5 minutes)          │
  │                                                                      │
  │    ●  BUSY        User is in a focus mode / Do Not Disturb          │
  │                                                                      │
  │    ○  OFFLINE     User disconnected or logged out                   │
  │                                                                      │
  └─────────────────────────────────────────────────────────────────────┘

  PRESENCE DATA STRUCTURE
  ═══════════════════════

  {
    "user_id": "usr_abc123",
    "status": "online",
    "last_active_at": "2026-01-21T15:30:00Z",
    "current_location": {
      "type": "document",
      "id": "inv_1234",
      "name": "Invoice #1234"
    },
    "connections": [
      {"device": "desktop", "browser": "Chrome"},
      {"device": "mobile", "app": "iOS"}
    ]
  }
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── realtime/
│   ├── __init__.py
│   ├── server.py                   # WebSocket server (Socket.IO)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── connection.py           # Connection tracking
│   │   ├── presence.py             # User presence
│   │   ├── room.py                 # Collaboration rooms
│   │   ├── cursor.py               # Cursor positions
│   │   └── notification.py         # Real-time notifications
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── connection_handler.py   # Connect/disconnect
│   │   ├── presence_handler.py     # Presence updates
│   │   ├── room_handler.py         # Room management
│   │   ├── cursor_handler.py       # Cursor sync
│   │   ├── document_handler.py     # Document collaboration
│   │   ├── notification_handler.py # Push notifications
│   │   └── activity_handler.py     # Activity feed
│   │
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── connection_manager.py   # Connection state
│   │   ├── presence_manager.py     # Presence state (Redis)
│   │   ├── room_manager.py         # Room subscriptions
│   │   └── broadcast_manager.py    # Message broadcasting
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── realtime_service.py     # Core realtime service
│   │   ├── notification_service.py # Notification delivery
│   │   └── activity_service.py     # Activity tracking
│   │
│   ├── collaboration/
│   │   ├── __init__.py
│   │   ├── ot_engine.py            # Operational Transform
│   │   ├── conflict_resolver.py    # Conflict resolution
│   │   └── sync_protocol.py        # Sync protocol
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── presence.py             # Presence API
│   │   ├── notifications.py        # Notifications API
│   │   └── activity.py             # Activity feed API
│   │
│   └── utils/
│       ├── __init__.py
│       ├── message_types.py        # Message type definitions
│       ├── validators.py           # Message validation
│       └── rate_limiter.py         # WebSocket rate limiting

frontend/src/
├── features/
│   └── realtime/
│       ├── components/
│       │   ├── PresenceIndicator.jsx
│       │   ├── UserAvatar.jsx
│       │   ├── OnlineUsersList.jsx
│       │   ├── ActivityFeed.jsx
│       │   ├── NotificationCenter.jsx
│       │   ├── NotificationToast.jsx
│       │   ├── CollaboratorCursors.jsx
│       │   ├── EditingIndicator.jsx
│       │   └── LiveBadge.jsx
│       │
│       ├── hooks/
│       │   ├── useWebSocket.js
│       │   ├── usePresence.js
│       │   ├── useRoom.js
│       │   ├── useCursors.js
│       │   ├── useNotifications.js
│       │   ├── useActivityFeed.js
│       │   └── useCollaboration.js
│       │
│       ├── context/
│       │   ├── WebSocketContext.jsx
│       │   ├── PresenceContext.jsx
│       │   └── NotificationContext.jsx
│       │
│       ├── services/
│       │   ├── socketService.js
│       │   └── notificationService.js
│       │
│       └── stores/
│           ├── presenceStore.js
│           ├── notificationStore.js
│           └── activityStore.js
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# WebSocket Server
python-socketio==5.10.0           # Socket.IO server
python-engineio==4.8.1            # Engine.IO (transport)
eventlet==0.34.2                  # Async networking
gevent==23.9.1                    # Alternative async

# Redis for Pub/Sub
redis==5.0.1                      # Redis client
aioredis==2.0.1                   # Async Redis

# Message Queue
kombu==5.3.4                      # Message transport

# Rate Limiting
limits==3.7.0                     # Rate limit algorithms

# Push Notifications
pywebpush==1.14.0                 # Web Push notifications
firebase-admin==6.3.0             # Firebase Cloud Messaging

# Real-time Sync
ypy-websocket==0.12.1             # Yjs WebSocket adapter (CRDT)
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "socket.io-client": "^4.7.2",
    "zustand": "^4.4.7",
    "@tanstack/react-query": "^5.17.0",
    "yjs": "^13.6.10",
    "y-websocket": "^1.5.0",
    "react-hot-toast": "^2.4.1",
    "framer-motion": "^10.17.0"
  }
}
```

---

## 📊 DATABASE SCHEMA

```sql
-- User Presence (mostly in Redis, but persisted for history)
CREATE TABLE user_presence_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- 'online', 'away', 'busy', 'offline'
    
    -- Location
    current_page VARCHAR(255),
    current_entity_type VARCHAR(50),
    current_entity_id UUID,
    
    -- Connection Info
    connection_id VARCHAR(100),
    device_type VARCHAR(20),  -- 'desktop', 'mobile', 'tablet'
    browser VARCHAR(50),
    ip_address INET,
    
    -- Timing
    connected_at TIMESTAMP,
    disconnected_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_presence_user (user_id, created_at DESC),
    INDEX idx_presence_tenant (tenant_id, created_at DESC)
);

-- Collaboration Sessions
CREATE TABLE collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Target Document
    entity_type VARCHAR(50) NOT NULL,  -- 'invoice', 'project', 'document'
    entity_id UUID NOT NULL,
    
    -- Session Info
    room_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Participants (current)
    active_users UUID[] DEFAULT '{}',
    max_concurrent_users INTEGER DEFAULT 0,
    
    -- Stats
    total_edits INTEGER DEFAULT 0,
    total_conflicts_resolved INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    INDEX idx_collab_entity (entity_type, entity_id),
    INDEX idx_collab_room (room_id),
    INDEX idx_collab_active (tenant_id, ended_at) WHERE ended_at IS NULL
);

-- Collaboration Events (for replay/audit)
CREATE TABLE collaboration_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Event
    event_type VARCHAR(50) NOT NULL,
    -- 'join', 'leave', 'edit', 'cursor_move', 'selection', 'undo', 'redo'
    
    -- Data
    event_data JSONB NOT NULL,
    
    -- Versioning
    version INTEGER NOT NULL,
    parent_version INTEGER,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_collab_events_session (session_id, version),
    INDEX idx_collab_events_time (session_id, created_at)
);

-- Real-time Notifications
CREATE TABLE realtime_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification Type
    type VARCHAR(50) NOT NULL,
    -- 'payment_received', 'invoice_overdue', 'project_update', 'mention', 'comment'
    
    -- Content
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Source
    source_type VARCHAR(50),
    source_id UUID,
    
    -- Action
    action_url VARCHAR(500),
    action_label VARCHAR(100),
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'normal',  -- 'low', 'normal', 'high', 'urgent'
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    -- Delivery
    delivered_websocket BOOLEAN DEFAULT FALSE,
    delivered_push BOOLEAN DEFAULT FALSE,
    delivered_email BOOLEAN DEFAULT FALSE,
    
    -- Expiration
    expires_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notifications_user (user_id, is_read, created_at DESC),
    INDEX idx_notifications_unread (user_id, created_at DESC) WHERE NOT is_read
);

-- Push Notification Subscriptions
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Subscription Details
    endpoint VARCHAR(500) NOT NULL,
    p256dh_key VARCHAR(255) NOT NULL,
    auth_key VARCHAR(255) NOT NULL,
    
    -- Device Info
    device_type VARCHAR(20),
    device_name VARCHAR(100),
    browser VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    
    UNIQUE(user_id, endpoint),
    INDEX idx_push_user (user_id, is_active)
);

-- Activity Feed
CREATE TABLE activity_feed (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Actor
    user_id UUID REFERENCES users(id),
    user_name VARCHAR(100),
    
    -- Action
    action VARCHAR(50) NOT NULL,
    -- 'created', 'updated', 'deleted', 'commented', 'assigned', 'completed'
    
    -- Target
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_name VARCHAR(255),
    
    -- Details
    details JSONB,
    
    -- Visibility
    visibility VARCHAR(20) DEFAULT 'team',  -- 'private', 'team', 'public'
    visible_to UUID[],  -- Specific users if visibility is 'private'
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_activity_tenant (tenant_id, created_at DESC),
    INDEX idx_activity_entity (entity_type, entity_id, created_at DESC),
    INDEX idx_activity_user (user_id, created_at DESC)
);

-- Cursor Positions (mostly in Redis, but schema for reference)
-- Stored in Redis as: cursor:{room_id}:{user_id} -> JSON
-- {
--   "user_id": "usr_xxx",
--   "position": {"line": 10, "column": 5},
--   "selection": {"start": {...}, "end": {...}},
--   "color": "#FF5733",
--   "last_update": "2026-01-21T15:30:00Z"
-- }

-- Edit Locks (optimistic locking)
CREATE TABLE edit_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Lock Target
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field_name VARCHAR(100),  -- NULL for entire entity
    
    -- Lock Holder
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES collaboration_sessions(id),
    
    -- Lock Info
    lock_type VARCHAR(20) DEFAULT 'soft',  -- 'soft', 'hard'
    reason VARCHAR(255),
    
    -- Expiration
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    UNIQUE(entity_type, entity_id, field_name),
    INDEX idx_locks_entity (entity_type, entity_id),
    INDEX idx_locks_user (user_id),
    INDEX idx_locks_expiry (expires_at)
);
```

---

## 🎯 FEATURE SPECIFICATIONS

### 18.1 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Initial connection with auth |
| `disconnect` | Client → Server | Connection closed |
| `presence:update` | Bidirectional | User presence change |
| `presence:list` | Server → Client | Online users list |
| `room:join` | Client → Server | Join collaboration room |
| `room:leave` | Client → Server | Leave room |
| `room:users` | Server → Client | Users in room |
| `cursor:move` | Client → Server | Cursor position update |
| `cursor:sync` | Server → Client | All cursors in room |
| `doc:edit` | Client → Server | Document edit |
| `doc:sync` | Server → Client | Document state sync |
| `doc:lock` | Client → Server | Request edit lock |
| `notify` | Server → Client | Push notification |
| `activity` | Server → Client | Activity feed item |
| `typing` | Bidirectional | Typing indicator |

### 18.2 Presence States

| State | Description | Timeout |
|-------|-------------|---------|
| `online` | Active connection | - |
| `away` | No activity | 5 min |
| `busy` | Do Not Disturb | Manual |
| `offline` | Disconnected | Immediate |

### 18.3 Notification Types

| Type | Priority | Channels |
|------|----------|----------|
| `payment_received` | High | WS, Push, Email |
| `invoice_overdue` | High | WS, Push, Email |
| `invoice_paid` | Normal | WS, Push |
| `project_update` | Normal | WS |
| `task_assigned` | Normal | WS, Push |
| `mention` | High | WS, Push |
| `comment` | Normal | WS |
| `document_shared` | Normal | WS, Push |

### 18.4 Collaboration Features

| Feature | Description |
|---------|-------------|
| **Live Cursors** | See other users' cursor positions |
| **Selections** | See highlighted selections |
| **Typing Indicator** | Know when someone is typing |
| **Edit Locks** | Soft locks prevent conflicts |
| **Conflict Resolution** | Automatic merge with OT |
| **Version History** | Track all changes |

---

## 🔗 API ENDPOINTS

### Presence

```
GET    /api/v1/presence                         # Get online users
GET    /api/v1/presence/:user_id                # Get user presence
PUT    /api/v1/presence/status                  # Update own status
```

### Notifications

```
GET    /api/v1/notifications                    # List notifications
GET    /api/v1/notifications/unread/count       # Unread count
PUT    /api/v1/notifications/:id/read           # Mark as read
PUT    /api/v1/notifications/read-all           # Mark all as read
DELETE /api/v1/notifications/:id                # Delete notification
POST   /api/v1/notifications/settings           # Update settings
```

### Push Subscriptions

```
POST   /api/v1/push/subscribe                   # Subscribe to push
DELETE /api/v1/push/unsubscribe                 # Unsubscribe
GET    /api/v1/push/subscriptions               # List subscriptions
POST   /api/v1/push/test                        # Send test notification
```

### Activity Feed

```
GET    /api/v1/activity                         # Get activity feed
GET    /api/v1/activity/entity/:type/:id        # Activity for entity
```

### Collaboration

```
GET    /api/v1/collaboration/sessions           # Active sessions
GET    /api/v1/collaboration/:entity/:id        # Session for entity
POST   /api/v1/collaboration/:entity/:id/lock   # Acquire lock
DELETE /api/v1/collaboration/:entity/:id/lock   # Release lock
```

---

## ⏱️ IMPLEMENTATION TIMELINE

| Week | Tasks | Hours |
|------|-------|-------|
| **Week 1** | Database schema, Socket.IO server setup | 10h |
| **Week 2** | Connection manager, Authentication | 12h |
| **Week 3** | Presence system (handlers, Redis state) | 12h |
| **Week 4** | Room manager, Subscription logic | 10h |
| **Week 5** | Cursor tracking, Live sync | 10h |
| **Week 6** | Notification system (models, service) | 12h |
| **Week 7** | Push notifications (Web Push, FCM) | 10h |
| **Week 8** | Activity feed | 8h |
| **Week 9** | Collaboration engine (OT basics) | 12h |
| **Week 10** | Edit locks, Conflict resolution | 10h |
| **Week 11** | Frontend: WebSocket context, hooks | 12h |
| **Week 12** | Frontend: Presence components | 10h |
| **Week 13** | Frontend: Notification center | 10h |
| **Week 14** | Frontend: Collaboration UI | 12h |
| **Week 15** | Testing, Performance optimization | 10h |

**Total: ~160 hours (15 weeks)**

---

## ✅ FEATURE CHECKLIST

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 18.1 | Socket.IO server setup | P0 | 🔲 |
| 18.2 | JWT authentication for WebSocket | P0 | 🔲 |
| 18.3 | Connection manager | P0 | 🔲 |
| 18.4 | Redis Pub/Sub integration | P0 | 🔲 |
| 18.5 | Presence tracking (online/away/busy) | P0 | 🔲 |
| 18.6 | Presence broadcasting | P0 | 🔲 |
| 18.7 | Room management | P0 | 🔲 |
| 18.8 | Room join/leave | P0 | 🔲 |
| 18.9 | Cursor position sync | P1 | 🔲 |
| 18.10 | Selection highlighting | P1 | 🔲 |
| 18.11 | Typing indicators | P1 | 🔲 |
| 18.12 | Real-time notifications | P0 | 🔲 |
| 18.13 | Web Push notifications | P1 | 🔲 |
| 18.14 | Push subscription management | P1 | 🔲 |
| 18.15 | Activity feed | P1 | 🔲 |
| 18.16 | Edit locks (soft locking) | P1 | 🔲 |
| 18.17 | Conflict detection | P1 | 🔲 |
| 18.18 | Operational Transform (basic) | P2 | 🔲 |
| 18.19 | Frontend: WebSocket hook | P0 | 🔲 |
| 18.20 | Frontend: Presence context | P0 | 🔲 |
| 18.21 | Frontend: Online users list | P0 | 🔲 |
| 18.22 | Frontend: Notification center | P0 | 🔲 |
| 18.23 | Frontend: Toast notifications | P0 | 🔲 |
| 18.24 | Frontend: Cursor overlays | P1 | 🔲 |
| 18.25 | Frontend: Activity feed widget | P1 | 🔲 |
| 18.26 | Horizontal scaling support | P1 | 🔲 |

---

*Phase 18 Plan - LogiAccounting Pro*
*Real-Time Collaboration*
