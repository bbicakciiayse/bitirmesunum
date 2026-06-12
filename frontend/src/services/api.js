/**
 * API service — all HTTP calls to the FastAPI backend go through here.
 * Base URL is read from the environment so it never has to be hardcoded.
 *
 * Local dev:   VITE_API_URL=http://localhost:8000  (frontend/.env)
 * Production:  VITE_API_URL=https://api.your-domain.com
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json();
}

// ── Health ────────────────────────────────────────────────────
export const getHealth = () => request("GET", "/health");

// ── Auth ─────────────────────────────────────────────────────
export const login         = (email, password) => request("POST", "/auth/login", { email, password });
export const verifyMfa     = (email, code)     => request("POST", "/auth/verify-mfa", { email, code });

// ── Payment ──────────────────────────────────────────────────
export const createCheckout  = (plan, email)   => request("POST", "/payment/create-checkout", { plan, email });
export const confirmPayment  = (session_id)    => request("POST", "/payment/confirm", { session_id });

// ── Data upload ───────────────────────────────────────────────
// Note: file upload uses FormData, not JSON — handled separately in the component
export const getDataPreview  = ()              => request("GET",  "/uploaded-data-preview");
export const selectTarget    = (target_column) => request("POST", "/select-target", { target_column });

// ── Training ─────────────────────────────────────────────────
export const trainModel      = (payload)       => request("POST", "/train", payload);
export const getModelMetrics = ()              => request("GET",  "/model-metrics");
export const saveModel       = ()              => request("POST", "/save-model");

// ── Prediction ────────────────────────────────────────────────
export const getModelInputSchema = ()          => request("GET",  "/model-input-schema");
export const predict             = (payload)   => request("POST", "/predict", payload);

// ── Sensitivity ───────────────────────────────────────────────
export const priceSensitivity = (payload)      => request("POST", "/price-sensitivity", payload);

// ── Dashboard ─────────────────────────────────────────────────
export const saveResult       = (result)       => request("POST", "/save-result", result);
export const getSavedResults  = ()             => request("GET",  "/saved-results");
export const getDashboardSummary = ()          => request("GET",  "/dashboard-summary");
