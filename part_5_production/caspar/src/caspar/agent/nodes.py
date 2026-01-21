# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: src/caspar/agent/nodes.py

"""
CASPAR Agent Nodes - Processing functions for each step in the graph.

Each node function:
1. Takes the current state as input
2. Performs some processing (often using an LLM)
3. Returns updates to merge into the state
"""

from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage

from caspar.config import settings, get_logger
from caspar.knowledge import get_retriever
from caspar.tools import (
    get_order_status,
    get_account_info,
    create_ticket,
)

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# Intent Classification Node
# ════════════════════════════════════════════════════════════════════════════

async def classify_intent(state: dict) -> dict:
    """
    Classify the customer's intent from their message.
    
    This is the entry point - determines which handler to route to.
    """
    logger.info("classify_intent_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    if not messages:
        return {"intent": "general"}
    
    # Get the last customer message
    last_message = messages[-1].content if messages else ""
    
    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
        temperature=0  # Deterministic for classification
    )
    
    classification_prompt = f"""Classify the customer's intent into ONE of these categories:

- faq: General questions about policies, products, services, shipping times, return policies, how things work
- order_inquiry: Questions about a SPECIFIC order (mentions order number, tracking number, "my order", "my package")
- account: Account-related issues (login, profile, password, settings, "my account")
- complaint: Expressing dissatisfaction, problems, wanting refunds, frustrated language
- handoff_request: Explicitly asking for a human agent, representative, or real person
- general: Anything else or unclear

IMPORTANT: 
- "How long does shipping take?" = faq (general policy question)
- "Where is my order?" or "Track order #123" = order_inquiry (specific order)

Customer message: "{last_message}"

Respond with just the category name, nothing else."""

    response = llm.invoke([HumanMessage(content=classification_prompt)])
    intent = response.content.strip().lower()
    
    # Validate intent
    valid_intents = ["faq", "order_inquiry", "account", "complaint", "handoff_request", "general"]
    if intent not in valid_intents:
        intent = "general"
    
    logger.info("classify_intent_complete", intent=intent)
    
    return {
        "intent": intent,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# ════════════════════════════════════════════════════════════════════════════
# Intent Handler Nodes
# ════════════════════════════════════════════════════════════════════════════

async def handle_faq(state: dict) -> dict:
    """
    Handle FAQ-type questions using the knowledge base.
    """
    logger.info("handle_faq_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Retrieve relevant knowledge
    retriever = get_retriever()
    docs = retriever.retrieve(last_message)
    
    context = "\n\n".join([doc.page_content for doc in docs]) if docs else ""
    
    return {
        "context": context,
        "handler_used": "faq",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


async def handle_order_inquiry(state: dict) -> dict:
    """
    Handle order-related inquiries by looking up order information.
    """
    logger.info("handle_order_inquiry_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Try to extract order ID from message
    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
        temperature=0
    )
    
    extract_prompt = f"""Extract the order ID from this message if present.
Order IDs look like: TF-XXXXX (e.g., TF-10001) or just the number (e.g., 10001)

Message: "{last_message}"

Respond with just the order ID (e.g., TF-10001 or 10001), or "NONE" if not found."""

    response = llm.invoke([HumanMessage(content=extract_prompt)])
    order_id = response.content.strip()
    
    context = ""
    order_info = None
    
    if order_id != "NONE":
        # Normalize order ID - add TF- prefix if needed
        if not order_id.startswith("TF-"):
            # Remove any non-numeric prefix and add TF-
            numeric_part = ''.join(filter(str.isdigit, order_id))
            if numeric_part:
                order_id = f"TF-{numeric_part}"
        
        # Look up order
        order_result = get_order_status(order_id)
        if order_result["found"]:
            order = order_result["order"]
            # Extract item names from item dicts
            item_names = [item["name"] if isinstance(item, dict) else str(item) for item in order["items"]]
            order_info = {
                "order_id": order["order_id"],
                "status": order["status"],
                "items": order["items"],
                "shipping_address": order.get("shipping_address", "N/A"),
                "tracking_number": order.get("tracking_number", "Not yet available"),
                "estimated_delivery": order.get("estimated_delivery", "TBD"),
            }
            context = f"""Order Information:
- Order ID: {order['order_id']}
- Status: {order['status']}
- Items: {', '.join(item_names)}
- Shipping: {order.get('shipping_method', 'N/A')}
- Tracking: {order.get('tracking_number') or 'Not yet available'}
- Estimated Delivery: {order.get('estimated_delivery') or 'TBD'}"""
        else:
            order_info = {"error": "Order not found"}
            context = f"Order {order_id} not found in system."
    else:
        context = "No order ID provided. Ask customer for their order number."
    
    return {
        "context": context,
        "handler_used": "order_inquiry",
        "order_id": order_id if order_id != "NONE" else None,
        "order_info": order_info,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


async def handle_account(state: dict) -> dict:
    """
    Handle account-related inquiries.
    """
    logger.info("handle_account_start", conversation_id=state.get("conversation_id"))
    
    customer_id = state.get("customer_id")
    context = ""
    
    if customer_id:
        account_result = get_account_info(customer_id)
        if account_result["found"]:
            account = account_result["account"]
            context = f"""Customer Account Information:
- Name: {account['name']}
- Email: {account['email']}
- Status: {account['status']}
- Loyalty Tier: {account.get('loyalty_tier', 'Standard')}
- Member Since: {account.get('member_since', 'N/A')}"""
        else:
            context = "Customer account not found."
    else:
        context = "No customer ID available. Ask customer to verify their identity."
    
    return {
        "context": context,
        "handler_used": "account",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


async def handle_complaint(state: dict) -> dict:
    """
    Handle customer complaints with empathy and create a ticket.
    """
    logger.info("handle_complaint_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    customer_id = state.get("customer_id", "UNKNOWN")
    
    # Create a support ticket for the complaint
    ticket_result = create_ticket(
        customer_id=customer_id,
        category="complaint",
        subject="Customer Complaint",
        description=last_message,
        priority="high",
        conversation_id=state.get("conversation_id")
    )
    
    ticket_id = ticket_result["ticket"]["ticket_id"]
    
    context = f"""Complaint ticket created:
- Ticket ID: {ticket_id}
- Priority: High
- Status: Open

Acknowledge the customer's frustration with empathy. Reference the ticket number.
Assure them their concern is being taken seriously."""
    
    return {
        "context": context,
        "handler_used": "complaint",
        "ticket_id": ticket_id,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


async def handle_general(state: dict) -> dict:
    """
    Handle general inquiries that don't fit other categories.
    """
    logger.info("handle_general_start", conversation_id=state.get("conversation_id"))
    
    # Use knowledge base for general context
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    retriever = get_retriever()
    docs = retriever.retrieve(last_message)
    
    context = "\n\n".join([doc.page_content for doc in docs]) if docs else ""
    
    return {
        "context": context,
        "handler_used": "general",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# ════════════════════════════════════════════════════════════════════════════
# Response Generation Node
# ════════════════════════════════════════════════════════════════════════════

async def respond(state: dict) -> dict:
    """
    Generate the final response to the customer.
    
    Uses all gathered context to craft a helpful, empathetic response.
    """
    logger.info("respond_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    context = state.get("context", "")
    intent = state.get("intent", "general")
    handler_used = state.get("handler_used", "general")
    
    # Build conversation history for context
    conversation_history = "\n".join([
        f"{'Customer' if isinstance(m, HumanMessage) else 'Agent'}: {m.content}"
        for m in messages[-5:]  # Last 5 messages for context
    ])
    
    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
        temperature=0.7  # Slightly creative for natural responses
    )
    
    system_prompt = """You are CASPAR, a friendly and helpful customer service assistant for TechFlow Solutions.

Your personality:
- Warm, professional, and empathetic
- Clear and concise in explanations
- Always helpful and solution-oriented
- Acknowledge customer feelings when appropriate

Guidelines:
- If you have specific information from the context, use it
- If you don't have enough information, ask clarifying questions
- Never make up information about orders, accounts, or policies
- For complaints, acknowledge feelings first, then offer solutions
- Keep responses conversational, not robotic"""

    user_prompt = f"""Intent: {intent}
Handler: {handler_used}

Context/Information gathered:
{context if context else "No specific context available."}

Recent conversation:
{conversation_history}

Generate a helpful response to the customer's last message. Be natural and conversational."""

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    
    ai_response = response.content
    
    logger.info("respond_complete", response_length=len(ai_response))
    
    return {
        "messages": [AIMessage(content=ai_response)],
        "pending_response": ai_response,  # For approval workflow
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
