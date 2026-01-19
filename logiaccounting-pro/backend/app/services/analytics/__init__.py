"""
Analytics Module for LogiAccounting Pro
Provides business intelligence and advanced analytics
"""

from .inventory_analytics import InventoryAnalytics
from .trend_analyzer import TrendAnalyzer
from .scenario_planner import ScenarioPlanner
from .insights_generator import InsightsGenerator
from .kpi_calculator import KPICalculator

__all__ = [
    'InventoryAnalytics',
    'TrendAnalyzer',
    'ScenarioPlanner',
    'InsightsGenerator',
    'KPICalculator'
]
