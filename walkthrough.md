# Walkthrough - Phase 13D Final Production Polish

## FIFA Judge Demo Walkthrough

### 1. Login
Navigate to `http://localhost:3000/login`

**Demo Credentials:**
- Email: `operator@stadium.aegis.com`
- Password: `password123`

*(These credentials work with the mock authentication system)*

### 2. Dashboard Overview
After login, you'll see the Operations Command Central:
- Live crowd count telemetry
- System health status
- Active incidents counter
- Interactive stadium map

### 3. Mission Control
Navigate to `/mission-control`

**Features:**
- Digital Twin visualization with live bus/shuttle positions
- Health and Risk gauges
- AI-generated recommendations with confidence scores
- Command approval workflow
- Operational timeline

**Demo Button:** Click "Start FIFA Demo" to cycle through 9 match scenarios:
1. Pre-Match (Gates open)
2. Kickoff
3. Goal (Celebration surge)
4. Halftime
5. Crowd Surge (Gate D bottleneck)
6. Medical Emergency
7. Power Failure
8. Security Alert
9. Evacuation

### 4. Copilot AI Assistant
Navigate to `/copilot`

**Try these queries:**
- "Why is Gate A crowded?"
- "Summarize active incidents"
- "Show volunteer shortages"
- "Recommend transport improvements"
- "Accessibility issues near Gate C"

**Features:**
- Multi-language support (EN, ES, FR, PT, AR)
- Workflow step execution
- Real-time streaming responses
- Confidence scoring
- Source attribution

### 5. Command Approval Flow
When a recommendation requires approval:
1. Click "Approve" to authorize
2. Command is logged in the audit ledger
3. Mission Control updates automatically

---

## Quick Start for Judges

```bash
# Start the complete system
start_all.bat

# Or manually:
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

**Open http://localhost:3000 and click "Start FIFA Demo"**