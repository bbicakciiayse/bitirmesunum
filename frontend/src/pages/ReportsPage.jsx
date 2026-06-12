import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import "./ReportsPage.css"

const STORAGE_KEY = "winsight_reports"

// ── Formatters ────────────────────────────────────────────
function fmtPrice(n) {
  if (n == null || n === "") return "—"
  return "$" + Math.round(Number(n)).toLocaleString("en-US")
}

function fmtDate(iso) {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
}

function fmtPct(v) {
  if (v == null) return "—"
  return (Number(v) * 100).toFixed(1) + "%"
}

// ── Outcome pill buttons ──────────────────────────────────
function OutcomePills({ current, onChange }) {
  return (
    <div className="rp-pills">
      {["Won", "Lost", "Pending"].map((o) => (
        <button
          key={o}
          className={[
            "rp-pill",
            `rp-pill-${o.toLowerCase()}`,
            current === o ? "rp-pill-active" : "",
          ].join(" ")}
          onClick={() => onChange(o)}
          aria-pressed={current === o}
        >
          {o}
        </button>
      ))}
    </div>
  )
}

// ── Single report card ────────────────────────────────────
function ReportCard({ report, onOutcomeChange }) {
  const outcome  = report.actualOutcome || "Pending"
  const resolved = outcome !== "Pending"
  const match    = resolved && outcome === report.predictedResult

  return (
    <div className="rp-card">
      {/* ── Header ── */}
      <div className="rp-card-head">
        <span className="rp-card-company">{report.company || "—"}</span>
        <span className="rp-card-date">{fmtDate(report.createdDate)}</span>
      </div>

      {report.notes && (
        <p className="rp-card-notes">{report.notes}</p>
      )}

      {/* ── Data row ── */}
      <div className="rp-card-data">
        <div className="rp-data-cell">
          <div className="rp-data-label">Final Price</div>
          <div className="rp-data-val">{fmtPrice(report.finalPrice)}</div>
        </div>

        <div className="rp-data-cell">
          <div className="rp-data-label">Predicted</div>
          <span className={`rp-status-pill rp-status-${report.predictedResult?.toLowerCase()}`}>
            {report.predictedResult || "—"}
          </span>
        </div>

        <div className="rp-data-cell">
          <div className="rp-data-label">Win Prob</div>
          <div className="rp-data-val">{fmtPct(report.winProbability)}</div>
        </div>

        <div className="rp-data-cell rp-data-outcome">
          <div className="rp-data-label">Actual Outcome</div>
          <OutcomePills
            current={outcome}
            onChange={(o) => onOutcomeChange(report.id, o)}
          />
        </div>
      </div>

      {/* ── Match comparison (visible once resolved) ── */}
      {resolved && (
        <div className={`rp-match ${match ? "rp-match-yes" : "rp-match-no"}`}>
          <span>Predicted: <strong>{report.predictedResult}</strong></span>
          <span className="rp-sep">·</span>
          <span>Actual: <strong>{outcome}</strong></span>
          <span className="rp-sep">·</span>
          <span>
            Prediction Match:{" "}
            <strong className={match ? "rp-green" : "rp-red"}>
              {match ? "Yes ✓" : "No ✗"}
            </strong>
          </span>
        </div>
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────
export default function ReportsPage() {
  const navigate = useNavigate()
  const [reports, setReports] = useState([])

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")
      setReports(stored)
    } catch {
      setReports([])
    }
  }, [])

  function handleOutcomeChange(id, outcome) {
    const updated = reports.map((r) => (r.id === id ? { ...r, actualOutcome: outcome } : r))
    setReports(updated)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    } catch { /* localStorage unavailable */ }
  }

  // ── Derived stats ──────────────────────────────────────
  const total    = reports.length
  const won      = reports.filter((r) => r.actualOutcome === "Won").length
  const lost     = reports.filter((r) => r.actualOutcome === "Lost").length
  const pending  = reports.filter((r) => (r.actualOutcome || "Pending") === "Pending").length
  const resolved = won + lost
  const matched  = reports.filter(
    (r) => r.actualOutcome !== "Pending" && r.actualOutcome === r.predictedResult
  ).length
  const accuracy = resolved > 0 ? Math.round((matched / resolved) * 100) : null

  return (
    <div className="rp-page">
      {/* ── Nav ── */}
      <nav className="rp-nav">
        <span className="rp-nav-logo" onClick={() => navigate("/")}>
          Win<span className="rp-accent">sight</span>
        </span>

        {/* Center tabs */}
        <div className="rp-nav-tabs">
          <button className="rp-nav-tab" onClick={() => navigate("/analysis")}>
            Analysis
          </button>
          <button className="rp-nav-tab rp-nav-tab-active" onClick={() => navigate("/reports")}>
            Reports
          </button>
        </div>

        {/* Far-right sign out */}
        <div className="rp-nav-right">
          <button className="rp-nav-signout" onClick={() => navigate("/")}>
            Sign Out
          </button>
        </div>
      </nav>

      <div className="rp-body">

        {/* ── Page header ── */}
        <div className="rp-page-head">
          <h1 className="rp-page-title">Reports</h1>
          <p className="rp-page-sub">
            Your saved offer predictions — see what Winsight predicted, what price you planned,
            and mark the real outcome when the deal closes.
          </p>
        </div>

        {/* ── Stats bar ── */}
        {total > 0 && (
          <div className="rp-stats">
            <div className="rp-stat-pill">
              <span className="rp-stat-num">{total}</span>
              <span className="rp-stat-lbl">Saved</span>
            </div>
            <div className="rp-stat-pill rp-stat-green">
              <span className="rp-stat-num">{won}</span>
              <span className="rp-stat-lbl">Won</span>
            </div>
            <div className="rp-stat-pill rp-stat-red">
              <span className="rp-stat-num">{lost}</span>
              <span className="rp-stat-lbl">Lost</span>
            </div>
            <div className="rp-stat-pill rp-stat-gray">
              <span className="rp-stat-num">{pending}</span>
              <span className="rp-stat-lbl">Pending</span>
            </div>
            {accuracy !== null && (
              <div className="rp-stat-pill rp-stat-blue">
                <span className="rp-stat-num">{accuracy}%</span>
                <span className="rp-stat-lbl">Accuracy</span>
              </div>
            )}
          </div>
        )}

        {/* ── Empty state ── */}
        {total === 0 && (
          <div className="rp-empty">
            <div className="rp-empty-icon">📋</div>
            <p className="rp-empty-title">No saved offers yet</p>
            <p className="rp-empty-sub">
              Run a prediction in the Analysis workspace, then use the
              "Save Offer" section at the bottom to log it here.
            </p>
            <button className="rp-empty-btn" onClick={() => navigate("/analysis")}>
              Go to Analysis
            </button>
          </div>
        )}

        {/* ── Report cards ── */}
        {total > 0 && (
          <div className="rp-cards">
            {reports.map((r) => (
              <ReportCard
                key={r.id}
                report={r}
                onOutcomeChange={handleOutcomeChange}
              />
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
