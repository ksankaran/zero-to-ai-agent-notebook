# From: Zero to AI Agent, Chapter 20, Section 20.2
# File: src/caspar/agent/persistence.py

"""
Conversation persistence using PostgreSQL.

This module provides checkpointing functionality that allows
conversations to survive restarts and be resumed later.

IMPORTANT: AsyncPostgresSaver must be used as an async context manager.
The checkpointer should stay open for the lifetime of your application.
"""

import os
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from caspar.config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def create_checkpointer_context():
    """
    Create a PostgreSQL checkpointer as an async context manager.
    
    This must be used with 'async with' and should wrap your entire
    application lifecycle (e.g., in FastAPI's lifespan).
    
    Yields:
        AsyncPostgresSaver if database is configured, None otherwise
    
    Environment Variables:
        DATABASE_URL: PostgreSQL connection string
                     Format: postgresql://user:pass@host:port/dbname
    
    Usage:
        async with create_checkpointer_context() as checkpointer:
            agent = await create_agent(checkpointer=checkpointer)
            # ... run your application ...
            # checkpointer stays open until you exit the 'async with'
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.warning(
            "no_database_url",
            message="DATABASE_URL not set - conversations won't persist across restarts"
        )
        yield None
        return
    
    try:
        # AsyncPostgresSaver MUST be used as async context manager
        async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
            # Set up the required tables (safe to call multiple times)
            await checkpointer.setup()
            
            logger.info("checkpointer_initialized", database="postgresql")
            
            # Yield the checkpointer - it stays open until we exit
            yield checkpointer
            
            # Cleanup happens automatically when we exit the 'async with'
            logger.info("checkpointer_closing")
        
    except Exception as e:
        logger.error(
            "checkpointer_failed",
            error=str(e),
            message="Falling back to in-memory state (no persistence)"
        )
        yield None
