export const SHORTCUTS = {
  global: [
    { keys: ['ctrl', 'k'], action: 'openCommandPalette', label: 'Open Command Palette' },
    { keys: ['ctrl', '/'], action: 'showShortcuts', label: 'Show Shortcuts' },
    { keys: ['escape'], action: 'closeModal', label: 'Close Modal / Cancel' }
  ],
  navigation: [
    { keys: ['g', 'd'], action: 'goToDashboard', label: 'Go to Dashboard' },
    { keys: ['g', 'i'], action: 'goToInventory', label: 'Go to Inventory' },
    { keys: ['g', 'p'], action: 'goToProjects', label: 'Go to Projects' },
    { keys: ['g', 't'], action: 'goToTransactions', label: 'Go to Transactions' },
    { keys: ['g', 'y'], action: 'goToPayments', label: 'Go to Payments' },
    { keys: ['g', 'r'], action: 'goToReports', label: 'Go to Reports' },
    { keys: ['g', 's'], action: 'goToSettings', label: 'Go to Settings' }
  ],
  actions: [
    { keys: ['ctrl', 'n'], action: 'newItem', label: 'New Item' },
    { keys: ['ctrl', 's'], action: 'saveForm', label: 'Save Form' },
    { keys: ['ctrl', 'e'], action: 'exportData', label: 'Export Data' }
  ]
};

export const COMMAND_ITEMS = [
  { id: 'nav-dashboard', label: 'Go to Dashboard', category: 'Navigation', path: '/dashboard', icon: '📊' },
  { id: 'nav-inventory', label: 'Go to Inventory', category: 'Navigation', path: '/inventory', icon: '📦' },
  { id: 'nav-projects', label: 'Go to Projects', category: 'Navigation', path: '/projects', icon: '📁' },
  { id: 'nav-transactions', label: 'Go to Transactions', category: 'Navigation', path: '/transactions', icon: '💰' },
  { id: 'nav-payments', label: 'Go to Payments', category: 'Navigation', path: '/payments', icon: '💳' },
  { id: 'nav-reports', label: 'Go to Reports', category: 'Navigation', path: '/reports', icon: '📈' },
  { id: 'nav-settings', label: 'Go to Settings', category: 'Navigation', path: '/settings', icon: '⚙️' },
  { id: 'nav-ai', label: 'Go to AI Dashboard', category: 'Navigation', path: '/ai-dashboard', icon: '🤖' },

  { id: 'new-material', label: 'New Material', category: 'Create', action: 'create', entity: 'material', icon: '➕' },
  { id: 'new-transaction', label: 'New Transaction', category: 'Create', action: 'create', entity: 'transaction', icon: '➕' },
  { id: 'new-payment', label: 'New Payment', category: 'Create', action: 'create', entity: 'payment', icon: '➕' },
  { id: 'new-project', label: 'New Project', category: 'Create', action: 'create', entity: 'project', icon: '➕' },

  { id: 'theme-light', label: 'Light Theme', category: 'Theme', action: 'theme', value: 'light', icon: '☀️' },
  { id: 'theme-dark', label: 'Dark Theme', category: 'Theme', action: 'theme', value: 'dark', icon: '🌙' },

  { id: 'shortcuts', label: 'Keyboard Shortcuts', category: 'Help', action: 'showShortcuts', icon: '⌨️' },
  { id: 'help', label: 'Help Center', category: 'Help', path: '/help', icon: '❓' }
];
