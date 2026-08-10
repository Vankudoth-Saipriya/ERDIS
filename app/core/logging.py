"""
ERDIS Logging Configuration with Secret Redaction
"""

import logging
import re
import sys
from typing import Any, Dict
import structlog
from app.core.config import settings

# Regex patterns to redact sensitive credentials from log sinks
SECRET_PATTERNS = [
    re.compile(r'(api_key|password|secret|authorization|token)\s*=\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
    re.compile(r'sk-[a-zA-Z0-9]{32,}', re.IGNORECASE),
]


def redact_secrets_processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Redacts sensitive information from log event dictionary prior to formatting."""
    for key, value in event_dict.items():
        if isinstance(value, str):
            for pattern in SECRET_PATTERNS:
                if pattern.search(value):
                    event_dict[key] = pattern.sub(r'\1=***REDACTED***', value)
    return event_dict


def setup_logging() -> None:
    """Configures structured logging for ERDIS."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            redact_secrets_processor,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()
