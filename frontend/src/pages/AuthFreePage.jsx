import { useState } from "react"
import { useNavigate } from "react-router-dom"
import "./AuthFreePage.css"

const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())

// Shared logo element — identical in every step
function Logo() {
  return (
    <div className="af-logo-wrap">
      <span className="af-logo">Win<span className="af-accent">sight</span></span>
    </div>
  )
}

export default function AuthFreePage() {
  const navigate = useNavigate()

  // ── step state ──────────────────────────────
  const [step,      setStep]      = useState("email")   // "email" | "verify" | "info"

  // ── email step ──────────────────────────────
  const [email,     setEmail]     = useState("")
  const [touched,   setTouched]   = useState(false)

  // ── verify step ─────────────────────────────
  const [code,      setCode]      = useState("")
  const [codeError, setCodeError] = useState(false)

  // ── info step ───────────────────────────────
  const [name,      setName]      = useState("")
  const [role,      setRole]      = useState("")
  const [company,   setCompany]   = useState("")
  const [industry,  setIndustry]  = useState("")
  const [infoTried, setInfoTried] = useState(false)

  // ── derived ─────────────────────────────────
  const valid          = isValidEmail(email)
  const showEmailError = touched && email.trim() !== "" && !valid
  const infoErrors     = infoTried
    ? { name: !name.trim(), role: !role, company: !company.trim(), industry: !industry }
    : {}

  // ── handlers ────────────────────────────────
  function handleEmailSubmit(e) {
    e.preventDefault()
    setTouched(true)
    if (valid) setStep("verify")
  }

  function handleVerify(e) {
    e.preventDefault()
    if (code.trim() === "123456") {
      setStep("info")
    } else {
      setCodeError(true)
    }
  }

  function handleInfoSubmit(e) {
    e.preventDefault()
    setInfoTried(true)
    if (name.trim() && role && company.trim() && industry) {
      navigate("/analysis")
    }
  }

  function goBackToEmail() {
    setStep("email")
    setCode("")
    setCodeError(false)
  }

  return (
    <div className="af-page">
      <main className="af-main">

        {/* ════ STEP 1 — Email entry ════ */}
        {step === "email" && (
          <div className="af-card">
            <Logo />

            <h1 className="af-title">Create your account</h1>
            <p className="af-sub">100% free. No credit card needed.</p>

            <form className="af-form" onSubmit={handleEmailSubmit} noValidate>
              <div className="af-field">
                <input
                  id="af-email"
                  className={`af-input${showEmailError ? " af-input-error" : ""}`}
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setTouched(false) }}
                  onBlur={() => setTouched(true)}
                  autoFocus
                  autoComplete="email"
                  aria-label="Work email"
                />
                {showEmailError && (
                  <span className="af-error-msg" role="alert">
                    Please enter a valid email address.
                  </span>
                )}
              </div>

              <button
                className="af-btn"
                type="submit"
                disabled={touched && email.trim() === ""}
              >
                Continue with email
              </button>
            </form>

            <p className="af-legal">
              By continuing, you acknowledge Winsight's{" "}
              <a className="af-legal-link" href="#">Privacy Policy</a>{" "}
              and agree to get occasional product updates and promotional emails.
            </p>

            <p className="af-have-account">
              Have an account?{" "}
              <button className="af-signin-link" onClick={() => navigate("/auth")}>
                Sign in
              </button>
            </p>
          </div>
        )}

        {/* ════ STEP 2 — Verify email ════ */}
        {step === "verify" && (
          <div className="af-card">
            <Logo />

            <h1 className="af-title">Verify your email</h1>
            <p className="af-sub">
              Enter the 6-digit code sent to{" "}
              <span className="af-email-display">{email}</span>.
            </p>

            <form className="af-form" onSubmit={handleVerify} noValidate>
              <div className="af-field">
                <input
                  id="af-code"
                  className={`af-input af-code-input${codeError ? " af-input-error" : ""}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(e) => { setCode(e.target.value); setCodeError(false) }}
                  autoFocus
                  autoComplete="one-time-code"
                />
                <span className="af-helper-text">Use 123456 for this demo.</span>
                {codeError && (
                  <span className="af-error-msg" role="alert">
                    Invalid code. Use 123456 for this demo.
                  </span>
                )}
              </div>

              <button className="af-btn" type="submit">
                Verify and continue
              </button>
            </form>

            <p className="af-have-account">
              <button className="af-signin-link" onClick={goBackToEmail}>
                Use a different email
              </button>
            </p>
          </div>
        )}

        {/* ════ STEP 3 — Account information ════ */}
        {step === "info" && (
          <div className="af-card af-card-info">

            {/* Thin blue accent strip */}
            <div className="af-info-deco" aria-hidden="true" />

            <div className="af-info-content">
              <Logo />

              <h1 className="af-title af-title-info">Tell us about your workspace</h1>
              <p className="af-sub af-sub-info">
                This helps us personalize your Winsight experience.
              </p>

              <form className="af-form af-form-info" onSubmit={handleInfoSubmit} noValidate>

                {/* ── Row 1: Name + Role ── */}
                <div className="af-info-grid">

                  <div className="af-field">
                    <label className="af-info-label" htmlFor="af-name">Name</label>
                    <input
                      id="af-name"
                      className={`af-input${infoErrors.name ? " af-input-error" : ""}`}
                      type="text"
                      placeholder="İlayda Çetin"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      autoFocus
                      autoComplete="name"
                    />
                    {infoErrors.name && (
                      <span className="af-error-msg" role="alert">Required</span>
                    )}
                  </div>

                  <div className="af-field">
                    <label className="af-info-label" htmlFor="af-role">Role</label>
                    <div className="af-select-wrap">
                      <select
                        id="af-role"
                        className={`af-input af-select${!role ? " af-select-empty" : ""}${infoErrors.role ? " af-input-error" : ""}`}
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                      >
                        <option value="">Select role</option>
                        <option value="Sales Manager">Sales Manager</option>
                        <option value="Pricing Analyst">Pricing Analyst</option>
                        <option value="Revenue Manager">Revenue Manager</option>
                        <option value="Founder / Executive">Founder / Executive</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    {infoErrors.role && (
                      <span className="af-error-msg" role="alert">Required</span>
                    )}
                  </div>

                </div>

                {/* ── Row 2: Company Name ── */}
                <div className="af-field">
                  <label className="af-info-label" htmlFor="af-company">Company Name</label>
                  <input
                    id="af-company"
                    className={`af-input${infoErrors.company ? " af-input-error" : ""}`}
                    type="text"
                    placeholder="Securify"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    autoComplete="organization"
                  />
                  {infoErrors.company && (
                    <span className="af-error-msg" role="alert">Required</span>
                  )}
                </div>

                {/* ── Row 3: Industry ── */}
                <div className="af-field">
                  <label className="af-info-label" htmlFor="af-industry">Industry</label>
                  <div className="af-select-wrap">
                    <select
                      id="af-industry"
                      className={`af-input af-select${!industry ? " af-select-empty" : ""}${infoErrors.industry ? " af-input-error" : ""}`}
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                    >
                      <option value="">Select industry</option>
                      <option value="Information Technology and Services">Information Technology and Services</option>
                      <option value="Software / SaaS">Software / SaaS</option>
                      <option value="Consulting">Consulting</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="Finance">Finance</option>
                      <option value="Education">Education</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                  {infoErrors.industry && (
                    <span className="af-error-msg" role="alert">Required</span>
                  )}
                </div>

                <button className="af-btn af-btn-create" type="submit">
                  Create my account
                </button>

              </form>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
