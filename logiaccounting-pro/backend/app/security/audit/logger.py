"""
Audit logging service for LogiAccounting Pro.
"""

import logging
import json
import asyncio
from typing import Optional, Dict, List, Any, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field
from queue import Queue
from threading import Thread, Lock
from contextlib import contextmanager

from .events import (
    AuditEvent,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    AuditCategory,
    AuditActor,
    AuditTarget,
    AuditChanges,
)


@dataclass
class AuditLoggerConfig:
    """Configuration for the audit logger."""

    enabled: bool = True
    async_logging: bool = True
    batch_size: int = 100
    flush_interval_seconds: int = 5
    log_to_file: bool = True
    log_to_console: bool = False
    log_file_path: str = "logs/audit.log"
    include_debug_events: bool = False
    sensitive_fields: Set[str] = field(default_factory=lambda: {
        "password", "secret", "token", "api_key", "credit_card",
        "ssn", "social_security", "bank_account"
    })
    redaction_string: str = "[REDACTED]"
    max_detail_size: int = 10000


class AuditLogger:
    """Central audit logging service."""

    def __init__(self, config: Optional[AuditLoggerConfig] = None):
        self._config = config or AuditLoggerConfig()
        self._handlers: List[Callable[[AuditEvent], None]] = []
        self._async_handlers: List[Callable[[AuditEvent], Any]] = []
        self._event_queue: Queue = Queue()
        self._batch: List[AuditEvent] = []
        self._batch_lock = Lock()
        self._context_stack: List[Dict[str, Any]] = []
        self._running = False
        self._worker_thread: Optional[Thread] = None

        self._setup_default_handler()

        if self._config.async_logging:
            self._start_worker()

    def _setup_default_handler(self) -> None:
        """Set up the default file/console handler."""
        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.DEBUG if self._config.include_debug_events else logging.INFO)

        if self._config.log_to_file:
            import os
            os.makedirs(os.path.dirname(self._config.log_file_path), exist_ok=True)
            file_handler = logging.FileHandler(self._config.log_file_path)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self._logger.addHandler(file_handler)

        if self._config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            ))
            self._logger.addHandler(console_handler)

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._running = True
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Background worker to process audit events."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=self._config.flush_interval_seconds)
                self._process_event(event)

                with self._batch_lock:
                    self._batch.append(event)
                    if len(self._batch) >= self._config.batch_size:
                        self._flush_batch()

            except Exception:
                with self._batch_lock:
                    if self._batch:
                        self._flush_batch()

    def _process_event(self, event: AuditEvent) -> None:
        """Process a single audit event."""
        event_dict = self._sanitize_event(event.to_dict())
        log_level = self._get_log_level(event.severity)
        self._logger.log(log_level, json.dumps(event_dict))

        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Handler error: {e}")

    def _flush_batch(self) -> None:
        """Flush the current batch of events."""
        if not self._batch:
            return

        batch_to_flush = self._batch.copy()
        self._batch.clear()

        for handler in self._async_handlers:
            try:
                handler(batch_to_flush)
            except Exception as e:
                self._logger.error(f"Async handler error: {e}")

    def _sanitize_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data in event."""
        return self._redact_sensitive_fields(event_dict)

    def _redact_sensitive_fields(self, data: Any, path: str = "") -> Any:
        """Recursively redact sensitive fields."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                full_path = f"{path}.{key}" if path else key
                if any(sensitive in key.lower() for sensitive in self._config.sensitive_fields):
                    result[key] = self._config.redaction_string
                else:
                    result[key] = self._redact_sensitive_fields(value, full_path)
            return result
        elif isinstance(data, list):
            return [self._redact_sensitive_fields(item, path) for item in data]
        elif isinstance(data, str) and len(data) > self._config.max_detail_size:
            return data[:self._config.max_detail_size] + "...[TRUNCATED]"
        return data

    def _get_log_level(self, severity: AuditSeverity) -> int:
        """Map audit severity to logging level."""
        mapping = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.NOTICE: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
            AuditSeverity.ALERT: logging.CRITICAL,
            AuditSeverity.EMERGENCY: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)

    def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
        if not self._config.enabled:
            return

        if event.severity == AuditSeverity.DEBUG and not self._config.include_debug_events:
            return

        context = self._get_merged_context()
        if context:
            event.metadata.update(context)

        if self._config.async_logging:
            self._event_queue.put(event)
        else:
            self._process_event(event)

    def log_auth(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an authentication event."""
        actor = AuditActor(
            user_id=user_id,
            email=email,
            ip_address=ip_address,
        )

        severity = AuditSeverity.INFO
        if outcome == AuditOutcome.FAILURE:
            severity = AuditSeverity.WARNING

        event = AuditEvent(
            event_type=event_type,
            outcome=outcome,
            severity=severity,
            category=AuditCategory.AUTHENTICATION,
            actor=actor,
            action=event_type.value.split(".")[-1],
            details=details or {},
        )
        self.log(event)

    def log_data_access(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: AuditActor,
        changes: Optional[AuditChanges] = None,
        entity_name: Optional[str] = None,
    ) -> None:
        """Log a data access or modification event."""
        event_type_map = {
            "create": AuditEventType.ENTITY_CREATED,
            "read": AuditEventType.ENTITY_READ,
            "update": AuditEventType.ENTITY_UPDATED,
            "delete": AuditEventType.ENTITY_DELETED,
            "export": AuditEventType.ENTITY_EXPORTED,
        }
        event_type = event_type_map.get(action, AuditEventType.DATA_ACCESSED)

        target = AuditTarget(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            organization_id=actor.organization_id,
        )

        category = AuditCategory.DATA_ACCESS
        if action in ("create", "update", "delete"):
            category = AuditCategory.DATA_MODIFICATION

        event = AuditEvent(
            event_type=event_type,
            category=category,
            actor=actor,
            target=target,
            changes=changes,
            action=action,
        )
        self.log(event)

    def log_security(
        self,
        event_type: AuditEventType,
        message: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        actor: Optional[AuditActor] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a security event."""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            category=AuditCategory.SECURITY,
            actor=actor,
            message=message,
            details=details or {},
        )
        self.log(event)

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: int,
        actor: Optional[AuditActor] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log an API request."""
        outcome = AuditOutcome.SUCCESS if status_code < 400 else AuditOutcome.FAILURE
        severity = AuditSeverity.INFO
        if status_code >= 500:
            severity = AuditSeverity.ERROR
        elif status_code >= 400:
            severity = AuditSeverity.WARNING

        event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            outcome=outcome,
            severity=severity,
            category=AuditCategory.SYSTEM,
            actor=actor,
            action=f"{method} {path}",
            details={
                "method": method,
                "path": path,
                "status_code": status_code,
            },
            duration_ms=duration_ms,
            request_id=request_id,
        )
        self.log(event)

    def add_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """Add a synchronous event handler."""
        self._handlers.append(handler)

    def add_async_handler(self, handler: Callable[[List[AuditEvent]], None]) -> None:
        """Add an asynchronous batch handler."""
        self._async_handlers.append(handler)

    def remove_handler(self, handler: Callable) -> bool:
        """Remove a handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True
        if handler in self._async_handlers:
            self._async_handlers.remove(handler)
            return True
        return False

    @contextmanager
    def context(self, **kwargs):
        """Add context to all events logged within the block."""
        self._context_stack.append(kwargs)
        try:
            yield
        finally:
            self._context_stack.pop()

    def _get_merged_context(self) -> Dict[str, Any]:
        """Get merged context from all stack levels."""
        merged = {}
        for ctx in self._context_stack:
            merged.update(ctx)
        return merged

    def flush(self) -> None:
        """Force flush all pending events."""
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                self._process_event(event)
                with self._batch_lock:
                    self._batch.append(event)
            except Exception:
                break

        with self._batch_lock:
            self._flush_batch()

    def shutdown(self) -> None:
        """Shutdown the audit logger."""
        self._running = False
        self.flush()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = logger


def log_event(event: AuditEvent) -> None:
    """Log an audit event using the global logger."""
    get_audit_logger().log(event)


def log_auth(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an authentication event using the global logger."""
    get_audit_logger().log_auth(
        event_type=event_type,
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        outcome=outcome,
        details=details,
    )
