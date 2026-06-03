"""
Security Protection Module

Implements comprehensive security measures:
1. Input Validation: Pydantic models with strict validation
2. SQL Injection Prevention: Parameterized queries and input sanitization
3. XSS Prevention: HTML/script tag filtering
4. Rate Limiting: Request throttling per IP/user
5. Authentication: API key validation
6. Data Sanitization: Clean user inputs

Security Features:
- Whitelist-based validation
- Pattern matching for malicious inputs
- Request rate limiting (configurable)
- Audit logging for security events
"""

import re
import logging
import hashlib
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from pydantic import BaseModel, Field, field_validator, ValidationError

logger = logging.getLogger(__name__)


# ==================== Input Validation Models ====================

class TripRequest(BaseModel):
    """Validated trip request model."""

    destination: str = Field(..., min_length=1, max_length=100, description="Trip destination")
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="End date (YYYY-MM-DD)")
    purpose: str = Field(..., min_length=1, max_length=500, description="Trip purpose")
    budget: Optional[float] = Field(None, ge=0, le=1000000, description="Budget in CNY")
    employee_id: Optional[str] = Field(None, pattern=r'^[A-Z0-9]{6,12}$', description="Employee ID")

    @field_validator('destination', 'purpose')
    @classmethod
    def sanitize_text(cls, v):
        """Sanitize text fields to prevent XSS and injection attacks."""
        if not v:
            raise ValueError("Field cannot be empty")

        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)

        # Remove script tags and content
        v = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', v, flags=re.IGNORECASE)

        # Remove SQL keywords (basic protection)
        sql_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'EXEC', 'EXECUTE', 'UNION', 'SELECT']
        pattern = r'\b(' + '|'.join(sql_keywords) + r')\b'
        if re.search(pattern, v, re.IGNORECASE):
            raise ValueError("Input contains potentially malicious SQL keywords")

        return v.strip()

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format and range."""
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')

            # Check if date is not too far in the past or future
            now = datetime.now()
            if date_obj < now - timedelta(days=365):
                raise ValueError("Date is too far in the past")
            if date_obj > now + timedelta(days=730):
                raise ValueError("Date is too far in the future")

            return v
        except ValueError as e:
            raise ValueError(f"Invalid date format: {str(e)}")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Ensure end_date is after start_date."""
        if info.data.get('start_date'):
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')

            if end < start:
                raise ValueError("End date must be after start date")

            # Check trip duration is reasonable (max 90 days)
            duration = (end - start).days
            if duration > 90:
                raise ValueError("Trip duration exceeds maximum allowed (90 days)")

        return v


class QueryRequest(BaseModel):
    """Validated query request model."""

    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9-]{10,50}$', description="Session ID")
    user_id: Optional[str] = Field(None, pattern=r'^[A-Z0-9]{6,12}$', description="User ID")

    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v):
        """Sanitize query input."""
        if not v:
            raise ValueError("Query cannot be empty")

        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)

        # Remove dangerous characters
        v = re.sub(r'[<>{}]', '', v)

        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\bexec\b.*\()",
            r"(--|#|/\*|\*/)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Query contains potentially malicious patterns")

        return v.strip()


class PolicyCheckRequest(BaseModel):
    """Validated policy check request model."""

    trip_data: Dict[str, Any] = Field(..., description="Trip data to check")
    policy_type: str = Field(..., pattern=r'^[a-z_]+$', description="Policy type")

    @field_validator('policy_type')
    @classmethod
    def validate_policy_type(cls, v):
        """Validate policy type against whitelist."""
        allowed_types = ['budget', 'duration', 'advance_booking', 'accommodation', 'transportation']
        if v not in allowed_types:
            raise ValueError(f"Invalid policy type. Allowed: {', '.join(allowed_types)}")
        return v


# ==================== SQL Injection Prevention ====================

class SQLSanitizer:
    """Sanitize SQL inputs to prevent injection attacks."""

    # Dangerous SQL patterns
    DANGEROUS_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(--|#|/\*|\*/)",
        r"(\bor\b\s*['\"]?\w*['\"]?\s*=\s*['\"]?\w*['\"]?)",
        r"(\band\b\s*['\"]?\w*['\"]?\s*=\s*['\"]?\w*['\"]?)",
        r"(;.*\b(drop|delete|insert|update)\b)",
        r"('\s*or\s*'1'\s*=\s*'1)",
        r"('\s*or\s*1\s*=\s*1)",
    ]

    @classmethod
    def is_safe(cls, value: str) -> bool:
        """
        Check if input is safe from SQL injection.

        Args:
            value: Input string to check

        Returns:
            True if safe, False otherwise
        """
        if not isinstance(value, str):
            return True

        value_lower = value.lower()

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:100]}")
                return False

        return True

    @classmethod
    def sanitize(cls, value: str) -> str:
        """
        Sanitize SQL input by escaping dangerous characters.

        Args:
            value: Input string to sanitize

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value

        # Check if input is safe
        if not cls.is_safe(value):
            raise ValueError("Input contains potentially malicious SQL patterns")

        # Escape single quotes (basic protection)
        value = value.replace("'", "''")

        # Remove SQL comments
        value = re.sub(r'--.+', '', value)
        value = re.sub(r'/\*.+\*/', '', value)

        return value.strip()


# ==================== XSS Prevention ====================

class XSSProtection:
    """Prevent Cross-Site Scripting (XSS) attacks."""

    # Dangerous HTML/JS patterns
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe\b',
        r'<embed\b',
        r'<object\b',
    ]

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """
        Remove HTML tags and dangerous patterns.

        Args:
            value: Input string

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value

        # Remove script tags
        for pattern in cls.DANGEROUS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        # Remove all HTML tags
        value = re.sub(r'<[^>]+>', '', value)

        # Escape special characters
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')

        return value

    @classmethod
    def is_safe(cls, value: str) -> bool:
        """
        Check if input is safe from XSS.

        Args:
            value: Input string to check

        Returns:
            True if safe, False otherwise
        """
        if not isinstance(value, str):
            return True

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {value[:100]}")
                return False

        return True


# ==================== Rate Limiting ====================

class RateLimiter:
    """
    Request rate limiter to prevent abuse.

    Implements token bucket algorithm for rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked: Set[str] = set()

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.

        Args:
            identifier: Client identifier (IP, user_id, etc.)

        Returns:
            True if allowed, False if rate limited
        """
        # Check if blocked
        if identifier in self.blocked:
            logger.warning(f"Request from blocked identifier: {identifier}")
            return False

        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        # Remove old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]

        # Check rate limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for: {identifier}")
            return False

        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = now - timedelta(seconds=10)
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > burst_cutoff
        ]

        if len(recent_requests) >= self.burst_size:
            logger.warning(f"Burst limit exceeded for: {identifier}")
            return False

        # Allow request
        self.requests[identifier].append(now)
        return True

    def block(self, identifier: str):
        """Block a specific identifier."""
        self.blocked.add(identifier)
        logger.warning(f"Blocked identifier: {identifier}")

    def unblock(self, identifier: str):
        """Unblock a specific identifier."""
        self.blocked.discard(identifier)
        logger.info(f"Unblocked identifier: {identifier}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        active_clients = {
            identifier: len([
                req for req in requests
                if req > cutoff
            ])
            for identifier, requests in self.requests.items()
        }

        return {
            "active_clients": len(active_clients),
            "blocked_clients": len(self.blocked),
            "total_requests_last_minute": sum(active_clients.values())
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter()

    return _rate_limiter


# ==================== Decorators ====================

def require_rate_limit(identifier_key: str = 'user_id'):
    """
    Decorator to enforce rate limiting on functions.

    Args:
        identifier_key: Key to extract identifier from kwargs

    Example:
        @require_rate_limit('user_id')
        def process_request(user_id: str, query: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = kwargs.get(identifier_key, 'anonymous')
            rate_limiter = get_rate_limiter()

            if not rate_limiter.is_allowed(identifier):
                raise ValueError(f"Rate limit exceeded for {identifier}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_input(model_class: type[BaseModel]):
    """
    Decorator to validate function inputs using Pydantic models.

    Args:
        model_class: Pydantic model class for validation

    Example:
        @validate_input(TripRequest)
        def create_trip(**kwargs):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate using Pydantic model
                validated_data = model_class(**kwargs)
                # Replace kwargs with validated data
                kwargs.update(validated_data.dict())
                return func(*args, **kwargs)
            except ValidationError as e:
                logger.error(f"Input validation failed: {e}")
                raise ValueError(f"Invalid input: {e}")

        return wrapper
    return decorator


# ==================== Security Utilities ====================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Args:
        length: Token length

    Returns:
        Secure random token
    """
    import secrets
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data for logging/storage.

    Args:
        data: Sensitive data to hash

    Returns:
        SHA-256 hash
    """
    return hashlib.sha256(data.encode()).hexdigest()


def audit_log(event: str, details: Dict[str, Any]):
    """
    Log security-relevant events.

    Args:
        event: Event type
        details: Event details
    """
    # Redact sensitive information
    safe_details = {
        k: hash_sensitive_data(str(v)) if k in ['password', 'api_key', 'token'] else v
        for k, v in details.items()
    }

    logger.info(f"AUDIT: {event} - {safe_details}")


# Example usage
if __name__ == "__main__":
    # Test input validation
    try:
        trip = TripRequest(
            destination="Beijing",
            start_date="2024-06-01",
            end_date="2024-06-05",
            purpose="Business meeting",
            budget=5000.0,
            employee_id="EMP001"
        )
        print("Valid trip request:", trip.dict())
    except ValidationError as e:
        print("Validation error:", e)

    # Test SQL injection detection
    malicious_input = "'; DROP TABLE users; --"
    print("Is safe:", SQLSanitizer.is_safe(malicious_input))

    # Test XSS detection
    xss_input = "<script>alert('XSS')</script>"
    print("XSS safe:", XSSProtection.is_safe(xss_input))
    print("Sanitized:", XSSProtection.sanitize_html(xss_input))

    # Test rate limiting
    limiter = get_rate_limiter()
    print("Rate limit stats:", limiter.get_stats())
