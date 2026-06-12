import { useState } from "react"
import { useNavigate } from "react-router-dom"
import "./LandingPage.css"

// ─── Config ───────────────────────────────────────────────────
const DEFAULT_PRICE = 40_000
const MAX_PRICE     = 100_000

// ─── Helpers ─────────────────────────────────────────────────
const calcWinProb = (price) =>
  Math.max(5, Math.min(98, 98.3 - (price / 1_000) * 0.2325))

const fmtUSD = (n) =>
  "$" + Math.round(n).toLocaleString("en-US")

// ─── SVG chart  (viewBox 260 × 116) ──────────────────────────
const VW = 260, VH = 116

function buildLinePath() {
  const pts = []
  for (let i = 0; i <= 60; i++) {
    const p    = (i / 60) * MAX_PRICE
    const prob = calcWinProb(p)
    pts.push(`${((p / MAX_PRICE) * VW).toFixed(1)},${(VH - (prob / 100) * VH).toFixed(1)}`)
  }
  return "M " + pts.join(" L ")
}
const CHART_LINE = buildLinePath()
const CHART_AREA = CHART_LINE + ` L ${VW},${VH} L 0,${VH} Z`

function chartDot(price) {
  const prob = calcWinProb(price)
  return { x: (price / MAX_PRICE) * VW, y: VH - (prob / 100) * VH }
}

// Circular ring constants  (120 × 120 SVG, cx/cy = 60)
const RING_R = 50
const RING_C = 2 * Math.PI * RING_R

// ─── Static content ───────────────────────────────────────────
const FEATURES = [
  {
    icon: "📊",
    title: "CRM / Excel Data Upload",
    desc:  "Upload sales opportunity data directly from Excel or CRM exports and preview your dataset before training.",
  },
  {
    icon: "🧠",
    title: "Train Your Own Model",
    desc:  "Select your target column and train models using performance metrics such as ROC-AUC, F1 Score, Accuracy, Precision, and Recall.",
  },
  {
    icon: "🎯",
    title: "Predict Win Probability",
    desc:  "Estimate whether a pricing opportunity is likely to be won or lost before sending the quote.",
  },
  {
    icon: "📈",
    title: "Performance Report",
    desc:  "Track model performance, prediction results, and saved pricing analyses in one clear dashboard.",
  },
]

const HIW_STEPS = [
  "Upload Your Data",
  "Select Target Column",
  "Train the Model",
  "Enter a Pricing Opportunity",
  "Analyze Win Probability",
  "Save Reports to Dashboard",
]


const FREE_FEATURES = [
  "Sample CRM dataset",
  "Win probability preview",
  "Price sensitivity preview",
  "Dashboard preview",
  "Guided demo workspace",
]

const PRO_FEATURES = [
  "CRM / Excel data upload",
  "Target column selection",
  "Model training workspace",
  "Win / Lost prediction",
  "Win probability calculation",
  "Price sensitivity analysis",
  "Expected value analysis",
  "Saved reports dashboard",
]

// ─── Landing Page ─────────────────────────────────────────────
export default function LandingPage() {
  const navigate = useNavigate()
  const [price, setPrice] = useState(DEFAULT_PRICE)

  const winProb  = calcWinProb(price)
  const dot      = chartDot(price)
  const isWin    = winProb >= 50

  // Ring SVG
  const ringOffset = RING_C - (winProb / 100) * RING_C

  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
  }

  return (
    <div className="landing">

      {/* ════ NAVBAR ════ */}
      <nav className="nav">
        <span className="nav-logo">Win<span className="accent">sight</span></span>

        <ul className="nav-links">
          <li><a href="#features"     onClick={(e) => { e.preventDefault(); scrollTo("features") }}>Features</a></li>
          <li><a href="#how-it-works" onClick={(e) => { e.preventDefault(); scrollTo("how-it-works") }}>How It Works</a></li>
          <li><a href="#pricing"      onClick={(e) => { e.preventDefault(); scrollTo("pricing") }}>Pricing</a></li>
          <li><span className="nav-static">Customers</span></li>
          <li><span className="nav-static">Contact</span></li>
        </ul>

        <div className="nav-actions">
          <button className="btn-ghost" onClick={() => navigate("/auth")}>Login</button>
        </div>
      </nav>

      {/* ════ HERO ════ */}
      <div className="hero-wrapper">
        <div className="hero-glow-secondary" aria-hidden="true" />

        <div className="hero">
          {/* Left — copy */}
          <div className="hero-left">
            <div className="hero-badge">
              <span className="badge-pulse" aria-hidden="true" />
              B2B Pricing Intelligence
            </div>

            <h1 className="hero-title">
              Predict Deal Outcomes<br />
              <span className="accent">Before You Quote</span>
            </h1>

            <p className="hero-subtitle">
              Upload your CRM or Excel data, analyze price sensitivity, and make
              smarter pricing decisions with AI-powered sales intelligence.
            </p>

            <div className="hero-ctas">
              <button className="btn-hero-primary"   onClick={() => navigate("/auth-free")}>Get Started Free</button>
              <button className="btn-hero-secondary" onClick={() => scrollTo("pricing")}>View Pricing</button>
            </div>
          </div>

          {/* Right — interactive dashboard mockup */}
          <div className="hero-right" aria-label="Dashboard preview">
            <div className="dashboard-mockup">

              {/* macOS-style window chrome */}
              <div className="mockup-chrome">
                <div className="chrome-dots" aria-hidden="true">
                  <span className="chrome-dot r" />
                  <span className="chrome-dot y" />
                  <span className="chrome-dot g" />
                </div>
                <span className="chrome-app-title">Winsight · Deal Analysis</span>
              </div>

              <div className="mockup-body">

                {/* ── Win Probability ring — main visual focus ── */}
                <div className="ring-section">
                  <div className="mockup-ring" aria-label={`Win probability ${winProb.toFixed(1)}%`}>
                    <svg width="120" height="120" viewBox="0 0 120 120" aria-hidden="true">
                      <circle
                        cx="60" cy="60" r={RING_R}
                        fill="none"
                        stroke="rgba(255,255,255,0.06)"
                        strokeWidth="7"
                      />
                      <circle
                        cx="60" cy="60" r={RING_R}
                        fill="none"
                        stroke={isWin ? "#34d399" : "#f87171"}
                        strokeWidth="7"
                        strokeDasharray={RING_C}
                        strokeDashoffset={ringOffset}
                        strokeLinecap="round"
                        transform="rotate(-90 60 60)"
                        style={{ transition: "stroke-dashoffset 0.4s ease, stroke 0.3s" }}
                      />
                    </svg>
                    <div className="ring-inner">
                      <span className={`ring-value ${isWin ? "green" : "red"}`}>
                        {Math.round(winProb)}%
                      </span>
                    </div>
                  </div>
                  <div className="ring-label">Win Probability</div>
                </div>

                {/* ── Stat rows: Predicted Result + Deal Price ── */}
                <div className="mockup-stats">
                  <div className="mockup-stat-row">
                    <span className="stat-key">Predicted Result</span>
                    <span className={`stat-val ${isWin ? "green" : "red"}`}>
                      {isWin ? "Won" : "At Risk"}
                    </span>
                  </div>
                  <div className="mockup-stat-row">
                    <span className="stat-key">Deal Price</span>
                    <span className="stat-val">{fmtUSD(price)}</span>
                  </div>
                </div>

                {/* ── Price vs Win Probability chart ── */}
                <div className="mockup-chart">
                  <div className="chart-label">Price vs Win Probability</div>
                  <svg
                    viewBox={`0 0 ${VW} ${VH}`}
                    width="100%"
                    style={{ display: "block" }}
                    aria-hidden="true"
                  >
                    <defs>
                      <linearGradient id="cGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#3b82f6" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0"   />
                      </linearGradient>
                    </defs>

                    {[0.25, 0.5, 0.75].map((pct) => {
                      const y = (VH - pct * VH).toFixed(1)
                      return (
                        <line key={pct} x1={0} y1={y} x2={VW} y2={y}
                          stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                      )
                    })}

                    <line x1={0} y1={VH} x2={VW} y2={VH}
                      stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

                    <path d={CHART_AREA} fill="url(#cGrad)" />
                    <path d={CHART_LINE} fill="none" stroke="#3b82f6"
                      strokeWidth="1.6" strokeLinecap="round" />

                    <line
                      x1={dot.x.toFixed(1)} y1={0}
                      x2={dot.x.toFixed(1)} y2={VH}
                      stroke="rgba(255,255,255,0.18)"
                      strokeWidth="1" strokeDasharray="3 3"
                    />
                    <circle
                      cx={dot.x.toFixed(1)}
                      cy={dot.y.toFixed(1)}
                      r={4}
                      fill="#3b82f6"
                      stroke="#fff"
                      strokeWidth="1.8"
                    />
                  </svg>
                </div>

              </div>{/* /mockup-body */}
            </div>{/* /dashboard-mockup */}
          </div>{/* /hero-right */}
        </div>{/* /hero */}
      </div>{/* /hero-wrapper */}

      {/* ════ FEATURES ════ */}
      <div className="section-outer" id="features">
        <div className="section">
          <h2 className="section-title">Everything You Need for Smarter Pricing Decisions</h2>
          <p className="section-subtitle">
            Winsight turns CRM and Excel data into win probability, price sensitivity, and clearer pricing insights.
          </p>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="feature-card">
                <div className="feature-icon" aria-hidden="true">{f.icon}</div>
                <div className="feature-title">{f.title}</div>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ════ HOW IT WORKS ════ */}
      <div className="section-outer alt-bg" id="how-it-works">
        <div className="section">
          <h2 className="section-title">From Data to Decision in Minutes</h2>
          <p className="section-subtitle">
            A structured, repeatable workflow that turns historical deal data into live pricing intelligence step by step.
          </p>
          <div className="hiw-flow">
            {HIW_STEPS.map((step, i) => (
              <div key={i} className="hiw-step-item">
                <div className="hiw-pill">{step}</div>
                {i < HIW_STEPS.length - 1 && (
                  <div className="hiw-arrow" aria-hidden="true">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ════ HIGHLIGHT BANNER ════ */}
      <div className="banner-outer">
        <div className="banner-glow" aria-hidden="true" />
        <div className="banner-inner">

          <div className="banner-text">
            <div className="banner-star" aria-hidden="true">⭐</div>
            <h2 className="banner-title">The must-have tool for modern sales teams</h2>
            <p className="banner-sub">
              Winsight helps sales teams turn deal data into clearer pricing decisions before every quote.
            </p>
          </div>

        </div>
      </div>

      {/* ════ PRICING ════ */}
      <div className="section-outer alt-bg" id="pricing">
        <div className="section">
          <h2 className="pricing-section-title">Pricing</h2>

          <div className="pricing-table">

            {/* ── Free Demo column ── */}
            <div className="pt-col">
              <div className="pt-plan">Free Demo</div>
              <div className="pt-price-row">
                <span className="pt-price">$0</span>
              </div>
              <div className="pt-period">Sample-data access</div>
              <p className="pt-desc">
                Explore Winsight with sample sales opportunity data before uploading your own files.
              </p>
              <hr className="pt-rule" />
              <ul className="pt-features">
                {FREE_FEATURES.map((f) => <li key={f}>{f}</li>)}
              </ul>
              <button
                className="btn-pt-free"
                onClick={() => navigate("/auth?plan=demo")}
              >
                Try Demo
              </button>
            </div>

            {/* ── Vertical divider ── */}
            <div className="pt-vdivider" aria-hidden="true" />

            {/* ── Professional column ── */}
            <div className="pt-col pt-col-pro">
              <div className="pt-plan">Professional</div>
              <div className="pt-price-row">
                <span className="pt-price">$199</span>
              </div>
              <div className="pt-period">per month</div>
              <p className="pt-desc">
                Create your workspace and unlock full pricing intelligence with your own CRM and Excel data.
              </p>
              <hr className="pt-rule" />
              <ul className="pt-features">
                {PRO_FEATURES.map((f) => <li key={f}>{f}</li>)}
              </ul>
              <button
                className="btn-pt-pro"
                onClick={() => navigate("/auth?plan=professional")}
              >
                Start Professional
              </button>
            </div>

          </div>
        </div>
      </div>

      {/* ════ FOOTER ════ */}
      <footer className="footer-bar">
        <div className="footer-inner">
          <span className="footer-logo">Win<span className="accent">sight</span></span>
          <span className="footer-text">© 2025 Winsight. Academic graduation project.</span>
        </div>
      </footer>

    </div>
  )
}
