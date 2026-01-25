"""
Input sanitization for LogiAccounting Pro.
"""

import re
import html
import unicodedata
from typing import Optional, Dict, List, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class ThreatType(str, Enum):
    """Types of security threats to detect."""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    XML_INJECTION = "xml_injection"
    HEADER_INJECTION = "header_injection"
    TEMPLATE_INJECTION = "template_injection"
    SSRF = "ssrf"
    UNSAFE_CONTENT = "unsafe_content"


class SanitizationMode(str, Enum):
    """Sanitization mode."""

    STRICT = "strict"
    MODERATE = "moderate"
    PERMISSIVE = "permissive"


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    original: str
    sanitized: str
    is_safe: bool
    threats_detected: List[ThreatType] = field(default_factory=list)
    modifications: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        """Check if the input was modified."""
        return self.original != self.sanitized


@dataclass
class SanitizerConfig:
    """Configuration for the input sanitizer."""

    mode: SanitizationMode = SanitizationMode.MODERATE
    max_length: int = 10000
    allow_html: bool = False
    allowed_html_tags: Set[str] = field(default_factory=lambda: {"b", "i", "u", "em", "strong", "p", "br"})
    allowed_html_attributes: Set[str] = field(default_factory=lambda: {"class", "id"})
    strip_null_bytes: bool = True
    normalize_unicode: bool = True
    detect_only: bool = False


SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE|UNION|HAVING|WHERE)\b\s)",
    r"(--|\#|\/\*|\*\/)",
    r"(\bOR\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?)",
    r"(\bAND\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?)",
    r"([\'\"];\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
    r"(\bUNION\b\s+\bSELECT\b)",
    r"(WAITFOR\s+DELAY)",
    r"(BENCHMARK\s*\()",
    r"(SLEEP\s*\()",
    r"([\'\"]?\s*;\s*\bDROP\b)",
    r"(xp_cmdshell)",
    r"(information_schema)",
    r"(sys\.)",
]

XSS_PATTERNS = [
    r"(<script[^>]*>)",
    r"(</script>)",
    r"(javascript\s*:)",
    r"(vbscript\s*:)",
    r"(on\w+\s*=)",
    r"(<iframe[^>]*>)",
    r"(<object[^>]*>)",
    r"(<embed[^>]*>)",
    r"(<link[^>]*>)",
    r"(<style[^>]*>)",
    r"(expression\s*\()",
    r"(url\s*\([^)]*javascript)",
    r"(<svg[^>]*onload)",
    r"(<img[^>]*onerror)",
    r"(document\.(cookie|write|location))",
    r"(window\.(location|open))",
    r"(eval\s*\()",
    r"(atob\s*\()",
    r"(btoa\s*\()",
    r"(String\.fromCharCode)",
]

PATH_TRAVERSAL_PATTERNS = [
    r"(\.\.\/)",
    r"(\.\.\\)",
    r"(%2e%2e%2f)",
    r"(%2e%2e\/)",
    r"(\.\.%2f)",
    r"(%2e%2e%5c)",
    r"(\.\.%5c)",
    r"(%252e%252e%252f)",
    r"(\/etc\/passwd)",
    r"(\/etc\/shadow)",
    r"(c:\\windows)",
    r"(c:\/windows)",
    r"(%00)",
    r"(\x00)",
]

COMMAND_INJECTION_PATTERNS = [
    r"(;\s*\w+)",
    r"(\|\s*\w+)",
    r"(&\s*\w+)",
    r"(`[^`]+`)",
    r"(\$\([^)]+\))",
    r"(\$\{[^}]+\})",
    r"(>\s*\/)",
    r"(<\s*\/)",
    r"(\bcat\b|\bls\b|\bdir\b|\brm\b|\bwhoami\b|\bid\b)",
    r"(\/bin\/)",
    r"(cmd\.exe)",
    r"(powershell)",
]

LDAP_INJECTION_PATTERNS = [
    r"(\*\))",
    r"(\)\()",
    r"(\(\|)",
    r"(\(&)",
    r"(\(!)",
    r"([\x00-\x1f])",
]

HEADER_INJECTION_PATTERNS = [
    r"(\r\n)",
    r"(\n)",
    r"(\r)",
    r"(%0d%0a)",
    r"(%0a)",
    r"(%0d)",
]


class InputSanitizer:
    """Input sanitization and threat detection service."""

    def __init__(self, config: Optional[SanitizerConfig] = None):
        self._config = config or SanitizerConfig()
        self._compiled_patterns: Dict[ThreatType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all detection patterns."""
        self._compiled_patterns[ThreatType.SQL_INJECTION] = [
            re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS
        ]
        self._compiled_patterns[ThreatType.XSS] = [
            re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS
        ]
        self._compiled_patterns[ThreatType.PATH_TRAVERSAL] = [
            re.compile(p, re.IGNORECASE) for p in PATH_TRAVERSAL_PATTERNS
        ]
        self._compiled_patterns[ThreatType.COMMAND_INJECTION] = [
            re.compile(p, re.IGNORECASE) for p in COMMAND_INJECTION_PATTERNS
        ]
        self._compiled_patterns[ThreatType.LDAP_INJECTION] = [
            re.compile(p, re.IGNORECASE) for p in LDAP_INJECTION_PATTERNS
        ]
        self._compiled_patterns[ThreatType.HEADER_INJECTION] = [
            re.compile(p, re.IGNORECASE) for p in HEADER_INJECTION_PATTERNS
        ]

    def _detect_threats(self, value: str) -> List[ThreatType]:
        """Detect threats in input value."""
        detected = []

        for threat_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(value):
                    if threat_type not in detected:
                        detected.append(threat_type)
                    break

        return detected

    def _strip_null_bytes(self, value: str) -> str:
        """Remove null bytes from input."""
        return value.replace("\x00", "").replace("%00", "")

    def _normalize_unicode(self, value: str) -> str:
        """Normalize unicode to NFC form."""
        return unicodedata.normalize("NFC", value)

    def _escape_html(self, value: str) -> str:
        """Escape HTML entities."""
        return html.escape(value, quote=True)

    def _strip_html_tags(self, value: str) -> str:
        """Remove all HTML tags."""
        return re.sub(r"<[^>]+>", "", value)

    def _sanitize_html(self, value: str) -> str:
        """Sanitize HTML, keeping only allowed tags."""
        if not self._config.allowed_html_tags:
            return self._escape_html(value)

        allowed_pattern = "|".join(self._config.allowed_html_tags)
        value = re.sub(
            rf"<(?!/?)(?!({allowed_pattern})\b)[^>]+>",
            "",
            value,
            flags=re.IGNORECASE
        )

        value = re.sub(
            r'(\s+on\w+\s*=\s*["\'][^"\']*["\'])',
            "",
            value,
            flags=re.IGNORECASE
        )

        return value

    def _sanitize_sql(self, value: str) -> str:
        """Sanitize potential SQL injection."""
        value = value.replace("'", "''")
        value = value.replace("\\", "\\\\")
        value = re.sub(r"--", "", value)
        value = re.sub(r"/\*.*?\*/", "", value, flags=re.DOTALL)
        return value

    def _sanitize_path(self, value: str) -> str:
        """Sanitize path traversal attempts."""
        value = re.sub(r"\.\.+[/\\]", "", value)
        value = re.sub(r"%2e%2e[%/\\]", "", value, flags=re.IGNORECASE)
        value = re.sub(r"%252e%252e%252f", "", value, flags=re.IGNORECASE)
        value = value.replace("\x00", "")
        return value

    def _sanitize_command(self, value: str) -> str:
        """Sanitize command injection attempts."""
        dangerous_chars = [";", "|", "&", "`", "$", "(", ")", "{", "}", "<", ">"]
        for char in dangerous_chars:
            value = value.replace(char, "")
        return value

    def _sanitize_header(self, value: str) -> str:
        """Sanitize header injection attempts."""
        value = value.replace("\r\n", " ")
        value = value.replace("\n", " ")
        value = value.replace("\r", " ")
        return value

    def sanitize(self, value: str) -> SanitizationResult:
        """Sanitize input value."""
        if not value:
            return SanitizationResult(
                original="",
                sanitized="",
                is_safe=True,
            )

        original = value
        modifications = []
        warnings = []

        if len(value) > self._config.max_length:
            value = value[:self._config.max_length]
            modifications.append(f"Truncated to {self._config.max_length} characters")

        if self._config.strip_null_bytes:
            new_value = self._strip_null_bytes(value)
            if new_value != value:
                modifications.append("Removed null bytes")
                value = new_value

        if self._config.normalize_unicode:
            new_value = self._normalize_unicode(value)
            if new_value != value:
                modifications.append("Normalized unicode")
                value = new_value

        threats = self._detect_threats(value)

        if self._config.detect_only:
            return SanitizationResult(
                original=original,
                sanitized=value,
                is_safe=len(threats) == 0,
                threats_detected=threats,
                modifications=modifications,
                warnings=[f"Detected: {t.value}" for t in threats],
            )

        if ThreatType.SQL_INJECTION in threats:
            value = self._sanitize_sql(value)
            modifications.append("Sanitized SQL injection patterns")

        if ThreatType.XSS in threats:
            if self._config.allow_html:
                value = self._sanitize_html(value)
                modifications.append("Sanitized HTML")
            else:
                value = self._escape_html(value)
                modifications.append("Escaped HTML entities")

        if ThreatType.PATH_TRAVERSAL in threats:
            value = self._sanitize_path(value)
            modifications.append("Sanitized path traversal patterns")

        if ThreatType.COMMAND_INJECTION in threats:
            value = self._sanitize_command(value)
            modifications.append("Sanitized command injection patterns")

        if ThreatType.HEADER_INJECTION in threats:
            value = self._sanitize_header(value)
            modifications.append("Sanitized header injection patterns")

        remaining_threats = self._detect_threats(value)

        return SanitizationResult(
            original=original,
            sanitized=value,
            is_safe=len(remaining_threats) == 0,
            threats_detected=threats,
            modifications=modifications,
            warnings=[f"Remaining threat: {t.value}" for t in remaining_threats],
        )

    def sanitize_dict(
        self,
        data: Dict[str, Any],
        exclude_keys: Optional[Set[str]] = None,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Sanitize all string values in a dictionary."""
        exclude = exclude_keys or set()
        sanitized = {}
        issues = []

        for key, value in data.items():
            if key in exclude:
                sanitized[key] = value
                continue

            if isinstance(value, str):
                result = self.sanitize(value)
                sanitized[key] = result.sanitized
                if result.threats_detected:
                    issues.append(f"Field '{key}': {', '.join(t.value for t in result.threats_detected)}")

            elif isinstance(value, dict):
                nested_sanitized, nested_issues = self.sanitize_dict(value, exclude)
                sanitized[key] = nested_sanitized
                issues.extend(f"{key}.{issue}" for issue in nested_issues)

            elif isinstance(value, list):
                sanitized_list = []
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        result = self.sanitize(item)
                        sanitized_list.append(result.sanitized)
                        if result.threats_detected:
                            issues.append(f"Field '{key}[{i}]': {', '.join(t.value for t in result.threats_detected)}")
                    elif isinstance(item, dict):
                        nested_sanitized, nested_issues = self.sanitize_dict(item, exclude)
                        sanitized_list.append(nested_sanitized)
                        issues.extend(f"{key}[{i}].{issue}" for issue in nested_issues)
                    else:
                        sanitized_list.append(item)
                sanitized[key] = sanitized_list

            else:
                sanitized[key] = value

        return sanitized, issues

    def is_safe(self, value: str) -> bool:
        """Quick check if value is safe."""
        return len(self._detect_threats(value)) == 0

    def detect_sql_injection(self, value: str) -> bool:
        """Detect SQL injection attempts."""
        for pattern in self._compiled_patterns[ThreatType.SQL_INJECTION]:
            if pattern.search(value):
                return True
        return False

    def detect_xss(self, value: str) -> bool:
        """Detect XSS attempts."""
        for pattern in self._compiled_patterns[ThreatType.XSS]:
            if pattern.search(value):
                return True
        return False

    def detect_path_traversal(self, value: str) -> bool:
        """Detect path traversal attempts."""
        for pattern in self._compiled_patterns[ThreatType.PATH_TRAVERSAL]:
            if pattern.search(value):
                return True
        return False

    def escape_for_sql(self, value: str) -> str:
        """Escape value for safe SQL usage."""
        return value.replace("'", "''").replace("\\", "\\\\")

    def escape_for_html(self, value: str) -> str:
        """Escape value for safe HTML display."""
        return html.escape(value, quote=True)

    def escape_for_json(self, value: str) -> str:
        """Escape value for safe JSON embedding."""
        return json.dumps(value)[1:-1]

    def strip_tags(self, value: str) -> str:
        """Remove all HTML/XML tags from value."""
        return self._strip_html_tags(value)

    def clean_filename(self, filename: str) -> str:
        """Clean a filename for safe filesystem usage."""
        filename = re.sub(r"[^\w\s\-\.]", "", filename)
        filename = re.sub(r"\.\.+", ".", filename)
        filename = filename.strip(". ")

        if not filename or filename in (".", ".."):
            filename = "unnamed"

        max_length = 255
        if len(filename) > max_length:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            if ext:
                filename = name[:max_length - len(ext) - 1] + "." + ext
            else:
                filename = filename[:max_length]

        return filename


_sanitizer: Optional[InputSanitizer] = None


def get_sanitizer() -> InputSanitizer:
    """Get the global sanitizer instance."""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = InputSanitizer()
    return _sanitizer


def set_sanitizer(sanitizer: InputSanitizer) -> None:
    """Set the global sanitizer instance."""
    global _sanitizer
    _sanitizer = sanitizer


def sanitize_input(value: str) -> SanitizationResult:
    """Sanitize input using the global sanitizer."""
    return get_sanitizer().sanitize(value)


def is_safe_input(value: str) -> bool:
    """Check if input is safe using the global sanitizer."""
    return get_sanitizer().is_safe(value)
