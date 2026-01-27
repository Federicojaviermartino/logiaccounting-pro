"""
Profitability Assistant Service
NLP-powered chatbot for natural language queries about projects and financial data
Uses Claude API for intelligent query understanding and response generation
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

# Optional Anthropic import
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class QueryResult:
    """Result of a natural language query"""
    query: str
    answer: str
    data: Optional[Dict] = None
    charts: Optional[List[Dict]] = None
    suggestions: Optional[List[str]] = None
    confidence: float = 1.0
    query_type: str = "unknown"


class ProfitabilityAssistant:
    """
    Natural Language Processing assistant for financial queries

    Supports questions like:
    - "What projects are over budget?"
    - "Show me the most profitable projects"
    - "Which suppliers have the highest expenses?"
    - "What's our cash flow trend?"
    - "Compare project A vs project B profitability"
    """

    EXAMPLE_QUERIES = [
        "What projects are over budget?",
        "Show me the most profitable projects",
        "Which suppliers have the highest expenses?",
        "What's our monthly revenue trend?",
        "Which projects are at risk?",
        "Compare expenses by category",
        "What payments are due this week?",
        "Show low stock materials"
    ]

    def __init__(self, db):
        self.db = db
        self.client = None

        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.client = anthropic.Anthropic()

    def query(self, user_query: str, user_context: Optional[Dict] = None) -> QueryResult:
        """
        Process a natural language query about projects and profitability

        Args:
            user_query: Natural language question
            user_context: Optional context about the user (role, permissions)

        Returns:
            QueryResult with answer and supporting data
        """
        # Normalize query
        query_lower = user_query.lower().strip()

        # If Claude API available, use NLP for query understanding
        if self.client:
            return self._process_with_claude(user_query, user_context)

        # Fallback to keyword-based query processing
        return self._process_with_keywords(query_lower, user_context)

    def _process_with_claude(self, query: str, user_context: Optional[Dict]) -> QueryResult:
        """
        Process query using Claude API for natural language understanding
        """
        # Gather current data context
        data_context = self._get_data_summary()

        system_prompt = """You are a financial assistant for LogiAccounting Pro.
You help users understand their project profitability, expenses, and cash flow.

You have access to the following data summary:
{data_context}

When answering:
1. Be concise and specific
2. Include relevant numbers and percentages
3. Suggest follow-up actions when appropriate
4. If you can't answer with the available data, explain what's missing

Respond in JSON format with this structure:
{{
    "answer": "Your natural language response",
    "query_type": "projects|expenses|revenue|payments|inventory|comparison|trend",
    "key_metrics": {{"metric_name": value}},
    "suggestions": ["Follow-up suggestion 1", "Follow-up suggestion 2"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=system_prompt.format(data_context=json.dumps(data_context, indent=2)),
                messages=[
                    {"role": "user", "content": query}
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Try to extract JSON from response
            try:
                # Handle potential markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                result_data = json.loads(response_text)

                return QueryResult(
                    query=query,
                    answer=result_data.get("answer", response_text),
                    data=result_data.get("key_metrics"),
                    suggestions=result_data.get("suggestions", []),
                    confidence=result_data.get("confidence", 0.9),
                    query_type=result_data.get("query_type", "general")
                )
            except json.JSONDecodeError:
                # Return raw text if not valid JSON
                return QueryResult(
                    query=query,
                    answer=response_text,
                    confidence=0.8,
                    query_type="general"
                )

        except Exception as e:
            # Fallback to keyword processing on error
            return self._process_with_keywords(query.lower(), user_context)

    def _process_with_keywords(self, query: str, user_context: Optional[Dict]) -> QueryResult:
        """
        Process query using keyword matching (fallback when Claude API unavailable)
        """
        # Detect query type and extract relevant data
        if any(word in query for word in ["over budget", "budget", "overspend"]):
            return self._query_over_budget_projects()

        elif any(word in query for word in ["profitable", "profit", "margin"]):
            return self._query_profitable_projects()

        elif any(word in query for word in ["supplier", "vendor", "expense by"]):
            return self._query_expenses_by_supplier()

        elif any(word in query for word in ["trend", "monthly", "revenue"]):
            return self._query_revenue_trend()

        elif any(word in query for word in ["risk", "at risk", "problem"]):
            return self._query_at_risk_projects()

        elif any(word in query for word in ["category", "expense category", "spending"]):
            return self._query_expenses_by_category()

        elif any(word in query for word in ["due", "payment", "upcoming"]):
            return self._query_upcoming_payments()

        elif any(word in query for word in ["stock", "inventory", "low"]):
            return self._query_low_stock()

        elif any(word in query for word in ["compare", "vs", "versus"]):
            return self._query_project_comparison(query)

        else:
            return self._query_general_summary()

    def _get_data_summary(self) -> Dict:
        """
        Get summary of all data for Claude context
        """
        projects = self.db.projects.find_all()
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()
        materials = self.db.materials.find_all()

        # Calculate project stats
        project_stats = []
        for project in projects:
            project_expenses = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "expense"
            )
            project_income = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "income"
            )

            budget = project.get("budget", 0)
            budget_used = (project_expenses / budget * 100) if budget > 0 else 0

            project_stats.append({
                "name": project.get("name"),
                "code": project.get("code"),
                "status": project.get("status"),
                "budget": budget,
                "expenses": project_expenses,
                "income": project_income,
                "profit": project_income - project_expenses,
                "budget_used_percent": round(budget_used, 1)
            })

        # Calculate totals
        total_income = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
        total_expenses = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")

        # Pending payments
        pending_payable = sum(p.get("amount", 0) for p in payments
                            if p.get("type") == "payable" and p.get("status") in ["pending", "overdue"])
        pending_receivable = sum(p.get("amount", 0) for p in payments
                                if p.get("type") == "receivable" and p.get("status") in ["pending", "overdue"])

        # Low stock items
        low_stock = [m for m in materials if m.get("quantity", 0) <= m.get("min_stock", 0)]

        return {
            "projects": project_stats,
            "totals": {
                "income": total_income,
                "expenses": total_expenses,
                "net_profit": total_income - total_expenses,
                "profit_margin": round((total_income - total_expenses) / total_income * 100, 1) if total_income > 0 else 0
            },
            "payments": {
                "pending_payable": pending_payable,
                "pending_receivable": pending_receivable,
                "overdue_count": len([p for p in payments if p.get("status") == "overdue"])
            },
            "inventory": {
                "total_items": len(materials),
                "low_stock_count": len(low_stock)
            }
        }

    def _query_over_budget_projects(self) -> QueryResult:
        """
        Find projects that are over budget
        """
        projects = self.db.projects.find_all()
        transactions = self.db.transactions.find_all()

        over_budget = []
        for project in projects:
            budget = project.get("budget", 0)
            if budget <= 0:
                continue

            expenses = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "expense"
            )

            if expenses > budget:
                over_budget.append({
                    "code": project.get("code"),
                    "name": project.get("name"),
                    "budget": budget,
                    "actual": expenses,
                    "over_by": expenses - budget,
                    "over_percent": round((expenses - budget) / budget * 100, 1)
                })

        over_budget.sort(key=lambda x: x["over_percent"], reverse=True)

        if over_budget:
            answer = f"Found {len(over_budget)} project(s) over budget:\n"
            for p in over_budget[:5]:
                answer += f"- {p['code']}: ${p['over_by']:,.2f} over ({p['over_percent']}%)\n"
        else:
            answer = "Good news! No projects are currently over budget."

        return QueryResult(
            query="over budget projects",
            answer=answer,
            data={"over_budget_projects": over_budget},
            query_type="projects",
            suggestions=["Review expense allocation", "Check for pending invoices"]
        )

    def _query_profitable_projects(self) -> QueryResult:
        """
        Find most profitable projects
        """
        projects = self.db.projects.find_all()
        transactions = self.db.transactions.find_all()

        profitability = []
        for project in projects:
            income = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "income"
            )
            expenses = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "expense"
            )

            profit = income - expenses
            margin = (profit / income * 100) if income > 0 else 0

            profitability.append({
                "code": project.get("code"),
                "name": project.get("name"),
                "income": income,
                "expenses": expenses,
                "profit": profit,
                "margin": round(margin, 1)
            })

        profitability.sort(key=lambda x: x["profit"], reverse=True)

        answer = "Most profitable projects:\n"
        for p in profitability[:5]:
            answer += f"- {p['code']}: ${p['profit']:,.2f} profit ({p['margin']}% margin)\n"

        return QueryResult(
            query="profitable projects",
            answer=answer,
            data={"project_profitability": profitability[:10]},
            query_type="projects",
            suggestions=["Analyze successful project patterns", "Scale profitable approaches"]
        )

    def _query_expenses_by_supplier(self) -> QueryResult:
        """
        Analyze expenses by supplier/vendor
        """
        transactions = self.db.transactions.find_all()
        users = self.db.users.find_all()

        supplier_expenses = {}
        for tx in transactions:
            if tx.get("type") == "expense":
                supplier_id = tx.get("supplier_id")
                if supplier_id:
                    if supplier_id not in supplier_expenses:
                        supplier = next((u for u in users if u["id"] == supplier_id), None)
                        supplier_expenses[supplier_id] = {
                            "name": supplier.get("company_name") if supplier else "Unknown",
                            "total": 0,
                            "count": 0
                        }
                    supplier_expenses[supplier_id]["total"] += tx.get("amount", 0)
                    supplier_expenses[supplier_id]["count"] += 1

        results = sorted(supplier_expenses.values(), key=lambda x: x["total"], reverse=True)

        if results:
            answer = "Top suppliers by expense:\n"
            for s in results[:5]:
                answer += f"- {s['name']}: ${s['total']:,.2f} ({s['count']} transactions)\n"
        else:
            answer = "No supplier expense data available."

        return QueryResult(
            query="expenses by supplier",
            answer=answer,
            data={"supplier_expenses": results[:10]},
            query_type="expenses",
            suggestions=["Negotiate bulk discounts", "Review supplier contracts"]
        )

    def _query_revenue_trend(self) -> QueryResult:
        """
        Analyze monthly revenue trend
        """
        transactions = self.db.transactions.find_all()

        monthly = {}
        for tx in transactions:
            date_str = tx.get("date") or tx.get("created_at", "")[:10]
            if not date_str:
                continue

            month = date_str[:7]  # YYYY-MM
            if month not in monthly:
                monthly[month] = {"income": 0, "expenses": 0}

            amount = tx.get("amount", 0)
            if tx.get("type") == "income":
                monthly[month]["income"] += amount
            else:
                monthly[month]["expenses"] += amount

        # Sort by month
        trend = [{"month": k, **v, "net": v["income"] - v["expenses"]}
                for k, v in sorted(monthly.items())]

        if trend:
            answer = "Monthly financial trend:\n"
            for m in trend[-6:]:  # Last 6 months
                answer += f"- {m['month']}: Income ${m['income']:,.0f}, Expenses ${m['expenses']:,.0f}, Net ${m['net']:,.0f}\n"
        else:
            answer = "Insufficient data for trend analysis."

        return QueryResult(
            query="revenue trend",
            answer=answer,
            data={"monthly_trend": trend},
            query_type="trend",
            suggestions=["Compare with previous year", "Identify seasonal patterns"]
        )

    def _query_at_risk_projects(self) -> QueryResult:
        """
        Identify projects at risk
        """
        projects = self.db.projects.find_all()
        transactions = self.db.transactions.find_all()

        at_risk = []
        for project in projects:
            if project.get("status") != "active":
                continue

            budget = project.get("budget", 0)
            expenses = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "expense"
            )

            risks = []

            # Budget risk
            if budget > 0:
                budget_used = expenses / budget * 100
                if budget_used > 90:
                    risks.append(f"Budget {budget_used:.0f}% used")
                elif budget_used > 75:
                    risks.append(f"Budget {budget_used:.0f}% used (approaching limit)")

            # Timeline risk (if end date is near)
            end_date = project.get("end_date")
            if end_date:
                try:
                    end = datetime.fromisoformat(end_date)
                    days_left = (end - datetime.utcnow()).days
                    if days_left < 0:
                        risks.append(f"Overdue by {abs(days_left)} days")
                    elif days_left < 14:
                        risks.append(f"Only {days_left} days remaining")
                except (ValueError, TypeError):
                    pass

            if risks:
                at_risk.append({
                    "code": project.get("code"),
                    "name": project.get("name"),
                    "risks": risks,
                    "budget_used": round(expenses / budget * 100, 1) if budget > 0 else None
                })

        if at_risk:
            answer = f"Found {len(at_risk)} project(s) at risk:\n"
            for p in at_risk[:5]:
                answer += f"- {p['code']}: {', '.join(p['risks'])}\n"
        else:
            answer = "No projects currently at significant risk."

        return QueryResult(
            query="at risk projects",
            answer=answer,
            data={"at_risk_projects": at_risk},
            query_type="projects",
            suggestions=["Review project timelines", "Reallocate resources if needed"]
        )

    def _query_expenses_by_category(self) -> QueryResult:
        """
        Analyze expenses by category
        """
        transactions = self.db.transactions.find_all()
        categories = self.db.categories.find_all()

        category_map = {c["id"]: c["name"] for c in categories}
        category_expenses = {}

        for tx in transactions:
            if tx.get("type") == "expense":
                cat_id = tx.get("category_id")
                cat_name = category_map.get(cat_id, "Uncategorized")

                if cat_name not in category_expenses:
                    category_expenses[cat_name] = 0
                category_expenses[cat_name] += tx.get("amount", 0)

        results = [{"category": k, "amount": v}
                  for k, v in sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)]

        total = sum(r["amount"] for r in results)

        answer = "Expenses by category:\n"
        for r in results[:7]:
            pct = (r["amount"] / total * 100) if total > 0 else 0
            answer += f"- {r['category']}: ${r['amount']:,.2f} ({pct:.1f}%)\n"

        return QueryResult(
            query="expenses by category",
            answer=answer,
            data={"category_expenses": results},
            query_type="expenses",
            suggestions=["Identify cost reduction opportunities", "Compare with budget allocations"]
        )

    def _query_upcoming_payments(self) -> QueryResult:
        """
        Show upcoming payment obligations
        """
        payments = self.db.payments.find_all()
        today = datetime.utcnow().date()
        week_end = today + timedelta(days=7)

        upcoming = []
        for p in payments:
            if p.get("status") not in ["pending", "overdue"]:
                continue

            due_date_str = p.get("due_date", "")[:10]
            try:
                due_date = datetime.fromisoformat(due_date_str).date()
                days_until = (due_date - today).days

                if days_until <= 7:
                    upcoming.append({
                        "reference": p.get("reference"),
                        "amount": p.get("amount"),
                        "type": p.get("type"),
                        "due_date": due_date_str,
                        "days_until": days_until,
                        "status": "overdue" if days_until < 0 else "due_soon"
                    })
            except (ValueError, TypeError):
                pass

        upcoming.sort(key=lambda x: x["days_until"])

        if upcoming:
            answer = f"Payments due this week ({len(upcoming)}):\n"
            for p in upcoming[:10]:
                status = "OVERDUE" if p["days_until"] < 0 else f"in {p['days_until']} days"
                answer += f"- {p['reference'] or 'N/A'}: ${p['amount']:,.2f} ({status})\n"
        else:
            answer = "No payments due in the next 7 days."

        return QueryResult(
            query="upcoming payments",
            answer=answer,
            data={"upcoming_payments": upcoming},
            query_type="payments",
            suggestions=["Schedule payments to avoid late fees", "Check available cash"]
        )

    def _query_low_stock(self) -> QueryResult:
        """
        Show low stock materials
        """
        materials = self.db.materials.find_all({"low_stock": True})

        if materials:
            answer = f"Low stock alert ({len(materials)} items):\n"
            for m in materials[:10]:
                answer += f"- {m['name']}: {m['quantity']} {m.get('unit', 'units')} (min: {m.get('min_stock', 0)})\n"
        else:
            answer = "All materials are above minimum stock levels."

        return QueryResult(
            query="low stock",
            answer=answer,
            data={"low_stock_items": materials},
            query_type="inventory",
            suggestions=["Create purchase orders", "Review reorder points"]
        )

    def _query_project_comparison(self, query: str) -> QueryResult:
        """
        Compare two projects
        """
        projects = self.db.projects.find_all()
        transactions = self.db.transactions.find_all()

        # Try to extract project codes from query
        comparison_data = []
        for project in projects[:2]:  # Compare first 2 projects for demo
            income = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "income"
            )
            expenses = sum(
                t.get("amount", 0) for t in transactions
                if t.get("project_id") == project["id"] and t.get("type") == "expense"
            )

            comparison_data.append({
                "code": project.get("code"),
                "name": project.get("name"),
                "budget": project.get("budget", 0),
                "income": income,
                "expenses": expenses,
                "profit": income - expenses,
                "margin": round((income - expenses) / income * 100, 1) if income > 0 else 0
            })

        if len(comparison_data) >= 2:
            p1, p2 = comparison_data[0], comparison_data[1]
            answer = f"Comparison: {p1['code']} vs {p2['code']}\n"
            answer += f"Budget: ${p1['budget']:,.0f} vs ${p2['budget']:,.0f}\n"
            answer += f"Profit: ${p1['profit']:,.0f} vs ${p2['profit']:,.0f}\n"
            answer += f"Margin: {p1['margin']}% vs {p2['margin']}%"
        else:
            answer = "Need at least 2 projects to compare."

        return QueryResult(
            query="project comparison",
            answer=answer,
            data={"comparison": comparison_data},
            query_type="comparison",
            suggestions=["Analyze differences in approach", "Apply successful patterns"]
        )

    def _query_general_summary(self) -> QueryResult:
        """
        General financial summary
        """
        data = self._get_data_summary()

        answer = f"""Financial Summary:
- Total Income: ${data['totals']['income']:,.2f}
- Total Expenses: ${data['totals']['expenses']:,.2f}
- Net Profit: ${data['totals']['net_profit']:,.2f}
- Profit Margin: {data['totals']['profit_margin']}%
- Active Projects: {len([p for p in data['projects'] if p['status'] == 'active'])}
- Pending Payables: ${data['payments']['pending_payable']:,.2f}
- Pending Receivables: ${data['payments']['pending_receivable']:,.2f}"""

        return QueryResult(
            query="general summary",
            answer=answer,
            data=data,
            query_type="general",
            suggestions=self.EXAMPLE_QUERIES[:4]
        )


# Service instance factory
def create_profitability_assistant(db) -> ProfitabilityAssistant:
    return ProfitabilityAssistant(db)
