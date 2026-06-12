# Pricing Intelligence App

A full-stack B2B sales win-probability and pricing intelligence platform.

## Monorepo Structure

```
pricing-intelligence-app/
├── frontend/        React + Vite SPA
├── backend/         FastAPI REST API
└── README.md        ← this file
```

## Local Development

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit as needed
uvicorn app.main:app --reload --reload-dir app
```

API runs at: http://localhost:8000
Docs at:     http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env            # edit VITE_API_URL if needed
npm run dev
```

App runs at: http://localhost:5173

## Environment Variables

| Location              | Variable          | Default                  |
|-----------------------|-------------------|--------------------------|
| `backend/.env`        | `FRONTEND_ORIGIN` | `http://localhost:5173`  |
| `frontend/.env`       | `VITE_API_URL`    | `http://localhost:8000`  |
