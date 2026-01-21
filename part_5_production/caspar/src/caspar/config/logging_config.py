# Save as: src/caspar/config/logging_config.py

"""
Production logging configuration.

Outputs JSON logs that can be shipped to any log aggregator.
"""

import structlog
import logging
import sys


def configure_production_logging():
    """
    Configure logging for production.
    
    Call this once at application startup.
    """
    
    # Configure structlog to output JSON
    structlog.configure(
        processors=[
            # Include context variables (set elsewhere in code)
            structlog.contextvars.merge_contextvars,
            
            # Add log level (info, warning, error, etc.)
            structlog.processors.add_log_level,
            
            # Include stack traces for errors
            structlog.processors.StackInfoRenderer(),
            
            # Add ISO-format timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            
            # Output as JSON (the key part!)
            structlog.processors.JSONRenderer(),
        ],
        
        # Only log INFO and above (not DEBUG)
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        
        # Use dict for context
        context_class=dict,
        
        # Output to stdout (Docker captures this)
        logger_factory=structlog.PrintLoggerFactory(),
        
        # Cache logger for performance
        cache_logger_on_first_use=True,
    )
    
    # Also configure Python's standard logging library
    # (some libraries use this instead of structlog)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def configure_development_logging():
    """
    Configure logging for development.
    
    Uses human-readable output instead of JSON.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            # Human-readable output with colors
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
    )
