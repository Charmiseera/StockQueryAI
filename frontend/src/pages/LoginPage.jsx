// LoginPage.jsx
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'

export default function LoginPage({ onLogin }) {
  const navigate = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handle = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/login', form)
      onLogin(data.access_token, data.email)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
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
              <p>"Ask your inventory anything — in plain English."</p>
            </div>
            <div className="auth-features-mini">
              {['AI-powered queries', 'Real-time inventory', 'Visual analytics', 'Voice input'].map(f => (
                <div key={f} className="auth-feat"><span className="auth-feat-dot"/>  {f}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h1 className="auth-title">Welcome back</h1>
            <p className="auth-subtitle">Sign in to your StockQuery AI account</p>
          </div>

          {error && <div className="auth-error">{error}</div>}

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
              <div className="auth-field-row">
                <label htmlFor="password">Password</label>
                <Link to="/forgot-password" className="auth-link-small">Forgot password?</Link>
              </div>
              <input
                id="password" name="password" type="password"
                value={form.password} onChange={handle}
                placeholder="••••••••"
                required
              />
            </div>
            <button type="submit" className="btn-primary btn-full" disabled={loading}>
              {loading ? <span className="btn-spinner"/> : 'Sign In →'}
            </button>
          </form>

          <p className="auth-switch">
            Don't have an account?{' '}
            <Link to="/signup" className="auth-link">Create one free →</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
