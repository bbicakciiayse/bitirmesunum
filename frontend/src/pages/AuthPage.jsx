import { useState } from "react"
import { useNavigate } from "react-router-dom"
import "./AuthPage.css"

export default function AuthPage() {
  const navigate = useNavigate()

  const [step,      setStep]      = useState("signin")  // "signin" | "mfa"
  const [email,     setEmail]     = useState("")
  const [password,  setPassword]  = useState("")
  const [code,      setCode]      = useState("")
  const [codeError, setCodeError] = useState(false)

  function handleSignIn(e) {
    e.preventDefault()
    setStep("mfa")
  }

  function handleMfa(e) {
    e.preventDefault()
    if (code.trim() === "123456") {
      navigate("/analysis")
    } else {
      setCodeError(true)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-bg-glow" aria-hidden="true" />

      <div className="auth-container">

        {/* Wordmark */}
        <div className="auth-logo">
          Win<span className="auth-accent">sight</span>
        </div>

        {/* ── Step: Sign In ── */}
        {step === "signin" && (
          <>
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-sub">
              Sign in to continue to your Winsight workspace.
            </p>

            <form className="auth-form" onSubmit={handleSignIn} noValidate>
              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-email">Email</label>
                <input
                  id="auth-email"
                  className="auth-input"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-password">Password</label>
                <input
                  id="auth-password"
                  className="auth-input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>

              <button className="auth-btn" type="submit">Sign In</button>
            </form>

            <p className="auth-footer-line">
              Don't have an account?{" "}
              <a className="auth-link" href="/#pricing">Sign up</a>
              {" "}or{" "}
              <a className="auth-link" href="/">learn more</a>
            </p>
          </>
        )}

        {/* ── Step: MFA ── */}
        {step === "mfa" && (
          <>
            <h1 className="auth-title">Verify your identity</h1>
            <p className="auth-sub">
              Enter the 6-digit verification code sent to your email.
            </p>

            <form className="auth-form" onSubmit={handleMfa} noValidate>
              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-code">
                  Verification Code
                </label>
                <input
                  id="auth-code"
                  className={`auth-input auth-code-input${codeError ? " auth-input-error" : ""}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value)
                    setCodeError(false)
                  }}
                  autoFocus
                  autoComplete="one-time-code"
                />
                {codeError && (
                  <span className="auth-error-msg">
                    Invalid code. Use 123456 for the demo.
                  </span>
                )}
              </div>

              <button className="auth-btn" type="submit">
                Verify and Continue
              </button>
            </form>

            <p className="auth-footer-line">
              Don't have an account?{" "}
              <a className="auth-link" href="/#pricing">Sign up</a>
              {" "}or{" "}
              <a className="auth-link" href="/">learn more</a>
            </p>
          </>
        )}

      </div>
    </div>
  )
}
