"""
Intelligent Cash Flow Predictor Service
Predicts cash flow for 30-60-90 days using historical patterns, seasonal trends, and project milestones
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import json

# Optional imports for ML capabilities
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


@dataclass
class CashFlowPrediction:
    """Cash flow prediction data structure"""
    date: str
    predicted_income: float
    predicted_expenses: float
    predicted_net: float
    confidence_lower: float
    confidence_upper: float
    factors: List[str]


@dataclass
class CashFlowForecast:
    """Complete cash flow forecast"""
    generated_at: str
    period_days: int
    current_balance: float
    predictions: List[Dict]
    summary: Dict[str, Any]
    insights: List[str]
    risk_alerts: List[str]
    project_impacts: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


class CashFlowPredictor:
    """
    Intelligent Cash Flow Prediction Engine

    Features:
    - Time series forecasting with Prophet
    - Seasonal trend detection
    - Project milestone impact analysis
    - Payment pattern learning
    - Risk alert generation
    """

    def __init__(self, db):
        self.db = db
        self.prophet_income = None
        self.prophet_expenses = None
        self._model_trained = False

    def predict(self, days: int = 90, include_pending_payments: bool = True) -> CashFlowForecast:
        """
        Generate cash flow predictions for specified number of days

        Args:
            days: Number of days to predict (30, 60, or 90 recommended)
            include_pending_payments: Include known pending payments in prediction

        Returns:
            CashFlowForecast with daily predictions and insights
        """
        if not PANDAS_AVAILABLE:
            return self._simple_prediction(days, include_pending_payments)

        # Get historical data
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()
        projects = self.db.projects.find_all()

        # Prepare data frames
        income_df, expense_df = self._prepare_historical_data(transactions)

        # Use Prophet if available and enough data, otherwise use statistical method
        if PROPHET_AVAILABLE and len(income_df) >= 14:
            predictions = self._prophet_predict(income_df, expense_df, days)
        else:
            predictions = self._statistical_predict(income_df, expense_df, days)

        # Incorporate known pending payments
        if include_pending_payments:
            predictions = self._incorporate_pending_payments(predictions, payments)

        # Add project milestone impacts
        project_impacts = self._analyze_project_impacts(projects, days)

        # Calculate current balance
        current_balance = self._calculate_current_balance(transactions, payments)

        # Generate insights and alerts
        insights = self._generate_insights(predictions, current_balance)
        risk_alerts = self._generate_risk_alerts(predictions, current_balance, payments)

        # Calculate summary
        summary = self._calculate_summary(predictions, current_balance)

        return CashFlowForecast(
            generated_at=datetime.utcnow().isoformat(),
            period_days=days,
            current_balance=current_balance,
            predictions=[p.to_dict() if hasattr(p, 'to_dict') else asdict(p) for p in predictions],
            summary=summary,
            insights=insights,
            risk_alerts=risk_alerts,
            project_impacts=project_impacts
        )

    def _prepare_historical_data(self, transactions: List[Dict]) -> Tuple["pd.DataFrame", "pd.DataFrame"]:
        """
        Prepare historical transaction data for time series analysis
        """
        income_data = []
        expense_data = []

        for tx in transactions:
            date_str = tx.get("date") or tx.get("created_at", "")[:10]
            try:
                date = datetime.fromisoformat(date_str.replace("Z", ""))
            except (ValueError, AttributeError):
                continue

            amount = tx.get("amount", 0)

            if tx.get("type") == "income":
                income_data.append({"ds": date, "y": amount})
            else:
                expense_data.append({"ds": date, "y": amount})

        # Aggregate by day
        income_df = pd.DataFrame(income_data) if income_data else pd.DataFrame(columns=["ds", "y"])
        expense_df = pd.DataFrame(expense_data) if expense_data else pd.DataFrame(columns=["ds", "y"])

        if not income_df.empty:
            income_df = income_df.groupby("ds")["y"].sum().reset_index()

        if not expense_df.empty:
            expense_df = expense_df.groupby("ds")["y"].sum().reset_index()

        return income_df, expense_df

    def _prophet_predict(
        self,
        income_df: "pd.DataFrame",
        expense_df: "pd.DataFrame",
        days: int
    ) -> List[CashFlowPrediction]:
        """
        Use Prophet for time series forecasting
        """
        predictions = []
        today = datetime.utcnow().date()

        # Train income model
        income_forecast = None
        if not income_df.empty and len(income_df) >= 7:
            try:
                model_income = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=False,
                    seasonality_mode='multiplicative'
                )
                model_income.fit(income_df)
                future_income = model_income.make_future_dataframe(periods=days)
                income_forecast = model_income.predict(future_income)
            except Exception:
                income_forecast = None

        # Train expense model
        expense_forecast = None
        if not expense_df.empty and len(expense_df) >= 7:
            try:
                model_expense = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=False,
                    seasonality_mode='multiplicative'
                )
                model_expense.fit(expense_df)
                future_expense = model_expense.make_future_dataframe(periods=days)
                expense_forecast = model_expense.predict(future_expense)
            except Exception:
                expense_forecast = None

        # Generate predictions for each day
        for i in range(days):
            pred_date = today + timedelta(days=i + 1)
            pred_date_str = pred_date.isoformat()

            # Get income prediction
            if income_forecast is not None:
                income_row = income_forecast[income_forecast["ds"].dt.date == pred_date]
                if not income_row.empty:
                    pred_income = max(0, income_row["yhat"].values[0])
                    income_lower = max(0, income_row["yhat_lower"].values[0])
                    income_upper = income_row["yhat_upper"].values[0]
                else:
                    pred_income = income_df["y"].mean() if not income_df.empty else 0
                    income_lower = pred_income * 0.7
                    income_upper = pred_income * 1.3
            else:
                pred_income = income_df["y"].mean() if not income_df.empty else 0
                income_lower = pred_income * 0.7
                income_upper = pred_income * 1.3

            # Get expense prediction
            if expense_forecast is not None:
                expense_row = expense_forecast[expense_forecast["ds"].dt.date == pred_date]
                if not expense_row.empty:
                    pred_expense = max(0, expense_row["yhat"].values[0])
                    expense_lower = max(0, expense_row["yhat_lower"].values[0])
                    expense_upper = expense_row["yhat_upper"].values[0]
                else:
                    pred_expense = expense_df["y"].mean() if not expense_df.empty else 0
                    expense_lower = pred_expense * 0.7
                    expense_upper = pred_expense * 1.3
            else:
                pred_expense = expense_df["y"].mean() if not expense_df.empty else 0
                expense_lower = pred_expense * 0.7
                expense_upper = pred_expense * 1.3

            pred_net = pred_income - pred_expense
            conf_lower = income_lower - expense_upper
            conf_upper = income_upper - expense_lower

            factors = []
            if i < 7:
                factors.append("Short-term (high confidence)")
            elif i < 30:
                factors.append("Medium-term")
            else:
                factors.append("Long-term (lower confidence)")

            # Check for weekly patterns
            if pred_date.weekday() in [5, 6]:
                factors.append("Weekend (typically lower activity)")
            if pred_date.day == 1:
                factors.append("Month start (often high payment activity)")
            if pred_date.day in [15, 30, 31]:
                factors.append("Mid/End month (payment cycles)")

            predictions.append(CashFlowPrediction(
                date=pred_date_str,
                predicted_income=round(pred_income, 2),
                predicted_expenses=round(pred_expense, 2),
                predicted_net=round(pred_net, 2),
                confidence_lower=round(conf_lower, 2),
                confidence_upper=round(conf_upper, 2),
                factors=factors
            ))

        return predictions

    def _statistical_predict(
        self,
        income_df: "pd.DataFrame",
        expense_df: "pd.DataFrame",
        days: int
    ) -> List[CashFlowPrediction]:
        """
        Simple statistical prediction when Prophet is not available
        Uses moving averages and basic seasonality
        """
        predictions = []
        today = datetime.utcnow().date()

        # Calculate averages
        avg_income = income_df["y"].mean() if not income_df.empty else 0
        avg_expense = expense_df["y"].mean() if not expense_df.empty else 0

        std_income = income_df["y"].std() if not income_df.empty and len(income_df) > 1 else avg_income * 0.3
        std_expense = expense_df["y"].std() if not expense_df.empty and len(expense_df) > 1 else avg_expense * 0.3

        # Simple weekly pattern detection
        weekly_income_factor = {0: 1.1, 1: 1.05, 2: 1.0, 3: 1.0, 4: 0.95, 5: 0.5, 6: 0.4}
        weekly_expense_factor = {0: 1.2, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.9, 5: 0.3, 6: 0.2}

        for i in range(days):
            pred_date = today + timedelta(days=i + 1)
            weekday = pred_date.weekday()

            # Apply weekly factors
            pred_income = avg_income * weekly_income_factor[weekday]
            pred_expense = avg_expense * weekly_expense_factor[weekday]

            # Month-end adjustments
            if pred_date.day in [1, 15, 28, 29, 30, 31]:
                pred_expense *= 1.3  # Higher expenses at month boundaries

            pred_net = pred_income - pred_expense

            # Confidence intervals widen over time
            time_factor = 1 + (i / days) * 0.5
            conf_lower = pred_net - (std_income + std_expense) * time_factor
            conf_upper = pred_net + (std_income + std_expense) * time_factor

            factors = ["Statistical estimate"]
            if i >= 30:
                factors.append("Long-term (lower confidence)")

            predictions.append(CashFlowPrediction(
                date=pred_date.isoformat(),
                predicted_income=round(pred_income, 2),
                predicted_expenses=round(pred_expense, 2),
                predicted_net=round(pred_net, 2),
                confidence_lower=round(conf_lower, 2),
                confidence_upper=round(conf_upper, 2),
                factors=factors
            ))

        return predictions

    def _simple_prediction(self, days: int, include_pending_payments: bool) -> CashFlowForecast:
        """
        Fallback prediction without pandas/numpy
        """
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()

        # Calculate simple averages
        income_total = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "income")
        expense_total = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "expense")

        num_days = 30  # Assume 30 days of history
        avg_daily_income = income_total / num_days if income_total > 0 else 0
        avg_daily_expense = expense_total / num_days if expense_total > 0 else 0

        predictions = []
        today = datetime.utcnow().date()

        for i in range(days):
            pred_date = today + timedelta(days=i + 1)
            pred_net = avg_daily_income - avg_daily_expense

            predictions.append({
                "date": pred_date.isoformat(),
                "predicted_income": round(avg_daily_income, 2),
                "predicted_expenses": round(avg_daily_expense, 2),
                "predicted_net": round(pred_net, 2),
                "confidence_lower": round(pred_net * 0.7, 2),
                "confidence_upper": round(pred_net * 1.3, 2),
                "factors": ["Simple average estimate"]
            })

        current_balance = income_total - expense_total

        return CashFlowForecast(
            generated_at=datetime.utcnow().isoformat(),
            period_days=days,
            current_balance=round(current_balance, 2),
            predictions=predictions,
            summary={
                "total_predicted_income": round(avg_daily_income * days, 2),
                "total_predicted_expenses": round(avg_daily_expense * days, 2),
                "total_predicted_net": round((avg_daily_income - avg_daily_expense) * days, 2),
                "avg_daily_net": round(avg_daily_income - avg_daily_expense, 2)
            },
            insights=["Using simple average - install pandas and prophet for advanced predictions"],
            risk_alerts=[],
            project_impacts=[]
        )

    def _incorporate_pending_payments(
        self,
        predictions: List[CashFlowPrediction],
        payments: List[Dict]
    ) -> List[CashFlowPrediction]:
        """
        Incorporate known pending payments into predictions
        """
        # Group pending payments by due date
        payment_by_date = {}
        for payment in payments:
            if payment.get("status") in ["pending", "overdue"]:
                due_date = payment.get("due_date", "")[:10]
                if due_date not in payment_by_date:
                    payment_by_date[due_date] = {"payable": 0, "receivable": 0}

                amount = payment.get("amount", 0)
                if payment.get("type") == "payable":
                    payment_by_date[due_date]["payable"] += amount
                else:
                    payment_by_date[due_date]["receivable"] += amount

        # Adjust predictions
        for pred in predictions:
            date_str = pred.date
            if date_str in payment_by_date:
                pred.predicted_expenses += payment_by_date[date_str]["payable"]
                pred.predicted_income += payment_by_date[date_str]["receivable"]
                pred.predicted_net = pred.predicted_income - pred.predicted_expenses
                pred.factors.append("Known pending payments included")

        return predictions

    def _analyze_project_impacts(self, projects: List[Dict], days: int) -> List[Dict]:
        """
        Analyze how active projects will impact cash flow
        """
        impacts = []
        today = datetime.utcnow().date()
        end_date = today + timedelta(days=days)

        for project in projects:
            if project.get("status") != "active":
                continue

            # Check if project has milestone dates within forecast period
            start_date_str = project.get("start_date")
            end_date_str = project.get("end_date")

            impact = {
                "project_id": project["id"],
                "project_code": project.get("code", "Unknown"),
                "project_name": project.get("name", "Unknown"),
                "budget": project.get("budget", 0),
                "impacts": []
            }

            # Budget-based impact estimation
            budget = project.get("budget", 0)
            if budget > 0:
                # Estimate remaining spend based on project duration
                if end_date_str:
                    try:
                        proj_end = datetime.fromisoformat(end_date_str).date()
                        if proj_end >= today and proj_end <= end_date:
                            impact["impacts"].append({
                                "type": "milestone",
                                "date": end_date_str,
                                "description": f"Project completion - potential final payment",
                                "estimated_amount": budget * 0.2  # Assume 20% final payment
                            })
                    except (ValueError, TypeError):
                        pass

            if impact["impacts"]:
                impacts.append(impact)

        return impacts

    def _calculate_current_balance(self, transactions: List[Dict], payments: List[Dict]) -> float:
        """
        Calculate current cash balance
        """
        income = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "income")
        expenses = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "expense")

        # Add received payments
        received = sum(p.get("amount", 0) for p in payments
                      if p.get("type") == "receivable" and p.get("status") == "paid")

        # Subtract paid payments
        paid = sum(p.get("amount", 0) for p in payments
                  if p.get("type") == "payable" and p.get("status") == "paid")

        return income + received - expenses - paid

    def _calculate_summary(self, predictions: List[CashFlowPrediction], current_balance: float) -> Dict:
        """
        Calculate summary statistics for the forecast
        """
        total_income = sum(p.predicted_income for p in predictions)
        total_expenses = sum(p.predicted_expenses for p in predictions)
        total_net = sum(p.predicted_net for p in predictions)

        # Calculate by period
        summary = {
            "total_predicted_income": round(total_income, 2),
            "total_predicted_expenses": round(total_expenses, 2),
            "total_predicted_net": round(total_net, 2),
            "projected_end_balance": round(current_balance + total_net, 2),
            "avg_daily_net": round(total_net / len(predictions), 2) if predictions else 0,
            "periods": {}
        }

        # 30-60-90 day breakdown
        for period in [30, 60, 90]:
            period_preds = predictions[:period]
            if period_preds:
                summary["periods"][f"{period}_days"] = {
                    "income": round(sum(p.predicted_income for p in period_preds), 2),
                    "expenses": round(sum(p.predicted_expenses for p in period_preds), 2),
                    "net": round(sum(p.predicted_net for p in period_preds), 2),
                    "projected_balance": round(current_balance + sum(p.predicted_net for p in period_preds), 2)
                }

        return summary

    def _generate_insights(self, predictions: List[CashFlowPrediction], current_balance: float) -> List[str]:
        """
        Generate actionable insights from predictions
        """
        insights = []

        if not predictions:
            return ["Insufficient data for insights"]

        total_net = sum(p.predicted_net for p in predictions)
        avg_daily = total_net / len(predictions)

        # Trend analysis
        if avg_daily > 0:
            insights.append(f"Positive cash flow trend: averaging ${avg_daily:.2f}/day")
        else:
            insights.append(f"Negative cash flow trend: averaging ${avg_daily:.2f}/day - consider cost optimization")

        # Balance projection
        end_balance = current_balance + total_net
        if end_balance < 0:
            insights.append(f"WARNING: Projected negative balance of ${end_balance:.2f}")
        elif end_balance < current_balance * 0.5:
            insights.append(f"Cash reserves projected to decrease by {((current_balance - end_balance) / current_balance * 100):.0f}%")

        # Identify high expense periods
        high_expense_days = [p for p in predictions if p.predicted_expenses > sum(x.predicted_expenses for x in predictions) / len(predictions) * 1.5]
        if high_expense_days:
            insights.append(f"High expense days detected: {len(high_expense_days)} days above average")

        return insights

    def _generate_risk_alerts(
        self,
        predictions: List[CashFlowPrediction],
        current_balance: float,
        payments: List[Dict]
    ) -> List[str]:
        """
        Generate risk alerts for cash flow issues
        """
        alerts = []

        # Check for negative balance
        running_balance = current_balance
        for i, pred in enumerate(predictions):
            running_balance += pred.predicted_net
            if running_balance < 0 and len(alerts) < 3:
                alerts.append(f"RISK: Negative balance projected on day {i + 1} ({pred.date})")

        # Check for overdue payments
        overdue = [p for p in payments if p.get("status") == "overdue"]
        if overdue:
            total_overdue = sum(p.get("amount", 0) for p in overdue)
            alerts.append(f"ALERT: {len(overdue)} overdue payments totaling ${total_overdue:.2f}")

        # Check for large upcoming payments
        large_payments = [p for p in payments
                        if p.get("status") == "pending" and p.get("amount", 0) > current_balance * 0.3]
        for p in large_payments[:3]:
            alerts.append(f"Large payment due: ${p.get('amount', 0):.2f} on {p.get('due_date', 'Unknown')}")

        return alerts


# Service instance factory
def create_cashflow_predictor(db) -> CashFlowPredictor:
    return CashFlowPredictor(db)
