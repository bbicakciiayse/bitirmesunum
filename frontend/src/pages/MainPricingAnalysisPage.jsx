import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import "./MainPricingAnalysisPage.css"

const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"

// ── SVG chart constants ───────────────────────────────────────
const CVW = 340, CVH = 140

function buildChartPaths(points) {
  if (!points || points.length === 0) return { line: "", area: "" }
  const priceMin = points[0].price
  const priceMax = points[points.length - 1].price
  const span     = priceMax - priceMin || 1

  const coords = points.map((p) => {
    const x = ((p.price - priceMin) / span * CVW).toFixed(1)
    const y = (CVH - p.win_probability * CVH).toFixed(1)
    return `${x},${y}`
  })

  const line = "M " + coords.join(" L ")
  const area = line + ` L ${CVW},${CVH} L 0,${CVH} Z`
  return { line, area }
}

function getSliderDot(points, sliderPrice) {
  if (!points || points.length === 0) return null
  const priceMin = points[0].price
  const priceMax = points[points.length - 1].price
  const span     = priceMax - priceMin || 1

  let closest = points[0]
  for (const p of points) {
    if (Math.abs(p.price - sliderPrice) < Math.abs(closest.price - sliderPrice))
      closest = p
  }

  return {
    x:    (closest.price - priceMin) / span * CVW,
    y:    CVH - closest.win_probability * CVH,
    prob: closest.win_probability,
    price: closest.price,
  }
}

const fmtUSD   = (n) => "$" + Math.round(n).toLocaleString("en-US")
const fmtPct   = (v) => (v * 100).toFixed(1) + "%"

// ── Ring constants ────────────────────────────────────────────
const RING_R = 50
const RING_C = 2 * Math.PI * RING_R

// ─────────────────────────────────────────────────────────────
export default function MainPricingAnalysisPage() {
  const navigate = useNavigate()

  // ── Backend health ────────────────────────────────────────
  // null = checking, true = reachable, false = unreachable
  const [backendOk, setBackendOk] = useState(null)

  useEffect(() => {
    const healthUrl = `${API}/health`
    console.log("Health check URL:", healthUrl)
    // no-cors skips the CORS preflight entirely — the fetch resolves if the
    // server is reachable and rejects only on a true network failure.
    fetch(healthUrl, { mode: "no-cors" })
      .then((r) => {
        console.log("Health check success:", r.status)
        setBackendOk(true)
      })
      .catch((err) => {
        console.log("Health check failed:", err.message)
        setBackendOk(false)
      })
  }, [])

  // ── Stage ─────────────────────────────────────────────────
  // "upload" → "columns" → "workspace" → "results"
  const [stage, setStage] = useState("upload")

  // ── Upload ────────────────────────────────────────────────
  const fileRef                    = useRef(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadError,   setUploadError]   = useState("")
  const [uploadData,    setUploadData]    = useState(null)
  // { file_name, row_count, col_count, columns, preview, suggested_target, suggested_price }

  // ── Column selection ──────────────────────────────────────
  const [targetCol,   setTargetCol]   = useState("")
  const [priceCol,    setPriceCol]    = useState("")

  // ── Training ──────────────────────────────────────────────
  const [trainLoading, setTrainLoading] = useState(false)
  const [trainError,   setTrainError]   = useState("")
  const [schema,       setSchema]       = useState([])
  const [priceRange,   setPriceRange]   = useState({ min: 0, max: 100000 })

  // ── Offer form ────────────────────────────────────────────
  const [formValues,   setFormValues]   = useState({})

  // ── Prediction ────────────────────────────────────────────
  const [predictLoading, setPredictLoading] = useState(false)
  const [predictError,   setPredictError]   = useState("")
  const [prediction,     setPrediction]     = useState(null)
  // { predicted_label, win_probability, probability_percent, deal_price, model_used }

  // ── Sensitivity chart ─────────────────────────────────────
  const [sensitivityData, setSensitivityData] = useState([])
  const [sliderPrice,     setSliderPrice]     = useState(0)

  // ── Save Offer — form fields ──────────────────────────────
  const [saveOfferName,  setSaveOfferName]  = useState("")
  const [saveOfferDate,  setSaveOfferDate]  = useState("")
  const [saveOfferPrice, setSaveOfferPrice] = useState("")
  const [saveOfferNotes, setSaveOfferNotes] = useState("")

  // ── Save Offer — per-offer analysis (from "Analyze This Offer") ──
  const [saveAnalyzing,      setSaveAnalyzing]      = useState(false)
  const [saveAnalysisResult, setSaveAnalysisResult] = useState(null)
  // null until "Analyze This Offer" succeeds
  // { predicted_label, win_probability, deal_price, … }
  const [saveAnalysisPrice,  setSaveAnalysisPrice]  = useState("")
  // price string at the moment analysis ran — used to detect staleness
  const [saveAnalysisError,  setSaveAnalysisError]  = useState("")

  // ── Save Offer — save state ───────────────────────────────
  const [offerSaved, setOfferSaved] = useState(false)

  // ═══════════════════════════════════════════════════════════
  //  Handlers
  // ═══════════════════════════════════════════════════════════

  async function handleFileChange(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploadLoading(true)
    setUploadError("")

    console.log("Uploading file to backend", file.name)

    try {
      const fd = new FormData()
      fd.append("file", file)
      // Do NOT set Content-Type manually — browser sets multipart/form-data + boundary automatically
      let res
      try {
        res = await fetch(`${API}/upload-data`, { method: "POST", body: fd })
      } catch (networkErr) {
        // fetch() itself threw — backend is not reachable at all
        throw new Error(`Backend is not reachable at ${API}`)
      }

      let json
      try {
        json = await res.json()
      } catch {
        throw new Error(`Server returned non-JSON response (status ${res.status})`)
      }

      if (!res.ok) {
        throw new Error(json.detail || `Upload failed (${res.status})`)
      }

      console.log("Upload response", json)
      setUploadData(json)
      setTargetCol(json.suggested_target || "")
      setPriceCol(json.suggested_price   || "")
      setStage("columns")
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploadLoading(false)
      if (fileRef.current) fileRef.current.value = ""
    }
  }

  async function handleTrain() {
    if (!targetCol || !priceCol) {
      setTrainError("Please select both the target column and the price column.")
      return
    }
    setTrainLoading(true)
    setTrainError("")

    try {
      const res = await fetch(`${API}/train`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ target_col: targetCol, price_col: priceCol }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || "Training failed")

      setSchema(json.schema)
      setPriceRange(json.price_range)

      // Initialise form values to empty strings
      const init = {}
      for (const f of json.schema) init[f.name] = ""
      setFormValues(init)

      setSliderPrice((json.price_range.min + json.price_range.max) / 2)
      setPrediction(null)
      setSensitivityData([])
      setStage("workspace")
    } catch (err) {
      setTrainError(err.message)
    } finally {
      setTrainLoading(false)
    }
  }

  function handleFieldChange(name, value) {
    setFormValues((prev) => ({ ...prev, [name]: value }))
  }

  async function handlePredict() {
    setPredictLoading(true)
    setPredictError("")
    setPrediction(null)
    setSensitivityData([])
    setOfferSaved(false)

    // Strip empty values before sending
    const offer = {}
    for (const [k, v] of Object.entries(formValues)) {
      if (v !== "" && v !== null && v !== undefined) offer[k] = v
    }

    try {
      // ── Predict ──
      const res = await fetch(`${API}/predict`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ offer }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || "Prediction failed")

      setPrediction(json)
      setSliderPrice(json.deal_price)
      setStage("results")

      // Reset Section 6 whenever a new main prediction runs
      setSaveOfferName(formValues["Company"] || "")
      setSaveOfferDate(new Date().toISOString().split("T")[0])
      setSaveOfferPrice(String(json.deal_price))
      setSaveOfferNotes("")
      setSaveAnalysisResult(null)
      setSaveAnalysisPrice("")
      setSaveAnalysisError("")
      setOfferSaved(false)

      // ── Sensitivity curve (fire-and-forget, non-blocking) ──
      fetch(`${API}/price-sensitivity`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ offer, steps: 60 }),
      })
        .then((r) => r.json())
        .then((d) => {
          if (d.points) setSensitivityData(d.points)
        })
        .catch(() => {})

    } catch (err) {
      setPredictError(err.message)
    } finally {
      setPredictLoading(false)
    }
  }

  // ── "Analyze This Offer": calls /predict with Section 6 price override ──
  async function handleAnalyzeOffer() {
    const price = parseFloat(saveOfferPrice)
    if (!saveOfferPrice || isNaN(price)) return

    setSaveAnalyzing(true)
    setSaveAnalysisError("")
    setSaveAnalysisResult(null)
    setOfferSaved(false)

    // Start from the main offer form values, then override the price column
    const offer = {}
    for (const [k, v] of Object.entries(formValues)) {
      if (v !== "" && v !== null && v !== undefined) offer[k] = v
    }
    offer[priceCol] = price   // Section 6 Final Offer Price overrides the slider

    try {
      const res = await fetch(`${API}/predict`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ offer }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || "Analysis failed")
      setSaveAnalysisResult(json)
      setSaveAnalysisPrice(saveOfferPrice)   // snapshot for staleness check
    } catch (err) {
      setSaveAnalysisError(err.message)
    } finally {
      setSaveAnalyzing(false)
    }
  }

  // ── "Save Offer": persists the latest analysis result to localStorage ──
  function handleSaveOffer() {
    if (!saveAnalysisResult) return
    const report = {
      id:              Date.now().toString(),
      company:         saveOfferName.trim() || "—",
      offerDate:       saveOfferDate,
      finalPrice:      parseFloat(saveAnalysisPrice),
      notes:           saveOfferNotes.trim(),
      predictedResult: saveAnalysisResult.predicted_label,
      winProbability:  saveAnalysisResult.win_probability,
      inputFields:     { ...formValues },
      createdDate:     new Date().toISOString(),
      actualOutcome:   "Pending",
    }
    try {
      const existing = JSON.parse(localStorage.getItem("winsight_reports") || "[]")
      localStorage.setItem("winsight_reports", JSON.stringify([report, ...existing]))
    } catch { /* localStorage unavailable */ }
    setOfferSaved(true)
  }

  // ═══════════════════════════════════════════════════════════
  //  Derived values for the result card
  // ═══════════════════════════════════════════════════════════
  const currentProb = (() => {
    if (!sensitivityData.length) return prediction?.win_probability ?? 0
    let closest = sensitivityData[0]
    for (const p of sensitivityData) {
      if (Math.abs(p.price - sliderPrice) < Math.abs(closest.price - sliderPrice))
        closest = p
    }
    return closest.win_probability
  })()

  const isWin      = currentProb >= 0.5
  const ringOffset = RING_C - currentProb * RING_C

  const { line: chartLine, area: chartArea } = buildChartPaths(sensitivityData)
  const dot = getSliderDot(sensitivityData, sliderPrice)

  // True when the user changed Final Offer Price after running "Analyze This Offer"
  const isAnalysisStale = saveAnalysisResult !== null && saveOfferPrice !== saveAnalysisPrice

  // ═══════════════════════════════════════════════════════════
  //  Render
  // ═══════════════════════════════════════════════════════════
  return (
    <div className="ap-page">

      {/* ── Top nav ── */}
      <nav className="ap-nav">
        <span className="ap-nav-logo" onClick={() => navigate("/")}>
          Win<span className="accent">sight</span>
        </span>

        {/* Center tabs */}
        <div className="ap-nav-tabs">
          <button className="ap-nav-tab ap-nav-tab-active" onClick={() => navigate("/analysis")}>
            Analysis
          </button>
          <button className="ap-nav-tab" onClick={() => navigate("/reports")}>
            Reports
          </button>
        </div>

        {/* Far-right sign out */}
        <div className="ap-nav-right">
          <button className="ap-nav-signout" onClick={() => navigate("/")}>
            Sign Out
          </button>
        </div>
      </nav>

      <div className="ap-body">

        {backendOk === false && (
          <div className="ap-backend-error">
            Backend is not reachable at {API}. Make sure the server is running.
          </div>
        )}

        {/* ════ SECTION 1 — Upload ════ */}
        <section className="ap-card" id="sec-upload">
          <div className="ap-card-header">
            <span className="ap-step-badge">1</span>
            <h2 className="ap-card-title">Upload Historical Sales Data</h2>
          </div>

          {stage === "upload" ? (
            <>
              <p className="ap-card-sub">
                Upload a CSV or Excel file containing your historical sales opportunity records.
                Winsight will detect the columns and train the model on your data.
              </p>

              <label className="ap-upload-zone" htmlFor="file-input">
                <div className="ap-upload-icon" aria-hidden="true">📂</div>
                <div className="ap-upload-label">
                  {uploadLoading ? "Reading file…" : "Click to choose a file"}
                </div>
                <div className="ap-upload-hint">.csv · .xlsx · .xls</div>
                <input
                  id="file-input"
                  ref={fileRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  disabled={uploadLoading}
                  hidden
                />
              </label>

              {uploadError && backendOk !== false && (
                <p className="ap-error">{uploadError}</p>
              )}
            </>
          ) : (
            /* Collapsed summary after upload */
            <div className="ap-summary-row">
              <span className="ap-summary-check">✓</span>
              <span className="ap-summary-text">
                <strong>{uploadData?.file_name}</strong>
                {" — "}
                {uploadData?.row_count?.toLocaleString()} rows ·{" "}
                {uploadData?.col_count} columns
              </span>
              <button
                className="ap-link-btn"
                onClick={() => {
                  setStage("upload")
                  setUploadData(null)
                  setPrediction(null)
                  setSensitivityData([])
                }}
              >
                Change file
              </button>
            </div>
          )}
        </section>

        {/* ════ SECTION 2 — Column Selection + Preview ════ */}
        {stage !== "upload" && (
          <section className="ap-card" id="sec-columns">
            <div className="ap-card-header">
              <span className="ap-step-badge">2</span>
              <h2 className="ap-card-title">Select Target and Price Columns</h2>
            </div>

            {(stage === "columns") ? (
              <>
                <p className="ap-card-sub">
                  Select the column that represents the deal outcome (Won / Lost) and the
                  column that represents the offer price.
                </p>

                <div className="ap-col-selectors">
                  <div className="ap-select-group">
                    <label className="ap-select-label">Target / Result column</label>
                    <select
                      className="ap-select"
                      value={targetCol}
                      onChange={(e) => setTargetCol(e.target.value)}
                    >
                      <option value="">— select —</option>
                      {uploadData?.columns.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  <div className="ap-select-group">
                    <label className="ap-select-label">Price / Amount column</label>
                    <select
                      className="ap-select"
                      value={priceCol}
                      onChange={(e) => setPriceCol(e.target.value)}
                    >
                      <option value="">— select —</option>
                      {uploadData?.columns.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Preview table */}
                {uploadData?.preview?.length > 0 && (
                  <div className="ap-preview-wrap">
                    <div className="ap-preview-label">File preview (first 5 rows)</div>
                    <div className="ap-table-scroll">
                      <table className="ap-table">
                        <thead>
                          <tr>
                            {uploadData.columns.map((c) => (
                              <th key={c} className={
                                c === targetCol ? "ap-th ap-th-target"
                                : c === priceCol  ? "ap-th ap-th-price"
                                : "ap-th"
                              }>{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {uploadData.preview.map((row, ri) => (
                            <tr key={ri}>
                              {uploadData.columns.map((c) => (
                                <td key={c} className="ap-td">{row[c]}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {trainError && <p className="ap-error">{trainError}</p>}

                <button
                  className="ap-btn-primary"
                  onClick={handleTrain}
                  disabled={trainLoading || !targetCol || !priceCol}
                >
                  {trainLoading
                    ? "Training model…"
                    : "Train Model"}
                </button>
              </>
            ) : (
              /* Collapsed summary */
              <div className="ap-summary-row">
                <span className="ap-summary-check">✓</span>
                <span className="ap-summary-text">
                  Target: <strong>{targetCol}</strong> · Price: <strong>{priceCol}</strong>
                </span>
                <button
                  className="ap-link-btn"
                  onClick={() => {
                    setStage("columns")
                    setPrediction(null)
                    setSensitivityData([])
                  }}
                >
                  Retrain
                </button>
              </div>
            )}
          </section>
        )}

        {/* ════ SECTION 3 — New Offer Form ════ */}
        {(stage === "workspace" || stage === "results") && (
          <section className="ap-card" id="sec-offer">
            <div className="ap-card-header">
              <span className="ap-step-badge">3</span>
              <h2 className="ap-card-title">Enter New Offer Details</h2>
            </div>

            <p className="ap-card-sub">
              Fill in the details of the offer you are planning to send. Winsight will
              estimate the probability of winning based on your uploaded historical sales
              data. Leave fields empty to use dataset averages.
            </p>

            <div className="ap-form-grid">
              {schema.map((field) => (
                <div key={field.name} className="ap-field">
                  <label className="ap-field-label">
                    {field.name}
                    {field.required && <span className="ap-required"> *</span>}
                  </label>

                  {field.type === "select" ? (
                    <select
                      className="ap-input ap-input-select"
                      value={formValues[field.name] ?? ""}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                    >
                      <option value="">— any —</option>
                      {field.options.map((o) => (
                        <option key={o} value={o}>{o}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      className="ap-input"
                      type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
                      placeholder={field.type === "number" ? "e.g. 50000" : ""}
                      value={formValues[field.name] ?? ""}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                    />
                  )}
                </div>
              ))}
            </div>

            {predictError && <p className="ap-error">{predictError}</p>}

            <button
              className="ap-btn-primary ap-btn-predict"
              onClick={handlePredict}
              disabled={predictLoading}
            >
              {predictLoading ? "Running model…" : "Predict Win Probability"}
            </button>
          </section>
        )}

        {/* ════ SECTION 4 — Prediction Result ════ */}
        {stage === "results" && prediction && (
          <section className="ap-card ap-card-result" id="sec-result">
            <div className="ap-card-header">
              <span className="ap-step-badge">4</span>
              <h2 className="ap-card-title">Prediction Result</h2>
            </div>

            <div className="ap-result-layout">

              {/* Ring */}
              <div className="ap-ring-wrap">
                <div className="ap-ring" aria-label={`Win probability ${fmtPct(currentProb)}`}>
                  <svg width="130" height="130" viewBox="0 0 120 120" aria-hidden="true">
                    <circle cx="60" cy="60" r={RING_R}
                      fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="7" />
                    <circle cx="60" cy="60" r={RING_R}
                      fill="none"
                      stroke={isWin ? "#34d399" : "#f87171"}
                      strokeWidth="7"
                      strokeDasharray={RING_C}
                      strokeDashoffset={ringOffset}
                      strokeLinecap="round"
                      transform="rotate(-90 60 60)"
                      style={{ transition: "stroke-dashoffset 0.45s ease, stroke 0.3s" }}
                    />
                  </svg>
                  <div className="ap-ring-inner">
                    <span className={`ap-ring-value ${isWin ? "green" : "red"}`}>
                      {Math.round(currentProb * 100)}%
                    </span>
                  </div>
                </div>
                <div className="ap-ring-label">Win Probability</div>
              </div>

              {/* Stats */}
              <div className="ap-result-stats">
                <div className="ap-stat-row">
                  <span className="ap-stat-key">Predicted Result</span>
                  <span className={`ap-stat-val ${prediction.predicted_label === "Won" ? "green" : "red"}`}>
                    {prediction.predicted_label}
                  </span>
                </div>
                <div className="ap-stat-row">
                  <span className="ap-stat-key">Win Probability</span>
                  <span className="ap-stat-val">{fmtPct(currentProb)}</span>
                </div>
                <div className="ap-stat-row">
                  <span className="ap-stat-key">Deal Price</span>
                  <span className="ap-stat-val">{fmtUSD(sliderPrice)}</span>
                </div>
                <div className="ap-stat-row">
                  <span className="ap-stat-key">Model</span>
                  <span className="ap-stat-val ap-stat-model">{prediction.model_used}</span>
                </div>
              </div>
            </div>

            {/* Result sentence */}
            <div className="ap-result-sentence">
              If you offer this price, Winsight estimates a{" "}
              <strong>{fmtPct(currentProb)}</strong> probability of winning this
              opportunity.
            </div>
          </section>
        )}

        {/* ════ SECTION 5 — Price Sensitivity ════ */}
        {stage === "results" && (
          <section className="ap-card" id="sec-sensitivity">
            <div className="ap-card-header">
              <span className="ap-step-badge">5</span>
              <h2 className="ap-card-title">Price Sensitivity</h2>
            </div>

            <p className="ap-card-sub">
              Move the slider to explore how the predicted win probability changes
              at different price points. All other offer details remain the same.
            </p>

            {sensitivityData.length === 0 ? (
              <div className="ap-chart-loading">Computing sensitivity curve…</div>
            ) : (
              <>
                {/* Chart */}
                <div className="ap-chart-wrap">
                  <div className="ap-chart-title">Price vs Win Probability</div>
                  <svg
                    viewBox={`0 0 ${CVW} ${CVH}`}
                    width="100%"
                    style={{ display: "block" }}
                    aria-hidden="true"
                  >
                    <defs>
                      <linearGradient id="sensGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#3b82f6" stopOpacity="0.28" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0"    />
                      </linearGradient>
                    </defs>

                    {/* Grid lines at 25%, 50%, 75% */}
                    {[0.25, 0.5, 0.75].map((pct) => (
                      <line key={pct}
                        x1={0} y1={(CVH - pct * CVH).toFixed(1)}
                        x2={CVW} y2={(CVH - pct * CVH).toFixed(1)}
                        stroke="rgba(255,255,255,0.05)" strokeWidth="1"
                      />
                    ))}
                    <line x1={0} y1={CVH} x2={CVW} y2={CVH}
                      stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

                    <path d={chartArea} fill="url(#sensGrad)" />
                    <path d={chartLine} fill="none"
                      stroke="#3b82f6" strokeWidth="1.8" strokeLinecap="round" />

                    {/* Current price marker */}
                    {dot && (
                      <>
                        <line
                          x1={dot.x.toFixed(1)} y1={0}
                          x2={dot.x.toFixed(1)} y2={CVH}
                          stroke="rgba(255,255,255,0.22)"
                          strokeWidth="1" strokeDasharray="3 3"
                        />
                        <circle
                          cx={dot.x.toFixed(1)} cy={dot.y.toFixed(1)}
                          r={4.5} fill="#3b82f6" stroke="#fff" strokeWidth="2"
                        />
                      </>
                    )}
                  </svg>
                </div>

                {/* Slider */}
                <div className="ap-slider-section">
                  <div className="ap-slider-row">
                    <span className="ap-slider-label">Price</span>
                    <span className="ap-slider-value">{fmtUSD(sliderPrice)}</span>
                    <span className="ap-slider-prob">
                      Win probability: <strong>{fmtPct(currentProb)}</strong>
                    </span>
                  </div>
                  <input
                    className="ap-slider"
                    type="range"
                    min={priceRange.min}
                    max={priceRange.max}
                    step={(priceRange.max - priceRange.min) / 200}
                    value={sliderPrice}
                    onChange={(e) => setSliderPrice(parseFloat(e.target.value))}
                    style={{
                      "--val": `${((sliderPrice - priceRange.min) / (priceRange.max - priceRange.min) * 100).toFixed(1)}%`,
                    }}
                  />
                  <div className="ap-slider-range-labels">
                    <span>{fmtUSD(priceRange.min)}</span>
                    <span>{fmtUSD(priceRange.max)}</span>
                  </div>
                </div>
              </>
            )}
          </section>
        )}

        {/* ════ SECTION 6 — Save Offer ════ */}
        {stage === "results" && prediction && (
          <section className="ap-card" id="sec-save">
            <div className="ap-card-header">
              <span className="ap-step-badge">6</span>
              <h2 className="ap-card-title">Save Offer</h2>
            </div>

            <p className="ap-card-sub">
              Save the offer you plan to send. Analyze the final offer price
              first, then store the prediction in Reports.
            </p>

            {offerSaved ? (
              /* ── Success state ── */
              <div className="ap-save-success">
                <span>✓ Offer saved to Reports.</span>
                <button className="ap-link-btn" onClick={() => navigate("/reports")}>
                  View Reports →
                </button>
              </div>
            ) : (
              <>
                {/* ── Four-field form ── */}
                <div className="ap-save-form">
                  <div className="ap-field">
                    <label className="ap-field-label">Company / Offer Name</label>
                    <input
                      className="ap-input"
                      type="text"
                      placeholder="e.g. Lentatech"
                      value={saveOfferName}
                      onChange={(e) => setSaveOfferName(e.target.value)}
                    />
                  </div>

                  <div className="ap-field">
                    <label className="ap-field-label">Offer Date</label>
                    <input
                      className="ap-input"
                      type="date"
                      value={saveOfferDate}
                      onChange={(e) => setSaveOfferDate(e.target.value)}
                    />
                  </div>

                  <div className="ap-field">
                    <label className="ap-field-label">
                      Final Offer Price <span className="ap-required">*</span>
                    </label>
                    <input
                      className="ap-input"
                      type="number"
                      placeholder="e.g. 8955"
                      value={saveOfferPrice}
                      onChange={(e) => setSaveOfferPrice(e.target.value)}
                    />
                  </div>

                  <div className="ap-field">
                    <label className="ap-field-label">Notes</label>
                    <input
                      className="ap-input"
                      type="text"
                      placeholder="Optional notes about this offer…"
                      value={saveOfferNotes}
                      onChange={(e) => setSaveOfferNotes(e.target.value)}
                    />
                  </div>
                </div>

                {/* ── Analyze button ── */}
                <button
                  className="ap-btn-primary ap-btn-analyze"
                  onClick={handleAnalyzeOffer}
                  disabled={saveAnalyzing || !saveOfferPrice}
                >
                  {saveAnalyzing ? "Analyzing offer…" : "Analyze This Offer"}
                </button>

                {saveAnalysisError && (
                  <p className="ap-error">{saveAnalysisError}</p>
                )}

                {/* ── Analysis preview (shown after Analyze succeeds) ── */}
                {saveAnalysisResult && (
                  <div className={`ap-analysis-preview${isAnalysisStale ? " ap-analysis-stale" : ""}`}>
                    <div className="ap-analysis-preview-title">
                      {isAnalysisStale
                        ? "⚠ Analysis outdated — price changed"
                        : "Prediction for this offer"}
                    </div>

                    <div className="ap-analysis-grid">
                      <div className="ap-analysis-item">
                        <span className="ap-analysis-label">Predicted Result</span>
                        <span className={`ap-analysis-val ${saveAnalysisResult.predicted_label === "Won" ? "green" : "red"}`}>
                          {saveAnalysisResult.predicted_label}
                        </span>
                      </div>
                      <div className="ap-analysis-item">
                        <span className="ap-analysis-label">Win Probability</span>
                        <span className="ap-analysis-val">
                          {(saveAnalysisResult.win_probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="ap-analysis-item">
                        <span className="ap-analysis-label">Final Offer Price</span>
                        <span className="ap-analysis-val">
                          ${Math.round(parseFloat(saveAnalysisPrice)).toLocaleString("en-US")}
                        </span>
                      </div>
                      <div className="ap-analysis-item">
                        <span className="ap-analysis-label">Offer Date</span>
                        <span className="ap-analysis-val">
                          {saveOfferDate
                            ? new Date(saveOfferDate + "T00:00:00").toLocaleDateString("en-US", {
                                month: "short", day: "numeric", year: "numeric",
                              })
                            : "—"}
                        </span>
                      </div>
                    </div>

                    {isAnalysisStale ? (
                      <p className="ap-stale-warning">
                        Analyze this offer again before saving.
                      </p>
                    ) : (
                      <button
                        className="ap-btn-primary ap-btn-save"
                        onClick={handleSaveOffer}
                      >
                        Save Offer
                      </button>
                    )}
                  </div>
                )}
              </>
            )}
          </section>
        )}

      </div>{/* /ap-body */}
    </div>
  )
}
