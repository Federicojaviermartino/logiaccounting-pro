# LogiAccounting Pro - Phase 4 Tasks (Part 1/3)

## SECURITY & PRODUCTIVITY: 2FA + Command Palette + Shortcuts

---

## TASK 1: TWO-FACTOR AUTHENTICATION (2FA)

### 1.1 Install Backend Dependencies

```bash
cd backend
pip install pyotp qrcode[pil]
```

### 1.2 Create 2FA Service

**File:** `backend/app/services/two_factor.py`

```python
"""
Two-Factor Authentication Service
TOTP-based 2FA compatible with Google Authenticator, Authy, etc.
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Optional, List, Dict
from datetime import datetime


class TwoFactorService:
    """Manages 2FA for users"""
    
    _instance = None
    _user_2fa: Dict[str, dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._user_2fa = {}
        return cls._instance
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for recovery"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def get_totp_uri(self, secret: str, email: str, issuer: str = "LogiAccounting") -> str:
        """Generate TOTP URI for QR code"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)
    
    def generate_qr_code(self, secret: str, email: str) -> str:
        """Generate QR code as base64 image"""
        uri = self.get_totp_uri(secret, email)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def setup_2fa(self, user_id: str, email: str) -> dict:
        """Initialize 2FA setup for a user"""
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()
        
        self._user_2fa[user_id] = {
            "secret": secret,
            "backup_codes": [self.hash_backup_code(c) for c in backup_codes],
            "backup_codes_plain": backup_codes,
            "enabled": False,
            "verified": False,
            "setup_at": datetime.utcnow().isoformat()
        }
        
        qr_code = self.generate_qr_code(secret, email)
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes
        }
    
    def verify_setup(self, user_id: str, code: str) -> bool:
        """Verify 2FA setup with initial code"""
        if user_id not in self._user_2fa:
            return False
        
        user_2fa = self._user_2fa[user_id]
        
        if self.verify_code(user_2fa["secret"], code):
            user_2fa["verified"] = True
            user_2fa["enabled"] = True
            user_2fa["enabled_at"] = datetime.utcnow().isoformat()
            user_2fa.pop("backup_codes_plain", None)
            return True
        
        return False
    
    def verify_login(self, user_id: str, code: str) -> bool:
        """Verify 2FA code during login"""
        if user_id not in self._user_2fa:
            return False
        
        user_2fa = self._user_2fa[user_id]
        
        if not user_2fa.get("enabled"):
            return True
        
        # Try TOTP code first
        if self.verify_code(user_2fa["secret"], code):
            return True
        
        # Try backup code
        code_hash = self.hash_backup_code(code)
        if code_hash in user_2fa["backup_codes"]:
            user_2fa["backup_codes"].remove(code_hash)
            return True
        
        return False
    
    def is_2fa_enabled(self, user_id: str) -> bool:
        """Check if user has 2FA enabled"""
        if user_id not in self._user_2fa:
            return False
        return self._user_2fa[user_id].get("enabled", False)
    
    def disable_2fa(self, user_id: str) -> bool:
        """Disable 2FA for a user"""
        if user_id in self._user_2fa:
            del self._user_2fa[user_id]
            return True
        return False
    
    def get_2fa_status(self, user_id: str) -> dict:
        """Get 2FA status for a user"""
        if user_id not in self._user_2fa:
            return {"enabled": False}
        
        user_2fa = self._user_2fa[user_id]
        return {
            "enabled": user_2fa.get("enabled", False),
            "verified": user_2fa.get("verified", False),
            "enabled_at": user_2fa.get("enabled_at"),
            "backup_codes_remaining": len(user_2fa.get("backup_codes", []))
        }


# Global instance
two_factor_service = TwoFactorService()
```

### 1.3 Create 2FA Routes

**File:** `backend/app/routes/two_factor.py`

```python
"""
Two-Factor Authentication routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.two_factor import two_factor_service
from app.utils.auth import get_current_user

router = APIRouter()


class VerifyCodeRequest(BaseModel):
    code: str


@router.get("/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Get current user's 2FA status"""
    return two_factor_service.get_2fa_status(current_user["id"])


@router.post("/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Initialize 2FA setup - returns QR code and backup codes"""
    if two_factor_service.is_2fa_enabled(current_user["id"]):
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    
    result = two_factor_service.setup_2fa(
        current_user["id"],
        current_user["email"]
    )
    
    return {
        "qr_code": f"data:image/png;base64,{result['qr_code']}",
        "secret": result["secret"],
        "backup_codes": result["backup_codes"],
        "message": "Scan the QR code with your authenticator app"
    }


@router.post("/verify-setup")
async def verify_2fa_setup(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify 2FA setup with code from authenticator"""
    if two_factor_service.verify_setup(current_user["id"], request.code):
        return {"success": True, "message": "2FA enabled successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.post("/disable")
async def disable_2fa(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA (requires current code)"""
    if not two_factor_service.is_2fa_enabled(current_user["id"]):
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    
    if not two_factor_service.verify_login(current_user["id"], request.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    two_factor_service.disable_2fa(current_user["id"])
    return {"success": True, "message": "2FA disabled"}
```

### 1.4 Update Auth Routes for 2FA Login

**Update:** `backend/app/routes/auth.py`

Add after imports:
```python
from app.services.two_factor import two_factor_service
```

Modify login endpoint to check for 2FA:
```python
@router.post("/login")
async def login(credentials: LoginRequest):
    """Login with email and password"""
    user = db.users.find_by_email(credentials.email)
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Check if 2FA is enabled
    if two_factor_service.is_2fa_enabled(user["id"]):
        return {
            "requires_2fa": True,
            "email": user["email"],
            "message": "Please enter your 2FA code"
        }
    
    # No 2FA, proceed with login
    token = create_access_token(user)
    db.users.update(user["id"], {"last_login": datetime.utcnow().isoformat()})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": sanitize_user(user)
    }


@router.post("/verify-2fa")
async def verify_2fa_login(email: str, code: str):
    """Verify 2FA code during login"""
    user = db.users.find_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not two_factor_service.verify_login(user["id"], code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    
    token = create_access_token(user)
    db.users.update(user["id"], {"last_login": datetime.utcnow().isoformat()})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": sanitize_user(user)
    }
```

### 1.5 Register 2FA Routes

**Update:** `backend/app/main.py`

```python
from app.routes import two_factor

app.include_router(two_factor.router, prefix="/api/v1/2fa", tags=["Two-Factor Auth"])
```

### 1.6 Add 2FA API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Two-Factor Auth API
export const twoFactorAPI = {
  getStatus: () => api.get('/api/v1/2fa/status'),
  setup: () => api.post('/api/v1/2fa/setup'),
  verifySetup: (code) => api.post('/api/v1/2fa/verify-setup', { code }),
  disable: (code) => api.post('/api/v1/2fa/disable', { code }),
  verifyLogin: (email, code) => api.post('/api/v1/auth/verify-2fa', null, { 
    params: { email, code } 
  })
};
```

### 1.7 Create TwoFactorSetup Component

**File:** `frontend/src/components/TwoFactorSetup.jsx`

```jsx
import { useState } from 'react';
import { twoFactorAPI } from '../services/api';

export default function TwoFactorSetup({ onComplete, onCancel }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [error, setError] = useState('');

  const handleSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await twoFactorAPI.setup();
      setSetupData(res.data);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      await twoFactorAPI.verifySetup(verifyCode);
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="two-factor-setup">
      {/* Step 1: Introduction */}
      {step === 1 && (
        <div className="setup-step">
          <div className="step-icon">🔐</div>
          <h3>Enable Two-Factor Authentication</h3>
          <p className="text-muted">
            Add an extra layer of security to your account using an 
            authenticator app like Google Authenticator or Authy.
          </p>
          <div className="flex gap-3 mt-6">
            <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSetup} disabled={loading}>
              {loading ? 'Setting up...' : 'Begin Setup'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: QR Code */}
      {step === 2 && setupData && (
        <div className="setup-step">
          <h3>Scan QR Code</h3>
          <p className="text-muted mb-4">Scan this QR code with your authenticator app:</p>
          <div className="qr-container">
            <img src={setupData.qr_code} alt="2FA QR Code" />
          </div>
          <div className="manual-entry mt-4">
            <p className="text-sm text-muted">Can't scan? Enter this code manually:</p>
            <code className="secret-code">{setupData.secret}</code>
          </div>
          <button className="btn btn-primary mt-4" onClick={() => setStep(3)}>Continue</button>
        </div>
      )}

      {/* Step 3: Verify */}
      {step === 3 && (
        <div className="setup-step">
          <h3>Verify Setup</h3>
          <p className="text-muted mb-4">Enter the 6-digit code from your authenticator app:</p>
          {error && <div className="error-message mb-4">{error}</div>}
          <input
            type="text"
            className="form-input verify-input"
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            maxLength={6}
            autoFocus
          />
          <div className="flex gap-3 mt-6">
            <button className="btn btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button 
              className="btn btn-primary" 
              onClick={handleVerify} 
              disabled={loading || verifyCode.length !== 6}
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Backup Codes */}
      {step === 4 && setupData && (
        <div className="setup-step">
          <div className="step-icon success">✅</div>
          <h3>2FA Enabled Successfully!</h3>
          <p className="text-muted mb-4">
            Save these backup codes in a secure place. Each can only be used once.
          </p>
          <div className="backup-codes">
            {setupData.backup_codes.map((code, i) => (
              <code key={i} className="backup-code">{code}</code>
            ))}
          </div>
          <div className="warning-box mt-4">
            ⚠️ These codes will not be shown again!
          </div>
          <button className="btn btn-primary mt-6" onClick={onComplete}>Done</button>
        </div>
      )}
    </div>
  );
}
```

### 1.8 Create TwoFactorVerify Component (for Login)

**File:** `frontend/src/components/TwoFactorVerify.jsx`

```jsx
import { useState } from 'react';
import { twoFactorAPI } from '../services/api';

export default function TwoFactorVerify({ email, onSuccess, onCancel }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await twoFactorAPI.verifyLogin(email, code);
      onSuccess(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && code.length === 6) {
      handleVerify();
    }
  };

  return (
    <div className="two-factor-verify">
      <div className="verify-icon">🔐</div>
      <h3>Two-Factor Authentication</h3>
      <p className="text-muted mb-4">Enter the 6-digit code from your authenticator app</p>
      
      {error && <div className="error-message mb-4">{error}</div>}
      
      <input
        type="text"
        className="form-input verify-input"
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
        onKeyPress={handleKeyPress}
        placeholder="000000"
        maxLength={6}
        autoFocus
      />
      
      <p className="text-sm text-muted mt-2">Or use a backup code</p>
      
      <div className="flex gap-3 mt-6">
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button 
          className="btn btn-primary" 
          onClick={handleVerify}
          disabled={loading || code.length < 6}
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </div>
    </div>
  );
}
```

### 1.9 Add 2FA Styles

**Add to:** `frontend/src/index.css`

```css
/* Two-Factor Authentication */
.two-factor-setup,
.two-factor-verify {
  text-align: center;
  padding: 20px;
}

.step-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.step-icon.success {
  color: var(--success);
}

.qr-container {
  display: inline-block;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: var(--shadow-md);
}

.qr-container img {
  width: 200px;
  height: 200px;
}

.secret-code {
  display: block;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  font-family: monospace;
  font-size: 1rem;
  letter-spacing: 2px;
  user-select: all;
}

.verify-input {
  max-width: 200px;
  margin: 0 auto;
  text-align: center;
  font-size: 1.5rem;
  letter-spacing: 8px;
  font-family: monospace;
}

.backup-codes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  max-width: 300px;
  margin: 0 auto;
}

.backup-code {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.9rem;
}

.warning-box {
  padding: 12px 16px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  color: #92400e;
  font-size: 0.9rem;
}

[data-theme="dark"] .warning-box {
  background: #422006;
  border-color: #d97706;
  color: #fbbf24;
}

.verify-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}
```

---

## TASK 2: GLOBAL SEARCH / COMMAND PALETTE

### 2.1 Create Shortcuts Data

**File:** `frontend/src/data/shortcuts.js`

```javascript
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
  // Navigation
  { id: 'nav-dashboard', label: 'Go to Dashboard', category: 'Navigation', path: '/dashboard', icon: '📊' },
  { id: 'nav-inventory', label: 'Go to Inventory', category: 'Navigation', path: '/inventory', icon: '📦' },
  { id: 'nav-projects', label: 'Go to Projects', category: 'Navigation', path: '/projects', icon: '📁' },
  { id: 'nav-transactions', label: 'Go to Transactions', category: 'Navigation', path: '/transactions', icon: '💰' },
  { id: 'nav-payments', label: 'Go to Payments', category: 'Navigation', path: '/payments', icon: '💳' },
  { id: 'nav-reports', label: 'Go to Reports', category: 'Navigation', path: '/reports', icon: '📈' },
  { id: 'nav-settings', label: 'Go to Settings', category: 'Navigation', path: '/settings', icon: '⚙️' },
  { id: 'nav-ai', label: 'Go to AI Dashboard', category: 'Navigation', path: '/ai-dashboard', icon: '🤖' },
  
  // Actions
  { id: 'new-material', label: 'New Material', category: 'Create', action: 'create', entity: 'material', icon: '➕' },
  { id: 'new-transaction', label: 'New Transaction', category: 'Create', action: 'create', entity: 'transaction', icon: '➕' },
  { id: 'new-payment', label: 'New Payment', category: 'Create', action: 'create', entity: 'payment', icon: '➕' },
  { id: 'new-project', label: 'New Project', category: 'Create', action: 'create', entity: 'project', icon: '➕' },
  
  // Theme
  { id: 'theme-light', label: 'Light Theme', category: 'Theme', action: 'theme', value: 'light', icon: '☀️' },
  { id: 'theme-dark', label: 'Dark Theme', category: 'Theme', action: 'theme', value: 'dark', icon: '🌙' },
  
  // Help
  { id: 'shortcuts', label: 'Keyboard Shortcuts', category: 'Help', action: 'showShortcuts', icon: '⌨️' },
  { id: 'help', label: 'Help Center', category: 'Help', path: '/help', icon: '❓' }
];
```

### 2.2 Create useKeyboardShortcuts Hook

**File:** `frontend/src/hooks/useKeyboardShortcuts.js`

```javascript
import { useEffect, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function useKeyboardShortcuts({ onCommandPalette, onShowShortcuts, onCloseModal }) {
  const navigate = useNavigate();
  const [pendingKey, setPendingKey] = useState(null);

  const handleKeyDown = useCallback((e) => {
    // Ignore if typing in input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
      if (e.key === 'Escape') e.target.blur();
      return;
    }

    const ctrl = e.ctrlKey || e.metaKey;
    const key = e.key.toLowerCase();

    // Ctrl + K: Command Palette
    if (ctrl && key === 'k') {
      e.preventDefault();
      onCommandPalette?.();
      return;
    }

    // Ctrl + /: Show Shortcuts
    if (ctrl && key === '/') {
      e.preventDefault();
      onShowShortcuts?.();
      return;
    }

    // Escape: Close Modal
    if (key === 'escape') {
      onCloseModal?.();
      return;
    }

    // G + Key navigation
    if (pendingKey === 'g') {
      setPendingKey(null);
      const routes = { d: '/dashboard', i: '/inventory', p: '/projects', t: '/transactions', y: '/payments', r: '/reports', s: '/settings' };
      if (routes[key]) navigate(routes[key]);
      return;
    }

    if (key === 'g') {
      setPendingKey('g');
      setTimeout(() => setPendingKey(null), 1000);
    }
  }, [navigate, pendingKey, onCommandPalette, onShowShortcuts, onCloseModal]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { pendingKey };
}
```

### 2.3 Create Command Palette Component

**File:** `frontend/src/components/CommandPalette.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { COMMAND_ITEMS } from '../data/shortcuts';

export default function CommandPalette({ isOpen, onClose, onShowShortcuts }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const { setTheme } = useTheme();

  const filteredItems = COMMAND_ITEMS.filter(item =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  const groupedItems = filteredItems.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredItems.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      executeItem(filteredItems[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  const executeItem = (item) => {
    if (!item) return;

    if (item.path) {
      navigate(item.path);
    } else if (item.action === 'theme') {
      setTheme(item.value);
    } else if (item.action === 'showShortcuts') {
      onShowShortcuts?.();
    } else if (item.action === 'create') {
      navigate(`/${item.entity}s?action=new`);
    }

    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="command-palette-overlay" onClick={onClose}>
      <div className="command-palette" onClick={e => e.stopPropagation()}>
        <div className="command-input-wrapper">
          <span className="command-icon">🔍</span>
          <input
            ref={inputRef}
            type="text"
            className="command-input"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="command-kbd">ESC</kbd>
        </div>

        <div className="command-results">
          {Object.entries(groupedItems).map(([category, items]) => (
            <div key={category} className="command-group">
              <div className="command-group-title">{category}</div>
              {items.map((item) => {
                const globalIndex = filteredItems.indexOf(item);
                return (
                  <div
                    key={item.id}
                    className={`command-item ${globalIndex === selectedIndex ? 'selected' : ''}`}
                    onClick={() => executeItem(item)}
                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                  >
                    <span className="command-item-icon">{item.icon}</span>
                    <span className="command-item-label">{item.label}</span>
                  </div>
                );
              })}
            </div>
          ))}
          {filteredItems.length === 0 && (
            <div className="command-empty">No results found</div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 2.4 Create ShortcutsHelp Modal

**File:** `frontend/src/components/ShortcutsHelp.jsx`

```jsx
import { SHORTCUTS } from '../data/shortcuts';

export default function ShortcutsHelp({ isOpen, onClose }) {
  if (!isOpen) return null;

  const renderKey = (key) => {
    const symbols = { ctrl: '⌘/Ctrl', shift: '⇧', alt: '⌥/Alt', escape: 'Esc' };
    return symbols[key] || key.toUpperCase();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>⌨️ Keyboard Shortcuts</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="shortcuts-grid">
            {Object.entries(SHORTCUTS).map(([section, shortcuts]) => (
              <div key={section} className="shortcuts-section">
                <h4>{section.charAt(0).toUpperCase() + section.slice(1)}</h4>
                {shortcuts.map((s, i) => (
                  <div key={i} className="shortcut-item">
                    <span className="shortcut-label">{s.label}</span>
                    <span className="shortcut-keys">
                      {s.keys.map((k, j) => (
                        <span key={j}>
                          <kbd>{renderKey(k)}</kbd>
                          {j < s.keys.length - 1 && (s.keys[0] === 'g' ? ' then ' : ' + ')}
                        </span>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 2.5 Add Command Palette Styles

**Add to:** `frontend/src/index.css`

```css
/* Command Palette */
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 9999;
}

.command-palette {
  width: 100%;
  max-width: 600px;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.command-input-wrapper {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.command-icon {
  font-size: 1.25rem;
  margin-right: 12px;
}

.command-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  color: var(--text-primary);
  outline: none;
}

.command-kbd {
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.command-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.command-group-title {
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}

.command-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s;
}

.command-item:hover,
.command-item.selected {
  background: var(--bg-tertiary);
}

.command-item-icon {
  font-size: 1.1rem;
}

.command-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
}

/* Shortcuts Help */
.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.shortcuts-section h4 {
  margin-bottom: 12px;
  color: var(--text-primary);
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}

.shortcut-label {
  color: var(--text-secondary);
}

.shortcut-keys kbd {
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
}
```

### 2.6 Integrate in Layout

**Update:** `frontend/src/components/Layout.jsx`

Add state and components:
```jsx
import { useState } from 'react';
import CommandPalette from './CommandPalette';
import ShortcutsHelp from './ShortcutsHelp';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

// Inside component:
const [showCommandPalette, setShowCommandPalette] = useState(false);
const [showShortcuts, setShowShortcuts] = useState(false);

useKeyboardShortcuts({
  onCommandPalette: () => setShowCommandPalette(true),
  onShowShortcuts: () => setShowShortcuts(true),
  onCloseModal: () => {
    setShowCommandPalette(false);
    setShowShortcuts(false);
  }
});

// In JSX, add before closing div:
<CommandPalette 
  isOpen={showCommandPalette} 
  onClose={() => setShowCommandPalette(false)}
  onShowShortcuts={() => { setShowCommandPalette(false); setShowShortcuts(true); }}
/>
<ShortcutsHelp isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
```

---

## TASK 3: BUILD AND TEST PART 1

```bash
# Backend deps
cd backend
pip install pyotp qrcode[pil]

# Test backend
pytest -v

# Test frontend
cd frontend
npm run dev

# Test:
# 1. Enable 2FA in Settings
# 2. Scan QR with authenticator
# 3. Verify with code
# 4. Press Ctrl+K for command palette
# 5. Press Ctrl+/ for shortcuts
# 6. Use G+D, G+I, etc. for navigation

git add .
git commit -m "feat: Phase 4.1 - Two-Factor Auth and Command Palette"
git push origin main
```

---

## COMPLETION CHECKLIST - PART 1

### Two-Factor Authentication
- [ ] Backend 2FA service
- [ ] 2FA routes (setup, verify, disable)
- [ ] QR code generation
- [ ] Backup codes
- [ ] Login flow with 2FA
- [ ] TwoFactorSetup component
- [ ] TwoFactorVerify component
- [ ] Settings 2FA section

### Command Palette
- [ ] Shortcuts data file
- [ ] useKeyboardShortcuts hook
- [ ] CommandPalette component
- [ ] ShortcutsHelp modal
- [ ] Integration in Layout
- [ ] Ctrl+K works
- [ ] Ctrl+/ works
- [ ] G+key navigation works

---

**Continue to Part 2 for Dashboard Widgets, Report Builder, and Backup/Restore**
