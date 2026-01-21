# CASPAR - Customer Service AI Agent

**C**ustomer **A**ssistance **S**ystem with **P**ersonalized **A**utomated **R**esponses

A production-ready AI customer service agent built with LangGraph, demonstrating:
- Intent classification and routing
- RAG-powered knowledge base
- Order lookup and ticket creation tools
- Sentiment analysis and frustration detection
- Human handoff with full context preservation

## Quick Start

### 1. Setup Environment

```bash
# Clone and enter directory
cd caspar

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 2. Build Knowledge Base

```bash
python scripts/build_knowledge_base.py
```

### 3. Run the API

```bash
uvicorn caspar.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Start a conversation
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-1000", "initial_message": "What is your return policy?"}'
```

## Project Structure

```
caspar/
├── src/caspar/
│   ├── agent/           # Core agent logic
│   │   ├── state.py     # State definition
│   │   ├── nodes.py     # Processing nodes
│   │   └── graph.py     # LangGraph workflow
│   ├── api/             # REST API
│   │   ├── main.py      # FastAPI application
│   │   └── metrics.py   # Metrics tracking
│   ├── config/          # Configuration
│   │   ├── settings.py  # Pydantic settings
│   │   └── logging.py   # Structured logging
│   ├── knowledge/       # RAG system
│   │   ├── loader.py    # Document loading
│   │   └── retriever.py # ChromaDB retrieval
│   ├── tools/           # Business tools
│   │   ├── orders.py    # Order lookup
│   │   ├── tickets.py   # Ticket creation
│   │   └── accounts.py  # Account info
│   └── handoff/         # Escalation system
│       ├── triggers.py  # Escalation triggers
│       ├── queue.py     # Handoff queue
│       ├── context.py   # Context builder
│       └── notifications.py
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── evaluation/     # Quality evaluation
├── data/               # Knowledge base content
├── scripts/            # Utility scripts
├── Dockerfile          # Container definition
└── docker-compose.yml  # Local development
```

## Running Tests

```bash
# Run unit tests (fast, no LLM calls)
python scripts/run_tests.py --suite unit

# Run integration tests (uses LLM)
python scripts/run_tests.py --suite integration

# Run all tests
python scripts/run_tests.py --suite all
```

## Docker Deployment

```bash
# Build image
docker build -t caspar:latest .

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY caspar:latest

# Or use docker-compose
docker-compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Current metrics |
| `/conversations` | POST | Start conversation |
| `/conversations/{id}/messages` | POST | Send message |
| `/conversations/{id}` | GET | Get status |
| `/conversations/{id}` | DELETE | End conversation |

## From the Book

This project is the capstone for **"Zero to AI Agent: Learn Python and Build Intelligent Systems from Scratch"** (Chapter 20).

## License

MIT
