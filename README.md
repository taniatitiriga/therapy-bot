# Therapy Bot 🌟

An empathetic AI chatbot for venting and mental health support, with the ability to schedule therapy sessions with human professionals or provide crisis hotline information depending on severity.

## Tech Stack

- **LangChain** - LLM orchestration framework
- **LangGraph** - Stateful agent workflow management
- **Google Gemini API** - AI language model (gemini-2.0-flash-exp)
- **Qdrant** - Vector database for conversation memory (in-memory fallback for MVP)
- **Google Calendar API** - Appointment scheduling (stub implementation for MVP)
- **Chainlit** - Web-based chat interface
- **uv** - Fast Python package manager

## Features

### 1. Empathetic Listening
The bot provides supportive responses by:
- Mirroring user's feelings ("Sounds like you had a hard day.")
- Asking follow-up questions ("How did that make you feel?")
- Simulating active listening
- Asking before giving advice ("Do you want to vent, or do you want advice?")

### 2. Smart Triage System
The bot analyzes conversation severity and recurrence:
- **Normal**: Everyday venting - continues empathetic conversation
- **Concerning**: Recurring serious issues - suggests professional help
- **Crisis**: Life-threatening situations - provides immediate hotline resources

### 3. Appointment Scheduling
When problems are recurring or user requests it:
- User specifies availability (e.g., "next Friday after 11 am", "any time next Tuesday")
- Optional preferences: therapist gender, city/location
- System broadcasts request to matching therapists
- First therapist to accept gets the appointment (ride-sharing model)
- Both parties receive Google Calendar invites

### 4. Crisis Intervention
For severe cases (suicide, self-harm mentions):
- Bot immediately stops conversation
- Provides crisis hotline number (988 - US National Suicide Prevention Lifeline)
- Encourages immediate professional help

### 5. User System
- **Regular Users**: Chat interface + calendar view of appointments
- **Therapist Users**: Receive appointment notifications with Accept/Reject buttons + calendar view
- Demo accounts: `alice`, `bob` (users), `dr_smith`, `dr_jones` (therapists)

## Installation

### Prerequisites
- Python 3.12 or higher
- uv package manager
- Google Gemini API key

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd therapy-bot
```

2. **Create `.env` file**
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

3. **Install dependencies**
```bash
uv sync
```

## Running the Application

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Direct command
```bash
uv run chainlit run src/app.py
```

The application will start at `http://localhost:8000`

In WSL, open your Windows browser and navigate to the URL.

## Usage

### Logging In
- Type a username: `alice`, `bob`, `dr_smith`, or `dr_jones`
- Or say "hi" to continue as a guest

### As a Regular User
1. Share what's on your mind
2. The bot will respond empathetically
3. If issues are recurring, bot may suggest scheduling with a therapist
4. You can also explicitly ask to "schedule an appointment"
5. View your appointments in the calendar section

### As a Therapist
1. Log in with therapist credentials (`dr_smith` or `dr_jones`)
2. Receive appointment request notifications
3. Accept or reject appointment requests
4. View confirmed appointments in calendar

## Project Structure

```
therapy-bot/
├── src/
│   ├── app.py              # Chainlit application entry point
│   ├── graph.py            # LangGraph workflow (triage → empathetic/scheduler/crisis)
│   ├── models.py           # Data models (User, AgentState)
│   ├── prompts.py          # System prompts and crisis response
│   └── services/
│       ├── calendar.py     # Therapist matching & appointment booking
│       ├── qdrant.py       # Conversation memory & recurrence detection
│       └── store.py        # In-memory user & appointment storage
├── .chainlit/
│   └── config.toml         # Chainlit configuration
├── chainlit.md             # Welcome page markdown
├── .env                    # Environment variables (API keys)
├── pyproject.toml          # Project dependencies
├── uv.lock                 # Dependency lock file
└── run.sh                  # Run script

```

## Architecture

### LangGraph Workflow

```
User Message → Triage Node → Route Decision
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Empathetic  Scheduler   Crisis
    Response      Flow      Response
        ↓           ↓           ↓
        └───────────┴───────────┘
                    ↓
              User receives reply
```

### Appointment Flow

```
Client Request → Filter Therapists → Broadcast to Matches
                                            ↓
                                    Therapists receive notification
                                            ↓
                                    First Accept wins
                                            ↓
                                    Calendar invites sent
```

## Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Required for Gemini API access
- `QDRANT_URL` - Optional, for production Qdrant instance

### Chainlit Settings
Edit `.chainlit/config.toml` to customize:
- UI theme and colors
- Session timeout
- File upload settings
- Telemetry preferences

## Development Notes

### Current MVP Limitations
1. **In-memory storage**: Users and appointments reset on restart
2. **Qdrant fallback**: Uses simple keyword matching instead of vector search
3. **Google Calendar stub**: Doesn't actually create calendar events
4. **No authentication**: Simple username-based login for demo

### Future Enhancements
1. Persistent database (PostgreSQL/MongoDB)
2. Real Qdrant vector search for better recurrence detection
3. Full Google Calendar API integration
4. OAuth authentication
5. Email/SMS notifications
6. Payment processing for appointments
7. Video call integration
8. Multi-language support

## Safety & Ethics

⚠️ **Important Disclaimers**:
- This is a supportive tool, NOT a replacement for professional mental health care
- Crisis detection is keyword-based and may not catch all cases
- Always encourages professional help for serious issues
- Provides immediate crisis hotline resources when needed