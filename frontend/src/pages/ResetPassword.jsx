// ResetPassword.jsx
import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '../services/api'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''

  const [form, setForm]     = useState({ password: '', confirm: '' })
  const [error, setError]   = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handle = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return }
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return }

    setLoading(true)
    try {
      await api.post('/reset-password', { token, new_password: form.password })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) return (
    <div className="auth-shell auth-shell-centered">
      <div className="auth-card auth-card-sm">
        <div className="auth-icon-wrap">⚠️</div>
        <h1 className="auth-title text-center">Invalid Link</h1>
        <p className="auth-subtitle text-center">This reset link is missing a token. Please request a new one.</p>
        <button className="btn-primary btn-full" onClick={() => navigate('/forgot-password')}>Request New Link →</button>
      </div>
    </div>
  )

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

        <div className="auth-icon-wrap">🔒</div>
        <h1 className="auth-title text-center">Set new password</h1>
        <p className="auth-subtitle text-center">Choose a strong password for your account.</p>

        {error && <div className="auth-error">{error}</div>}

        {success ? (
          <div className="auth-success">
            ✅ Password reset successfully! You can now sign in with your new password.
            <button className="btn-primary btn-full" style={{marginTop:'1rem'}} onClick={() => navigate('/login')}>
              Sign In →
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="auth-form">
            <div className="auth-field">
              <label htmlFor="password">New password</label>
              <input
                id="password" name="password" type="password"
                value={form.password} onChange={handle}
                placeholder="Min. 6 characters"
                required autoFocus
              />
            </div>
            <div className="auth-field">
              <label htmlFor="confirm">Confirm new password</label>
              <input
                id="confirm" name="confirm" type="password"
                value={form.confirm} onChange={handle}
                placeholder="Repeat your password"
                required
              />
            </div>
            <button type="submit" className="btn-primary btn-full" disabled={loading}>
              {loading ? <span className="btn-spinner"/> : 'Reset Password →'}
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
