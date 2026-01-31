# Setup Guide

## Quick Start (5 minutes)

### 1. Get a Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 2. Install uv (if not already installed)

**Linux/WSL/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd therapy-bot

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env

# Install dependencies (this will also create a virtual environment)
uv sync
```

### 4. Run the Application

```bash
# Make the run script executable (Linux/WSL/macOS only)
chmod +x run.sh

# Run the application
./run.sh

# Or directly:
uv run chainlit run src/app.py
```

### 5. Open in Browser

The application will be available at: `http://localhost:8000`

**For WSL users**: Open this URL in your Windows browser (Chrome, Edge, Firefox, etc.)

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"
**Solution**: Make sure your `.env` file exists and contains:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

### Issue: "uv: command not found"
**Solution**: Install uv using the instructions in step 2 above, then restart your terminal.

### Issue: "Port 8000 already in use"
**Solution**: 
1. Find and kill the process using port 8000:
   ```bash
   # Linux/WSL/macOS
   lsof -ti:8000 | xargs kill -9
   
   # Or specify a different port
   uv run chainlit run src/app.py --port 8001
   ```

### Issue: Python version error
**Solution**: Make sure you have Python 3.12 or higher:
```bash
python --version
# If you need to install Python 3.12, uv can do it for you:
uv python install 3.12
```

### Issue: Application starts but shows errors in browser
**Solution**: 
1. Check the terminal for error messages
2. Verify your API key is correct
3. Make sure you have internet connection (needed for Gemini API)

## Testing the Application

### Test as a Regular User

1. Open `http://localhost:8000`
2. Type: `alice` (to log in as Alice)
3. Try saying: "I had a really tough day at work"
4. The bot should respond empathetically
5. Try requesting an appointment: "I'd like to schedule an appointment"

### Test as a Therapist

1. Open `http://localhost:8000` in a new incognito/private window
2. Type: `dr_smith` (to log in as Dr. Smith)
3. You should see any pending appointment requests
4. Click "Accept" to confirm an appointment

### Test Crisis Detection

1. Type a message containing crisis keywords (for testing only!)
2. The bot should immediately provide the crisis hotline number
3. **Note**: This is for testing purposes only. Real crisis situations should always be directed to professionals.

## Demo Accounts

### Regular Users
- **alice** - Alice User (New York, Female)
- **bob** - Bob User (Brooklyn, Male)

### Therapists
- **dr_smith** - Dr. Jane Smith (New York, Female)
- **dr_jones** - Dr. John Jones (Brooklyn, Male)

## Next Steps

- Read the main [README.md](README.md) for full documentation
- Customize the `.chainlit/config.toml` for your preferences
- Explore the code in the `src/` directory
- Consider implementing the future enhancements listed in README.md
