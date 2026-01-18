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

        start = now.replace(day=1, hour=0, minute=0, second=0)
        return start, now

    def process_query(self, user_id: str, message: str, language: str = "en") -> dict:
        """Process a user query and return response"""
        intent, confidence = self.detect_intent(message)
        start_date, end_date = self.extract_time_period(message)

        if user_id not in self._conversations:
            self._conversations[user_id] = []

        self._conversations[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

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

        client_revenue = {}
        for project in projects:
            client = project.get("client", "Unknown")
            project_txns = [t for t in transactions if t.get("project_id") == project.get("id") and t.get("type") == "income"]
            revenue = sum(t.get("amount", 0) for t in project_txns)
            client_revenue[client] = client_revenue.get(client, 0) + revenue

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
