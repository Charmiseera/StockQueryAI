// SignupPage.jsx
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'

export default function SignupPage() {
  const navigate = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '', confirm: '' })
  const [error, setError]   = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [devToken, setDevToken] = useState('')

  const handle = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return }
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return }

    setLoading(true)
    try {
      const { data } = await api.post('/register', {
        email: form.email,
        password: form.password,
      })
      setSuccess(data.message)
      if (data.dev_token) setDevToken(data.dev_token)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-left">
        <div className="auth-left-content">
          <div className="auth-brand" onClick={() => navigate('/')}>
            <svg viewBox="0 0 24 24" fill="none" width="28" height="28">
              <rect x="2" y="3" width="20" height="14" rx="1.5" stroke="#00ff88" strokeWidth="1.8"/>
              <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.8" strokeLinecap="round"/>
              <path d="M6 7h4M6 10h9M6 13h6" stroke="#00ff88" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
            <span>StockQuery <strong>AI</strong></span>
          </div>
          <div className="auth-left-quotes">
            <div className="auth-quote">
              <p>"Join thousands managing smarter inventory with AI."</p>
            </div>
            <div className="auth-features-mini">
              {['Free to start', 'No credit card needed', '990+ products indexed', 'Email alerts included'].map(f => (
                <div key={f} className="auth-feat"><span className="auth-feat-dot"/>  {f}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h1 className="auth-title">Create account</h1>
            <p className="auth-subtitle">Start querying your inventory in seconds</p>
          </div>

          {error   && <div className="auth-error">{error}</div>}
          {success && (
            <div className="auth-success">
              <div>✅ {success}</div>
              {devToken && (
                <div className="dev-token">
                  <span>⚙️ Dev mode — SMTP not configured.<br/>
                  <a href={`/verify-email?token=${devToken}`}>Click here to verify your email</a></span>
                </div>
              )}
              <button className="btn-primary btn-full" style={{marginTop:'1rem'}} onClick={() => navigate('/login')}>
                Go to Sign In →
              </button>
            </div>
          )}

          {!success && (
            <form onSubmit={submit} className="auth-form">
              <div className="auth-field">
                <label htmlFor="email">Email address</label>
                <input
                  id="email" name="email" type="email"
                  value={form.email} onChange={handle}
                  placeholder="you@example.com"
                  required autoFocus
                />
              </div>
              <div className="auth-field">
                <label htmlFor="password">Password</label>
                <input
                  id="password" name="password" type="password"
                  value={form.password} onChange={handle}
                  placeholder="Min. 6 characters"
                  required
                />
              </div>
              <div className="auth-field">
                <label htmlFor="confirm">Confirm password</label>
                <input
                  id="confirm" name="confirm" type="password"
                  value={form.confirm} onChange={handle}
                  placeholder="Repeat your password"
                  required
                />
              </div>

              <div className="auth-strength">
                <div className={`strength-bar ${form.password.length >= 6 ? (form.password.length >= 10 ? 'strong' : 'ok') : ''}`}/>
                <span>{form.password.length === 0 ? '' : form.password.length < 6 ? 'Too short' : form.password.length < 10 ? 'Good' : 'Strong'}</span>
              </div>

              <button type="submit" className="btn-primary btn-full" disabled={loading}>
                {loading ? <span className="btn-spinner"/> : 'Create Account →'}
              </button>

              <p className="auth-terms">
                By signing up you agree to our <span className="auth-link">Terms</span> and <span className="auth-link">Privacy Policy</span>.
              </p>
            </form>
          )}

          <p className="auth-switch">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign in →</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
