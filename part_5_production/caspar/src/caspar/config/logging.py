# From: Zero to AI Agent, Chapter 20, Section 20.1
# File: src/caspar/config/logging.py

"""
CASPAR Logging Configuration

Provides structured logging using structlog for better
observability in production environments.
"""

import logging
import structlog
from .settings import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Set the log level based on settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            # Use console renderer in development, JSON in production
            structlog.dev.ConsoleRenderer()
            if settings.environment == "development"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Also configure standard logging for third-party libraries
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with the given name."""
    return structlog.get_logger(name)
