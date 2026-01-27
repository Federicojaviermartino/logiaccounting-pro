"""
AI Base Classes
Base classes and data structures for AI features
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from uuid import uuid4


class PredictionConfidence(str, Enum):
    """Confidence levels for predictions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AIResult:
    """Standard result container for AI operations."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    processing_time_ms: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None

    @classmethod
    def ok(cls, data: Any, **kwargs) -> "AIResult":
        """Create successful result."""
        return cls(success=True, data=data, **kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs) -> "AIResult":
        """Create failed result."""
        return cls(success=False, error=error, **kwargs)


@dataclass
class Prediction:
    """Base prediction result."""
    id: str = field(default_factory=lambda: f"pred_{uuid4().hex[:12]}")
    value: float = 0.0
    confidence: float = 0.0
    confidence_level: PredictionConfidence = PredictionConfidence.MEDIUM
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    features_used: List[str] = field(default_factory=list)
    model_version: str = "1.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "value": self.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "timestamp": self.timestamp.isoformat(),
            "features_used": self.features_used,
            "model_version": self.model_version,
        }


@dataclass
class Anomaly:
    """Detected anomaly."""
    id: str = field(default_factory=lambda: f"anom_{uuid4().hex[:12]}")
    type: str = "unknown"
    severity: AlertSeverity = AlertSeverity.MEDIUM
    score: float = 0.0
    description: str = ""
    entity_type: str = ""
    entity_id: str = ""
    details: Dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    recommended_action: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity.value,
            "score": self.score,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "detected_at": self.detected_at.isoformat(),
            "recommended_action": self.recommended_action,
        }


@dataclass
class Recommendation:
    """AI-generated recommendation."""
    id: str = field(default_factory=lambda: f"rec_{uuid4().hex[:12]}")
    type: str = ""
    title: str = ""
    description: str = ""
    priority: int = 5
    confidence: float = 0.0
    potential_impact: Optional[str] = None
    actions: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "potential_impact": self.potential_impact,
            "actions": self.actions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# ==================== Abstract Base Classes ====================

class BasePredictor(ABC):
    """Base class for predictors."""

    @abstractmethod
    async def train(self, data: List[Dict], **kwargs) -> AIResult:
        """Train the model."""
        pass

    @abstractmethod
    async def predict(self, **kwargs) -> AIResult:
        """Make predictions."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """Get model information."""
        pass


class BaseDetector(ABC):
    """Base class for anomaly detectors."""

    @abstractmethod
    async def detect(self, data: Union[Dict, List[Dict]], **kwargs) -> List[Anomaly]:
        """Detect anomalies."""
        pass

    @abstractmethod
    async def train(self, data: List[Dict], **kwargs) -> AIResult:
        """Train detection model."""
        pass


class BaseExtractor(ABC):
    """Base class for data extractors."""

    @abstractmethod
    async def extract(self, data: bytes, **kwargs) -> AIResult:
        """Extract data from input."""
        pass


class BaseAssistant(ABC):
    """Base class for AI assistants."""

    @abstractmethod
    async def process_message(self, message: str, context: Dict = None, **kwargs) -> str:
        """Process a message and generate response."""
        pass

    @abstractmethod
    async def get_suggestions(self, context: Dict = None, **kwargs) -> List[str]:
        """Get suggested queries."""
        pass
