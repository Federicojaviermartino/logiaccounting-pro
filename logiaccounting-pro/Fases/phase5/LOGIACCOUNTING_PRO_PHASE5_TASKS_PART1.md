# LogiAccounting Pro - Phase 5 Tasks (Part 1/3)

## AI ASSISTANT + APPROVAL WORKFLOWS + RECURRING TRANSACTIONS

---

## TASK 1: AI CHAT ASSISTANT 🤖

### 1.1 Create AI Assistant Service

**File:** `backend/app/services/ai_assistant.py`

```python
"""
AI Chat Assistant Service
Natural language processing for queries and commands
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models.store import db


class AIAssistantService:
    """Handles natural language queries and commands"""
    
    _instance = None
    _conversations: Dict[str, List[dict]] = {}
    
    # Intent patterns (English & Spanish)
    INTENTS = {
        "query_sales": [
            r"(how much|cuánto|cuanto).*(sold|sold|vendimos|ventas|revenue|ingresos)",
            r"(total|show).*(sales|ventas|revenue)",
            r"(ventas|sales).*(mes|month|week|semana|today|hoy)"
        ],
        "query_expenses": [
            r"(how much|cuánto|cuanto).*(spent|gastamos|gastos|expenses)",
            r"(total|show).*(expenses|gastos)",
            r"(gastos|expenses).*(mes|month|week|semana)"
        ],
        "query_payments": [
            r"(overdue|vencidos|pending|pendientes).*(payments|pagos)",
            r"(payments|pagos).*(due|vencen|pending)",
            r"(show|mostrar).*(payments|pagos)"
        ],
        "query_inventory": [
            r"(low stock|bajo stock|stock bajo|inventory|inventario)",
            r"(materials|materiales).*(stock|cantidad)",
            r"(show|mostrar).*(inventory|inventario|materials)"
        ],
        "query_projects": [
            r"(project|proyecto).*(status|estado|progress)",
            r"(show|mostrar).*(projects|proyectos)",
            r"(active|activos).*(projects|proyectos)"
        ],
        "query_clients": [
            r"(top|mejores).*(clients|clientes)",
            r"(who|quién|cuales).*(clients|clientes)",
            r"(best|mejor).*(client|cliente)"
        ],
        "create_transaction": [
            r"(create|crear|add|agregar).*(transaction|transacción|transaccion)",
            r"(register|registrar).*(expense|gasto|income|ingreso)"
        ],
        "help": [
            r"(help|ayuda|what can you|qué puedes|que puedes)",
            r"(how to|cómo|como).*(use|usar)"
        ],
        "greeting": [
            r"^(hi|hello|hola|hey|buenos días|buenas).*$",
            r"^(good morning|good afternoon|buenas tardes).*$"
        ]
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._conversations = {}
        return cls._instance
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """Detect user intent from message"""
        message_lower = message.lower().strip()
        
        for intent, patterns in self.INTENTS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent, 0.9
        
        return "unknown", 0.3
    
    def extract_time_period(self, message: str) -> Tuple[datetime, datetime]:
        """Extract time period from message"""
        message_lower = message.lower()
        now = datetime.utcnow()
        
        if any(w in message_lower for w in ["today", "hoy"]):
            start = now.replace(hour=0, minute=0, second=0)
            return start, now
        
        if any(w in message_lower for w in ["this week", "esta semana", "week", "semana"]):
            start = now - timedelta(days=now.weekday())
            return start.replace(hour=0, minute=0, second=0), now
        
        if any(w in message_lower for w in ["this month", "este mes", "month", "mes"]):
            start = now.replace(day=1, hour=0, minute=0, second=0)
            return start, now
        
        if any(w in message_lower for w in ["this year", "este año", "year", "año"]):
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            return start, now
        
        if any(w in message_lower for w in ["last month", "mes pasado"]):
            first_this_month = now.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0)
            return last_month_start, last_month_end
        
        # Default: this month
        start = now.replace(day=1, hour=0, minute=0, second=0)
        return start, now
    
    def process_query(self, user_id: str, message: str, language: str = "en") -> dict:
        """Process a user query and return response"""
        intent, confidence = self.detect_intent(message)
        start_date, end_date = self.extract_time_period(message)
        
        # Store in conversation history
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        self._conversations[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Generate response based on intent
        response = self._generate_response(intent, start_date, end_date, language, message)
        
        self._conversations[user_id].append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "intent": intent,
            "confidence": confidence,
            "message": response["message"],
            "data": response.get("data"),
            "suggestions": response.get("suggestions", [])
        }
    
    def _generate_response(
        self, 
        intent: str, 
        start_date: datetime, 
        end_date: datetime, 
        language: str,
        original_message: str
    ) -> dict:
        """Generate response based on detected intent"""
        
        is_spanish = language == "es" or any(w in original_message.lower() for w in ["cuánto", "mostrar", "ventas", "gastos"])
        
        if intent == "greeting":
            return {
                "message": "¡Hola! Soy tu asistente de LogiAccounting. ¿En qué puedo ayudarte?" if is_spanish 
                          else "Hello! I'm your LogiAccounting assistant. How can I help you?",
                "suggestions": [
                    "Show sales this month" if not is_spanish else "Mostrar ventas del mes",
                    "Overdue payments" if not is_spanish else "Pagos vencidos",
                    "Low stock items" if not is_spanish else "Materiales con bajo stock"
                ]
            }
        
        if intent == "help":
            return {
                "message": self._get_help_message(is_spanish),
                "suggestions": []
            }
        
        if intent == "query_sales":
            return self._query_sales(start_date, end_date, is_spanish)
        
        if intent == "query_expenses":
            return self._query_expenses(start_date, end_date, is_spanish)
        
        if intent == "query_payments":
            return self._query_payments(is_spanish)
        
        if intent == "query_inventory":
            return self._query_inventory(is_spanish)
        
        if intent == "query_projects":
            return self._query_projects(is_spanish)
        
        if intent == "query_clients":
            return self._query_top_clients(is_spanish)
        
        if intent == "create_transaction":
            return {
                "message": "Para crear una transacción, ve a Transacciones → Nueva Transacción" if is_spanish
                          else "To create a transaction, go to Transactions → New Transaction",
                "suggestions": ["Go to Transactions" if not is_spanish else "Ir a Transacciones"]
            }
        
        # Unknown intent
        return {
            "message": "No estoy seguro de entender. ¿Puedes reformular tu pregunta?" if is_spanish
                      else "I'm not sure I understand. Could you rephrase your question?",
            "suggestions": [
                "Sales this month" if not is_spanish else "Ventas del mes",
                "Pending payments" if not is_spanish else "Pagos pendientes",
                "Help" if not is_spanish else "Ayuda"
            ]
        }
    
    def _query_sales(self, start: datetime, end: datetime, spanish: bool) -> dict:
        """Query sales/income transactions"""
        transactions = db.transactions.find_all()
        
        income = [t for t in transactions 
                  if t.get("type") == "income" 
                  and start.isoformat() <= t.get("date", "") <= end.isoformat()]
        
        total = sum(t.get("amount", 0) for t in income)
        count = len(income)
        
        period = f"del {start.strftime('%d/%m')} al {end.strftime('%d/%m')}" if spanish else f"from {start.strftime('%m/%d')} to {end.strftime('%m/%d')}"
        
        return {
            "message": f"{'Ventas' if spanish else 'Sales'} {period}: **${total:,.2f}** ({count} {'transacciones' if spanish else 'transactions'})",
            "data": {"total": total, "count": count, "period": {"start": start.isoformat(), "end": end.isoformat()}},
            "suggestions": ["Compare with last month" if not spanish else "Comparar con mes anterior"]
        }
    
    def _query_expenses(self, start: datetime, end: datetime, spanish: bool) -> dict:
        """Query expense transactions"""
        transactions = db.transactions.find_all()
        
        expenses = [t for t in transactions 
                    if t.get("type") == "expense" 
                    and start.isoformat() <= t.get("date", "") <= end.isoformat()]
        
        total = sum(t.get("amount", 0) for t in expenses)
        count = len(expenses)
        
        period = f"del {start.strftime('%d/%m')} al {end.strftime('%d/%m')}" if spanish else f"from {start.strftime('%m/%d')} to {end.strftime('%m/%d')}"
        
        return {
            "message": f"{'Gastos' if spanish else 'Expenses'} {period}: **${total:,.2f}** ({count} {'transacciones' if spanish else 'transactions'})",
            "data": {"total": total, "count": count},
            "suggestions": ["Show by category" if not spanish else "Mostrar por categoría"]
        }
    
    def _query_payments(self, spanish: bool) -> dict:
        """Query overdue and pending payments"""
        payments = db.payments.find_all()
        today = datetime.utcnow().date().isoformat()
        
        overdue = [p for p in payments if p.get("status") == "pending" and p.get("due_date", "") < today]
        pending = [p for p in payments if p.get("status") == "pending"]
        
        overdue_amount = sum(p.get("amount", 0) for p in overdue)
        pending_amount = sum(p.get("amount", 0) for p in pending)
        
        msg = f"{'Pagos vencidos' if spanish else 'Overdue payments'}: **{len(overdue)}** (${overdue_amount:,.2f})\n"
        msg += f"{'Total pendientes' if spanish else 'Total pending'}: **{len(pending)}** (${pending_amount:,.2f})"
        
        return {
            "message": msg,
            "data": {"overdue_count": len(overdue), "overdue_amount": overdue_amount, "pending_count": len(pending)},
            "suggestions": ["Show overdue list" if not spanish else "Ver lista de vencidos"]
        }
    
    def _query_inventory(self, spanish: bool) -> dict:
        """Query low stock materials"""
        materials = db.materials.find_all()
        
        low_stock = [m for m in materials 
                     if m.get("quantity", 0) <= m.get("min_stock", 0) and m.get("state") == "active"]
        
        if low_stock:
            items = ", ".join([m.get("name", "Unknown")[:20] for m in low_stock[:5]])
            msg = f"{'Materiales con bajo stock' if spanish else 'Low stock materials'}: **{len(low_stock)}**\n"
            msg += f"{'Incluye' if spanish else 'Including'}: {items}"
            if len(low_stock) > 5:
                msg += f" (+{len(low_stock) - 5} {'más' if spanish else 'more'})"
        else:
            msg = "✅ " + ("Todos los materiales tienen stock suficiente" if spanish else "All materials have sufficient stock")
        
        return {
            "message": msg,
            "data": {"low_stock_count": len(low_stock), "items": [m.get("name") for m in low_stock]},
            "suggestions": ["Go to Inventory" if not spanish else "Ir a Inventario"]
        }
    
    def _query_projects(self, spanish: bool) -> dict:
        """Query project status"""
        projects = db.projects.find_all()
        
        by_status = {}
        for p in projects:
            status = p.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        msg = f"{'Proyectos' if spanish else 'Projects'}:\n"
        for status, count in by_status.items():
            emoji = {"active": "🟢", "completed": "✅", "on_hold": "🟡", "cancelled": "🔴"}.get(status, "⚪")
            msg += f"{emoji} {status.title()}: **{count}**\n"
        
        return {
            "message": msg.strip(),
            "data": {"by_status": by_status, "total": len(projects)},
            "suggestions": ["Show active projects" if not spanish else "Ver proyectos activos"]
        }
    
    def _query_top_clients(self, spanish: bool) -> dict:
        """Query top clients by revenue"""
        transactions = db.transactions.find_all()
        projects = db.projects.find_all()
        
        # Group by client from projects
        client_revenue = {}
        for project in projects:
            client = project.get("client", "Unknown")
            # Sum transactions linked to this project
            project_txns = [t for t in transactions if t.get("project_id") == project.get("id") and t.get("type") == "income"]
            revenue = sum(t.get("amount", 0) for t in project_txns)
            client_revenue[client] = client_revenue.get(client, 0) + revenue
        
        # Sort and get top 5
        top_clients = sorted(client_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_clients:
            msg = f"{'Top clientes por ingresos' if spanish else 'Top clients by revenue'}:\n"
            for i, (client, revenue) in enumerate(top_clients, 1):
                msg += f"{i}. **{client}**: ${revenue:,.2f}\n"
        else:
            msg = "No hay datos suficientes de clientes" if spanish else "Not enough client data"
        
        return {
            "message": msg.strip(),
            "data": {"top_clients": [{"name": c, "revenue": r} for c, r in top_clients]},
            "suggestions": ["Show all projects" if not spanish else "Ver todos los proyectos"]
        }
    
    def _get_help_message(self, spanish: bool) -> str:
        """Return help message"""
        if spanish:
            return """Puedo ayudarte con:

📊 **Consultas de datos:**
- "¿Cuánto vendimos este mes?"
- "Mostrar gastos de la semana"
- "Pagos vencidos"
- "Materiales con bajo stock"
- "Estado de proyectos"
- "Top clientes"

💡 **Tips:**
- Puedo entender español e inglés
- Especifica períodos: "hoy", "esta semana", "este mes"
"""
        else:
            return """I can help you with:

📊 **Data queries:**
- "How much did we sell this month?"
- "Show expenses this week"
- "Overdue payments"
- "Low stock materials"
- "Project status"
- "Top clients"

💡 **Tips:**
- I understand both English and Spanish
- Specify time periods: "today", "this week", "this month"
"""
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get conversation history for a user"""
        return self._conversations.get(user_id, [])[-limit:]
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history"""
        if user_id in self._conversations:
            self._conversations[user_id] = []


ai_assistant = AIAssistantService()
```

### 1.2 Create AI Assistant Routes

**File:** `backend/app/routes/assistant.py`

```python
"""
AI Assistant routes
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.ai_assistant import ai_assistant
from app.utils.auth import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    language: str = "en"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to the AI assistant"""
    return ai_assistant.process_query(
        user_id=current_user["id"],
        message=request.message,
        language=request.language
    )


@router.get("/history")
async def get_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history"""
    return {"messages": ai_assistant.get_conversation_history(current_user["id"], limit)}


@router.delete("/history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    """Clear conversation history"""
    ai_assistant.clear_conversation(current_user["id"])
    return {"message": "Conversation cleared"}
```

### 1.3 Register Routes

**Update:** `backend/app/main.py`

```python
from app.routes import assistant

app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["AI Assistant"])
```

### 1.4 Add Assistant API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// AI Assistant API
export const assistantAPI = {
  chat: (message, language = 'en') => api.post('/api/v1/assistant/chat', { message, language }),
  getHistory: (limit = 20) => api.get('/api/v1/assistant/history', { params: { limit } }),
  clearHistory: () => api.delete('/api/v1/assistant/history')
};
```

### 1.5 Create AI Assistant Component

**File:** `frontend/src/components/AIAssistant.jsx`

```jsx
import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { assistantAPI } from '../services/api';

export default function AIAssistant() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await assistantAPI.getHistory();
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await assistantAPI.chat(userMessage, i18n.language);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.message,
        suggestions: res.data.suggestions,
        data: res.data.data
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      await assistantAPI.clearHistory();
      setMessages([]);
    } catch (err) {
      console.error('Failed to clear:', err);
    }
  };

  const renderMessage = (msg, idx) => {
    const isUser = msg.role === 'user';
    
    return (
      <div key={idx} className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-avatar">
          {isUser ? '👤' : '🤖'}
        </div>
        <div className="message-content">
          <div 
            className="message-text"
            dangerouslySetInnerHTML={{ 
              __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>') 
            }}
          />
          {msg.suggestions && msg.suggestions.length > 0 && (
            <div className="message-suggestions">
              {msg.suggestions.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => handleSuggestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Floating Button */}
      <button 
        className={`ai-assistant-fab ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="AI Assistant"
      >
        {isOpen ? '✕' : '🤖'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="ai-assistant-window">
          <div className="ai-assistant-header">
            <div className="ai-assistant-title">
              <span>🤖</span>
              <span>AI Assistant</span>
            </div>
            <button className="ai-clear-btn" onClick={handleClear} title="Clear chat">
              🗑️
            </button>
          </div>

          <div className="ai-assistant-messages">
            {messages.length === 0 && (
              <div className="ai-welcome">
                <div className="ai-welcome-icon">🤖</div>
                <h4>Hi! I'm your AI Assistant</h4>
                <p>Ask me about sales, expenses, payments, inventory, or projects.</p>
                <div className="ai-quick-actions">
                  <button onClick={() => handleSuggestion('Sales this month')}>📊 Sales</button>
                  <button onClick={() => handleSuggestion('Overdue payments')}>💳 Payments</button>
                  <button onClick={() => handleSuggestion('Low stock')}>📦 Inventory</button>
                </div>
              </div>
            )}
            {messages.map(renderMessage)}
            {loading && (
              <div className="chat-message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="ai-assistant-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              disabled={loading}
            />
            <button onClick={handleSend} disabled={!input.trim() || loading}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

### 1.6 Add AI Assistant Styles

**Add to:** `frontend/src/index.css`

```css
/* AI Assistant */
.ai-assistant-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
  z-index: 9998;
}

.ai-assistant-fab:hover {
  transform: scale(1.1);
}

.ai-assistant-fab.open {
  background: var(--text-muted);
}

.ai-assistant-window {
  position: fixed;
  bottom: 96px;
  right: 24px;
  width: 380px;
  height: 500px;
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 9999;
}

.ai-assistant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-assistant-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.ai-clear-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  color: white;
}

.ai-assistant-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.ai-welcome {
  text-align: center;
  padding: 24px;
}

.ai-welcome-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.ai-welcome h4 {
  margin-bottom: 8px;
}

.ai-welcome p {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.ai-quick-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.ai-quick-actions button {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.ai-quick-actions button:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.chat-message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 75%;
}

.message-text {
  padding: 10px 14px;
  border-radius: 16px;
  background: var(--bg-tertiary);
  font-size: 0.9rem;
  line-height: 1.5;
}

.chat-message.user .message-text {
  background: var(--primary);
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.chat-message.assistant .message-text {
  border-radius: 16px 16px 16px 4px;
}

.message-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.suggestion-chip {
  padding: 6px 12px;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-chip:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.ai-assistant-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.ai-assistant-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.ai-assistant-input button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.ai-assistant-input button:hover:not(:disabled) {
  background: var(--primary-dark);
}

.ai-assistant-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .ai-assistant-window {
    width: calc(100% - 32px);
    right: 16px;
    bottom: 80px;
    height: 60vh;
  }
}
```

### 1.7 Add Assistant to Layout

**Update:** `frontend/src/components/Layout.jsx`

Add import and component at the end:
```jsx
import AIAssistant from './AIAssistant';

// At the end of the component, before closing </div>:
<AIAssistant />
```

---

## TASK 2: APPROVAL WORKFLOWS ✅

### 2.1 Create Approval Service

**File:** `backend/app/services/approval_service.py`

```python
"""
Approval Workflow Service
Multi-level approval system for transactions and payments
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models.store import db
from app.utils.activity_logger import activity_logger


class ApprovalService:
    """Manages approval workflows"""
    
    _instance = None
    _approvals: Dict[str, dict] = {}
    _rules: List[dict] = []
    _counter = 0
    
    DEFAULT_RULES = [
        {"min_amount": 1000, "max_amount": 5000, "levels": 1, "approvers": ["manager"]},
        {"min_amount": 5000, "max_amount": 10000, "levels": 2, "approvers": ["manager", "director"]},
        {"min_amount": 10000, "max_amount": None, "levels": 3, "approvers": ["manager", "director", "cfo"]}
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._approvals = {}
            cls._rules = cls.DEFAULT_RULES.copy()
            cls._counter = 0
        return cls._instance
    
    def get_rules(self) -> List[dict]:
        """Get all approval rules"""
        return self._rules
    
    def update_rules(self, rules: List[dict]):
        """Update approval rules"""
        self._rules = rules
    
    def requires_approval(self, amount: float) -> Optional[dict]:
        """Check if amount requires approval and return matching rule"""
        for rule in sorted(self._rules, key=lambda r: r["min_amount"]):
            if amount >= rule["min_amount"]:
                if rule["max_amount"] is None or amount < rule["max_amount"]:
                    return rule
        return None
    
    def create_approval_request(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: dict,
        amount: float,
        requested_by: str,
        requested_by_email: str
    ) -> Optional[dict]:
        """Create an approval request if needed"""
        rule = self.requires_approval(amount)
        if not rule:
            return None
        
        self._counter += 1
        approval_id = f"APR-{self._counter:06d}"
        
        approval = {
            "id": approval_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_data": entity_data,
            "amount": amount,
            "status": "pending",
            "current_level": 1,
            "required_levels": rule["levels"],
            "approver_roles": rule["approvers"],
            "approvals": [],
            "requested_by": requested_by,
            "requested_by_email": requested_by_email,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._approvals[approval_id] = approval
        
        activity_logger.log(
            user_id=requested_by,
            user_email=requested_by_email,
            user_role="user",
            action="CREATE",
            entity_type="approval",
            entity_id=approval_id,
            details={"amount": amount, "entity_type": entity_type}
        )
        
        return approval
    
    def approve(
        self,
        approval_id: str,
        approver_id: str,
        approver_email: str,
        approver_role: str,
        comment: str = ""
    ) -> dict:
        """Approve an approval request"""
        if approval_id not in self._approvals:
            return {"error": "Approval not found"}
        
        approval = self._approvals[approval_id]
        
        if approval["status"] != "pending":
            return {"error": "Approval is not pending"}
        
        # Check if approver has already approved
        if any(a["approver_id"] == approver_id for a in approval["approvals"]):
            return {"error": "Already approved by this user"}
        
        # Add approval
        approval["approvals"].append({
            "approver_id": approver_id,
            "approver_email": approver_email,
            "approver_role": approver_role,
            "action": "approved",
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check if all levels are complete
        if len(approval["approvals"]) >= approval["required_levels"]:
            approval["status"] = "approved"
            approval["completed_at"] = datetime.utcnow().isoformat()
        else:
            approval["current_level"] = len(approval["approvals"]) + 1
        
        approval["updated_at"] = datetime.utcnow().isoformat()
        
        activity_logger.log(
            user_id=approver_id,
            user_email=approver_email,
            user_role=approver_role,
            action="APPROVE",
            entity_type="approval",
            entity_id=approval_id
        )
        
        return approval
    
    def reject(
        self,
        approval_id: str,
        rejector_id: str,
        rejector_email: str,
        rejector_role: str,
        reason: str = ""
    ) -> dict:
        """Reject an approval request"""
        if approval_id not in self._approvals:
            return {"error": "Approval not found"}
        
        approval = self._approvals[approval_id]
        
        if approval["status"] != "pending":
            return {"error": "Approval is not pending"}
        
        approval["status"] = "rejected"
        approval["rejected_by"] = rejector_id
        approval["rejection_reason"] = reason
        approval["completed_at"] = datetime.utcnow().isoformat()
        approval["updated_at"] = datetime.utcnow().isoformat()
        
        approval["approvals"].append({
            "approver_id": rejector_id,
            "approver_email": rejector_email,
            "approver_role": rejector_role,
            "action": "rejected",
            "comment": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        activity_logger.log(
            user_id=rejector_id,
            user_email=rejector_email,
            user_role=rejector_role,
            action="REJECT",
            entity_type="approval",
            entity_id=approval_id
        )
        
        return approval
    
    def get_pending_approvals(self, role: Optional[str] = None) -> List[dict]:
        """Get all pending approvals, optionally filtered by approver role"""
        pending = [a for a in self._approvals.values() if a["status"] == "pending"]
        
        if role:
            filtered = []
            for approval in pending:
                level_idx = approval["current_level"] - 1
                if level_idx < len(approval["approver_roles"]):
                    required_role = approval["approver_roles"][level_idx]
                    if role == required_role or role == "admin":
                        filtered.append(approval)
            return filtered
        
        return pending
    
    def get_approval(self, approval_id: str) -> Optional[dict]:
        """Get a specific approval"""
        return self._approvals.get(approval_id)
    
    def get_all_approvals(self, status: Optional[str] = None) -> List[dict]:
        """Get all approvals"""
        approvals = list(self._approvals.values())
        if status:
            approvals = [a for a in approvals if a["status"] == status]
        return sorted(approvals, key=lambda a: a["created_at"], reverse=True)


approval_service = ApprovalService()
```

### 2.2 Create Approval Routes

**File:** `backend/app/routes/approvals.py`

```python
"""
Approval Workflow routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.approval_service import approval_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class ApprovalActionRequest(BaseModel):
    comment: str = ""


class UpdateRulesRequest(BaseModel):
    rules: List[dict]


@router.get("/rules")
async def get_rules(current_user: dict = Depends(require_roles("admin"))):
    """Get approval rules"""
    return {"rules": approval_service.get_rules()}


@router.put("/rules")
async def update_rules(
    request: UpdateRulesRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update approval rules"""
    approval_service.update_rules(request.rules)
    return {"message": "Rules updated", "rules": approval_service.get_rules()}


@router.get("/pending")
async def get_pending(current_user: dict = Depends(get_current_user)):
    """Get pending approvals for current user"""
    role = current_user.get("role", "user")
    pending = approval_service.get_pending_approvals(role if role != "admin" else None)
    return {"approvals": pending}


@router.get("")
async def get_all(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all approvals"""
    return {"approvals": approval_service.get_all_approvals(status)}


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific approval"""
    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    request: ApprovalActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve a request"""
    result = approval_service.approve(
        approval_id=approval_id,
        approver_id=current_user["id"],
        approver_email=current_user["email"],
        approver_role=current_user.get("role", "user"),
        comment=request.comment
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{approval_id}/reject")
async def reject(
    approval_id: str,
    request: ApprovalActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reject a request"""
    result = approval_service.reject(
        approval_id=approval_id,
        rejector_id=current_user["id"],
        rejector_email=current_user["email"],
        rejector_role=current_user.get("role", "user"),
        reason=request.comment
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
```

### 2.3 Register Approval Routes

**Update:** `backend/app/main.py`

```python
from app.routes import approvals

app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["Approvals"])
```

### 2.4 Add Approvals API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Approvals API
export const approvalsAPI = {
  getRules: () => api.get('/api/v1/approvals/rules'),
  updateRules: (rules) => api.put('/api/v1/approvals/rules', { rules }),
  getPending: () => api.get('/api/v1/approvals/pending'),
  getAll: (status) => api.get('/api/v1/approvals', { params: { status } }),
  get: (id) => api.get(`/api/v1/approvals/${id}`),
  approve: (id, comment = '') => api.post(`/api/v1/approvals/${id}/approve`, { comment }),
  reject: (id, comment = '') => api.post(`/api/v1/approvals/${id}/reject`, { comment })
};
```

### 2.5 Create Approvals Page

**File:** `frontend/src/pages/Approvals.jsx`

```jsx
import { useState, useEffect } from 'react';
import { approvalsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Approvals() {
  const { user } = useAuth();
  const [approvals, setApprovals] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [comment, setComment] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, [filter]);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const res = filter === 'pending' 
        ? await approvalsAPI.getPending()
        : await approvalsAPI.getAll(filter === 'all' ? null : filter);
      setApprovals(res.data.approvals);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approval) => {
    setActionLoading(true);
    try {
      await approvalsAPI.approve(approval.id, comment);
      setComment('');
      setSelectedApproval(null);
      loadApprovals();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (approval) => {
    if (!comment.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    setActionLoading(true);
    try {
      await approvalsAPI.reject(approval.id, comment);
      setComment('');
      setSelectedApproval(null);
      loadApprovals();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reject');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'badge-warning',
      approved: 'badge-success',
      rejected: 'badge-danger'
    };
    return <span className={`badge ${styles[status]}`}>{status}</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        ✅ Review and approve transactions that exceed defined thresholds.
      </div>

      {/* Filters */}
      <div className="section mb-6">
        <div className="flex gap-2">
          {['pending', 'approved', 'rejected', 'all'].map(f => (
            <button
              key={f}
              className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Approvals List */}
      <div className="section">
        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : approvals.length === 0 ? (
          <div className="text-center text-muted">No approvals found</div>
        ) : (
          <div className="approvals-list">
            {approvals.map(approval => (
              <div key={approval.id} className="approval-card">
                <div className="approval-header">
                  <div>
                    <code>{approval.id}</code>
                    {getStatusBadge(approval.status)}
                  </div>
                  <div className="approval-amount">${approval.amount.toLocaleString()}</div>
                </div>
                
                <div className="approval-details">
                  <div><strong>Type:</strong> {approval.entity_type}</div>
                  <div><strong>Requested by:</strong> {approval.requested_by_email}</div>
                  <div><strong>Date:</strong> {new Date(approval.created_at).toLocaleDateString()}</div>
                  <div><strong>Level:</strong> {approval.current_level} of {approval.required_levels}</div>
                </div>

                {approval.entity_data && (
                  <div className="approval-entity-preview">
                    <pre>{JSON.stringify(approval.entity_data, null, 2).substring(0, 200)}...</pre>
                  </div>
                )}

                {/* Approval History */}
                {approval.approvals.length > 0 && (
                  <div className="approval-history">
                    <strong>History:</strong>
                    {approval.approvals.map((a, i) => (
                      <div key={i} className={`history-item ${a.action}`}>
                        {a.action === 'approved' ? '✅' : '❌'} {a.approver_email} ({a.approver_role})
                        {a.comment && <span className="history-comment">- {a.comment}</span>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Actions */}
                {approval.status === 'pending' && (
                  <div className="approval-actions">
                    {selectedApproval?.id === approval.id ? (
                      <div className="action-form">
                        <input
                          type="text"
                          className="form-input"
                          placeholder="Comment (required for rejection)"
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                        />
                        <div className="flex gap-2 mt-2">
                          <button 
                            className="btn btn-success"
                            onClick={() => handleApprove(approval)}
                            disabled={actionLoading}
                          >
                            ✓ Approve
                          </button>
                          <button 
                            className="btn btn-danger"
                            onClick={() => handleReject(approval)}
                            disabled={actionLoading}
                          >
                            ✗ Reject
                          </button>
                          <button 
                            className="btn btn-secondary"
                            onClick={() => { setSelectedApproval(null); setComment(''); }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button 
                        className="btn btn-primary"
                        onClick={() => setSelectedApproval(approval)}
                      >
                        Review
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
```

### 2.6 Add Approval Styles

**Add to:** `frontend/src/index.css`

```css
/* Approvals */
.approvals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.approval-card {
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-bg);
}

.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.approval-header code {
  margin-right: 12px;
}

.approval-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.approval-details {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
  font-size: 0.9rem;
}

.approval-entity-preview {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.approval-entity-preview pre {
  margin: 0;
  font-size: 0.8rem;
  white-space: pre-wrap;
  color: var(--text-muted);
}

.approval-history {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 0.9rem;
}

.history-item {
  margin-top: 8px;
  padding-left: 8px;
}

.history-item.approved {
  border-left: 3px solid #10b981;
}

.history-item.rejected {
  border-left: 3px solid #ef4444;
}

.history-comment {
  color: var(--text-muted);
  font-style: italic;
}

.approval-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.action-form {
  max-width: 500px;
}
```

---

## TASK 3: ADD ROUTES TO APP

### 3.1 Update App.jsx

```jsx
const Approvals = lazy(() => import('./pages/Approvals'));

// Add route:
<Route path="/approvals" element={
  <PrivateRoute roles={['admin']}>
    <Layout><Approvals /></Layout>
  </PrivateRoute>
} />
```

### 3.2 Update Layout Navigation

```javascript
{ path: '/approvals', icon: '✅', label: 'Approvals', roles: ['admin'] },
```

---

## COMPLETION CHECKLIST - PART 1

### AI Assistant
- [ ] Backend service with NLP
- [ ] Intent detection (10+ intents)
- [ ] Time period extraction
- [ ] Chat routes
- [ ] Frontend chat widget
- [ ] Conversation history
- [ ] Suggestions system
- [ ] Multi-language (EN/ES)

### Approval Workflows
- [ ] Approval service
- [ ] Configurable rules
- [ ] Multi-level approvals
- [ ] Approve/Reject actions
- [ ] Approval routes
- [ ] Frontend page
- [ ] History tracking

---

**Continue to Part 2 for Recurring Transactions, Budget Management, and Document Management**
