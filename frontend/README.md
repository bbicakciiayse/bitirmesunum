# Frontend — React + Vite

## Setup

```bash
npm install
cp .env.example .env
```

## Run

```bash
npm run dev
```

App runs at: http://localhost:5173

## Environment Variables

| Variable       | Description              | Default                 |
|----------------|--------------------------|-------------------------|
| `VITE_API_URL` | FastAPI backend base URL | http://localhost:8000   |

## Pages

| File                          | Route         | Status      |
|-------------------------------|---------------|-------------|
| `LandingPage.jsx`             | `/`           | 🔲 Skeleton |
| `AuthPage.jsx`                | `/auth`       | 🔲 Skeleton |
| `MainPricingAnalysisPage.jsx` | `/analysis`   | 🔲 Skeleton |
| `DashboardPage.jsx`           | `/dashboard`  | 🔲 Skeleton |

## Build

```bash
npm run build    # outputs to dist/
npm run preview  # preview the production build locally
```
