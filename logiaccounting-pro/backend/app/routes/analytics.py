"""
Analytics API Routes
Advanced analytics and ML forecasting endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import get_current_user, require_roles

from app.services.analytics import (
    InventoryAnalytics,
    TrendAnalyzer,
    ScenarioPlanner,
    InsightsGenerator,
    KPICalculator
)
from app.services.ml import CashFlowForecaster

router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class ScenarioRequest(BaseModel):
    """Scenario analysis request body"""
    scenario_type: str
    parameters: dict = {}


class ScenarioCompareRequest(BaseModel):
    """Multiple scenarios comparison request"""
    scenarios: list


# ============================================
# DASHBOARD & KPIs
# ============================================

@router.get("/dashboard")
async def get_analytics_dashboard(current_user: dict = Depends(require_roles("admin"))):
    """
    Get main analytics dashboard with all KPIs

    Returns comprehensive dashboard data including:
    - Financial KPIs
    - Health score
    - Trend indicators
    - Key metrics
    """
    try:
        kpi_calc = KPICalculator(db)
        dashboard_data = kpi_calc.get_dashboard_kpis()
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-score")
async def get_health_score(current_user: dict = Depends(require_roles("admin"))):
    """
    Get financial health score (0-100)

    Calculates overall business health based on:
    - Profitability
    - Cash flow
    - Receivables
    - Growth
    - Expense control
    """
    try:
        kpi_calc = KPICalculator(db)
        health = kpi_calc.get_health_score()

        return {
            'score': health.score,
            'grade': health.grade,
            'category': health.category,
            'components': health.components,
            'recommendations': health.recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi-trends/{metric}")
async def get_kpi_trends(
    metric: str,
    periods: int = Query(6, ge=1, le=24),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get KPI trend over time

    Args:
        metric: revenue, expenses, profit, margin
        periods: Number of periods (default 6)
    """
    try:
        kpi_calc = KPICalculator(db)
        trends = kpi_calc.get_kpi_trends(metric, periods)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FORECASTING
# ============================================

@router.get("/forecast/cashflow")
async def forecast_cashflow(
    days: int = Query(90, ge=7, le=365),
    include_pending: bool = Query(True),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get cash flow forecast

    Query params:
        days: Forecast period (default 90)
        include_pending: Include pending payments (default true)
    """
    try:
        forecaster = CashFlowForecaster(db)
        forecast = forecaster.forecast(
            days=days,
            include_pending=include_pending,
            scenarios=True,
            confidence_level=0.95
        )
        return forecast.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/inventory/{sku}")
async def forecast_inventory_demand(
    sku: str,
    days: int = Query(90, ge=7, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get demand forecast for specific inventory item

    Args:
        sku: Material/inventory item ID
        days: Forecast period (default 90)
    """
    try:
        analytics = InventoryAnalytics(db)
        forecast = analytics.get_demand_forecast(sku=sku, days=days)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# INVENTORY ANALYTICS
# ============================================

@router.get("/inventory/overview")
async def get_inventory_overview(current_user: dict = Depends(require_roles("admin"))):
    """Get inventory analytics overview"""
    try:
        analytics = InventoryAnalytics(db)
        overview = analytics.get_inventory_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/demand/{sku}")
async def get_inventory_demand(
    sku: str,
    days: int = Query(90, ge=7, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get demand forecast and recommendations for SKU

    Query params:
        days: Forecast period (default 90)
    """
    try:
        analytics = InventoryAnalytics(db)
        demand = analytics.get_demand_forecast(sku=sku, days=days)
        return demand
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/reorder")
async def get_reorder_recommendations(current_user: dict = Depends(require_roles("admin"))):
    """Get reorder recommendations for all items"""
    try:
        analytics = InventoryAnalytics(db)
        recommendations = analytics.get_reorder_recommendations()
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/abc")
async def get_abc_analysis(current_user: dict = Depends(require_roles("admin"))):
    """Get ABC inventory classification"""
    try:
        analytics = InventoryAnalytics(db)
        abc = analytics.get_abc_analysis()
        return abc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TREND ANALYSIS
# ============================================

@router.get("/trends")
async def get_trends_overview(current_user: dict = Depends(require_roles("admin"))):
    """Get comprehensive trend analysis"""
    try:
        analyzer = TrendAnalyzer(db)
        trends = analyzer.get_trends_overview()
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{metric}")
async def get_metric_trend(
    metric: str,
    period: str = Query("monthly"),
    months: int = Query(12, ge=1, le=36),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get trend for specific metric

    Args:
        metric: revenue, expenses, profit

    Query params:
        period: monthly, weekly (default monthly)
        months: Number of months (default 12)
    """
    try:
        analyzer = TrendAnalyzer(db)
        trend = analyzer.get_metric_trend(metric=metric, period=period, months=months)
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/yoy")
async def get_yoy_analysis(current_user: dict = Depends(require_roles("admin"))):
    """Get year-over-year comparison"""
    try:
        analyzer = TrendAnalyzer(db)
        yoy = analyzer.get_yoy_analysis()
        return yoy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/seasonality")
async def get_seasonality(current_user: dict = Depends(require_roles("admin"))):
    """Get seasonality analysis"""
    try:
        analyzer = TrendAnalyzer(db)
        seasonality = analyzer.get_seasonality_analysis()
        return seasonality
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SCENARIO PLANNING
# ============================================

@router.post("/scenario")
async def run_scenario(
    request: ScenarioRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Run scenario analysis

    Body:
        scenario_type: revenue_change, expense_change, growth, breakeven
        parameters: Scenario-specific parameters
    """
    try:
        planner = ScenarioPlanner(db)
        result = planner.run_scenario(
            scenario_type=request.scenario_type,
            parameters=request.parameters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario/compare")
async def compare_scenarios(
    request: ScenarioCompareRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Compare multiple scenarios

    Body:
        scenarios: List of scenario definitions
    """
    try:
        if not request.scenarios:
            raise HTTPException(status_code=400, detail="scenarios list is required")

        planner = ScenarioPlanner(db)
        comparison = planner.get_scenario_comparison(request.scenarios)
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenario/bwe")
async def get_best_worst_expected(current_user: dict = Depends(require_roles("admin"))):
    """Get best, worst, and expected case scenarios"""
    try:
        planner = ScenarioPlanner(db)
        bwe = planner.get_best_worst_expected()
        return bwe
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AI INSIGHTS
# ============================================

@router.get("/insights")
async def get_insights(current_user: dict = Depends(require_roles("admin"))):
    """Get AI-generated business insights"""
    try:
        generator = InsightsGenerator(db)
        insights = generator.get_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/weekly")
async def get_weekly_summary(current_user: dict = Depends(require_roles("admin"))):
    """Get weekly business summary"""
    try:
        generator = InsightsGenerator(db)
        summary = generator.get_weekly_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EXPORT
# ============================================

@router.get("/export")
async def export_analytics(
    export_type: str = Query("dashboard"),
    export_format: str = Query("json"),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Export analytics data

    Query params:
        type: dashboard, forecast, inventory
        format: json, csv (default json)
    """
    try:
        # Get data based on type
        if export_type == 'dashboard':
            kpi_calc = KPICalculator(db)
            data = kpi_calc.get_dashboard_kpis()
        elif export_type == 'forecast':
            forecaster = CashFlowForecaster(db)
            data = forecaster.forecast().to_dict()
        elif export_type == 'inventory':
            analytics = InventoryAnalytics(db)
            data = analytics.get_inventory_overview()
        elif export_type == 'insights':
            generator = InsightsGenerator(db)
            data = generator.get_insights()
        else:
            raise HTTPException(status_code=400, detail=f'Unknown export type: {export_type}')

        # For now, return JSON (CSV export can be added later)
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
