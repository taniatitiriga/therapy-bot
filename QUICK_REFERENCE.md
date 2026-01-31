# Quick Reference Card

## 🚀 Start the App
```bash
./run.sh
```
Then open: `http://localhost:8000`

## 👥 Demo Accounts

| Username | Password | Type | Location | Gender |
|----------|----------|------|----------|--------|
| alice | alice123 | User | New York | Female |
| bob | bob123 | User | Brooklyn | Male |
| dr_smith | doctor123 | Therapist | New York | Female |
| dr_jones | doctor123 | Therapist | Brooklyn | Male |

## 💬 Example Conversations

### Casual Venting
```
You: I had a really tough day at work
Bot: Sounds like you had a hard day. How did that make you feel?
```

### Requesting Appointment
```
You: I'd like to schedule an appointment
Bot: When would you like to have a session?
You: Next Friday after 11 am with a female therapist
Bot: I've sent your availability to matching therapists...
```

### Crisis Detection
```
You: [crisis keywords]
Bot: Please reach out to 988 as soon as possible...
```

## 🔧 Common Commands

```bash
# Install dependencies
uv sync

# Run application
uv run chainlit run src/app.py

# Run on different port
uv run chainlit run src/app.py --port 8001

# Check Python version
python --version

# Stop the application
Ctrl+C in terminal
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/app.py` | Main Chainlit application |
| `src/graph.py` | LangGraph workflow logic |
| `src/prompts.py` | AI prompts and responses |
| `.env` | API keys (keep secret!) |
| `.chainlit/config.toml` | UI configuration |

## 🎯 Bot Behavior

### Severity Levels
- **Normal**: Empathetic conversation continues
- **Concerning**: Suggests professional help after recurrence
- **Crisis**: Provides hotline, stops conversation

### Appointment Flow
1. User expresses need or bot suggests
2. User provides availability + preferences
3. System broadcasts to matching therapists
4. First therapist to accept gets appointment
5. Both receive calendar invite

## 🔑 Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional
QDRANT_URL=http://localhost:6333
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Change port: `--port 8001` |
| API key error | Check `.env` file exists |
| uv not found | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Python version | Use Python 3.12: `uv python install 3.12` |

## 📊 Project Structure

```
therapy-bot/
├── src/
│   ├── app.py           # 🌐 Web interface
│   ├── graph.py         # 🤖 AI workflow
│   ├── models.py        # 📦 Data models
│   ├── prompts.py       # 💭 AI prompts
│   └── services/        # 🔧 Backend services
├── .env                 # 🔐 Secrets
├── .chainlit/           # ⚙️ Config
└── run.sh              # ▶️ Start script
```

## 🎨 Customization

### Change Bot Name
Edit `.chainlit/config.toml`:
```toml
[UI]
name = "Your Bot Name"
```

### Modify Prompts
Edit `src/prompts.py`:
```python
TRIAGE_SYSTEM_PROMPT = """
Your custom prompt here...
"""
```

### Add Users
Edit `src/services/store.py`:
```python
def seed_demo_users():
    add_user(User("id", "username", "Name", "City", "email", "gender", False))
```

## 📚 Documentation

- **Full Guide**: `README.md`
- **Setup**: `SETUP.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **This Card**: `QUICK_REFERENCE.md`

## 🆘 Crisis Hotline

**US**: 988 (Suicide & Crisis Lifeline)

*Always direct real crises to professionals*

---

**Need help?** Check the full documentation in `README.md` and `SETUP.md`
