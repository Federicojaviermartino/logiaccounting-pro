# LogiAccounting Pro - Phase 10 Tasks Part 3

## API ROUTES & FRONTEND COMPONENTS

---

## TASK 10: ANALYTICS API ROUTES

### 10.1 Create Analytics Router

**File:** `backend/app/routes/analytics.py`

```python
"""
Analytics API Routes
Advanced analytics and ML forecasting endpoints
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os

from app.database import db
from app.services.analytics import (
    ForecastingEngine,
    KPICalculator,
    RevenueAnalytics,
    CustomerAnalytics,
    InventoryAnalytics,
    TrendAnalyzer,
    ScenarioPlanner,
    InsightsGenerator
)

analytics_bp = Blueprint('analytics', __name__)

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')


def token_required(f):
    """JWT token verification decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user_id = data.get('user_id')
            request.user_role = data.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Admin role verification decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated


# ============================================
# DASHBOARD & KPIs
# ============================================

@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
def get_analytics_dashboard():
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
        
        return jsonify(dashboard_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/health-score', methods=['GET'])
@token_required
def get_health_score():
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
        
        return jsonify({
            'score': health.score,
            'grade': health.grade,
            'category': health.category,
            'components': health.components,
            'recommendations': health.recommendations
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/kpi-trends/<metric>', methods=['GET'])
@token_required
def get_kpi_trends(metric):
    """
    Get KPI trend over time
    
    Args:
        metric: revenue, expenses, profit, margin
    
    Query params:
        periods: Number of periods (default 6)
    """
    try:
        periods = request.args.get('periods', 6, type=int)
        
        kpi_calc = KPICalculator(db)
        trends = kpi_calc.get_kpi_trends(metric, periods)
        
        return jsonify(trends), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# FORECASTING
# ============================================

@analytics_bp.route('/forecast/revenue', methods=['GET'])
@token_required
def forecast_revenue():
    """
    Get revenue forecast
    
    Query params:
        days: Forecast period (default 90)
        model: prophet, arima, exponential, ensemble, auto (default auto)
    """
    try:
        days = request.args.get('days', 90, type=int)
        model = request.args.get('model', 'auto')
        
        engine = ForecastingEngine(db)
        forecast = engine.forecast_revenue(days=days, model=model)
        
        return jsonify(forecast.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/forecast/expenses', methods=['GET'])
@token_required
def forecast_expenses():
    """
    Get expense forecast
    
    Query params:
        days: Forecast period (default 90)
        model: prophet, arima, exponential, ensemble, auto (default auto)
    """
    try:
        days = request.args.get('days', 90, type=int)
        model = request.args.get('model', 'auto')
        
        engine = ForecastingEngine(db)
        forecast = engine.forecast_expenses(days=days, model=model)
        
        return jsonify(forecast.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/forecast/cashflow', methods=['GET'])
@token_required
def forecast_cashflow():
    """
    Get cash flow forecast
    
    Query params:
        days: Forecast period (default 90)
        include_pending: Include pending payments (default true)
    """
    try:
        days = request.args.get('days', 90, type=int)
        include_pending = request.args.get('include_pending', 'true').lower() == 'true'
        
        engine = ForecastingEngine(db)
        forecast = engine.forecast_cashflow(days=days, include_pending=include_pending)
        
        return jsonify(forecast.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/forecast/inventory/<sku>', methods=['GET'])
@token_required
def forecast_inventory_demand(sku):
    """
    Get demand forecast for specific inventory item
    
    Args:
        sku: Material/inventory item ID
    
    Query params:
        days: Forecast period (default 90)
    """
    try:
        days = request.args.get('days', 90, type=int)
        
        engine = ForecastingEngine(db)
        forecast = engine.forecast_inventory_demand(sku=sku, days=days)
        
        return jsonify(forecast.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# REVENUE ANALYTICS
# ============================================

@analytics_bp.route('/revenue/overview', methods=['GET'])
@token_required
def get_revenue_overview():
    """
    Get comprehensive revenue overview
    
    Query params:
        months: Analysis period (default 12)
    """
    try:
        months = request.args.get('months', 12, type=int)
        
        analytics = RevenueAnalytics(db)
        overview = analytics.get_revenue_overview(months=months)
        
        return jsonify(overview), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/revenue/by-customer', methods=['GET'])
@token_required
def get_revenue_by_customer():
    """
    Get revenue breakdown by customer
    
    Query params:
        top_n: Number of top customers (default 10)
    """
    try:
        top_n = request.args.get('top_n', 10, type=int)
        
        analytics = RevenueAnalytics(db)
        data = analytics.get_revenue_by_customer(top_n=top_n)
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/revenue/by-region', methods=['GET'])
@token_required
def get_revenue_by_region():
    """Get revenue breakdown by region (EU/US)"""
    try:
        analytics = RevenueAnalytics(db)
        data = analytics.get_revenue_by_region()
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/revenue/recurring', methods=['GET'])
@token_required
def get_recurring_revenue():
    """Get recurring vs one-time revenue analysis"""
    try:
        analytics = RevenueAnalytics(db)
        data = analytics.get_recurring_revenue_analysis()
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# CUSTOMER ANALYTICS
# ============================================

@analytics_bp.route('/customers/overview', methods=['GET'])
@token_required
def get_customer_overview():
    """Get customer analytics overview"""
    try:
        analytics = CustomerAnalytics(db)
        overview = analytics.get_customer_overview()
        
        return jsonify(overview), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/customers/rfm', methods=['GET'])
@token_required
def get_rfm_analysis():
    """
    Get RFM (Recency, Frequency, Monetary) analysis
    
    Returns customer segmentation based on purchase behavior
    """
    try:
        analytics = CustomerAnalytics(db)
        rfm = analytics.get_rfm_analysis()
        
        return jsonify(rfm), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/customers/clv', methods=['GET'])
@token_required
def get_customer_clv():
    """
    Get Customer Lifetime Value analysis
    
    Query params:
        top_n: Number of customers to return (default 20)
    """
    try:
        top_n = request.args.get('top_n', 20, type=int)
        
        analytics = CustomerAnalytics(db)
        clv = analytics.get_customer_clv(top_n=top_n)
        
        return jsonify(clv), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/customers/segments', methods=['GET'])
@token_required
def get_customer_segments():
    """Get customer segment distribution"""
    try:
        analytics = CustomerAnalytics(db)
        segments = analytics.get_customer_segments()
        
        return jsonify(segments), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/customers/churn-risk', methods=['GET'])
@token_required
def get_churn_risk():
    """Get customers at risk of churning"""
    try:
        analytics = CustomerAnalytics(db)
        risk = analytics.get_churn_risk()
        
        return jsonify(risk), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# INVENTORY ANALYTICS
# ============================================

@analytics_bp.route('/inventory/overview', methods=['GET'])
@token_required
def get_inventory_overview():
    """Get inventory analytics overview"""
    try:
        analytics = InventoryAnalytics(db)
        overview = analytics.get_inventory_overview()
        
        return jsonify(overview), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/inventory/demand/<sku>', methods=['GET'])
@token_required
def get_inventory_demand(sku):
    """
    Get demand forecast and recommendations for SKU
    
    Query params:
        days: Forecast period (default 90)
    """
    try:
        days = request.args.get('days', 90, type=int)
        
        analytics = InventoryAnalytics(db)
        demand = analytics.get_demand_forecast(sku=sku, days=days)
        
        return jsonify(demand), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/inventory/reorder', methods=['GET'])
@token_required
def get_reorder_recommendations():
    """Get reorder recommendations for all items"""
    try:
        analytics = InventoryAnalytics(db)
        recommendations = analytics.get_reorder_recommendations()
        
        return jsonify(recommendations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/inventory/abc', methods=['GET'])
@token_required
def get_abc_analysis():
    """Get ABC inventory classification"""
    try:
        analytics = InventoryAnalytics(db)
        abc = analytics.get_abc_analysis()
        
        return jsonify(abc), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# TREND ANALYSIS
# ============================================

@analytics_bp.route('/trends', methods=['GET'])
@token_required
def get_trends_overview():
    """Get comprehensive trend analysis"""
    try:
        analyzer = TrendAnalyzer(db)
        trends = analyzer.get_trends_overview()
        
        return jsonify(trends), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/trends/<metric>', methods=['GET'])
@token_required
def get_metric_trend(metric):
    """
    Get trend for specific metric
    
    Args:
        metric: revenue, expenses, profit
    
    Query params:
        period: monthly, weekly (default monthly)
        months: Number of months (default 12)
    """
    try:
        period = request.args.get('period', 'monthly')
        months = request.args.get('months', 12, type=int)
        
        analyzer = TrendAnalyzer(db)
        trend = analyzer.get_metric_trend(metric=metric, period=period, months=months)
        
        return jsonify(trend), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/trends/yoy', methods=['GET'])
@token_required
def get_yoy_analysis():
    """Get year-over-year comparison"""
    try:
        analyzer = TrendAnalyzer(db)
        yoy = analyzer.get_yoy_analysis()
        
        return jsonify(yoy), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/trends/seasonality', methods=['GET'])
@token_required
def get_seasonality():
    """Get seasonality analysis"""
    try:
        analyzer = TrendAnalyzer(db)
        seasonality = analyzer.get_seasonality_analysis()
        
        return jsonify(seasonality), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# SCENARIO PLANNING
# ============================================

@analytics_bp.route('/scenario', methods=['POST'])
@token_required
def run_scenario():
    """
    Run scenario analysis
    
    Body:
        scenario_type: revenue_change, expense_change, growth, breakeven, sensitivity
        parameters: Scenario-specific parameters
    """
    try:
        data = request.get_json()
        scenario_type = data.get('scenario_type')
        parameters = data.get('parameters', {})
        
        if not scenario_type:
            return jsonify({'error': 'scenario_type is required'}), 400
        
        planner = ScenarioPlanner(db)
        result = planner.run_scenario(scenario_type=scenario_type, parameters=parameters)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/scenario/compare', methods=['POST'])
@token_required
def compare_scenarios():
    """
    Compare multiple scenarios
    
    Body:
        scenarios: List of scenario definitions
    """
    try:
        data = request.get_json()
        scenarios = data.get('scenarios', [])
        
        if not scenarios:
            return jsonify({'error': 'scenarios list is required'}), 400
        
        planner = ScenarioPlanner(db)
        comparison = planner.get_scenario_comparison(scenarios)
        
        return jsonify(comparison), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/scenario/bwe', methods=['GET'])
@token_required
def get_best_worst_expected():
    """Get best, worst, and expected case scenarios"""
    try:
        planner = ScenarioPlanner(db)
        bwe = planner.get_best_worst_expected()
        
        return jsonify(bwe), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# AI INSIGHTS
# ============================================

@analytics_bp.route('/insights', methods=['GET'])
@token_required
def get_insights():
    """Get AI-generated business insights"""
    try:
        generator = InsightsGenerator(db)
        insights = generator.get_insights()
        
        return jsonify(insights), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/insights/weekly', methods=['GET'])
@token_required
def get_weekly_summary():
    """Get weekly business summary"""
    try:
        generator = InsightsGenerator(db)
        summary = generator.get_weekly_summary()
        
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# EXPORT
# ============================================

@analytics_bp.route('/export', methods=['GET'])
@token_required
def export_analytics():
    """
    Export analytics data
    
    Query params:
        format: json, csv (default json)
        type: dashboard, forecast, customers, inventory
    """
    try:
        export_format = request.args.get('format', 'json')
        export_type = request.args.get('type', 'dashboard')
        
        # Get data based on type
        if export_type == 'dashboard':
            kpi_calc = KPICalculator(db)
            data = kpi_calc.get_dashboard_kpis()
        elif export_type == 'forecast':
            engine = ForecastingEngine(db)
            data = engine.forecast_cashflow().to_dict()
        elif export_type == 'customers':
            analytics = CustomerAnalytics(db)
            data = analytics.get_rfm_analysis()
        elif export_type == 'inventory':
            analytics = InventoryAnalytics(db)
            data = analytics.get_inventory_overview()
        else:
            return jsonify({'error': f'Unknown export type: {export_type}'}), 400
        
        if export_format == 'csv':
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if isinstance(data, dict) and 'customers' in data:
                # Export customer list
                customers = data.get('customers', [])
                if customers:
                    writer = csv.DictWriter(output, fieldnames=customers[0].keys())
                    writer.writeheader()
                    writer.writerows(customers)
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=analytics_{export_type}.csv'
            }
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 10.2 Register Analytics Blueprint

**Update:** `backend/app/__init__.py`

```python
# Add to existing imports
from app.routes.analytics import analytics_bp

# Add to blueprint registration
app.register_blueprint(analytics_bp, url_prefix='/api/v1/analytics')
```

---

## TASK 11: FRONTEND API SERVICE

### 11.1 Create Analytics API Service

**File:** `frontend/src/services/analyticsApi.js`

```javascript
/**
 * Analytics API Service
 * Handles all analytics and ML forecasting API calls
 */

import api from './api';

const analyticsApi = {
  // ============================================
  // DASHBOARD & KPIs
  // ============================================
  
  /**
   * Get main analytics dashboard
   */
  getDashboard: async () => {
    const response = await api.get('/analytics/dashboard');
    return response.data;
  },

  /**
   * Get financial health score
   */
  getHealthScore: async () => {
    const response = await api.get('/analytics/health-score');
    return response.data;
  },

  /**
   * Get KPI trends
   * @param {string} metric - revenue, expenses, profit, margin
   * @param {number} periods - Number of periods
   */
  getKPITrends: async (metric, periods = 6) => {
    const response = await api.get(`/analytics/kpi-trends/${metric}`, {
      params: { periods }
    });
    return response.data;
  },

  // ============================================
  // FORECASTING
  // ============================================

  /**
   * Get revenue forecast
   * @param {number} days - Forecast period
   * @param {string} model - Forecasting model
   */
  forecastRevenue: async (days = 90, model = 'auto') => {
    const response = await api.get('/analytics/forecast/revenue', {
      params: { days, model }
    });
    return response.data;
  },

  /**
   * Get expense forecast
   */
  forecastExpenses: async (days = 90, model = 'auto') => {
    const response = await api.get('/analytics/forecast/expenses', {
      params: { days, model }
    });
    return response.data;
  },

  /**
   * Get cash flow forecast
   */
  forecastCashflow: async (days = 90, includePending = true) => {
    const response = await api.get('/analytics/forecast/cashflow', {
      params: { days, include_pending: includePending }
    });
    return response.data;
  },

  /**
   * Get inventory demand forecast
   * @param {string} sku - Item SKU
   */
  forecastInventory: async (sku, days = 90) => {
    const response = await api.get(`/analytics/forecast/inventory/${sku}`, {
      params: { days }
    });
    return response.data;
  },

  // ============================================
  // REVENUE ANALYTICS
  // ============================================

  /**
   * Get revenue overview
   */
  getRevenueOverview: async (months = 12) => {
    const response = await api.get('/analytics/revenue/overview', {
      params: { months }
    });
    return response.data;
  },

  /**
   * Get revenue by customer
   */
  getRevenueByCustomer: async (topN = 10) => {
    const response = await api.get('/analytics/revenue/by-customer', {
      params: { top_n: topN }
    });
    return response.data;
  },

  /**
   * Get revenue by region
   */
  getRevenueByRegion: async () => {
    const response = await api.get('/analytics/revenue/by-region');
    return response.data;
  },

  /**
   * Get recurring revenue analysis
   */
  getRecurringRevenue: async () => {
    const response = await api.get('/analytics/revenue/recurring');
    return response.data;
  },

  // ============================================
  // CUSTOMER ANALYTICS
  // ============================================

  /**
   * Get customer overview
   */
  getCustomerOverview: async () => {
    const response = await api.get('/analytics/customers/overview');
    return response.data;
  },

  /**
   * Get RFM analysis
   */
  getRFMAnalysis: async () => {
    const response = await api.get('/analytics/customers/rfm');
    return response.data;
  },

  /**
   * Get customer lifetime value
   */
  getCustomerCLV: async (topN = 20) => {
    const response = await api.get('/analytics/customers/clv', {
      params: { top_n: topN }
    });
    return response.data;
  },

  /**
   * Get customer segments
   */
  getCustomerSegments: async () => {
    const response = await api.get('/analytics/customers/segments');
    return response.data;
  },

  /**
   * Get churn risk analysis
   */
  getChurnRisk: async () => {
    const response = await api.get('/analytics/customers/churn-risk');
    return response.data;
  },

  // ============================================
  // INVENTORY ANALYTICS
  // ============================================

  /**
   * Get inventory overview
   */
  getInventoryOverview: async () => {
    const response = await api.get('/analytics/inventory/overview');
    return response.data;
  },

  /**
   * Get demand forecast for SKU
   */
  getInventoryDemand: async (sku, days = 90) => {
    const response = await api.get(`/analytics/inventory/demand/${sku}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get reorder recommendations
   */
  getReorderRecommendations: async () => {
    const response = await api.get('/analytics/inventory/reorder');
    return response.data;
  },

  /**
   * Get ABC analysis
   */
  getABCAnalysis: async () => {
    const response = await api.get('/analytics/inventory/abc');
    return response.data;
  },

  // ============================================
  // TREND ANALYSIS
  // ============================================

  /**
   * Get trends overview
   */
  getTrendsOverview: async () => {
    const response = await api.get('/analytics/trends');
    return response.data;
  },

  /**
   * Get metric trend
   */
  getMetricTrend: async (metric, period = 'monthly', months = 12) => {
    const response = await api.get(`/analytics/trends/${metric}`, {
      params: { period, months }
    });
    return response.data;
  },

  /**
   * Get year-over-year analysis
   */
  getYoYAnalysis: async () => {
    const response = await api.get('/analytics/trends/yoy');
    return response.data;
  },

  /**
   * Get seasonality analysis
   */
  getSeasonality: async () => {
    const response = await api.get('/analytics/trends/seasonality');
    return response.data;
  },

  // ============================================
  // SCENARIO PLANNING
  // ============================================

  /**
   * Run scenario analysis
   */
  runScenario: async (scenarioType, parameters) => {
    const response = await api.post('/analytics/scenario', {
      scenario_type: scenarioType,
      parameters
    });
    return response.data;
  },

  /**
   * Compare multiple scenarios
   */
  compareScenarios: async (scenarios) => {
    const response = await api.post('/analytics/scenario/compare', {
      scenarios
    });
    return response.data;
  },

  /**
   * Get best/worst/expected scenarios
   */
  getBWEScenarios: async () => {
    const response = await api.get('/analytics/scenario/bwe');
    return response.data;
  },

  // ============================================
  // AI INSIGHTS
  // ============================================

  /**
   * Get AI-generated insights
   */
  getInsights: async () => {
    const response = await api.get('/analytics/insights');
    return response.data;
  },

  /**
   * Get weekly summary
   */
  getWeeklySummary: async () => {
    const response = await api.get('/analytics/insights/weekly');
    return response.data;
  },

  // ============================================
  // EXPORT
  // ============================================

  /**
   * Export analytics data
   */
  exportData: async (type = 'dashboard', format = 'json') => {
    const response = await api.get('/analytics/export', {
      params: { type, format },
      responseType: format === 'csv' ? 'blob' : 'json'
    });
    return response.data;
  }
};

export default analyticsApi;
```

---

## TASK 12: ANALYTICS DASHBOARD PAGE

### 12.1 Create Main Analytics Dashboard

**File:** `frontend/src/pages/AnalyticsDashboard.jsx`

```jsx
/**
 * Analytics Dashboard Page
 * Main hub for business intelligence and analytics
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import analyticsApi from '../services/analyticsApi';
import KPICard from '../components/analytics/KPICard';
import HealthScoreGauge from '../components/analytics/HealthScoreGauge';
import InsightCard from '../components/analytics/InsightCard';
import TrendIndicator from '../components/analytics/TrendIndicator';
import LoadingSpinner from '../components/common/LoadingSpinner';
import '../styles/analytics.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AnalyticsDashboard = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboardData, insightsData, forecastData] = await Promise.all([
        analyticsApi.getDashboard(),
        analyticsApi.getInsights(),
        analyticsApi.forecastCashflow(90)
      ]);

      setDashboard(dashboardData);
      setInsights(insightsData);
      setForecast(forecastData);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(t('common.errorLoading'));
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  // Prepare chart data
  const getCashFlowChartData = () => {
    if (!forecast?.predictions) return null;

    const labels = forecast.predictions.slice(0, 30).map(p => {
      const date = new Date(p.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels,
      datasets: [
        {
          label: 'Predicted Cash Flow',
          data: forecast.predictions.slice(0, 30).map(p => p.predicted),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'Upper Bound',
          data: forecast.predictions.slice(0, 30).map(p => p.upper_bound),
          borderColor: 'rgba(34, 197, 94, 0.5)',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        },
        {
          label: 'Lower Bound',
          data: forecast.predictions.slice(0, 30).map(p => p.lower_bound),
          borderColor: 'rgba(239, 68, 68, 0.5)',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        }
      ]
    };
  };

  const getKPIDistributionData = () => {
    if (!dashboard?.kpis) return null;

    const kpis = dashboard.kpis;
    
    return {
      labels: ['Revenue', 'Expenses', 'Profit'],
      datasets: [{
        data: [
          kpis.revenue?.value || 0,
          kpis.expenses?.value || 0,
          Math.max(0, kpis.profit?.value || 0)
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(59, 130, 246, 0.8)'
        ],
        borderWidth: 0
      }]
    };
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <LoadingSpinner size="large" />
        <p>{t('common.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <div className="error-icon">⚠️</div>
        <h3>{t('common.error')}</h3>
        <p>{error}</p>
        <button onClick={loadDashboardData} className="btn btn-primary">
          {t('common.retry')}
        </button>
      </div>
    );
  }

  const kpis = dashboard?.kpis || {};
  const healthScore = dashboard?.health_score || {};

  return (
    <div className="analytics-dashboard">
      {/* Header */}
      <div className="analytics-header">
        <div className="header-content">
          <h1>{t('analytics.dashboard')}</h1>
          <p className="subtitle">Business Intelligence & Forecasting</p>
        </div>
        <div className="header-actions">
          <button 
            onClick={loadDashboardData} 
            className="btn btn-outline"
            title="Refresh data"
          >
            <span className="icon">🔄</span>
            Refresh
          </button>
          <button className="btn btn-primary">
            <span className="icon">📊</span>
            Export Report
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="analytics-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'forecasts' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecasts')}
        >
          Forecasts
        </button>
        <button 
          className={`tab ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          AI Insights
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Health Score & KPIs Row */}
          <div className="analytics-row health-kpis-row">
            {/* Health Score */}
            <div className="health-score-card">
              <h3>Financial Health Score</h3>
              <HealthScoreGauge 
                score={healthScore.score || 0}
                grade={healthScore.grade || 'N/A'}
                category={healthScore.category || 'Unknown'}
              />
              {healthScore.recommendations?.length > 0 && (
                <div className="health-recommendations">
                  <h4>Recommendations</h4>
                  <ul>
                    {healthScore.recommendations.slice(0, 3).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid">
              <KPICard
                title="Revenue"
                value={formatCurrency(kpis.revenue?.value || 0)}
                change={kpis.revenue?.change_percent}
                trend={kpis.revenue?.trend}
                icon="💰"
                color="green"
              />
              <KPICard
                title="Expenses"
                value={formatCurrency(kpis.expenses?.value || 0)}
                change={kpis.expenses?.change_percent}
                trend={kpis.expenses?.trend}
                icon="💸"
                color="red"
                invertTrend
              />
              <KPICard
                title="Net Profit"
                value={formatCurrency(kpis.profit?.value || 0)}
                change={kpis.profit?.change_percent}
                trend={kpis.profit?.trend}
                icon="📈"
                color="blue"
              />
              <KPICard
                title="Profit Margin"
                value={`${kpis.net_margin?.value || 0}%`}
                target={`Target: ${kpis.net_margin?.target || 10}%`}
                status={kpis.net_margin?.status}
                icon="📊"
                color="purple"
              />
            </div>
          </div>

          {/* Charts Row */}
          <div className="analytics-row charts-row">
            {/* Cash Flow Forecast Chart */}
            <div className="chart-card large">
              <div className="chart-header">
                <h3>30-Day Cash Flow Forecast</h3>
                <div className="chart-legend">
                  <span className="legend-item">
                    <span className="dot blue"></span>
                    Predicted
                  </span>
                  <span className="legend-item">
                    <span className="dot green"></span>
                    Upper Bound
                  </span>
                  <span className="legend-item">
                    <span className="dot red"></span>
                    Lower Bound
                  </span>
                </div>
              </div>
              <div className="chart-container">
                {getCashFlowChartData() && (
                  <Line
                    data={getCashFlowChartData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index',
                          intersect: false,
                          callbacks: {
                            label: (context) => {
                              return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: false,
                          ticks: {
                            callback: (value) => formatCurrency(value)
                          }
                        }
                      },
                      interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                      }
                    }}
                  />
                )}
              </div>
              {forecast?.summary && (
                <div className="chart-footer">
                  <div className="forecast-stat">
                    <span className="label">Current Balance</span>
                    <span className="value">{formatCurrency(forecast.summary.current_balance || 0)}</span>
                  </div>
                  <div className="forecast-stat">
                    <span className="label">Projected (90 days)</span>
                    <span className="value">{formatCurrency(forecast.summary.projected_balance || 0)}</span>
                  </div>
                  <div className="forecast-stat">
                    <span className="label">Model Accuracy</span>
                    <span className="value">{((forecast.accuracy_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              )}
            </div>

            {/* Distribution Chart */}
            <div className="chart-card small">
              <h3>Financial Distribution</h3>
              <div className="chart-container doughnut">
                {getKPIDistributionData() && (
                  <Doughnut
                    data={getKPIDistributionData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                          labels: {
                            padding: 20,
                            usePointStyle: true
                          }
                        },
                        tooltip: {
                          callbacks: {
                            label: (context) => {
                              return `${context.label}: ${formatCurrency(context.raw)}`;
                            }
                          }
                        }
                      },
                      cutout: '60%'
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Additional KPIs Row */}
          <div className="analytics-row secondary-kpis">
            <div className="kpi-card-mini">
              <span className="icon">💵</span>
              <div className="content">
                <span className="label">Cash Runway</span>
                <span className="value">
                  {kpis.cash_runway?.runway_months || 0} months
                </span>
              </div>
              <TrendIndicator status={kpis.cash_runway?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">📦</span>
              <div className="content">
                <span className="label">Inventory Turnover</span>
                <span className="value">
                  {kpis.inventory_turnover?.turnover_ratio || 0}x
                </span>
              </div>
              <TrendIndicator status={kpis.inventory_turnover?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">🧾</span>
              <div className="content">
                <span className="label">Receivables</span>
                <span className="value">
                  {formatCurrency(kpis.receivables_aging?.total || 0)}
                </span>
              </div>
              <TrendIndicator status={kpis.receivables_aging?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">🎯</span>
              <div className="content">
                <span className="label">Project Profitability</span>
                <span className="value">
                  {kpis.project_profitability?.profitability_rate || 0}%
                </span>
              </div>
              <TrendIndicator status={kpis.project_profitability?.status} />
            </div>
          </div>
        </>
      )}

      {/* Forecasts Tab */}
      {activeTab === 'forecasts' && (
        <div className="forecasts-content">
          <p>Forecasting features coming soon...</p>
          {/* Add ForecastingCenter component here */}
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && insights && (
        <div className="insights-content">
          {/* Summary */}
          <div className="insights-summary">
            <div className={`summary-badge ${insights.summary?.status}`}>
              <span className="status-text">{insights.summary?.category || 'Unknown'}</span>
            </div>
            <p className="summary-message">{insights.summary?.message}</p>
          </div>

          {/* Key Insights */}
          <div className="insights-section">
            <h3>Key Insights</h3>
            <div className="insights-grid">
              {insights.key_insights?.map((insight, idx) => (
                <InsightCard
                  key={idx}
                  icon={insight.icon}
                  title={insight.title}
                  detail={insight.detail}
                  type={insight.type}
                />
              ))}
            </div>
          </div>

          {/* Opportunities */}
          {insights.opportunities?.length > 0 && (
            <div className="insights-section">
              <h3>Opportunities</h3>
              <div className="opportunities-list">
                {insights.opportunities.map((opp, idx) => (
                  <div key={idx} className="opportunity-card">
                    <span className="opp-icon">{opp.icon}</span>
                    <div className="opp-content">
                      <h4>{opp.title}</h4>
                      <p>{opp.detail}</p>
                      {opp.potential_impact && (
                        <span className="impact-badge">
                          Potential: {opp.potential_impact}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risks */}
          {insights.risks?.length > 0 && (
            <div className="insights-section">
              <h3>Risk Alerts</h3>
              <div className="risks-list">
                {insights.risks.map((risk, idx) => (
                  <div key={idx} className={`risk-card ${risk.severity}`}>
                    <span className="risk-icon">{risk.icon}</span>
                    <div className="risk-content">
                      <h4>{risk.title}</h4>
                      <p>{risk.detail}</p>
                      <span className="action-text">{risk.action}</span>
                    </div>
                    <span className={`severity-badge ${risk.severity}`}>
                      {risk.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {insights.recommendations?.length > 0 && (
            <div className="insights-section">
              <h3>Recommendations</h3>
              <div className="recommendations-list">
                {insights.recommendations.map((rec, idx) => (
                  <div key={idx} className={`recommendation-card ${rec.priority}`}>
                    <div className="rec-header">
                      <span className={`priority-badge ${rec.priority}`}>
                        {rec.priority}
                      </span>
                      <span className="category">{rec.category}</span>
                    </div>
                    <h4>{rec.title}</h4>
                    <ul className="action-list">
                      {rec.actions?.map((action, actionIdx) => (
                        <li key={actionIdx}>{action}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
```

---

## TASK 13: ANALYTICS COMPONENTS

### 13.1 KPI Card Component

**File:** `frontend/src/components/analytics/KPICard.jsx`

```jsx
/**
 * KPI Card Component
 * Displays a single KPI with trend indicator
 */

import React from 'react';
import TrendIndicator from './TrendIndicator';

const KPICard = ({ 
  title, 
  value, 
  change, 
  trend, 
  target,
  status,
  icon, 
  color = 'blue',
  invertTrend = false 
}) => {
  const getTrendClass = () => {
    if (!trend) return '';
    if (invertTrend) {
      return trend === 'up' ? 'negative' : (trend === 'down' ? 'positive' : '');
    }
    return trend === 'up' ? 'positive' : (trend === 'down' ? 'negative' : '');
  };

  const formatChange = (val) => {
    if (val === undefined || val === null) return null;
    const sign = val >= 0 ? '+' : '';
    return `${sign}${val.toFixed(1)}%`;
  };

  return (
    <div className={`kpi-card color-${color}`}>
      <div className="kpi-header">
        <span className="kpi-icon">{icon}</span>
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-body">
        <span className="kpi-value">{value}</span>
        {change !== undefined && change !== null && (
          <span className={`kpi-change ${getTrendClass()}`}>
            {trend === 'up' && '↑'}
            {trend === 'down' && '↓'}
            {trend === 'stable' && '→'}
            {formatChange(change)}
          </span>
        )}
      </div>
      {target && (
        <div className="kpi-footer">
          <span className="kpi-target">{target}</span>
          {status && <TrendIndicator status={status} size="small" />}
        </div>
      )}
    </div>
  );
};

export default KPICard;
```

### 13.2 Health Score Gauge Component

**File:** `frontend/src/components/analytics/HealthScoreGauge.jsx`

```jsx
/**
 * Health Score Gauge Component
 * Visual gauge display for financial health score
 */

import React from 'react';

const HealthScoreGauge = ({ score, grade, category }) => {
  const getScoreColor = () => {
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 60) return '#3b82f6'; // Blue
    if (score >= 40) return '#f59e0b'; // Yellow
    if (score >= 20) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="health-score-gauge">
      <svg viewBox="0 0 100 100" className="gauge-svg">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
        />
        {/* Score arc */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={getScoreColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
        {/* Score text */}
        <text
          x="50"
          y="45"
          textAnchor="middle"
          className="score-value"
          fill={getScoreColor()}
        >
          {score}
        </text>
        <text
          x="50"
          y="58"
          textAnchor="middle"
          className="score-grade"
        >
          Grade: {grade}
        </text>
      </svg>
      <div className="score-category">
        <span className={`category-badge ${category?.toLowerCase()}`}>
          {category}
        </span>
      </div>
    </div>
  );
};

export default HealthScoreGauge;
```

### 13.3 Trend Indicator Component

**File:** `frontend/src/components/analytics/TrendIndicator.jsx`

```jsx
/**
 * Trend Indicator Component
 * Visual status indicator for KPIs
 */

import React from 'react';

const TrendIndicator = ({ status, size = 'medium' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'good':
      case 'excellent':
        return { icon: '✓', color: 'green', label: 'Good' };
      case 'warning':
      case 'fair':
        return { icon: '!', color: 'yellow', label: 'Warning' };
      case 'critical':
      case 'poor':
        return { icon: '✕', color: 'red', label: 'Critical' };
      default:
        return { icon: '–', color: 'gray', label: 'N/A' };
    }
  };

  const config = getStatusConfig();

  return (
    <span 
      className={`trend-indicator ${config.color} ${size}`}
      title={config.label}
    >
      {config.icon}
    </span>
  );
};

export default TrendIndicator;
```

### 13.4 Insight Card Component

**File:** `frontend/src/components/analytics/InsightCard.jsx`

```jsx
/**
 * Insight Card Component
 * Displays AI-generated business insights
 */

import React from 'react';

const InsightCard = ({ icon, title, detail, type }) => {
  return (
    <div className={`insight-card type-${type}`}>
      <span className="insight-icon">{icon}</span>
      <div className="insight-content">
        <h4 className="insight-title">{title}</h4>
        <p className="insight-detail">{detail}</p>
      </div>
    </div>
  );
};

export default InsightCard;
```

---

## TASK 14: ANALYTICS STYLES

### 14.1 Create Analytics Stylesheet

**File:** `frontend/src/styles/analytics.css`

```css
/**
 * Analytics Dashboard Styles
 * Professional enterprise styling for ML analytics
 */

/* ============================================
   VARIABLES
   ============================================ */
:root {
  --analytics-primary: #3b82f6;
  --analytics-success: #22c55e;
  --analytics-warning: #f59e0b;
  --analytics-danger: #ef4444;
  --analytics-purple: #8b5cf6;
  --analytics-bg: #f8fafc;
  --analytics-card-bg: #ffffff;
  --analytics-border: #e2e8f0;
  --analytics-text: #1e293b;
  --analytics-text-muted: #64748b;
}

/* ============================================
   LAYOUT
   ============================================ */
.analytics-dashboard {
  padding: 24px;
  background: var(--analytics-bg);
  min-height: 100vh;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.analytics-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--analytics-text);
  margin: 0;
}

.analytics-header .subtitle {
  color: var(--analytics-text-muted);
  font-size: 14px;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* ============================================
   TABS
   ============================================ */
.analytics-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--analytics-border);
  padding-bottom: 8px;
}

.analytics-tabs .tab {
  padding: 10px 20px;
  border: none;
  background: none;
  color: var(--analytics-text-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.analytics-tabs .tab:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--analytics-primary);
}

.analytics-tabs .tab.active {
  background: var(--analytics-primary);
  color: white;
}

/* ============================================
   ROWS
   ============================================ */
.analytics-row {
  margin-bottom: 24px;
}

.health-kpis-row {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.secondary-kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .health-kpis-row {
    grid-template-columns: 1fr;
  }
  
  .charts-row {
    grid-template-columns: 1fr;
  }
  
  .secondary-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .secondary-kpis {
    grid-template-columns: 1fr;
  }
}

/* ============================================
   HEALTH SCORE CARD
   ============================================ */
.health-score-card {
  background: var(--analytics-card-bg);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.health-score-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 16px 0;
  text-align: center;
}

.health-score-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gauge-svg {
  width: 160px;
  height: 160px;
}

.gauge-svg .score-value {
  font-size: 24px;
  font-weight: 700;
}

.gauge-svg .score-grade {
  font-size: 10px;
  fill: var(--analytics-text-muted);
}

.score-category {
  margin-top: 12px;
}

.category-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.category-badge.excellent { background: #dcfce7; color: #166534; }
.category-badge.good { background: #dbeafe; color: #1e40af; }
.category-badge.fair { background: #fef3c7; color: #92400e; }
.category-badge.poor { background: #fed7aa; color: #9a3412; }
.category-badge.critical { background: #fee2e2; color: #991b1b; }

.health-recommendations {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--analytics-border);
}

.health-recommendations h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 8px 0;
}

.health-recommendations ul {
  margin: 0;
  padding: 0 0 0 16px;
  font-size: 12px;
  color: var(--analytics-text-muted);
}

.health-recommendations li {
  margin-bottom: 4px;
}

/* ============================================
   KPI CARDS
   ============================================ */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.kpi-card {
  background: var(--analytics-card-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid var(--analytics-primary);
}

.kpi-card.color-green { border-left-color: var(--analytics-success); }
.kpi-card.color-red { border-left-color: var(--analytics-danger); }
.kpi-card.color-blue { border-left-color: var(--analytics-primary); }
.kpi-card.color-purple { border-left-color: var(--analytics-purple); }

.kpi-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.kpi-icon {
  font-size: 20px;
}

.kpi-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--analytics-text-muted);
}

.kpi-body {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--analytics-text);
}

.kpi-change {
  font-size: 13px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
}

.kpi-change.positive {
  color: var(--analytics-success);
  background: rgba(34, 197, 94, 0.1);
}

.kpi-change.negative {
  color: var(--analytics-danger);
  background: rgba(239, 68, 68, 0.1);
}

.kpi-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--analytics-border);
}

.kpi-target {
  font-size: 12px;
  color: var(--analytics-text-muted);
}

/* ============================================
   MINI KPI CARDS
   ============================================ */
.kpi-card-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--analytics-card-bg);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-card-mini .icon {
  font-size: 24px;
}

.kpi-card-mini .content {
  flex: 1;
}

.kpi-card-mini .label {
  display: block;
  font-size: 12px;
  color: var(--analytics-text-muted);
}

.kpi-card-mini .value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: var(--analytics-text);
}

/* ============================================
   TREND INDICATOR
   ============================================ */
.trend-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.trend-indicator.small {
  width: 20px;
  height: 20px;
  font-size: 10px;
}

.trend-indicator.green { background: #dcfce7; color: #166534; }
.trend-indicator.yellow { background: #fef3c7; color: #92400e; }
.trend-indicator.red { background: #fee2e2; color: #991b1b; }
.trend-indicator.gray { background: #f1f5f9; color: #64748b; }

/* ============================================
   CHART CARDS
   ============================================ */
.chart-card {
  background: var(--analytics-card-bg);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--analytics-text-muted);
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.blue { background: rgb(59, 130, 246); }
.dot.green { background: rgb(34, 197, 94); }
.dot.red { background: rgb(239, 68, 68); }

.chart-container {
  height: 300px;
}

.chart-container.doughnut {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-footer {
  display: flex;
  justify-content: space-around;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--analytics-border);
}

.forecast-stat {
  text-align: center;
}

.forecast-stat .label {
  display: block;
  font-size: 12px;
  color: var(--analytics-text-muted);
  margin-bottom: 4px;
}

.forecast-stat .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--analytics-text);
}

/* ============================================
   INSIGHTS
   ============================================ */
.insights-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.insights-summary {
  background: var(--analytics-card-bg);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-badge {
  display: inline-block;
  padding: 8px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.summary-badge.excellent { background: #dcfce7; color: #166534; }
.summary-badge.good { background: #dbeafe; color: #1e40af; }
.summary-badge.fair { background: #fef3c7; color: #92400e; }
.summary-badge.concerning { background: #fed7aa; color: #9a3412; }
.summary-badge.critical { background: #fee2e2; color: #991b1b; }

.summary-message {
  font-size: 16px;
  color: var(--analytics-text);
  margin: 0;
}

.insights-section {
  background: var(--analytics-card-bg);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.insights-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 16px 0;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.insight-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--analytics-bg);
  border-radius: 12px;
  border-left: 3px solid var(--analytics-primary);
}

.insight-icon {
  font-size: 24px;
}

.insight-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 4px 0;
}

.insight-detail {
  font-size: 13px;
  color: var(--analytics-text-muted);
  margin: 0;
}

/* Opportunities */
.opportunities-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.opportunity-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(34, 197, 94, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.opp-icon {
  font-size: 28px;
}

.opp-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 4px 0;
}

.opp-content p {
  font-size: 13px;
  color: var(--analytics-text-muted);
  margin: 0 0 8px 0;
}

.impact-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--analytics-success);
  color: white;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
}

/* Risks */
.risks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  align-items: flex-start;
}

.risk-card.high,
.risk-card.critical {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.risk-card.medium {
  background: rgba(245, 158, 11, 0.05);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.risk-icon {
  font-size: 28px;
}

.risk-content {
  flex: 1;
}

.risk-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 4px 0;
}

.risk-content p {
  font-size: 13px;
  color: var(--analytics-text-muted);
  margin: 0 0 8px 0;
}

.action-text {
  font-size: 12px;
  color: var(--analytics-primary);
  font-weight: 500;
}

.severity-badge {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.severity-badge.high,
.severity-badge.critical {
  background: var(--analytics-danger);
  color: white;
}

.severity-badge.medium {
  background: var(--analytics-warning);
  color: white;
}

/* Recommendations */
.recommendations-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.recommendation-card {
  padding: 20px;
  border-radius: 12px;
  background: var(--analytics-bg);
  border-left: 4px solid var(--analytics-primary);
}

.recommendation-card.high {
  border-left-color: var(--analytics-danger);
}

.recommendation-card.medium {
  border-left-color: var(--analytics-warning);
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.priority-badge {
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.priority-badge.high { background: #fee2e2; color: #991b1b; }
.priority-badge.medium { background: #fef3c7; color: #92400e; }
.priority-badge.low { background: #dbeafe; color: #1e40af; }

.rec-header .category {
  font-size: 12px;
  color: var(--analytics-text-muted);
}

.recommendation-card h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--analytics-text);
  margin: 0 0 12px 0;
}

.action-list {
  margin: 0;
  padding: 0 0 0 16px;
  font-size: 13px;
  color: var(--analytics-text-muted);
}

.action-list li {
  margin-bottom: 4px;
}

/* ============================================
   LOADING & ERROR STATES
   ============================================ */
.analytics-loading,
.analytics-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.analytics-loading p {
  margin-top: 16px;
  color: var(--analytics-text-muted);
}

.analytics-error .error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.analytics-error h3 {
  color: var(--analytics-danger);
  margin: 0 0 8px 0;
}

.analytics-error p {
  color: var(--analytics-text-muted);
  margin: 0 0 16px 0;
}

/* ============================================
   BUTTONS
   ============================================ */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-primary {
  background: var(--analytics-primary);
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-outline {
  background: white;
  color: var(--analytics-text);
  border: 1px solid var(--analytics-border);
}

.btn-outline:hover {
  background: var(--analytics-bg);
  border-color: var(--analytics-primary);
  color: var(--analytics-primary);
}

.btn .icon {
  font-size: 16px;
}
```

---

## TASK 15: NAVIGATION UPDATE

### 15.1 Update App Router

**Update:** `frontend/src/App.jsx`

```jsx
// Add import
import AnalyticsDashboard from './pages/AnalyticsDashboard';

// Add route inside Routes
<Route path="/analytics" element={<PrivateRoute><AnalyticsDashboard /></PrivateRoute>} />
```

### 15.2 Update Sidebar Navigation

**Update:** `frontend/src/components/layout/Sidebar.jsx`

```jsx
// Add to navigation items (admin only)
{
  path: '/analytics',
  icon: '📊',
  label: t('nav.analytics'),
  roles: ['admin']
}
```

### 15.3 Update Translations

**Update:** `frontend/src/i18n/translations/en.js`

```javascript
// Add to nav section
analytics: 'Analytics',

// Add analytics section
analytics: {
  dashboard: 'Analytics Dashboard',
  healthScore: 'Health Score',
  forecasting: 'Forecasting',
  insights: 'AI Insights',
  trends: 'Trend Analysis',
  scenarios: 'Scenario Planning',
  customers: 'Customer Analytics',
  inventory: 'Inventory Analytics',
  export: 'Export Report'
}
```

---

## ✅ PHASE 10 COMPLETE CHECKLIST

| Component | Status |
|-----------|--------|
| Analytics Package Init | ✅ |
| Forecasting Engine | ✅ |
| KPI Calculator | ✅ |
| Revenue Analytics | ✅ |
| Customer Analytics (RFM/CLV) | ✅ |
| Inventory Analytics | ✅ |
| Trend Analyzer | ✅ |
| Scenario Planner | ✅ |
| Insights Generator | ✅ |
| Analytics API Routes | ✅ |
| Frontend API Service | ✅ |
| Analytics Dashboard Page | ✅ |
| KPI Card Component | ✅ |
| Health Score Gauge | ✅ |
| Trend Indicator | ✅ |
| Insight Card | ✅ |
| Analytics Styles | ✅ |
| Navigation Update | ✅ |

---

*Phase 10 Tasks Part 3 - LogiAccounting Pro*
*API Routes & Frontend Components*
*Advanced Analytics & ML Forecasting*
