"""
Request Validation Middleware
Validates incoming requests for security and data integrity.
"""

import re
import json
from typing import Optional, List, Dict, Set, Callable, Any
from dataclasses import dataclass
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    RELAXED = "relaxed"


class ThreatType(str, Enum):
    """Types of security threats detected."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    XML_INJECTION = "xml_injection"
    HEADER_INJECTION = "header_injection"
    OVERSIZED_PAYLOAD = "oversized_payload"
    INVALID_CONTENT_TYPE = "invalid_content_type"
    MALFORMED_JSON = "malformed_json"


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    threat_type: Optional[ThreatType] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ThreatPatterns:
    """Security threat detection patterns."""

    SQL_INJECTION_PATTERNS = [
        r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)(\s|$)",
        r"(\s|^)(OR|AND)\s+\d+\s*=\s*\d+",
        r"'(\s|)*(OR|AND)(\s|)*'",
        r"--(\s|$)",
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
        r"EXEC(\s|UTE)?(\s|\()",
        r"xp_\w+",
        r"sp_\w+",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"<\s*img[^>]+src\s*=\s*['\"]?\s*javascript:",
        r"<\s*iframe",
        r"<\s*object",
        r"<\s*embed",
        r"<\s*form[^>]+action",
        r"expression\s*\(",
        r"url\s*\(\s*['\"]?\s*javascript:",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e/",
        r"%2e%2e\\",
        r"\.%00",
        r"%00\.",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`[^`]+`",
        r"\|\s*\w+",
        r">\s*/",
        r"<\s*/",
    ]

    LDAP_INJECTION_PATTERNS = [
        r"[)(|*\\]",
        r"\x00",
    ]

    HEADER_INJECTION_PATTERNS = [
        r"[\r\n]",
        r"%0[dD]",
        r"%0[aA]",
    ]


class InputSanitizer:
    """Input sanitization utilities."""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Basic string sanitization."""
        if not isinstance(value, str):
            return value

        value = value.replace("\x00", "")

        value = re.sub(r"[\r\n]", " ", value)

        return value.strip()

    @staticmethod
    def sanitize_html(value: str) -> str:
        """Remove HTML tags from string."""
        if not isinstance(value, str):
            return value

        clean = re.sub(r"<[^>]+>", "", value)
        return clean

    @staticmethod
    def escape_html(value: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(value, str):
            return value

        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        for char, escape in replacements.items():
            value = value.replace(char, escape)
        return value


class ThreatDetector:
    """Detects security threats in request data."""

    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        self.level = level
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        flags = re.IGNORECASE

        self.sql_patterns = [
            re.compile(p, flags) for p in ThreatPatterns.SQL_INJECTION_PATTERNS
        ]
        self.xss_patterns = [
            re.compile(p, flags) for p in ThreatPatterns.XSS_PATTERNS
        ]
        self.path_patterns = [
            re.compile(p, flags) for p in ThreatPatterns.PATH_TRAVERSAL_PATTERNS
        ]
        self.cmd_patterns = [
            re.compile(p) for p in ThreatPatterns.COMMAND_INJECTION_PATTERNS
        ]
        self.ldap_patterns = [
            re.compile(p) for p in ThreatPatterns.LDAP_INJECTION_PATTERNS
        ]
        self.header_patterns = [
            re.compile(p, flags) for p in ThreatPatterns.HEADER_INJECTION_PATTERNS
        ]

    def check_sql_injection(self, value: str) -> ValidationResult:
        """Check for SQL injection attempts."""
        if not isinstance(value, str):
            return ValidationResult(is_valid=True)

        for pattern in self.sql_patterns:
            if pattern.search(value):
                return ValidationResult(
                    is_valid=False,
                    threat_type=ThreatType.SQL_INJECTION,
                    message="Potential SQL injection detected",
                    details={"pattern": pattern.pattern, "value_sample": value[:100]},
                )

        return ValidationResult(is_valid=True)

    def check_xss(self, value: str) -> ValidationResult:
        """Check for XSS attempts."""
        if not isinstance(value, str):
            return ValidationResult(is_valid=True)

        for pattern in self.xss_patterns:
            if pattern.search(value):
                return ValidationResult(
                    is_valid=False,
                    threat_type=ThreatType.XSS,
                    message="Potential XSS attack detected",
                    details={"pattern": pattern.pattern, "value_sample": value[:100]},
                )

        return ValidationResult(is_valid=True)

    def check_path_traversal(self, value: str) -> ValidationResult:
        """Check for path traversal attempts."""
        if not isinstance(value, str):
            return ValidationResult(is_valid=True)

        for pattern in self.path_patterns:
            if pattern.search(value):
                return ValidationResult(
                    is_valid=False,
                    threat_type=ThreatType.PATH_TRAVERSAL,
                    message="Potential path traversal attack detected",
                    details={"pattern": pattern.pattern, "value_sample": value[:100]},
                )

        return ValidationResult(is_valid=True)

    def check_command_injection(self, value: str) -> ValidationResult:
        """Check for command injection attempts."""
        if not isinstance(value, str):
            return ValidationResult(is_valid=True)

        if self.level != ValidationLevel.STRICT:
            return ValidationResult(is_valid=True)

        for pattern in self.cmd_patterns:
            if pattern.search(value):
                return ValidationResult(
                    is_valid=False,
                    threat_type=ThreatType.COMMAND_INJECTION,
                    message="Potential command injection detected",
                    details={"pattern": pattern.pattern, "value_sample": value[:100]},
                )

        return ValidationResult(is_valid=True)

    def check_value(self, value: str) -> ValidationResult:
        """Run all threat checks on a value."""
        checks = [
            self.check_sql_injection,
            self.check_xss,
            self.check_path_traversal,
        ]

        if self.level == ValidationLevel.STRICT:
            checks.append(self.check_command_injection)

        for check in checks:
            result = check(value)
            if not result.is_valid:
                return result

        return ValidationResult(is_valid=True)

    def check_dict(self, data: dict, depth: int = 0, max_depth: int = 10) -> ValidationResult:
        """Recursively check dictionary values."""
        if depth > max_depth:
            return ValidationResult(is_valid=True)

        for key, value in data.items():
            key_result = self.check_value(str(key))
            if not key_result.is_valid:
                key_result.details = key_result.details or {}
                key_result.details["field"] = "key"
                return key_result

            if isinstance(value, str):
                result = self.check_value(value)
                if not result.is_valid:
                    result.details = result.details or {}
                    result.details["field"] = key
                    return result
            elif isinstance(value, dict):
                result = self.check_dict(value, depth + 1, max_depth)
                if not result.is_valid:
                    return result
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        result = self.check_value(item)
                        if not result.is_valid:
                            result.details = result.details or {}
                            result.details["field"] = f"{key}[{i}]"
                            return result
                    elif isinstance(item, dict):
                        result = self.check_dict(item, depth + 1, max_depth)
                        if not result.is_valid:
                            return result

        return ValidationResult(is_valid=True)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Request validation middleware for security.

    Features:
    - SQL injection detection
    - XSS attack prevention
    - Path traversal detection
    - Command injection detection
    - Content type validation
    - Payload size limits
    - JSON validation
    """

    def __init__(
        self,
        app,
        validation_level: ValidationLevel = ValidationLevel.MODERATE,
        max_body_size: int = 10 * 1024 * 1024,
        allowed_content_types: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        validate_query_params: bool = True,
        validate_headers: bool = True,
        validate_body: bool = True,
        on_threat_detected: Optional[Callable[[Request, ValidationResult], None]] = None,
    ):
        super().__init__(app)
        self.validation_level = validation_level
        self.max_body_size = max_body_size
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        ]
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
        self.validate_query_params = validate_query_params
        self.validate_headers = validate_headers
        self.validate_body = validate_body
        self.on_threat_detected = on_threat_detected
        self.detector = ThreatDetector(validation_level)

    def _should_validate(self, request: Request) -> bool:
        """Check if request should be validated."""
        path = request.url.path
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        return True

    def _validate_content_type(self, request: Request) -> ValidationResult:
        """Validate request content type."""
        if request.method not in ["POST", "PUT", "PATCH"]:
            return ValidationResult(is_valid=True)

        content_type = request.headers.get("content-type", "")
        base_type = content_type.split(";")[0].strip().lower()

        if not base_type:
            return ValidationResult(is_valid=True)

        for allowed in self.allowed_content_types:
            if base_type == allowed or base_type.startswith(allowed):
                return ValidationResult(is_valid=True)

        return ValidationResult(
            is_valid=False,
            threat_type=ThreatType.INVALID_CONTENT_TYPE,
            message=f"Invalid content type: {base_type}",
            details={"content_type": base_type, "allowed": self.allowed_content_types},
        )

    def _validate_content_length(self, request: Request) -> ValidationResult:
        """Validate request content length."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_body_size:
                    return ValidationResult(
                        is_valid=False,
                        threat_type=ThreatType.OVERSIZED_PAYLOAD,
                        message=f"Request body too large: {length} bytes",
                        details={"size": length, "max_size": self.max_body_size},
                    )
            except ValueError:
                pass

        return ValidationResult(is_valid=True)

    def _validate_query_params(self, request: Request) -> ValidationResult:
        """Validate query parameters."""
        if not self.validate_query_params:
            return ValidationResult(is_valid=True)

        for key, value in request.query_params.items():
            key_result = self.detector.check_value(key)
            if not key_result.is_valid:
                key_result.details = key_result.details or {}
                key_result.details["location"] = "query_param"
                key_result.details["param"] = key
                return key_result

            result = self.detector.check_value(value)
            if not result.is_valid:
                result.details = result.details or {}
                result.details["location"] = "query_param"
                result.details["param"] = key
                return result

        return ValidationResult(is_valid=True)

    def _validate_headers(self, request: Request) -> ValidationResult:
        """Validate request headers."""
        if not self.validate_headers:
            return ValidationResult(is_valid=True)

        sensitive_headers = ["authorization", "cookie", "x-api-key"]

        for key, value in request.headers.items():
            if key.lower() in sensitive_headers:
                continue

            for pattern in self.detector.header_patterns:
                if pattern.search(value):
                    return ValidationResult(
                        is_valid=False,
                        threat_type=ThreatType.HEADER_INJECTION,
                        message="Potential header injection detected",
                        details={"header": key},
                    )

        return ValidationResult(is_valid=True)

    async def _validate_body(self, request: Request, body: bytes) -> ValidationResult:
        """Validate request body."""
        if not self.validate_body:
            return ValidationResult(is_valid=True)

        if not body:
            return ValidationResult(is_valid=True)

        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                data = json.loads(body.decode("utf-8"))
                if isinstance(data, dict):
                    return self.detector.check_dict(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            result = self.detector.check_dict(item)
                            if not result.is_valid:
                                return result
                        elif isinstance(item, str):
                            result = self.detector.check_value(item)
                            if not result.is_valid:
                                return result
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    threat_type=ThreatType.MALFORMED_JSON,
                    message=f"Invalid JSON: {str(e)}",
                )

        return ValidationResult(is_valid=True)

    def _create_error_response(self, result: ValidationResult) -> JSONResponse:
        """Create error response for validation failure."""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "validation_error",
                "message": result.message or "Request validation failed",
                "threat_type": result.threat_type.value if result.threat_type else None,
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process and validate the request."""
        if not self._should_validate(request):
            return await call_next(request)

        content_type_result = self._validate_content_type(request)
        if not content_type_result.is_valid:
            if self.on_threat_detected:
                self.on_threat_detected(request, content_type_result)
            return self._create_error_response(content_type_result)

        content_length_result = self._validate_content_length(request)
        if not content_length_result.is_valid:
            if self.on_threat_detected:
                self.on_threat_detected(request, content_length_result)
            return self._create_error_response(content_length_result)

        query_result = self._validate_query_params(request)
        if not query_result.is_valid:
            if self.on_threat_detected:
                self.on_threat_detected(request, query_result)
            return self._create_error_response(query_result)

        header_result = self._validate_headers(request)
        if not header_result.is_valid:
            if self.on_threat_detected:
                self.on_threat_detected(request, header_result)
            return self._create_error_response(header_result)

        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()

            body_result = await self._validate_body(request, body)
            if not body_result.is_valid:
                if self.on_threat_detected:
                    self.on_threat_detected(request, body_result)
                return self._create_error_response(body_result)

            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        return await call_next(request)


class ValidationConfig:
    """Builder class for validation middleware configuration."""

    def __init__(self):
        self.validation_level = ValidationLevel.MODERATE
        self.max_body_size = 10 * 1024 * 1024
        self.allowed_content_types: List[str] = []
        self.excluded_paths: List[str] = []
        self.validate_query_params = True
        self.validate_headers = True
        self.validate_body = True

    def set_level(self, level: ValidationLevel) -> "ValidationConfig":
        """Set validation strictness level."""
        self.validation_level = level
        return self

    def set_max_body_size(self, size_bytes: int) -> "ValidationConfig":
        """Set maximum request body size."""
        self.max_body_size = size_bytes
        return self

    def allow_content_type(self, content_type: str) -> "ValidationConfig":
        """Add allowed content type."""
        self.allowed_content_types.append(content_type)
        return self

    def exclude_path(self, path: str) -> "ValidationConfig":
        """Exclude path from validation."""
        self.excluded_paths.append(path)
        return self

    def disable_query_validation(self) -> "ValidationConfig":
        """Disable query parameter validation."""
        self.validate_query_params = False
        return self

    def disable_header_validation(self) -> "ValidationConfig":
        """Disable header validation."""
        self.validate_headers = False
        return self

    def disable_body_validation(self) -> "ValidationConfig":
        """Disable body validation."""
        self.validate_body = False
        return self

    def build(self) -> dict:
        """Build configuration dictionary."""
        return {
            "validation_level": self.validation_level,
            "max_body_size": self.max_body_size,
            "allowed_content_types": self.allowed_content_types if self.allowed_content_types else None,
            "excluded_paths": self.excluded_paths if self.excluded_paths else None,
            "validate_query_params": self.validate_query_params,
            "validate_headers": self.validate_headers,
            "validate_body": self.validate_body,
        }
