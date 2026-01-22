"""
Distributed tracing with OpenTelemetry.
"""
import logging
import functools
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.propagate import extract, inject
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    TracerProvider = None


_current_trace_id: ContextVar[Optional[str]] = ContextVar('current_trace_id', default=None)
_current_span_id: ContextVar[Optional[str]] = ContextVar('current_span_id', default=None)

_tracer: Optional[Any] = None


def setup_tracing(
    service_name: str = "logiaccounting-pro",
    otlp_endpoint: str = "http://localhost:4317",
    environment: str = "development",
    sample_rate: float = 1.0
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing
        otlp_endpoint: OTLP collector endpoint
        environment: Environment name
        sample_rate: Sampling rate (0.0 to 1.0)
    """
    global _tracer

    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available, tracing disabled")
        return False

    try:
        resource = Resource.create({
            SERVICE_NAME: service_name,
            "deployment.environment": environment,
            "service.version": "1.0.0",
        })

        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)

        logger.info(f"Tracing initialized: {service_name} -> {otlp_endpoint}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return False


def instrument_fastapi(app: Any) -> bool:
    """Instrument FastAPI application."""
    if not OPENTELEMETRY_AVAILABLE:
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")
        return False


def instrument_sqlalchemy(engine: Any) -> bool:
    """Instrument SQLAlchemy engine."""
    if not OPENTELEMETRY_AVAILABLE:
        return False

    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumented for tracing")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")
        return False


def instrument_redis(client: Any) -> bool:
    """Instrument Redis client."""
    if not OPENTELEMETRY_AVAILABLE:
        return False

    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented for tracing")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument Redis: {e}")
        return False


def instrument_httpx() -> bool:
    """Instrument HTTPX client."""
    if not OPENTELEMETRY_AVAILABLE:
        return False

    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented for tracing")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument HTTPX: {e}")
        return False


def get_tracer(name: str = "logiaccounting-pro") -> Any:
    """Get or create a tracer instance."""
    global _tracer

    if not OPENTELEMETRY_AVAILABLE:
        return None

    if _tracer is None:
        _tracer = trace.get_tracer(name)

    return _tracer


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    if not OPENTELEMETRY_AVAILABLE:
        return _current_trace_id.get()

    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, '032x')

    return _current_trace_id.get()


def get_current_span_id() -> Optional[str]:
    """Get the current span ID."""
    if not OPENTELEMETRY_AVAILABLE:
        return _current_span_id.get()

    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, '016x')

    return _current_span_id.get()


def set_span_attribute(key: str, value: Any):
    """Set attribute on current span."""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def set_span_status(success: bool, message: str = ""):
    """Set status on current span."""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        if success:
            span.set_status(Status(StatusCode.OK, message))
        else:
            span.set_status(Status(StatusCode.ERROR, message))


def add_span_event(name: str, attributes: Dict[str, Any] = None):
    """Add event to current span."""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def trace_span(
    name: str = None,
    kind: str = "internal",
    attributes: Dict[str, Any] = None
) -> Callable:
    """
    Decorator to create a span for a function.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind (internal, server, client, producer, consumer)
        attributes: Additional span attributes

    Usage:
        @trace_span("process_invoice", attributes={"invoice.type": "standard"})
        async def process_invoice(invoice_id: str):
            ...
    """
    span_kinds = {
        "internal": SpanKind.INTERNAL if OPENTELEMETRY_AVAILABLE else None,
        "server": SpanKind.SERVER if OPENTELEMETRY_AVAILABLE else None,
        "client": SpanKind.CLIENT if OPENTELEMETRY_AVAILABLE else None,
        "producer": SpanKind.PRODUCER if OPENTELEMETRY_AVAILABLE else None,
        "consumer": SpanKind.CONSUMER if OPENTELEMETRY_AVAILABLE else None,
    }

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not OPENTELEMETRY_AVAILABLE:
                return await func(*args, **kwargs)

            tracer = get_tracer()
            if tracer is None:
                return await func(*args, **kwargs)

            with tracer.start_as_current_span(
                span_name,
                kind=span_kinds.get(kind, SpanKind.INTERNAL),
                attributes=attributes or {}
            ) as span:
                try:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not OPENTELEMETRY_AVAILABLE:
                return func(*args, **kwargs)

            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)

            with tracer.start_as_current_span(
                span_name,
                kind=span_kinds.get(kind, SpanKind.INTERNAL),
                attributes=attributes or {}
            ) as span:
                try:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)

                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class TracingMiddleware:
    """
    ASGI middleware for distributed tracing.
    """

    def __init__(
        self,
        app,
        service_name: str = "logiaccounting-pro",
        excluded_paths: list = None
    ):
        self.app = app
        self.service_name = service_name
        self.excluded_paths = excluded_paths or ["/health", "/ready", "/metrics"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            await self.app(scope, receive, send)
            return

        if not OPENTELEMETRY_AVAILABLE:
            await self.app(scope, receive, send)
            return

        tracer = get_tracer(self.service_name)
        if tracer is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        carrier = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in headers.items()
        }

        ctx = extract(carrier)

        method = scope.get("method", "UNKNOWN")
        span_name = f"{method} {path}"

        with tracer.start_as_current_span(
            span_name,
            context=ctx,
            kind=SpanKind.SERVER,
            attributes={
                "http.method": method,
                "http.url": path,
                "http.scheme": scope.get("scheme", "http"),
                "http.host": headers.get(b"host", b"").decode() if b"host" in headers else "",
                "http.user_agent": headers.get(b"user-agent", b"").decode() if b"user-agent" in headers else "",
            }
        ) as span:
            status_code = 500

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                    span.set_attribute("http.status_code", status_code)

                    if status_code >= 400:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
                    else:
                        span.set_status(Status(StatusCode.OK))

                await send(message)

            try:
                tenant_id = headers.get(b"x-tenant-id", b"").decode() if b"x-tenant-id" in headers else None
                if tenant_id:
                    span.set_attribute("tenant.id", tenant_id)

                await self.app(scope, receive, send_wrapper)

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class SpanContext:
    """
    Context manager for creating spans.

    Usage:
        async with SpanContext("process_batch", attributes={"batch.size": 100}) as span:
            for item in batch:
                await process_item(item)
            span.set_attribute("batch.processed", len(batch))
    """

    def __init__(
        self,
        name: str,
        kind: str = "internal",
        attributes: Dict[str, Any] = None
    ):
        self.name = name
        self.kind = kind
        self.attributes = attributes or {}
        self._span = None
        self._token = None

    async def __aenter__(self):
        if not OPENTELEMETRY_AVAILABLE:
            return self

        tracer = get_tracer()
        if tracer is None:
            return self

        span_kinds = {
            "internal": SpanKind.INTERNAL,
            "server": SpanKind.SERVER,
            "client": SpanKind.CLIENT,
            "producer": SpanKind.PRODUCER,
            "consumer": SpanKind.CONSUMER,
        }

        self._span = tracer.start_span(
            self.name,
            kind=span_kinds.get(self.kind, SpanKind.INTERNAL),
            attributes=self.attributes
        )

        self._token = trace.context_api.attach(
            trace.set_span_in_context(self._span)
        )

        return self._span

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._span is None:
            return False

        if exc_type is not None:
            self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        else:
            self._span.set_status(Status(StatusCode.OK))

        self._span.end()

        if self._token:
            trace.context_api.detach(self._token)

        return False

    def __enter__(self):
        if not OPENTELEMETRY_AVAILABLE:
            return self

        tracer = get_tracer()
        if tracer is None:
            return self

        span_kinds = {
            "internal": SpanKind.INTERNAL,
            "server": SpanKind.SERVER,
            "client": SpanKind.CLIENT,
            "producer": SpanKind.PRODUCER,
            "consumer": SpanKind.CONSUMER,
        }

        self._span = tracer.start_span(
            self.name,
            kind=span_kinds.get(self.kind, SpanKind.INTERNAL),
            attributes=self.attributes
        )

        self._token = trace.context_api.attach(
            trace.set_span_in_context(self._span)
        )

        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._span is None:
            return False

        if exc_type is not None:
            self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        else:
            self._span.set_status(Status(StatusCode.OK))

        self._span.end()

        if self._token:
            trace.context_api.detach(self._token)

        return False
