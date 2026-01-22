"""
Structured logging configuration with correlation IDs.
"""
import logging
import sys
import json
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None


_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_tenant_id: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class LogContext:
    """
    Context manager for adding context to log messages.

    Usage:
        with LogContext(request_id="abc123", user_id="user-1"):
            logger.info("Processing request")
    """

    def __init__(self, **kwargs):
        self.context = kwargs
        self._token = None

    def __enter__(self):
        current = _log_context.get().copy()
        current.update(self.context)
        self._token = _log_context.set(current)

        if 'correlation_id' in self.context:
            _correlation_id.set(self.context['correlation_id'])
        if 'tenant_id' in self.context:
            _tenant_id.set(self.context['tenant_id'])
        if 'user_id' in self.context:
            _user_id.set(self.context['user_id'])

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            _log_context.reset(self._token)
        return False


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_id.get()


def get_tenant_id() -> Optional[str]:
    """Get current tenant ID."""
    return _tenant_id.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return _user_id.get()


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    _correlation_id.set(correlation_id)


def set_tenant_id(tenant_id: str):
    """Set tenant ID for current context."""
    _tenant_id.set(tenant_id)


def set_user_id(user_id: str):
    """Set user ID for current context."""
    _user_id.set(user_id)


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    """

    def __init__(self, service_name: str = "logiaccounting-pro"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        if _correlation_id.get():
            log_entry["correlation_id"] = _correlation_id.get()

        if _tenant_id.get():
            log_entry["tenant_id"] = _tenant_id.get()

        if _user_id.get():
            log_entry["user_id"] = _user_id.get()

        context = _log_context.get()
        if context:
            log_entry["context"] = context

        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        log_entry["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }

        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """
    Wrapper for structured logging with automatic context injection.

    Usage:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id="user-123", action="login")
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context injection."""
        extra = {'extra_fields': kwargs}

        if _correlation_id.get():
            extra['extra_fields']['correlation_id'] = _correlation_id.get()
        if _tenant_id.get():
            extra['extra_fields']['tenant_id'] = _tenant_id.get()
        if _user_id.get():
            extra['extra_fields']['user_id'] = _user_id.get()

        context = _log_context.get()
        if context:
            extra['extra_fields'].update(context)

        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        if exc_info:
            kwargs['exc_info'] = sys.exc_info()
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        if exc_info:
            kwargs['exc_info'] = sys.exc_info()
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = sys.exc_info()
        self._log(logging.ERROR, message, **kwargs)


def setup_logging(
    service_name: str = "logiaccounting-pro",
    log_level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure structured logging.

    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for logs
        log_file: Optional file path for file logging
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if json_format:
        console_handler.setFormatter(JSONFormatter(service_name))
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(JSONFormatter(service_name))
        root_logger.addHandler(file_handler)

    if STRUCTLOG_AVAILABLE:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def log_function_call(logger: Optional[StructuredLogger] = None, level: str = "debug"):
    """
    Decorator to log function calls.

    Usage:
        @log_function_call(logger, level="info")
        async def process_invoice(invoice_id: str):
            ...
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            log_method = getattr(logger, level)
            log_method(
                f"Calling {func.__name__}",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )

            try:
                result = await func(*args, **kwargs)
                log_method(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}",
                    function=func.__name__,
                    error=str(e),
                    exc_info=True
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            log_method = getattr(logger, level)
            log_method(
                f"Calling {func.__name__}",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )

            try:
                result = func(*args, **kwargs)
                log_method(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    f"Error in {func.__name__}",
                    function=func.__name__,
                    error=str(e),
                    exc_info=True
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class LoggingMiddleware:
    """
    ASGI middleware for request logging.
    """

    def __init__(
        self,
        app,
        logger: Optional[StructuredLogger] = None,
        excluded_paths: list = None
    ):
        self.app = app
        self.logger = logger or get_logger("http")
        self.excluded_paths = excluded_paths or ["/health", "/ready", "/metrics"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            await self.app(scope, receive, send)
            return

        import time
        import uuid

        start_time = time.perf_counter()
        correlation_id = None
        method = scope.get("method", "UNKNOWN")

        headers = dict(scope.get("headers", []))

        correlation_id = headers.get(b"x-correlation-id", b"").decode()
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        tenant_id = headers.get(b"x-tenant-id", b"").decode()
        user_agent = headers.get(b"user-agent", b"").decode()

        set_correlation_id(correlation_id)
        if tenant_id:
            set_tenant_id(tenant_id)

        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)

                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = response_headers

            await send(message)

        try:
            self.logger.info(
                f"Request started: {method} {path}",
                method=method,
                path=path,
                user_agent=user_agent
            )

            await self.app(scope, receive, send_wrapper)

        except Exception as e:
            self.logger.error(
                f"Request error: {method} {path}",
                method=method,
                path=path,
                error=str(e),
                exc_info=True
            )
            raise

        finally:
            duration = time.perf_counter() - start_time
            duration_ms = round(duration * 1000, 2)

            log_level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
            log_method = getattr(self.logger, log_level)

            log_method(
                f"Request completed: {method} {path}",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms
            )


class AuditLogger:
    """
    Specialized logger for audit trail.
    """

    def __init__(self, service_name: str = "logiaccounting-pro"):
        self.logger = get_logger("audit")
        self.service_name = service_name

    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an auditable action."""
        self.logger.info(
            f"Audit: {action} on {entity_type}",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id or get_user_id(),
            tenant_id=tenant_id or get_tenant_id(),
            changes=changes,
            metadata=metadata,
            audit=True
        )

    def log_login(self, user_id: str, tenant_id: str, ip_address: str, success: bool):
        """Log login attempt."""
        self.logger.info(
            f"Login {'successful' if success else 'failed'}",
            action="login",
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            success=success,
            audit=True
        )

    def log_data_access(
        self,
        entity_type: str,
        entity_ids: list,
        access_type: str = "read"
    ):
        """Log data access."""
        self.logger.info(
            f"Data access: {access_type} {entity_type}",
            action=f"data_{access_type}",
            entity_type=entity_type,
            entity_count=len(entity_ids),
            user_id=get_user_id(),
            tenant_id=get_tenant_id(),
            audit=True
        )


audit_logger = AuditLogger()
