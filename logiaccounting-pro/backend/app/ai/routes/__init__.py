"""
AI Routes
"""

from .cashflow import router as cashflow_router
from .invoice import router as invoice_router
from .assistant import router as assistant_router
from .payments import router as payments_router
from .anomaly import router as anomaly_router
from .usage import router as usage_router

__all__ = [
    'cashflow_router',
    'invoice_router',
    'assistant_router',
    'payments_router',
    'anomaly_router',
    'usage_router',
]
