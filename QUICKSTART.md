# Quick Start Guide

## Prerequisites

- Python 3.9+ with `uv` installed
- Node.js 18+ and npm

## Setup Instructions

### 1. Install Python Dependencies

```bash
uv sync
```

This will install:
- FastAPI
- SQLAlchemy
- Uvicorn
- Other required packages

### 2. Set Up PostgreSQL Database

Make sure you have PostgreSQL installed and running. Create a database:

```bash
createdb banking_system
```

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/banking_system"
```

Or add it to your `.env` file (copy from `.env.example`).

The database tables will be automatically created when you first run the API. To populate with sample data:

```bash
uv run python DB/db_usage_example.py
```

### 3. Start the Backend API

```bash
uv run python api/main.py
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### 4. Start the Frontend

Open a new terminal:

```bash
cd web
npm install
npm run dev
```

The web app will be available at `http://localhost:5173`

## Usage

1. **View Customers**: Navigate to `http://localhost:5173` to see the customer list
2. **Search**: Use the search bar to find customers by name, phone, or email
3. **View Details**: Click on any customer card to see:
   - Personal information
   - All debts
   - Scheduled calls
   - Quick actions
4. **Schedule Call**: Click "Schedule Call" button, select date/time, add notes
5. **View History**: Click "Call History" to see past calls and upload transcripts

## Features

- ✅ Modern React UI with Tailwind CSS
- ✅ FastAPI backend with automatic API documentation
- ✅ Customer search and filtering
- ✅ Debt tracking and visualization
- ✅ Call scheduling with status tracking
- ✅ Call history with transcript upload
- ✅ AI-powered transcript analysis (via Gemini)

## Troubleshooting

### Database Issues

If you need to recreate the database:
```bash
# Drop and recreate the PostgreSQL database
dropdb banking_system
createdb banking_system
uv run python DB/db_usage_example.py
```

Make sure your `DATABASE_URL` environment variable is set correctly:
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/banking_system"
```

### Port Conflicts

If port 8000 is in use, modify `api/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change port
```

If port 5173 is in use, Vite will automatically use the next available port.

### API Connection Issues

Make sure the backend is running before starting the frontend. The frontend proxies API requests to `http://localhost:8000` by default (configured in `web/vite.config.js`).
