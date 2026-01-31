# Development Guide

## Architecture Overview

### LangGraph State Machine

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Triage Node                         │
│ - Check recurrence (Qdrant)        │
│ - Classify severity (LLM)          │
│ - Generate empathetic reply        │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Route Decision                      │
│ - Crisis? → Crisis Node             │
│ - Booking? → Scheduler Node         │
│ - Normal? → End (reply sent)        │
└──────┬──────────────────────────────┘
       │
   ┌───┴───┐
   ▼       ▼
┌─────┐ ┌──────────┐
│Crisis│ │Scheduler │
│Node  │ │Node      │
└─────┘ └──────────┘
```

### Data Flow

```
User Message
    ↓
Chainlit (app.py)
    ↓
LangGraph (graph.py)
    ↓
┌─────────────┬─────────────┬─────────────┐
│   Qdrant    │     LLM     │   Store     │
│  (memory)   │  (Gemini)   │  (users)    │
└─────────────┴─────────────┴─────────────┘
    ↓
Response to User
```

## Code Structure

### `src/app.py` - Chainlit Application
**Responsibilities:**
- User session management
- Login flow
- Message handling
- Therapist notifications
- Calendar display
- Action callbacks (Accept/Reject)

**Key Functions:**
- `start()` - Initialize chat session
- `main()` - Handle user messages
- `on_accept()` - Handle appointment acceptance
- `on_reject()` - Handle appointment rejection

### `src/graph.py` - LangGraph Workflow
**Responsibilities:**
- Message triage and severity classification
- Recurrence detection
- Empathetic response generation
- Appointment scheduling flow
- Crisis intervention

**Key Functions:**
- `triage_node()` - Main analysis and response
- `crisis_node()` - Crisis response
- `scheduler_node()` - Multi-step booking
- `route_after_triage()` - Decision routing

**State Management:**
```python
AgentState = {
    "messages": List[BaseMessage],
    "user_id": str,
    "recurrence_count": int,
    "booking_step": str,  # none, ask_intent, wait_intent, ask_slots, wait_slots, done
    "booking_data": dict,
}
```

### `src/models.py` - Data Models
**User Model:**
```python
User(
    user_id: str,
    username: str,
    full_name: str,
    location: str,
    email: str,
    gender: str,
    is_therapist: bool
)
```

### `src/services/` - Backend Services

#### `store.py` - Data Storage
**In-Memory Storage:**
- `_users`: Dict[user_id, User]
- `_pending_requests`: Dict[therapist_id, List[request]]
- `_confirmed_appointments`: Dict[request_id, appointment]

**Upgrade Path:**
```python
# Replace with database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://...')
Session = sessionmaker(bind=engine)
```

#### `qdrant.py` - Conversation Memory
**Current Implementation:**
- In-memory keyword matching
- Simple recurrence detection

**Upgrade Path:**
```python
from qdrant_client import QdrantClient
from langchain.embeddings import GoogleGenerativeAIEmbeddings

client = QdrantClient(url=os.getenv("QDRANT_URL"))
embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001")

# Store with embeddings
# Search by semantic similarity
```

#### `calendar.py` - Appointment Management
**Current Implementation:**
- Therapist filtering
- Request broadcasting
- First-accept-wins logic
- Stub calendar integration

**Upgrade Path:**
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_calendar_event(user, therapist, timeslot):
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': f'Therapy Session',
        'start': {'dateTime': timeslot},
        # ...
    }
    service.events().insert(calendarId='primary', body=event).execute()
```

## Adding New Features

### 1. Add a New Conversation Flow

**Example: Add "Mood Tracking" feature**

1. **Update AgentState** (`models.py`):
```python
class AgentState(TypedDict, total=False):
    # ... existing fields
    mood_tracking_step: str
    mood_history: List[dict]
```

2. **Create Node** (`graph.py`):
```python
def mood_tracking_node(state: AgentState) -> dict:
    step = state.get("mood_tracking_step", "none")
    if step == "ask_mood":
        return {
            "messages": [AIMessage(content="How are you feeling today? (1-10)")],
            "mood_tracking_step": "wait_mood"
        }
    # ... handle response
```

3. **Add Routing** (`graph.py`):
```python
workflow.add_node("mood_tracker", mood_tracking_node)
workflow.add_conditional_edges("triage", route_decision, {
    # ... existing routes
    "mood_tracker": "mood_tracker"
})
```

### 2. Add a New User Field

1. **Update Model** (`models.py`):
```python
class User:
    def __init__(self, ..., new_field: str = ""):
        # ...
        self.new_field = new_field
```

2. **Update Store** (`store.py`):
```python
def seed_demo_users():
    add_user(User("user_1", "alice", ..., new_field="value"))
```

3. **Use in Logic** (`graph.py` or `app.py`):
```python
user = store.get_user(user_id)
if user.new_field == "something":
    # ... custom logic
```

### 3. Customize AI Behavior

**Edit Prompts** (`prompts.py`):
```python
TRIAGE_SYSTEM_PROMPT = """
You are an empathetic AI assistant.

NEW INSTRUCTION: Always ask about sleep quality.

1. If the user mentions sleep issues...
2. Otherwise, reply empathetically...
"""
```

**Adjust Temperature** (`graph.py`):
```python
# More creative (0.7-1.0)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.8)

# More focused (0.0-0.3)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.1)
```

## Testing

### Manual Testing Checklist

- [ ] User login (alice, bob)
- [ ] Therapist login (dr_smith, dr_jones)
- [ ] Guest mode
- [ ] Normal conversation
- [ ] Recurring issue detection
- [ ] Appointment request flow
- [ ] Therapist notification
- [ ] Accept appointment
- [ ] Reject appointment
- [ ] Calendar display
- [ ] Crisis detection

### Adding Automated Tests

Create `tests/test_graph.py`:
```python
import pytest
from src.graph import app_graph
from langchain_core.messages import HumanMessage

def test_normal_conversation():
    inputs = {
        "messages": [HumanMessage(content="I had a good day")],
        "user_id": "test_user",
        "recurrence_count": 0,
        "booking_step": "none",
    }
    result = app_graph.invoke(inputs)
    assert len(result["messages"]) > 1
    # Check response is empathetic

def test_crisis_detection():
    inputs = {
        "messages": [HumanMessage(content="I want to hurt myself")],
        "user_id": "test_user",
        "recurrence_count": 0,
        "booking_step": "none",
    }
    result = app_graph.invoke(inputs)
    last_message = result["messages"][-1].content
    assert "988" in last_message
```

Run tests:
```bash
uv run pytest tests/
```

## Production Deployment

### 1. Database Setup

**PostgreSQL with SQLAlchemy:**
```python
# models.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserDB(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    # ... other fields
```

### 2. Environment Configuration

**Production `.env`:**
```bash
GOOGLE_API_KEY=prod_key
QDRANT_URL=https://your-qdrant.cloud
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379
SECRET_KEY=your_secret_key
```

### 3. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY .chainlit/ ./.chainlit/
COPY chainlit.md ./

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "chainlit", "run", "src/app.py", "--host", "0.0.0.0"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - qdrant
      - postgres
  
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: therapy_bot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

### 4. Monitoring

**Add Logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def triage_node(state: AgentState) -> dict:
    logger.info(f"Processing message for user {state['user_id']}")
    # ... existing code
```

**Add Metrics:**
```python
from prometheus_client import Counter, Histogram

message_counter = Counter('messages_processed', 'Total messages processed')
response_time = Histogram('response_time_seconds', 'Response time')

@response_time.time()
def triage_node(state: AgentState) -> dict:
    message_counter.inc()
    # ... existing code
```

## Common Customizations

### Change Crisis Hotline Number
Edit `src/prompts.py`:
```python
HOTLINE_NUMBER = "your_country_hotline"
```

### Add More Demo Users
Edit `src/services/store.py`:
```python
def seed_demo_users():
    # ... existing users
    add_user(User("user_3", "charlie", "Charlie User", "Boston", "charlie@example.com", "male", False))
```

### Customize UI Theme
Edit `.chainlit/config.toml`:
```toml
[UI.theme.light.primary]
main = "#FF6B6B"  # Red theme
```

### Change AI Model
Edit `src/graph.py`:
```python
# Use different Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)

# Or switch to OpenAI
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", temperature=0.3)
```

## Debugging Tips

### Enable Debug Logging
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "your_key"
```

### Print State at Each Node
```python
def triage_node(state: AgentState) -> dict:
    print(f"DEBUG: Current state: {state}")
    # ... existing code
```

### Test Individual Functions
```python
# In Python REPL
from src.services.store import seed_demo_users, get_user

seed_demo_users()
user = get_user("user_1")
print(user.username)  # Should print "alice"
```

## Performance Optimization

### 1. Cache LLM Responses
```python
from langchain.cache import InMemoryCache
import langchain
langchain.llm_cache = InMemoryCache()
```

### 2. Async Processing
```python
# Already using async in app.py
async def main(message: cl.Message):
    async for output in app_graph.astream(inputs):
        # Process streaming output
```

### 3. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
async def main(message: cl.Message):
    # ... existing code
```

## Security Considerations

### 1. Input Validation
```python
def sanitize_input(content: str) -> str:
    # Remove potentially harmful content
    return content.strip()[:1000]  # Limit length
```

### 2. API Key Protection
- Never commit `.env` to git (already in `.gitignore`)
- Use environment variables in production
- Rotate keys regularly

### 3. User Data Privacy
- Implement data retention policies
- Add GDPR compliance features
- Encrypt sensitive data

## Getting Help

- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Chainlit Docs**: https://docs.chainlit.io/
- **Gemini API**: https://ai.google.dev/docs

## Contributing

When adding features:
1. Update relevant documentation
2. Add tests if possible
3. Follow existing code style
4. Update CHANGELOG.md (if exists)
5. Test thoroughly before committing
