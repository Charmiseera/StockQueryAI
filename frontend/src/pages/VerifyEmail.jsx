// VerifyEmail.jsx
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../services/api'

export default function VerifyEmail() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''

  const [status, setStatus] = useState('loading') // loading | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return }
    api.get(`/verify-email?token=${token}`)
      .then(r => { setStatus('success'); setMessage(r.data.message) })
      .catch(e => { setStatus('error'); setMessage(e.response?.data?.detail || 'Verification failed.') })
  }, [token])

  return (
    <div className="auth-shell auth-shell-centered">
      <div className="auth-card auth-card-sm text-center">
        <div className="auth-brand auth-brand-centered" onClick={() => navigate('/')}>
          <svg viewBox="0 0 24 24" fill="none" width="24" height="24">
            <rect x="2" y="3" width="20" height="14" rx="1.5" stroke="#00ff88" strokeWidth="1.8"/>
            <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <span>StockQuery <strong>AI</strong></span>
        </div>

        {status === 'loading' && (
          <>
            <div className="auth-icon-wrap spinning">📧</div>
            <h1 className="auth-title">Verifying your email…</h1>
            <p className="auth-subtitle">Please wait a moment.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="auth-icon-wrap">✅</div>
            <h1 className="auth-title">Email Verified!</h1>
            <p className="auth-subtitle">{message}</p>
            <button className="btn-primary btn-full" style={{marginTop:'1.5rem'}} onClick={() => navigate('/login')}>
              Sign In →
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="auth-icon-wrap">❌</div>
            <h1 className="auth-title">Verification Failed</h1>
            <p className="auth-subtitle">{message}</p>
            <button className="btn-primary btn-full" style={{marginTop:'1.5rem'}} onClick={() => navigate('/signup')}>
              Try Signing Up Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
