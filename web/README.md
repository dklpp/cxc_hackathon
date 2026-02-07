# Customer Debt Management Web UI

Modern React-based web interface for internal workers to track customer information, debts, schedule calls, and manage call history with transcript analysis.

## Features

- **Customer Management**: Search and view customer profiles
- **Debt Tracking**: View all customer debts with detailed information
- **Call Scheduling**: Schedule calls with status tracking (pending/completed/cancelled)
- **Call History**: View all past calls with transcripts and analysis results
- **Transcript Upload**: Upload call transcripts for AI-powered analysis

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy
- **UI Components**: Lucide React icons, modern responsive design

## Setup

### Backend (FastAPI)

1. Install dependencies:
```bash
uv sync
```

2. Start the API server:
```bash
uv run python api/main.py
```

The API will be available at `http://localhost:8000`

### Frontend (React)

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The web app will be available at `http://localhost:5173`

## Usage

1. **View Customers**: Browse the customer list or search by name, phone, or email
2. **Customer Details**: Click on a customer to view:
   - Personal information
   - All debts with balances and status
   - Scheduled calls
   - Quick actions to schedule calls or view history
3. **Schedule Call**: Click "Schedule Call" button, select date/time, and add notes
4. **Call History**: View all past calls, upload transcripts, and see analysis results

## API Endpoints

- `GET /api/customers` - List/search customers
- `GET /api/customers/{id}` - Get customer details
- `GET /api/customers/{id}/debts` - Get customer debts
- `GET /api/customers/{id}/call-history` - Get call history
- `POST /api/scheduled-calls` - Schedule a new call
- `POST /api/customers/{id}/upload-transcript` - Upload and analyze transcript

## Development

The frontend uses Vite for fast development with hot module replacement. The backend uses FastAPI with automatic API documentation at `/docs`.
