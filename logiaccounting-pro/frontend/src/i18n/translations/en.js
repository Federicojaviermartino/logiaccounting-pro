export default {
  // Common
  common: {
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    import: 'Import',
    loading: 'Loading...',
    noData: 'No data available',
    confirm: 'Confirm',
    close: 'Close',
    yes: 'Yes',
    no: 'No',
    all: 'All',
    actions: 'Actions',
    status: 'Status',
    date: 'Date',
    amount: 'Amount',
    description: 'Description',
    name: 'Name',
    type: 'Type',
    category: 'Category',
    total: 'Total',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information'
  },

  // Navigation
  nav: {
    dashboard: 'Dashboard',
    inventory: 'Inventory',
    movements: 'Movements',
    projects: 'Projects',
    transactions: 'Transactions',
    payments: 'Payments',
    users: 'Users',
    reports: 'Reports',
    aiDashboard: 'AI Dashboard',
    invoiceOcr: 'Invoice OCR',
    assistant: 'Assistant',
    activityLog: 'Activity Log',
    bulkOperations: 'Bulk Operations',
    settings: 'Settings',
    logout: 'Logout',
    logistics: 'Logistics',
    finance: 'Finance',
    aiTools: 'AI Tools',
    administration: 'Administration'
  },

  // Dashboard
  dashboard: {
    title: 'Dashboard',
    welcome: 'Welcome',
    totalRevenue: 'Total Revenue',
    totalExpenses: 'Total Expenses',
    netProfit: 'Net Profit',
    pendingPayments: 'Pending Payments',
    lowStock: 'Low Stock Items',
    activeProjects: 'Active Projects',
    recentActivity: 'Recent Activity',
    quickActions: 'Quick Actions'
  },

  // Inventory
  inventory: {
    title: 'Inventory Management',
    materials: 'Materials',
    addMaterial: 'Add Material',
    editMaterial: 'Edit Material',
    reference: 'Reference',
    unit: 'Unit',
    quantity: 'Quantity',
    minStock: 'Min. Stock',
    unitCost: 'Unit Cost',
    totalValue: 'Total Value',
    state: 'State',
    available: 'Available',
    reserved: 'Reserved',
    damaged: 'Damaged',
    lowStockAlert: 'Low Stock Alert'
  },

  // Movements
  movements: {
    title: 'Stock Movements',
    addMovement: 'Add Movement',
    entry: 'Entry',
    exit: 'Exit',
    transfer: 'Transfer',
    adjustment: 'Adjustment',
    material: 'Material',
    fromLocation: 'From Location',
    toLocation: 'To Location',
    reason: 'Reason'
  },

  // Projects
  projects: {
    title: 'Projects',
    addProject: 'Add Project',
    editProject: 'Edit Project',
    client: 'Client',
    budget: 'Budget',
    startDate: 'Start Date',
    endDate: 'End Date',
    progress: 'Progress',
    statusActive: 'Active',
    statusCompleted: 'Completed',
    statusOnHold: 'On Hold',
    statusCancelled: 'Cancelled'
  },

  // Transactions
  transactions: {
    title: 'Transactions',
    addTransaction: 'Add Transaction',
    editTransaction: 'Edit Transaction',
    income: 'Income',
    expense: 'Expense',
    vendor: 'Vendor',
    invoiceNumber: 'Invoice Number',
    paymentMethod: 'Payment Method'
  },

  // Payments
  payments: {
    title: 'Payments',
    addPayment: 'Add Payment',
    editPayment: 'Edit Payment',
    receivable: 'Receivable',
    payable: 'Payable',
    dueDate: 'Due Date',
    paidDate: 'Paid Date',
    statusPending: 'Pending',
    statusPaid: 'Paid',
    statusOverdue: 'Overdue',
    markAsPaid: 'Mark as Paid'
  },

  // Users
  users: {
    title: 'User Management',
    addUser: 'Add User',
    editUser: 'Edit User',
    email: 'Email',
    firstName: 'First Name',
    lastName: 'Last Name',
    role: 'Role',
    roleAdmin: 'Administrator',
    roleClient: 'Client',
    roleSupplier: 'Supplier',
    statusActive: 'Active',
    statusInactive: 'Inactive'
  },

  // Reports
  reports: {
    title: 'Reports & Analytics',
    cashFlow: 'Cash Flow',
    profitLoss: 'Profit & Loss',
    inventoryReport: 'Inventory Report',
    projectReport: 'Project Report',
    generateReport: 'Generate Report',
    downloadPdf: 'Download PDF',
    period: 'Period'
  },

  // AI Features
  ai: {
    dashboard: 'AI Analytics Dashboard',
    invoiceOcr: 'Smart Invoice Processing',
    assistant: 'Profitability Assistant',
    cashflowPrediction: 'Cash Flow Prediction',
    anomalyDetection: 'Anomaly Detection',
    paymentScheduler: 'Payment Scheduler',
    processingInvoice: 'Processing invoice...',
    extractedData: 'Extracted Data',
    confidence: 'Confidence',
    askAssistant: 'Ask the assistant...',
    analyzing: 'Analyzing...'
  },

  // Activity Log
  activity: {
    title: 'Activity Log',
    user: 'User',
    action: 'Action',
    entity: 'Entity',
    timestamp: 'Timestamp',
    details: 'Details',
    actionLogin: 'Login',
    actionLogout: 'Logout',
    actionCreate: 'Create',
    actionUpdate: 'Update',
    actionDelete: 'Delete',
    actionExport: 'Export',
    actionImport: 'Import'
  },

  // Bulk Operations
  bulk: {
    title: 'Bulk Operations',
    importData: 'Import Data',
    exportData: 'Export Data',
    massUpdate: 'Mass Update',
    massDelete: 'Mass Delete',
    selectEntity: 'Select Entity',
    downloadTemplate: 'Download Template',
    uploadFile: 'Upload File',
    skipErrors: 'Skip Errors',
    processing: 'Processing...',
    importResults: 'Import Results',
    rowsProcessed: 'Rows Processed',
    rowsImported: 'Rows Imported',
    rowsSkipped: 'Rows Skipped'
  },

  // Settings
  settings: {
    title: 'Settings',
    userPreferences: 'User Preferences',
    systemSettings: 'System Settings',
    language: 'Language',
    theme: 'Theme',
    notifications: 'Notifications',
    emailNotifications: 'Email Notifications',
    currency: 'Currency',
    dateFormat: 'Date Format',
    timezone: 'Timezone',
    saveChanges: 'Save Changes'
  },

  // Auth
  auth: {
    login: 'Login',
    logout: 'Logout',
    email: 'Email',
    password: 'Password',
    forgotPassword: 'Forgot Password?',
    rememberMe: 'Remember Me',
    loginButton: 'Sign In',
    loginError: 'Invalid email or password'
  },

  // Messages
  messages: {
    savedSuccessfully: 'Saved successfully',
    deletedSuccessfully: 'Deleted successfully',
    updatedSuccessfully: 'Updated successfully',
    createdSuccessfully: 'Created successfully',
    errorOccurred: 'An error occurred',
    confirmDelete: 'Are you sure you want to delete this item?',
    unsavedChanges: 'You have unsaved changes. Are you sure you want to leave?'
  }
};
