// ForgotPassword.jsx
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail]     = useState('')
  const [sent, setSent]       = useState(false)
  const [devToken, setDevToken] = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/forgot-password', { email })
      setSent(true)
      if (data.dev_token) setDevToken(data.dev_token)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell auth-shell-centered">
      <div className="auth-card auth-card-sm">
        <div className="auth-brand auth-brand-centered" onClick={() => navigate('/')}>
          <svg viewBox="0 0 24 24" fill="none" width="24" height="24">
            <rect x="2" y="3" width="20" height="14" rx="1.5" stroke="#00ff88" strokeWidth="1.8"/>
            <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <span>StockQuery <strong>AI</strong></span>
        </div>

        <div className="auth-icon-wrap">🔑</div>
        <h1 className="auth-title text-center">Forgot password?</h1>
        <p className="auth-subtitle text-center">
          Enter your email and we'll send you a link to reset your password.
        </p>

        {error && <div className="auth-error">{error}</div>}

        {sent ? (
          <div className="auth-success">
            <div>📧 Check your inbox! A reset link has been sent (if that email exists).</div>
            {devToken && (
              <div className="dev-token">
                ⚙️ Dev mode — SMTP not configured.<br/>
                <a href={`/reset-password?token=${devToken}`}>Click here to reset password</a>
              </div>
            )}
            <button className="btn-primary btn-full" style={{marginTop:'1rem'}} onClick={() => navigate('/login')}>
              Back to Sign In
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="auth-form">
            <div className="auth-field">
              <label htmlFor="email">Email address</label>
              <input
                id="email" name="email" type="email"
                value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required autoFocus
              />
            </div>
            <button type="submit" className="btn-primary btn-full" disabled={loading}>
              {loading ? <span className="btn-spinner"/> : 'Send Reset Link →'}
            </button>
          </form>
        )}

        <p className="auth-switch">
          <Link to="/login" className="auth-link">← Back to Sign In</Link>
        </p>
      </div>
    </div>
  )
}
