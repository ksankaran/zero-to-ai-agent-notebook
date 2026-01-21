# Save as: src/caspar/api/main.py

"""
CASPAR API - Production-ready FastAPI application.

Provides REST endpoints for the customer service agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid

from caspar.config import settings, get_logger
from caspar.agent import create_checkpointer_context, create_agent, create_initial_state
from caspar.knowledge import get_retriever

logger = get_logger(__name__)

# Store active conversations in memory
# Note: For horizontal scaling, use Redis instead
conversations: dict = {}

# The agent instance (initialized on startup)
agent = None


# ─────────────────────────────────────────────────────────────
# LIFESPAN - STARTUP AND SHUTDOWN
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize resources on startup, cleanup on shutdown.
    
    The checkpointer context manager MUST wrap the yield to keep
    the database connection open during the server's lifetime.
    """
    global agent
    
    logger.info("starting_caspar_api", version="1.0.0")
    
    # Step 1: Initialize knowledge base (validates it's ready)
    retriever = get_retriever()
    logger.info("knowledge_base_ready")
    
    # Step 2: Create checkpointer context
    # The 'async with' keeps the database connection open
    async with create_checkpointer_context() as checkpointer:
        
        # Step 3: Create the agent with the checkpointer
        agent = await create_agent(checkpointer=checkpointer)
        logger.info(
            "agent_initialized",
            persistence_enabled=checkpointer is not None
        )
        
        # Step 4: Server runs here (while inside the 'async with')
        yield
        
        # Step 5: Cleanup on shutdown
        logger.info("shutting_down_caspar_api")
        conversations.clear()
    
    # Database connection closes automatically when we exit 'async with'


# ─────────────────────────────────────────────────────────────
# FASTAPI APP SETUP
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="CASPAR API",
    description="Customer Service AI Agent powered by LangGraph",
    version="1.0.0",
    lifespan=lifespan,  # Connect our startup/shutdown logic
)

# CORS middleware allows web browsers to call our API
# Without this, browsers block requests from different domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, list specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# REQUEST MODELS (what clients send to us)
# ─────────────────────────────────────────────────────────────

class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""
    customer_id: str = Field(..., description="Customer identifier")
    initial_message: str | None = Field(None, description="Optional first message")


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    message: str = Field(..., min_length=1, max_length=10000)


# ─────────────────────────────────────────────────────────────
# RESPONSE MODELS (what we send back to clients)
# ─────────────────────────────────────────────────────────────

class StartConversationResponse(BaseModel):
    """Response with new conversation details."""
    conversation_id: str
    message: str


class SendMessageResponse(BaseModel):
    """Response from the agent."""
    response: str
    intent: str | None = None
    needs_escalation: bool = False
    ticket_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class ConversationStatus(BaseModel):
    """Current status of a conversation."""
    conversation_id: str
    customer_id: str
    message_count: int
    intent: str | None
    needs_escalation: bool
    created_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    agent_ready: bool


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check if the service is healthy.
    
    Used by:
    - Load balancers to know if this instance can receive traffic
    - Kubernetes/Docker health checks
    - Monitoring systems
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        agent_ready=agent is not None,
    )


@app.post("/conversations", response_model=StartConversationResponse, tags=["Conversations"])
async def start_conversation(request: StartConversationRequest):
    """
    Start a new conversation with CASPAR.
    
    Returns a conversation ID to use for subsequent messages.
    """
    # Generate a unique ID for this conversation
    conversation_id = f"conv-{uuid.uuid4().hex[:12]}"
    
    # Initialize the agent's state for this conversation
    state = create_initial_state(
        conversation_id=conversation_id,
        customer_id=request.customer_id,
    )
    
    # Store in memory (keyed by conversation_id)
    conversations[conversation_id] = {
        "state": state,
        "customer_id": request.customer_id,
    }
    
    logger.info(
        "conversation_started",
        conversation_id=conversation_id,
        customer_id=request.customer_id,
    )
    
    # If the client sent an initial message, process it immediately
    if request.initial_message:
        response = await _process_message(conversation_id, request.initial_message)
        return StartConversationResponse(
            conversation_id=conversation_id,
            message=response.response,
        )
    
    # Otherwise, return a greeting
    return StartConversationResponse(
        conversation_id=conversation_id,
        message="Hello! I'm CASPAR, your customer service assistant. How can I help you today?",
    )


@app.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    tags=["Conversations"],
)
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message in an existing conversation.
    
    The agent will process the message and return a response.
    """
    # Check if conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )
    
    # Process the message (see helper function below)
    return await _process_message(conversation_id, request.message)


@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationStatus,
    tags=["Conversations"],
)
async def get_conversation(conversation_id: str):
    """Get the current status of a conversation."""
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )
    
    conv = conversations[conversation_id]
    state = conv["state"]
    
    return ConversationStatus(
        conversation_id=conversation_id,
        customer_id=conv["customer_id"],
        message_count=len(state.get("messages", [])),
        intent=state.get("intent"),
        needs_escalation=state.get("needs_escalation", False),
        created_at=state.get("started_at", "unknown"),
    )


@app.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def end_conversation(conversation_id: str):
    """End a conversation and clean up resources."""
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )
    
    del conversations[conversation_id]
    
    logger.info("conversation_ended", conversation_id=conversation_id)
    
    return {"status": "ended", "conversation_id": conversation_id}


# ─────────────────────────────────────────────────────────────
# METRICS ENDPOINT
# ─────────────────────────────────────────────────────────────

from caspar.api.metrics import metrics

@app.get("/metrics", tags=["System"])
async def get_metrics():
    """
    Get current metrics.
    
    Returns counters, latencies, and uptime.
    Useful for monitoring dashboards.
    """
    return metrics.get_stats()


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

async def _process_message(conversation_id: str, message: str) -> SendMessageResponse:
    """
    Process a message through the agent.
    
    This is a helper function used by multiple endpoints.
    The underscore prefix indicates it's private (not an endpoint).
    """
    from langchain_core.messages import HumanMessage
    
    # Get the conversation from memory
    conv = conversations[conversation_id]
    state = conv["state"]
    
    # Add the user's message to the conversation history
    state["messages"].append(HumanMessage(content=message))
    
    # Configure the agent with this conversation's thread_id
    # This enables persistence (if checkpointer is available)
    config = {"configurable": {"thread_id": conversation_id}}
    
    try:
        # ═══════════════════════════════════════════════════════
        # THIS IS THE KEY LINE - Run the LangGraph agent!
        # ═══════════════════════════════════════════════════════
        result = await agent.ainvoke(state, config)
        
        # Update stored state with the result
        conv["state"] = result
        
        # Extract the AI's response (last message)
        ai_response = result["messages"][-1].content if result["messages"] else \
            "I apologize, but I couldn't process your request."
        
        logger.info(
            "message_processed",
            conversation_id=conversation_id,
            intent=result.get("intent"),
            needs_escalation=result.get("needs_escalation", False),
        )
        
        # Build and return the response
        return SendMessageResponse(
            response=ai_response,
            intent=result.get("intent"),
            needs_escalation=result.get("needs_escalation", False),
            ticket_id=result.get("ticket_id"),
            metadata={
                "sentiment_score": result.get("sentiment_score"),
                "frustration_level": result.get("frustration_level"),
            },
        )
        
    except Exception as e:
        logger.error(
            "message_processing_error", 
            error=str(e), 
            conversation_id=conversation_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your message. Please try again.",
        )
