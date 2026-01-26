"""
Fixed Assets & Depreciation Module.

This module provides comprehensive fixed asset management including:
- Asset categories with depreciation profiles
- Fixed asset register
- Multiple depreciation methods (Straight-line, Declining Balance, etc.)
- Asset lifecycle management (acquisition, depreciation, disposal)
- Batch depreciation processing
- GL integration
"""
from app.fixed_assets.routes import router

__all__ = ["router"]
