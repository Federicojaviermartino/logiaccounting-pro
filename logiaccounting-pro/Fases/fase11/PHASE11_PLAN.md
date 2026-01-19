# LogiAccounting Pro - Phase 11: Mobile Native Apps

## React Native Cross-Platform Mobile Application

---

## 📱 EXECUTIVE SUMMARY

Phase 11 transforms LogiAccounting Pro into a true mobile-first enterprise platform by building native iOS and Android applications using React Native. This phase delivers offline-capable, biometric-secured mobile apps that enable field operations, real-time notifications, and document scanning capabilities.

---

## 🎯 OBJECTIVES

### Primary Goals

1. **Cross-Platform Native Apps** - Single codebase for iOS and Android
2. **Offline-First Architecture** - Full functionality without connectivity
3. **Biometric Authentication** - Face ID, Touch ID, fingerprint support
4. **Push Notifications** - Real-time alerts for payments, approvals, inventory
5. **Document Scanning** - Camera-based invoice/receipt capture with OCR
6. **Mobile-Optimized Dashboard** - Touch-friendly analytics and KPIs
7. **Barcode/QR Scanning** - Inventory management on the go
8. **Secure Data Sync** - Background synchronization with conflict resolution

### Business Value

- **Field Operations** - Warehouse staff can manage inventory anywhere
- **Executive Access** - Real-time KPIs and approvals on mobile
- **Faster Processing** - Scan and upload documents instantly
- **Improved Response** - Push notifications for urgent items
- **Offline Reliability** - Works in warehouses with poor connectivity

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    REACT NATIVE APPLICATION                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Screens    │  │  Components  │  │   Services   │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ Dashboard    │  │ Cards        │  │ API Client   │          │
│  │ Inventory    │  │ Charts       │  │ Auth Service │          │
│  │ Projects     │  │ Forms        │  │ Sync Engine  │          │
│  │ Transactions │  │ Lists        │  │ Push Handler │          │
│  │ Payments     │  │ Scanner      │  │ Storage      │          │
│  │ Analytics    │  │ Camera       │  │ Biometrics   │          │
│  │ Settings     │  │ Modals       │  │ OCR Service  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    STATE MANAGEMENT                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Redux     │  │  RTK Query  │  │  Persist    │       │   │
│  │  │   Store     │  │  Cache      │  │  Storage    │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    NATIVE MODULES                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ Camera  │ │Biometric│ │  Push   │ │ SQLite  │         │   │
│  │  │ Scanner │ │  Auth   │ │ Notif.  │ │ Storage │         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (Existing)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  REST API    │  │  WebSocket   │  │  Push Server │          │
│  │  /api/v1/*   │  │  Real-time   │  │  FCM / APNs  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 PROJECT STRUCTURE

```
mobile/
├── android/                      # Android native code
│   ├── app/
│   │   ├── build.gradle
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       └── java/
│   └── gradle.properties
├── ios/                          # iOS native code
│   ├── LogiAccountingPro/
│   │   ├── AppDelegate.mm
│   │   └── Info.plist
│   ├── Podfile
│   └── LogiAccountingPro.xcworkspace
├── src/
│   ├── app/                      # App entry and configuration
│   │   ├── App.tsx
│   │   ├── store.ts
│   │   └── theme.ts
│   ├── screens/                  # Screen components
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── BiometricScreen.tsx
│   │   │   └── PinScreen.tsx
│   │   ├── dashboard/
│   │   │   └── DashboardScreen.tsx
│   │   ├── inventory/
│   │   │   ├── InventoryListScreen.tsx
│   │   │   ├── InventoryDetailScreen.tsx
│   │   │   ├── ScannerScreen.tsx
│   │   │   └── MovementScreen.tsx
│   │   ├── projects/
│   │   │   ├── ProjectListScreen.tsx
│   │   │   └── ProjectDetailScreen.tsx
│   │   ├── transactions/
│   │   │   ├── TransactionListScreen.tsx
│   │   │   ├── TransactionFormScreen.tsx
│   │   │   └── DocumentScanScreen.tsx
│   │   ├── payments/
│   │   │   ├── PaymentListScreen.tsx
│   │   │   └── PaymentDetailScreen.tsx
│   │   ├── analytics/
│   │   │   └── AnalyticsScreen.tsx
│   │   └── settings/
│   │       ├── SettingsScreen.tsx
│   │       ├── ProfileScreen.tsx
│   │       └── SyncScreen.tsx
│   ├── components/               # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── cards/
│   │   │   ├── KPICard.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── TransactionCard.tsx
│   │   │   └── PaymentCard.tsx
│   │   ├── charts/
│   │   │   ├── MiniLineChart.tsx
│   │   │   ├── PieChart.tsx
│   │   │   └── BarChart.tsx
│   │   ├── lists/
│   │   │   ├── InventoryItem.tsx
│   │   │   ├── TransactionItem.tsx
│   │   │   └── PaymentItem.tsx
│   │   ├── forms/
│   │   │   ├── TransactionForm.tsx
│   │   │   ├── MovementForm.tsx
│   │   │   └── PaymentForm.tsx
│   │   └── scanner/
│   │       ├── BarcodeScanner.tsx
│   │       ├── DocumentScanner.tsx
│   │       └── QRScanner.tsx
│   ├── navigation/               # Navigation configuration
│   │   ├── AppNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   ├── MainNavigator.tsx
│   │   └── TabNavigator.tsx
│   ├── services/                 # Business logic services
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── inventory.ts
│   │   │   ├── projects.ts
│   │   │   ├── transactions.ts
│   │   │   ├── payments.ts
│   │   │   └── analytics.ts
│   │   ├── auth/
│   │   │   ├── authService.ts
│   │   │   ├── biometricService.ts
│   │   │   └── tokenService.ts
│   │   ├── sync/
│   │   │   ├── syncEngine.ts
│   │   │   ├── conflictResolver.ts
│   │   │   └── queueManager.ts
│   │   ├── notifications/
│   │   │   ├── pushService.ts
│   │   │   └── notificationHandler.ts
│   │   ├── scanner/
│   │   │   ├── barcodeService.ts
│   │   │   └── ocrService.ts
│   │   └── storage/
│   │       ├── secureStorage.ts
│   │       ├── sqliteService.ts
│   │       └── cacheService.ts
│   ├── store/                    # Redux store
│   │   ├── index.ts
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── inventorySlice.ts
│   │   │   ├── projectsSlice.ts
│   │   │   ├── transactionsSlice.ts
│   │   │   ├── paymentsSlice.ts
│   │   │   ├── syncSlice.ts
│   │   │   └── settingsSlice.ts
│   │   └── api/
│   │       └── apiSlice.ts
│   ├── hooks/                    # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useBiometrics.ts
│   │   ├── useSync.ts
│   │   ├── useOffline.ts
│   │   ├── useNotifications.ts
│   │   └── useScanner.ts
│   ├── utils/                    # Utilities
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── permissions.ts
│   │   └── constants.ts
│   ├── i18n/                     # Internationalization
│   │   ├── index.ts
│   │   └── locales/
│   │       ├── en.json
│   │       ├── es.json
│   │       ├── de.json
│   │       └── fr.json
│   └── types/                    # TypeScript types
│       ├── navigation.ts
│       ├── api.ts
│       └── models.ts
├── __tests__/                    # Tests
│   ├── screens/
│   ├── components/
│   └── services/
├── .env.development
├── .env.production
├── app.json
├── babel.config.js
├── metro.config.js
├── package.json
├── tsconfig.json
└── README.md
```

---

## 🔧 TECHNOLOGY STACK

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| React Native | 0.73+ | Cross-platform framework |
| TypeScript | 5.3+ | Type safety |
| Expo (optional) | 50+ | Development tooling |

### Navigation & State

| Library | Purpose |
|---------|---------|
| @react-navigation/native | Navigation framework |
| @react-navigation/bottom-tabs | Tab navigation |
| @react-navigation/stack | Stack navigation |
| @reduxjs/toolkit | State management |
| redux-persist | State persistence |
| RTK Query | API caching |

### Native Features

| Library | Purpose |
|---------|---------|
| react-native-camera | Camera/scanning |
| react-native-vision-camera | Advanced camera |
| react-native-biometrics | Face ID/Touch ID |
| @react-native-firebase/messaging | Push notifications |
| react-native-sqlite-storage | Local database |
| @react-native-async-storage/async-storage | Key-value storage |
| react-native-keychain | Secure storage |
| react-native-permissions | Permission handling |
| react-native-mlkit | On-device OCR |

### UI Components

| Library | Purpose |
|---------|---------|
| react-native-paper | Material Design components |
| react-native-vector-icons | Icon library |
| react-native-chart-kit | Charts |
| react-native-reanimated | Animations |
| react-native-gesture-handler | Touch gestures |
| react-native-safe-area-context | Safe area handling |

### Development

| Tool | Purpose |
|------|---------|
| Flipper | Debugging |
| React Native Debugger | State inspection |
| Detox | E2E testing |
| Jest | Unit testing |

---

## 📱 FEATURE SPECIFICATIONS

### 11.1 Authentication System

#### Biometric Authentication

```typescript
// Supported methods
- Face ID (iOS)
- Touch ID (iOS)  
- Fingerprint (Android)
- PIN fallback (all platforms)

// Flow
1. User opens app
2. Check if biometrics enabled
3. Prompt biometric authentication
4. On success → Load secure tokens
5. On failure → Fall back to PIN
6. Max 3 attempts → Require password login
```

#### Secure Token Storage

```typescript
// Token storage strategy
- Access token → Secure Keychain/Keystore
- Refresh token → Encrypted storage
- User data → SQLite (encrypted)
- Session → Memory only
```

### 11.2 Offline-First Architecture

#### Data Synchronization Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐                      ┌─────────────┐       │
│  │   SQLite    │◄────── Read ────────│    App UI   │       │
│  │  (Offline)  │                      │             │       │
│  └──────┬──────┘                      └──────┬──────┘       │
│         │                                    │              │
│         │ Sync                         Write │              │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌─────────────┐                      ┌─────────────┐       │
│  │    Sync     │◄───── Queue ────────│   Action    │       │
│  │   Engine    │                      │   Queue     │       │
│  └──────┬──────┘                      └─────────────┘       │
│         │                                                    │
│         │ HTTP                                               │
│         ▼                                                    │
│  ┌─────────────┐                                            │
│  │  REST API   │                                            │
│  │  (Backend)  │                                            │
│  └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Conflict Resolution

```typescript
// Strategy: Last-Write-Wins with Merge
1. Track modification timestamps
2. Compare local vs server timestamps
3. For conflicts:
   - Numeric fields: Server wins
   - Text fields: Show merge dialog
   - Critical data: Flag for review
4. Log all conflicts for audit
```

#### Offline Capabilities

| Feature | Offline Support |
|---------|-----------------|
| View Dashboard | ✅ Cached data |
| View Inventory | ✅ Full list |
| Create Movement | ✅ Queued |
| Scan Barcode | ✅ Local lookup |
| View Projects | ✅ Full list |
| Create Transaction | ✅ Queued |
| Scan Document | ✅ Stored locally |
| View Payments | ✅ Cached |
| Record Payment | ✅ Queued |
| View Analytics | ⚠️ Last sync |
| Push Notifications | ❌ Requires network |

### 11.3 Push Notifications

#### Notification Types

| Type | Trigger | Priority |
|------|---------|----------|
| Payment Due | 3 days before due date | High |
| Payment Overdue | Day after due date | Critical |
| Low Stock Alert | Below minimum threshold | High |
| Approval Request | New approval needed | High |
| Project Update | Status change | Normal |
| Sync Complete | Background sync done | Low |
| Weekly Summary | Every Monday 9 AM | Normal |

#### Backend Integration

```python
# Push notification service
- Firebase Cloud Messaging (FCM) for Android
- Apple Push Notification Service (APNs) for iOS
- Unified backend API for sending
- Device token registration
- Topic subscriptions (role-based)
```

### 11.4 Document & Barcode Scanning

#### Document Scanner

```typescript
// Capabilities
- Auto-edge detection
- Perspective correction
- Image enhancement
- Multi-page capture
- On-device OCR
- Cloud OCR fallback

// Extracted Data
- Invoice number
- Vendor name
- Amount
- Date
- Line items (advanced)
```

#### Barcode/QR Scanner

```typescript
// Supported formats
- Code 128 (inventory)
- Code 39 (materials)
- QR Code (product info)
- EAN-13 (products)
- UPC-A (products)

// Actions
- Look up inventory item
- Create movement
- Update quantity
- Link to project
```

### 11.5 Mobile Dashboard

#### KPI Cards (Touch Optimized)

```
┌─────────────────────────────────────┐
│  📊 Dashboard           🔔 3        │
├─────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐ │
│ │   Revenue     │ │   Expenses    │ │
│ │   $125,400    │ │   $89,200     │ │
│ │   ↑ 12.3%     │ │   ↓ 5.2%      │ │
│ └───────────────┘ └───────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │    Profit     │ │  Cash Flow    │ │
│ │   $36,200     │ │   $48,500     │ │
│ │   ↑ 8.7%      │ │   ↑ 15.1%     │ │
│ └───────────────┘ └───────────────┘ │
├─────────────────────────────────────┤
│        📈 Trend (swipeable)         │
│  ┌─────────────────────────────┐    │
│  │     ╭─────╮                 │    │
│  │   ╭─╯     ╰─╮    ╭──       │    │
│  │ ──╯         ╰────╯         │    │
│  └─────────────────────────────┘    │
├─────────────────────────────────────┤
│  🔴 3 Overdue Payments              │
│  📦 5 Low Stock Items               │
│  ✅ 2 Pending Approvals             │
└─────────────────────────────────────┘
```

---

## ⏱️ IMPLEMENTATION TIMELINE

### Week 1-2: Project Setup & Core Infrastructure

| Task | Hours |
|------|-------|
| React Native project initialization | 4 |
| Navigation setup | 4 |
| Redux store configuration | 4 |
| API client setup | 4 |
| Theme and styling system | 4 |
| Common components library | 8 |
| **Subtotal** | **28** |

### Week 3-4: Authentication & Security

| Task | Hours |
|------|-------|
| Login screen | 4 |
| Biometric authentication | 6 |
| PIN screen | 4 |
| Secure token storage | 4 |
| Auto-logout | 2 |
| Session management | 4 |
| **Subtotal** | **24** |

### Week 5-6: Core Screens

| Task | Hours |
|------|-------|
| Dashboard screen | 8 |
| Inventory list & detail | 8 |
| Projects list & detail | 6 |
| Transactions list & form | 8 |
| Payments list & detail | 6 |
| **Subtotal** | **36** |

### Week 7-8: Offline & Sync

| Task | Hours |
|------|-------|
| SQLite setup | 4 |
| Offline data storage | 8 |
| Sync engine | 12 |
| Conflict resolution | 6 |
| Background sync | 4 |
| **Subtotal** | **34** |

### Week 9-10: Native Features

| Task | Hours |
|------|-------|
| Push notifications setup | 8 |
| Notification handlers | 4 |
| Barcode scanner | 6 |
| Document scanner | 8 |
| OCR integration | 6 |
| **Subtotal** | **32** |

### Week 11-12: Analytics & Polish

| Task | Hours |
|------|-------|
| Mobile analytics dashboard | 8 |
| Charts implementation | 6 |
| Settings & profile | 4 |
| Internationalization | 4 |
| Performance optimization | 6 |
| Testing & bug fixes | 8 |
| **Subtotal** | **36** |

### Total: ~190 hours (12 weeks)

---

## 🎨 UI/UX GUIDELINES

### Design Principles

1. **Touch-First** - Minimum 44pt touch targets
2. **Thumb Zone** - Primary actions in easy reach
3. **Glanceable** - Key info visible immediately
4. **Offline Aware** - Clear sync status indicators
5. **Native Feel** - Platform-specific patterns

### Color Scheme

```typescript
const colors = {
  // Primary
  primary: '#3B82F6',      // Blue
  primaryDark: '#2563EB',
  primaryLight: '#93C5FD',
  
  // Semantic
  success: '#22C55E',      // Green
  warning: '#F59E0B',      // Amber
  danger: '#EF4444',       // Red
  info: '#06B6D4',         // Cyan
  
  // Neutral
  background: '#F8FAFC',
  surface: '#FFFFFF',
  text: '#1E293B',
  textMuted: '#64748B',
  border: '#E2E8F0',
  
  // Dark mode
  darkBackground: '#0F172A',
  darkSurface: '#1E293B',
  darkText: '#F1F5F9',
};
```

### Typography Scale

```typescript
const typography = {
  h1: { fontSize: 28, fontWeight: '700' },
  h2: { fontSize: 24, fontWeight: '600' },
  h3: { fontSize: 20, fontWeight: '600' },
  h4: { fontSize: 18, fontWeight: '500' },
  body: { fontSize: 16, fontWeight: '400' },
  bodySmall: { fontSize: 14, fontWeight: '400' },
  caption: { fontSize: 12, fontWeight: '400' },
  button: { fontSize: 16, fontWeight: '600' },
};
```

### Spacing System

```typescript
const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};
```

---

## 🔐 SECURITY REQUIREMENTS

### Data Protection

| Requirement | Implementation |
|-------------|----------------|
| Token Storage | Keychain (iOS) / Keystore (Android) |
| Local Database | SQLCipher encryption |
| Network | TLS 1.3, certificate pinning |
| Screenshots | Disabled on sensitive screens |
| Background | Blur sensitive content |
| Clipboard | Auto-clear after 60 seconds |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                         │
└─────────────────────────────────────────────────────────────┘

App Launch
    │
    ▼
┌─────────────┐
│ Has Token?  │──── No ────► Login Screen ──► Password Auth
└──────┬──────┘                                     │
       │ Yes                                        │
       ▼                                            │
┌─────────────┐                                     │
│ Biometrics  │──── No ────► PIN Screen            │
│  Enabled?   │                  │                  │
└──────┬──────┘                  │                  │
       │ Yes                     │                  │
       ▼                         │                  │
┌─────────────┐                  │                  │
│  Biometric  │                  │                  │
│   Prompt    │                  │                  │
└──────┬──────┘                  │                  │
       │                         │                  │
       ▼                         ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      MAIN APP                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 SUCCESS METRICS

### Performance Targets

| Metric | Target |
|--------|--------|
| App Launch | < 2 seconds |
| Screen Transition | < 300ms |
| API Response (cached) | < 100ms |
| Offline Data Load | < 500ms |
| Sync Time (100 records) | < 5 seconds |
| Barcode Scan | < 500ms |
| OCR Processing | < 3 seconds |

### Quality Metrics

| Metric | Target |
|--------|--------|
| Crash-free Rate | > 99.5% |
| ANR Rate (Android) | < 0.1% |
| Battery Impact | < 5% per hour active |
| Storage Usage | < 100MB base |
| Memory Usage | < 200MB |

### User Adoption

| Metric | Target (6 months) |
|--------|-------------------|
| Install Rate | 80% of active users |
| Daily Active Users | 60% of installs |
| Offline Usage | 25% of sessions |
| Scanner Usage | 40% of warehouse users |
| Push Opt-in | 75% of users |

---

## 🚀 DEPLOYMENT STRATEGY

### App Store Requirements

#### iOS (App Store)

- iOS 14.0 minimum
- iPhone and iPad support
- App Store screenshots
- Privacy policy URL
- App review guidelines compliance

#### Android (Play Store)

- Android 8.0 (API 26) minimum
- 64-bit support required
- Target SDK 34+
- Play Store listing assets
- Data safety form

### Release Process

```
Development → Internal Testing → Beta Testing → Production
     │              │                 │              │
     │         TestFlight         Google Play    App Store
     │         (internal)           (alpha)       Connect
     │              │                 │              │
     └──────────────┴─────────────────┴──────────────┘
                           │
                    CI/CD Pipeline
                    (Fastlane + GitHub Actions)
```

### Version Strategy

```
Major.Minor.Patch (Build)
  1  .  0  .  0   (100)

Major: Breaking changes, major features
Minor: New features, improvements  
Patch: Bug fixes, small improvements
Build: Auto-incremented
```

---

## 📋 FEATURE CHECKLIST

| # | Feature | Priority | Hours |
|---|---------|----------|-------|
| 11.1 | Project Setup & Configuration | P0 | 8 |
| 11.2 | Navigation System | P0 | 8 |
| 11.3 | Redux Store & Persistence | P0 | 8 |
| 11.4 | Common Components Library | P0 | 12 |
| 11.5 | Login Screen | P0 | 4 |
| 11.6 | Biometric Authentication | P0 | 6 |
| 11.7 | PIN Screen | P0 | 4 |
| 11.8 | Dashboard Screen | P0 | 8 |
| 11.9 | Inventory Screens | P0 | 12 |
| 11.10 | Projects Screens | P1 | 10 |
| 11.11 | Transactions Screens | P0 | 12 |
| 11.12 | Payments Screens | P0 | 10 |
| 11.13 | SQLite Offline Storage | P0 | 8 |
| 11.14 | Sync Engine | P0 | 16 |
| 11.15 | Push Notifications | P1 | 12 |
| 11.16 | Barcode Scanner | P1 | 8 |
| 11.17 | Document Scanner | P1 | 10 |
| 11.18 | Analytics Screen | P1 | 10 |
| 11.19 | Settings & Profile | P2 | 6 |
| 11.20 | Internationalization | P2 | 6 |
| 11.21 | Testing & QA | P0 | 12 |

**Total Estimated Hours: ~190 hours**

---

*Phase 11 Plan - LogiAccounting Pro*
*Mobile Native Apps (React Native)*
*Cross-Platform iOS & Android*
