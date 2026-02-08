# Automated Client Engagement Platform

An AI-powered platform that transforms traditional cold calling into data-driven, personalized client engagement for financial institutions.

## Problem

Financial institutions face significant challenges with traditional outreach:
- **Low Success Rates** - Cold calls achieve only 10-15% effectiveness
- **Time-Intensive Research** - Manual client research requires substantial resources
- **Missed Opportunities** - Without data-driven insights, clients are contacted at suboptimal times
- **Scalability Constraints** - Human agents cannot efficiently analyze large volumes of client data

## Solution

A four-stage automated pipeline that analyzes customer data, generates personalized strategies, and executes outreach through AI-powered voice calls.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. DATA        │ →  │  2. PROFILE     │ →  │  3. OUTREACH    │ →  │  4. INSIGHTS    │
│  INGESTION      │    │  GENERATION     │    │  EXECUTION      │    │  DASHBOARD      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │                      │
        ▼                      ▼                      ▼                      ▼
   Customer DB            AI Agents             ElevenLabs              Track all
   (SQLite)               analyze &             Voice Calls            interactions
                          strategize            + Email/SMS            & outcomes
```

## Key Innovation

**Distributed AI Architecture** - Using smaller, specialized models for dedicated tasks rather than one large model. Achieved **30% improvement in efficiency**.

## Built With

### Backend
- **Python 3.9+** - Core language
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Database

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation

### AI/ML Services
- **Google Gemini** (via OpenRouter) - Strategy generation & transcript analysis
- **ElevenLabs** - AI voice synthesis for outbound calls

### Communication
- **Twilio** - Outbound phone calls & SMS

## Project Structure

```
cxc_hackathon/
├── api/                         # FastAPI backend
│   └── main.py                  # REST API endpoints
│
├── DB/                          # Database layer
│   ├── db_manager.py            # SQLAlchemy models & CRUD
│   ├── customers/               # 10 sample customer profiles (JSON)
│   └── SCHEMA.md                # Database schema docs
│
├── strategy_planning/           # AI strategy generation
│   ├── prompt_template.py       # Prompt builder with placeholders
│   ├── strategy_pipeline.py     # Main strategy pipeline
│   └── gemini_example.py        # Gemini API integration
│
├── transcript_analysis/         # Call transcript processing
│   ├── transcript_analyzer.py   # AI-powered transcript analysis
│   └── prompt_template.py       # Analysis prompts
│
├── prompts/                     # Master AI prompts
│   ├── master_prompt_voice.md   # Voice call agent prompt
│   └── master_prompt_email.md   # Email/SMS prompt
│
├── stt/                         # Speech-to-text
│   └── speech_to_text.py        # Deepgram integration
│
├── tts/                         # Text-to-speech
│   └── text_to_speech.py        # ElevenLabs integration
│
├── web/                         # React dashboard
│   └── src/
│       └── pages/
│           ├── CustomerList.jsx
│           ├── CustomerDetail.jsx
│           └── CallHistory.jsx
│
└── tests/outbound_calling/      # Twilio + OpenAI prototype
    ├── realtime_server.py       # WebSocket bridge
    └── server.py                # Flask server for TwiML
```

## Customer Profile Types

The system classifies customers into 5 profile types for personalized engagement:

| Type | Name | Credit Score | Days Past Due | Approach |
|------|------|--------------|---------------|----------|
| 1 | Low-Risk Recovery | 700+ | 0-30 | Friendly, fee waiver offers |
| 2 | Early Financial Stress | 650+ | 15-60 | Educational, helpful |
| 3 | Moderate Hardship | 580-650 | 60-120 | Payment plan options |
| 4 | Severe Crisis | <580 | 120+ | Compassionate, resources |
| 5 | High-Value VIP | Any | Any | Premium treatment |

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- [uv](https://github.com/astral-sh/uv) package manager

### 1. Clone and Setup

```bash
git clone https://github.com/dklpp/cxc_hackathon.git
cd cxc_hackathon

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync --no-install-project

# Activate virtual environment
source .venv/bin/activate
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
ELEVEN_LABS_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### 3. Initialize Database

```bash
uv run python DB/db_usage_example.py
```

This creates the SQLite database and loads 10 sample customers.

### 4. Run the API Server

```bash
uv run uvicorn api.main:app --reload
```

API available at `http://localhost:8000`

### 5. Run the Frontend (optional)

```bash
cd web
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

## Usage Examples

### Generate a Strategy for a Customer

```python
from strategy_planning.prompt_template import build_strategy_prompt

prompt = build_strategy_prompt(
    customer_first_name="Maria",
    customer_last_name="Santos",
    credit_score=785,
    days_past_due=15,
    preferred_channel="call"
)
# Send to Gemini for strategy generation
```

### Analyze a Call Transcript

```python
from transcript_analysis import TranscriptAnalyzer

analyzer = TranscriptAnalyzer()
result = analyzer.analyze_transcript_file(
    "call_recording.txt",
    customer_id=1
)
print(result['call_outcome'])
print(result['recommendations'])
```

## Sample Customers

The system includes 10 realistic customer profiles:

1. **Maria Santos** - Good standing, forgot payment while traveling (15 days)
2. **David Kim** - Autopay card expired (5 days)
3. **James Wilson** - Laid off from GM (62 days)
4. **Tyrone Washington** - Medical emergency (58 days)
5. **Robert Miller** - Job loss + divorce (328 days)
6. **Sarah Chen** - New job starting, needs 2-week grace (8 days)
7. **Patricia Nguyen** - Bank processing delay (3 days)
8. **Michael O'Brien** - Self-employed, slow season (95 days)
9. **Linda Martinez** - Recently widowed (35 days)
10. **Emmanuel Okafor** - Recent grad, first missed payment (12 days)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers` | List all customers |
| GET | `/customers/{id}` | Get customer details |
| GET | `/customers/{id}/summary` | Get customer with debts & history |
| POST | `/customers/{id}/call` | Initiate AI call to customer |
| GET | `/communications` | List all communication logs |

## Expected Outcomes

- Increase engagement success rates beyond industry standard 10-15%
- Reduce research and preparation time per client interaction
- Scale personalized outreach without proportional increases in resources
- Improve customer satisfaction through relevant, well-timed communications
