# LogiAccounting Pro - Phase 3 Tasks (Part 3/3)

## INTERNATIONALIZATION + PWA + PERFORMANCE

---

## TASK 9: INTERNATIONALIZATION (i18n)

### 9.1 Install Dependencies

```bash
cd frontend
npm install react-i18next i18next i18next-browser-languagedetector
```

### 9.2 Create i18n Configuration

**File:** `frontend/src/i18n/index.js`

```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import es from './locales/es.json';

const resources = {
  en: { translation: en },
  es: { translation: es }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  });

export default i18n;
```

### 9.3 Create English Translations

**File:** `frontend/src/i18n/locales/en.json`

```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "add": "Add",
    "create": "Create",
    "update": "Update",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "import": "Import",
    "loading": "Loading...",
    "noData": "No data available",
    "confirm": "Confirm",
    "back": "Back",
    "next": "Next",
    "yes": "Yes",
    "no": "No",
    "all": "All",
    "actions": "Actions",
    "status": "Status",
    "date": "Date",
    "amount": "Amount",
    "description": "Description",
    "name": "Name",
    "email": "Email",
    "phone": "Phone",
    "address": "Address",
    "active": "Active",
    "inactive": "Inactive",
    "pending": "Pending",
    "completed": "Completed",
    "success": "Success",
    "error": "Error",
    "warning": "Warning"
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "register": "Register",
    "email": "Email Address",
    "password": "Password",
    "forgotPassword": "Forgot Password?",
    "rememberMe": "Remember me",
    "loginTitle": "Welcome Back",
    "loginSubtitle": "Enterprise Logistics & Accounting Platform",
    "loginButton": "Sign In",
    "invalidCredentials": "Invalid email or password",
    "sessionExpired": "Session expired. Please login again."
  },
  "nav": {
    "dashboard": "Dashboard",
    "inventory": "Inventory",
    "projects": "Projects",
    "movements": "Movements",
    "transactions": "Transactions",
    "payments": "Payments",
    "users": "Users",
    "reports": "Reports",
    "settings": "Settings",
    "aiDashboard": "AI Dashboard",
    "invoiceOcr": "Invoice OCR",
    "assistant": "Assistant",
    "activityLog": "Activity Log",
    "bulkOperations": "Bulk Operations",
    "logistics": "Logistics",
    "finance": "Finance",
    "aiTools": "AI Tools",
    "administration": "Administration"
  },
  "dashboard": {
    "title": "Dashboard",
    "welcome": "Welcome back",
    "activeProjects": "Active Projects",
    "pendingPayments": "Pending Payments",
    "lowStockItems": "Low Stock Items",
    "monthlyRevenue": "Monthly Revenue",
    "monthlyExpenses": "Monthly Expenses",
    "netProfit": "Net Profit",
    "recentTransactions": "Recent Transactions",
    "quickActions": "Quick Actions",
    "addMaterial": "Add Material",
    "newTransaction": "New Transaction",
    "viewPayments": "View Payments",
    "stockMovement": "Stock Movement",
    "aiInsights": "AI Insights",
    "cashForecast": "30-Day Cash Forecast",
    "anomaliesDetected": "Anomalies Detected",
    "riskScore": "Risk Score"
  },
  "inventory": {
    "title": "Inventory Management",
    "materials": "Materials",
    "addMaterial": "Add Material",
    "editMaterial": "Edit Material",
    "reference": "Reference",
    "materialName": "Material Name",
    "category": "Category",
    "location": "Location",
    "quantity": "Quantity",
    "minStock": "Min. Stock",
    "unit": "Unit",
    "unitCost": "Unit Cost",
    "totalValue": "Total Value",
    "state": "State",
    "lowStock": "Low Stock",
    "inStock": "In Stock",
    "outOfStock": "Out of Stock",
    "categories": "Categories",
    "locations": "Locations"
  },
  "projects": {
    "title": "Projects",
    "addProject": "Add Project",
    "editProject": "Edit Project",
    "projectName": "Project Name",
    "client": "Client",
    "budget": "Budget",
    "spent": "Spent",
    "remaining": "Remaining",
    "startDate": "Start Date",
    "endDate": "End Date",
    "status": "Status",
    "planning": "Planning",
    "inProgress": "In Progress",
    "onHold": "On Hold",
    "cancelled": "Cancelled"
  },
  "transactions": {
    "title": "Transactions",
    "addTransaction": "Add Transaction",
    "editTransaction": "Edit Transaction",
    "type": "Type",
    "income": "Income",
    "expense": "Expense",
    "vendor": "Vendor",
    "invoiceNumber": "Invoice Number",
    "project": "Project",
    "totalIncome": "Total Income",
    "totalExpenses": "Total Expenses",
    "balance": "Balance"
  },
  "payments": {
    "title": "Payments",
    "addPayment": "Add Payment",
    "editPayment": "Edit Payment",
    "paymentType": "Payment Type",
    "payable": "Payable",
    "receivable": "Receivable",
    "dueDate": "Due Date",
    "paidDate": "Paid Date",
    "paid": "Paid",
    "overdue": "Overdue",
    "markAsPaid": "Mark as Paid",
    "totalPending": "Total Pending",
    "totalOverdue": "Total Overdue",
    "totalPaid": "Total Paid"
  },
  "users": {
    "title": "User Management",
    "addUser": "Add User",
    "editUser": "Edit User",
    "firstName": "First Name",
    "lastName": "Last Name",
    "role": "Role",
    "admin": "Administrator",
    "client": "Client",
    "supplier": "Supplier",
    "company": "Company",
    "lastLogin": "Last Login",
    "createdAt": "Created At"
  },
  "reports": {
    "title": "Reports",
    "overview": "Overview",
    "cashFlow": "Cash Flow",
    "expensesByCategory": "Expenses by Category",
    "projectProfitability": "Project Profitability",
    "inventoryStatus": "Inventory Status",
    "paymentSummary": "Payment Summary",
    "generateReport": "Generate Report",
    "downloadPdf": "Download PDF",
    "downloadCsv": "Download CSV",
    "downloadExcel": "Download Excel",
    "period": "Period",
    "thisMonth": "This Month",
    "lastMonth": "Last Month",
    "thisQuarter": "This Quarter",
    "thisYear": "This Year",
    "custom": "Custom Range"
  },
  "ai": {
    "dashboard": "AI Dashboard",
    "cashFlowPredictor": "Cash Flow Predictor",
    "anomalyDetection": "Anomaly Detection",
    "paymentScheduler": "Payment Scheduler",
    "invoiceOcr": "Invoice OCR",
    "assistant": "Profitability Assistant",
    "runScan": "Run Scan",
    "predict": "Predict",
    "optimize": "Optimize",
    "uploadInvoice": "Upload Invoice",
    "processInvoice": "Process Invoice",
    "askQuestion": "Ask a question...",
    "suggestedQuestions": "Suggested Questions",
    "predictedIncome": "Predicted Income",
    "predictedExpenses": "Predicted Expenses",
    "predictedNet": "Predicted Net",
    "anomaliesFound": "Anomalies Found",
    "potentialSavings": "Potential Savings"
  },
  "settings": {
    "title": "Settings",
    "userPreferences": "User Preferences",
    "systemSettings": "System Settings",
    "language": "Language",
    "theme": "Theme",
    "lightTheme": "Light",
    "darkTheme": "Dark",
    "systemTheme": "System",
    "dateFormat": "Date Format",
    "currency": "Currency",
    "notifications": "Notifications",
    "emailNotifications": "Email Notifications",
    "pushNotifications": "Push Notifications",
    "companyName": "Company Name",
    "taxRate": "Default Tax Rate",
    "paymentTerms": "Payment Terms (days)",
    "lowStockThreshold": "Low Stock Threshold",
    "savePreferences": "Save Preferences",
    "saveSettings": "Save Settings"
  },
  "activity": {
    "title": "Activity Log",
    "action": "Action",
    "entity": "Entity",
    "user": "User",
    "timestamp": "Timestamp",
    "details": "Details",
    "login": "Login",
    "logout": "Logout",
    "create": "Create",
    "update": "Update",
    "delete": "Delete",
    "export": "Export",
    "import": "Import"
  },
  "bulk": {
    "title": "Bulk Operations",
    "import": "Import Data",
    "export": "Export Data",
    "downloadTemplate": "Download Template",
    "uploadFile": "Upload File",
    "selectEntity": "Select Entity",
    "importProgress": "Import Progress",
    "rowsProcessed": "Rows Processed",
    "successful": "Successful",
    "failed": "Failed",
    "errors": "Errors",
    "skipErrors": "Skip rows with errors"
  },
  "notifications": {
    "title": "Notifications",
    "markAllRead": "Mark all as read",
    "noNotifications": "No notifications",
    "paymentDue": "Payment due soon",
    "paymentOverdue": "Payment overdue",
    "lowStock": "Low stock alert",
    "anomalyDetected": "Anomaly detected"
  },
  "errors": {
    "generic": "Something went wrong. Please try again.",
    "networkError": "Network error. Please check your connection.",
    "unauthorized": "You are not authorized to perform this action.",
    "notFound": "The requested resource was not found.",
    "validation": "Please check the form for errors.",
    "serverError": "Server error. Please try again later."
  }
}
```

### 9.4 Create Spanish Translations

**File:** `frontend/src/i18n/locales/es.json`

```json
{
  "common": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar",
    "edit": "Editar",
    "add": "Agregar",
    "create": "Crear",
    "update": "Actualizar",
    "search": "Buscar",
    "filter": "Filtrar",
    "export": "Exportar",
    "import": "Importar",
    "loading": "Cargando...",
    "noData": "No hay datos disponibles",
    "confirm": "Confirmar",
    "back": "Volver",
    "next": "Siguiente",
    "yes": "Sí",
    "no": "No",
    "all": "Todos",
    "actions": "Acciones",
    "status": "Estado",
    "date": "Fecha",
    "amount": "Monto",
    "description": "Descripción",
    "name": "Nombre",
    "email": "Correo",
    "phone": "Teléfono",
    "address": "Dirección",
    "active": "Activo",
    "inactive": "Inactivo",
    "pending": "Pendiente",
    "completed": "Completado",
    "success": "Éxito",
    "error": "Error",
    "warning": "Advertencia"
  },
  "auth": {
    "login": "Iniciar Sesión",
    "logout": "Cerrar Sesión",
    "register": "Registrarse",
    "email": "Correo Electrónico",
    "password": "Contraseña",
    "forgotPassword": "¿Olvidaste tu contraseña?",
    "rememberMe": "Recordarme",
    "loginTitle": "Bienvenido",
    "loginSubtitle": "Plataforma de Logística y Contabilidad Empresarial",
    "loginButton": "Ingresar",
    "invalidCredentials": "Correo o contraseña inválidos",
    "sessionExpired": "Sesión expirada. Por favor ingresa nuevamente."
  },
  "nav": {
    "dashboard": "Panel",
    "inventory": "Inventario",
    "projects": "Proyectos",
    "movements": "Movimientos",
    "transactions": "Transacciones",
    "payments": "Pagos",
    "users": "Usuarios",
    "reports": "Reportes",
    "settings": "Configuración",
    "aiDashboard": "Panel IA",
    "invoiceOcr": "OCR Facturas",
    "assistant": "Asistente",
    "activityLog": "Registro de Actividad",
    "bulkOperations": "Operaciones Masivas",
    "logistics": "Logística",
    "finance": "Finanzas",
    "aiTools": "Herramientas IA",
    "administration": "Administración"
  },
  "dashboard": {
    "title": "Panel de Control",
    "welcome": "Bienvenido",
    "activeProjects": "Proyectos Activos",
    "pendingPayments": "Pagos Pendientes",
    "lowStockItems": "Items con Stock Bajo",
    "monthlyRevenue": "Ingresos Mensuales",
    "monthlyExpenses": "Gastos Mensuales",
    "netProfit": "Ganancia Neta",
    "recentTransactions": "Transacciones Recientes",
    "quickActions": "Acciones Rápidas",
    "addMaterial": "Agregar Material",
    "newTransaction": "Nueva Transacción",
    "viewPayments": "Ver Pagos",
    "stockMovement": "Movimiento de Stock",
    "aiInsights": "Insights de IA",
    "cashForecast": "Pronóstico 30 Días",
    "anomaliesDetected": "Anomalías Detectadas",
    "riskScore": "Puntuación de Riesgo"
  },
  "inventory": {
    "title": "Gestión de Inventario",
    "materials": "Materiales",
    "addMaterial": "Agregar Material",
    "editMaterial": "Editar Material",
    "reference": "Referencia",
    "materialName": "Nombre del Material",
    "category": "Categoría",
    "location": "Ubicación",
    "quantity": "Cantidad",
    "minStock": "Stock Mínimo",
    "unit": "Unidad",
    "unitCost": "Costo Unitario",
    "totalValue": "Valor Total",
    "state": "Estado",
    "lowStock": "Stock Bajo",
    "inStock": "En Stock",
    "outOfStock": "Sin Stock",
    "categories": "Categorías",
    "locations": "Ubicaciones"
  },
  "projects": {
    "title": "Proyectos",
    "addProject": "Agregar Proyecto",
    "editProject": "Editar Proyecto",
    "projectName": "Nombre del Proyecto",
    "client": "Cliente",
    "budget": "Presupuesto",
    "spent": "Gastado",
    "remaining": "Restante",
    "startDate": "Fecha de Inicio",
    "endDate": "Fecha de Fin",
    "status": "Estado",
    "planning": "Planificación",
    "inProgress": "En Progreso",
    "onHold": "En Espera",
    "cancelled": "Cancelado"
  },
  "transactions": {
    "title": "Transacciones",
    "addTransaction": "Agregar Transacción",
    "editTransaction": "Editar Transacción",
    "type": "Tipo",
    "income": "Ingreso",
    "expense": "Gasto",
    "vendor": "Proveedor",
    "invoiceNumber": "Número de Factura",
    "project": "Proyecto",
    "totalIncome": "Total Ingresos",
    "totalExpenses": "Total Gastos",
    "balance": "Balance"
  },
  "payments": {
    "title": "Pagos",
    "addPayment": "Agregar Pago",
    "editPayment": "Editar Pago",
    "paymentType": "Tipo de Pago",
    "payable": "Por Pagar",
    "receivable": "Por Cobrar",
    "dueDate": "Fecha de Vencimiento",
    "paidDate": "Fecha de Pago",
    "paid": "Pagado",
    "overdue": "Vencido",
    "markAsPaid": "Marcar como Pagado",
    "totalPending": "Total Pendiente",
    "totalOverdue": "Total Vencido",
    "totalPaid": "Total Pagado"
  },
  "users": {
    "title": "Gestión de Usuarios",
    "addUser": "Agregar Usuario",
    "editUser": "Editar Usuario",
    "firstName": "Nombre",
    "lastName": "Apellido",
    "role": "Rol",
    "admin": "Administrador",
    "client": "Cliente",
    "supplier": "Proveedor",
    "company": "Empresa",
    "lastLogin": "Último Acceso",
    "createdAt": "Fecha de Creación"
  },
  "reports": {
    "title": "Reportes",
    "overview": "Resumen",
    "cashFlow": "Flujo de Caja",
    "expensesByCategory": "Gastos por Categoría",
    "projectProfitability": "Rentabilidad de Proyectos",
    "inventoryStatus": "Estado del Inventario",
    "paymentSummary": "Resumen de Pagos",
    "generateReport": "Generar Reporte",
    "downloadPdf": "Descargar PDF",
    "downloadCsv": "Descargar CSV",
    "downloadExcel": "Descargar Excel",
    "period": "Período",
    "thisMonth": "Este Mes",
    "lastMonth": "Mes Anterior",
    "thisQuarter": "Este Trimestre",
    "thisYear": "Este Año",
    "custom": "Personalizado"
  },
  "ai": {
    "dashboard": "Panel de IA",
    "cashFlowPredictor": "Predictor de Flujo de Caja",
    "anomalyDetection": "Detección de Anomalías",
    "paymentScheduler": "Programador de Pagos",
    "invoiceOcr": "OCR de Facturas",
    "assistant": "Asistente de Rentabilidad",
    "runScan": "Ejecutar Escaneo",
    "predict": "Predecir",
    "optimize": "Optimizar",
    "uploadInvoice": "Subir Factura",
    "processInvoice": "Procesar Factura",
    "askQuestion": "Haz una pregunta...",
    "suggestedQuestions": "Preguntas Sugeridas",
    "predictedIncome": "Ingresos Proyectados",
    "predictedExpenses": "Gastos Proyectados",
    "predictedNet": "Neto Proyectado",
    "anomaliesFound": "Anomalías Encontradas",
    "potentialSavings": "Ahorro Potencial"
  },
  "settings": {
    "title": "Configuración",
    "userPreferences": "Preferencias de Usuario",
    "systemSettings": "Configuración del Sistema",
    "language": "Idioma",
    "theme": "Tema",
    "lightTheme": "Claro",
    "darkTheme": "Oscuro",
    "systemTheme": "Sistema",
    "dateFormat": "Formato de Fecha",
    "currency": "Moneda",
    "notifications": "Notificaciones",
    "emailNotifications": "Notificaciones por Email",
    "pushNotifications": "Notificaciones Push",
    "companyName": "Nombre de la Empresa",
    "taxRate": "Tasa de Impuesto Predeterminada",
    "paymentTerms": "Términos de Pago (días)",
    "lowStockThreshold": "Umbral de Stock Bajo",
    "savePreferences": "Guardar Preferencias",
    "saveSettings": "Guardar Configuración"
  },
  "activity": {
    "title": "Registro de Actividad",
    "action": "Acción",
    "entity": "Entidad",
    "user": "Usuario",
    "timestamp": "Fecha y Hora",
    "details": "Detalles",
    "login": "Inicio de Sesión",
    "logout": "Cierre de Sesión",
    "create": "Crear",
    "update": "Actualizar",
    "delete": "Eliminar",
    "export": "Exportar",
    "import": "Importar"
  },
  "bulk": {
    "title": "Operaciones Masivas",
    "import": "Importar Datos",
    "export": "Exportar Datos",
    "downloadTemplate": "Descargar Plantilla",
    "uploadFile": "Subir Archivo",
    "selectEntity": "Seleccionar Entidad",
    "importProgress": "Progreso de Importación",
    "rowsProcessed": "Filas Procesadas",
    "successful": "Exitosos",
    "failed": "Fallidos",
    "errors": "Errores",
    "skipErrors": "Omitir filas con errores"
  },
  "notifications": {
    "title": "Notificaciones",
    "markAllRead": "Marcar todo como leído",
    "noNotifications": "Sin notificaciones",
    "paymentDue": "Pago próximo a vencer",
    "paymentOverdue": "Pago vencido",
    "lowStock": "Alerta de stock bajo",
    "anomalyDetected": "Anomalía detectada"
  },
  "errors": {
    "generic": "Algo salió mal. Por favor intenta de nuevo.",
    "networkError": "Error de red. Verifica tu conexión.",
    "unauthorized": "No tienes autorización para realizar esta acción.",
    "notFound": "El recurso solicitado no fue encontrado.",
    "validation": "Por favor revisa el formulario por errores.",
    "serverError": "Error del servidor. Intenta más tarde."
  }
}
```

### 9.5 Create Language Selector Component

**File:** `frontend/src/components/LanguageSelector.jsx`

```jsx
import { useTranslation } from 'react-i18next';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' }
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();

  const handleChange = (langCode) => {
    i18n.changeLanguage(langCode);
    localStorage.setItem('language', langCode);
  };

  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  return (
    <div className="language-selector">
      <select 
        value={i18n.language}
        onChange={(e) => handleChange(e.target.value)}
        className="lang-select"
      >
        {languages.map(lang => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
}
```

### 9.6 Add Language Selector Styles

**Add to:** `frontend/src/index.css`

```css
/* Language Selector */
.language-selector {
  display: flex;
  align-items: center;
}

.lang-select {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.85rem;
  color: var(--text-primary);
  cursor: pointer;
  outline: none;
}

.lang-select:hover {
  border-color: var(--primary);
}

.lang-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}
```

### 9.7 Update main.jsx to Include i18n

**Update:** `frontend/src/main.jsx`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import './i18n';  // Add this line
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

### 9.8 Add Language Selector to Layout

**Update header-right in:** `frontend/src/components/Layout.jsx`

```jsx
import LanguageSelector from './LanguageSelector';
// ... existing imports

// In header-right div:
<div className="header-right">
  <LanguageSelector />
  <ThemeToggle />
  <NotificationBell />
  <div className="user-info">
    {/* ... */}
  </div>
</div>
```

---

## TASK 10: PWA SUPPORT

### 10.1 Create Web App Manifest

**File:** `frontend/public/manifest.json`

```json
{
  "name": "LogiAccounting Pro",
  "short_name": "LogiAccounting",
  "description": "Enterprise logistics and accounting platform with AI-powered features",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#667eea",
  "orientation": "portrait-primary",
  "scope": "/",
  "icons": [
    {
      "src": "/icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable any"
    }
  ],
  "categories": ["business", "finance", "productivity"],
  "screenshots": [],
  "prefer_related_applications": false
}
```

### 10.2 Create Service Worker

**File:** `frontend/public/sw.js`

```javascript
const CACHE_NAME = 'logiaccounting-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys()
      .then((keys) => {
        return Promise.all(
          keys
            .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
            .map((key) => caches.delete(key))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip API requests (always network)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // For navigation requests, try network first, fall back to cache/offline
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.match(request)
            .then((cached) => cached || caches.match('/offline.html'));
        })
    );
    return;
  }

  // For static assets, cache first
  event.respondWith(
    caches.match(request)
      .then((cached) => {
        if (cached) {
          return cached;
        }
        
        return fetch(request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200) {
              return response;
            }

            // Clone and cache
            const responseToCache = response.clone();
            caches.open(DYNAMIC_CACHE)
              .then((cache) => {
                cache.put(request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Return offline page for HTML requests
            if (request.headers.get('accept').includes('text/html')) {
              return caches.match('/offline.html');
            }
          });
      })
  );
});

// Background sync (future feature)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-transactions') {
    console.log('[SW] Syncing transactions...');
    // Implement sync logic here
  }
});

// Push notifications (future feature)
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};
  const options = {
    body: data.body || 'New notification',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-72.png',
    vibrate: [100, 50, 100],
    data: { url: data.url || '/' }
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'LogiAccounting Pro', options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
```

### 10.3 Create Offline Page

**File:** `frontend/public/offline.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - LogiAccounting Pro</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #f1f5f9;
    }
    
    .container {
      text-align: center;
      padding: 40px;
      max-width: 500px;
    }
    
    .icon {
      font-size: 80px;
      margin-bottom: 24px;
    }
    
    h1 {
      font-size: 2rem;
      margin-bottom: 16px;
      color: #f1f5f9;
    }
    
    p {
      font-size: 1.1rem;
      color: #94a3b8;
      margin-bottom: 32px;
      line-height: 1.6;
    }
    
    .btn {
      display: inline-block;
      padding: 12px 32px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    .logo {
      margin-bottom: 40px;
    }
    
    .logo span {
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">
      <span>📊 LogiAccounting Pro</span>
    </div>
    
    <div class="icon">📡</div>
    
    <h1>You're Offline</h1>
    
    <p>
      It looks like you've lost your internet connection. 
      Please check your network and try again.
    </p>
    
    <button class="btn" onclick="window.location.reload()">
      Try Again
    </button>
  </div>
  
  <script>
    // Auto-retry when back online
    window.addEventListener('online', () => {
      window.location.reload();
    });
  </script>
</body>
</html>
```

### 10.4 Update index.html

**Update:** `frontend/index.html`

Add in `<head>`:
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#667eea">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="LogiAccounting">
<link rel="apple-touch-icon" href="/icons/icon-192.png">
```

Add before `</body>`:
```html
<script>
  // Register service worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((reg) => console.log('SW registered:', reg.scope))
        .catch((err) => console.log('SW registration failed:', err));
    });
  }
</script>
```

### 10.5 Create PWA Icons (Placeholder)

Create directory and placeholder icons:
```bash
mkdir -p frontend/public/icons
```

**Note:** Generate actual icons using a tool like:
- https://realfavicongenerator.net/
- https://maskable.app/editor

For now, create a simple SVG that can be used:

**File:** `frontend/public/icons/icon.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#667eea"/>
  <text x="256" y="320" text-anchor="middle" font-size="240" font-family="Arial" fill="white">📊</text>
</svg>
```

---

## TASK 11: PERFORMANCE OPTIMIZATION

### 11.1 Implement Lazy Loading for Pages

**Update:** `frontend/src/App.jsx`

```jsx
import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Eagerly load Login (needed immediately)
import Login from './pages/Login';
import Layout from './components/Layout';

// Lazy load all other pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Inventory = lazy(() => import('./pages/Inventory'));
const Projects = lazy(() => import('./pages/Projects'));
const Movements = lazy(() => import('./pages/Movements'));
const Transactions = lazy(() => import('./pages/Transactions'));
const Payments = lazy(() => import('./pages/Payments'));
const Users = lazy(() => import('./pages/Users'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));
const ActivityLog = lazy(() => import('./pages/ActivityLog'));
const BulkOperations = lazy(() => import('./pages/BulkOperations'));

// AI Pages
const AIDashboard = lazy(() => import('./pages/AIDashboard'));
const InvoiceOCR = lazy(() => import('./pages/InvoiceOCR'));
const Assistant = lazy(() => import('./pages/Assistant'));

// Loading component
function PageLoader() {
  return (
    <div className="page-loader">
      <div className="loading-spinner"></div>
      <p>Loading...</p>
    </div>
  );
}

function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <PageLoader />;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        <Route path="/dashboard" element={
          <PrivateRoute>
            <Layout><Dashboard /></Layout>
          </PrivateRoute>
        } />
        
        {/* ... rest of routes wrapped in Layout */}
        
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
```

### 11.2 Add Page Loader Styles

**Add to:** `frontend/src/index.css`

```css
/* Page Loader */
.page-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-secondary);
}

.page-loader p {
  margin-top: 16px;
  color: var(--text-muted);
}
```

### 11.3 Create Debounce Hook

**File:** `frontend/src/hooks/useDebounce.js`

```javascript
import { useState, useEffect } from 'react';

export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function useDebouncedCallback(callback, delay = 300) {
  const [timeoutId, setTimeoutId] = useState(null);

  const debouncedCallback = (...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    const newTimeoutId = setTimeout(() => {
      callback(...args);
    }, delay);
    
    setTimeoutId(newTimeoutId);
  };

  return debouncedCallback;
}
```

### 11.4 Create Image Lazy Loading Component

**File:** `frontend/src/components/LazyImage.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';

export default function LazyImage({ src, alt, className, placeholder }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} className={`lazy-image-container ${className || ''}`}>
      {isInView ? (
        <img
          src={src}
          alt={alt}
          className={`lazy-image ${isLoaded ? 'loaded' : ''}`}
          onLoad={() => setIsLoaded(true)}
        />
      ) : (
        <div className="lazy-image-placeholder">
          {placeholder || '📷'}
        </div>
      )}
    </div>
  );
}
```

### 11.5 Add Lazy Image Styles

**Add to:** `frontend/src/index.css`

```css
/* Lazy Image */
.lazy-image-container {
  position: relative;
  overflow: hidden;
}

.lazy-image {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.lazy-image.loaded {
  opacity: 1;
}

.lazy-image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  color: var(--text-muted);
  font-size: 2rem;
  min-height: 100px;
}
```

### 11.6 Optimize Vite Build Configuration

**Update:** `frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // Split chunks for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunk for React
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Chart libraries
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
          // i18n
          'i18n-vendor': ['i18next', 'react-i18next'],
        }
      }
    },
    // Chunk size warning limit
    chunkSizeWarningLimit: 500,
    // Enable source maps for production debugging
    sourcemap: false,
    // Minify
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
});
```

---

## TASK 12: FINAL BUILD AND DEPLOY

### 12.1 Create i18n Folder Structure

```bash
mkdir -p frontend/src/i18n/locales
```

### 12.2 Install All Phase 3 Dependencies

```bash
cd frontend
npm install react-i18next i18next i18next-browser-languagedetector
```

### 12.3 Run Tests

```bash
# Backend tests
cd backend
pytest -v

# Frontend build test
cd frontend
npm run build
```

### 12.4 Commit and Push

```bash
git add .
git commit -m "feat: Phase 3 Complete - Dark mode, i18n, PWA, Activity Log, Bulk Ops, Performance"
git push origin main
```

---

## COMPLETION CHECKLIST - PART 3

### i18n
- [ ] react-i18next installed
- [ ] i18n configuration created
- [ ] English translations complete
- [ ] Spanish translations complete
- [ ] Language selector component
- [ ] Language persists in localStorage

### PWA
- [ ] manifest.json created
- [ ] Service worker created
- [ ] Offline page created
- [ ] Icons created (placeholder)
- [ ] index.html updated
- [ ] App installable on mobile

### Performance
- [ ] Lazy loading implemented
- [ ] Page loader component
- [ ] useDebounce hook
- [ ] LazyImage component
- [ ] Vite build optimized
- [ ] Bundle size < 500KB

---

## PHASE 3 MASTER CHECKLIST

### Track A - UX ✓
- [ ] Dark Mode
- [ ] Settings Page
- [ ] Advanced Filters

### Track B - Enterprise ✓
- [ ] Activity Log
- [ ] Bulk Operations
- [ ] Email Notifications

### Track C - International ✓
- [ ] i18n (EN/ES)
- [ ] PWA Support
- [ ] Performance Optimization

### Final Verification
- [ ] All features working
- [ ] Build successful
- [ ] No console errors
- [ ] Responsive on mobile
- [ ] PWA installable
- [ ] Performance score > 80

---

**END OF PHASE 3 TASKS**
