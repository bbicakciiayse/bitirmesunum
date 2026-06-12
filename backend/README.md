# Backend — FastAPI

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --reload-dir app
```

- API:  http://localhost:8000
- Docs: http://localhost:8000/docs

## Environment Variables

| Variable          | Description                        | Default                 |
|-------------------|------------------------------------|-------------------------|
| `FRONTEND_ORIGIN` | Allowed CORS origin (React app)    | http://localhost:5173   |

## Endpoints (all mock/stub for now)

| Method | Path                      | Status   |
|--------|---------------------------|----------|
| GET    | /health                   | ✅ Live  |
| POST   | /auth/login               | 🔲 Mock  |
| POST   | /auth/verify-mfa          | 🔲 Mock  |
| POST   | /payment/create-checkout  | 🔲 Mock  |
| POST   | /payment/confirm          | 🔲 Mock  |
| POST   | /upload-data              | 🔲 Mock  |
| GET    | /uploaded-data-preview    | 🔲 Mock  |
| POST   | /select-target            | 🔲 Mock  |
| POST   | /train                    | 🔲 Mock  |
| GET    | /model-metrics            | 🔲 Mock  |
| POST   | /save-model               | 🔲 Mock  |
| GET    | /model-input-schema       | 🔲 Mock  |
| POST   | /predict                  | 🔲 Mock  |
| POST   | /price-sensitivity        | 🔲 Mock  |
| POST   | /save-result              | 🔲 Mock  |
| GET    | /saved-results            | 🔲 Mock  |
| GET    | /dashboard-summary        | 🔲 Mock  |
