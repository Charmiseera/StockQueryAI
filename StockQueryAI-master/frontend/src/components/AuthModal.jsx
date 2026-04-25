import { useState } from 'react'
import api from '../services/api'

export default function AuthModal({ isOpen, onClose, onAuthSuccess, isMandatory = false }) {
  const [isLogin, setIsLogin] = useState(true)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  if (!isOpen) return null

  // Validation functions
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validatePassword = (pwd) => {
    return pwd.length >= 6
  }

  const validateForm = () => {
    if (!email.trim()) {
      setError('Email is required')
      return false
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address')
      return false
    }

    if (!password) {
      setError('Password is required')
      return false
    }

    if (!validatePassword(password)) {
      setError('Password must be at least 6 characters')
      return false
    }

    if (!isLogin) {
      if (!name.trim()) {
        setError('Name is required')
        return false
      }

      if (password !== confirmPassword) {
        setError('Passwords do not match')
        return false
      }
    }

    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      if (isLogin) {
        const { data } = await api.post('/login', { email, password })
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('email', data.email)
        localStorage.setItem('user', JSON.stringify({ email: data.email }))
        onAuthSuccess(data)
        onClose()
        // Reset form
        setEmail('')
        setPassword('')
        setConfirmPassword('')
      } else {
        // Register
        const { data } = await api.post('/register', { email, password })
        if (data.success) {
          setSuccessMsg('Registration successful! Please login with your credentials.')
          // Switch to login mode after 1.5 seconds
          setTimeout(() => {
            setIsLogin(true)
            setEmail('')
            setPassword('')
            setConfirmPassword('')
            setName('')
            setSuccessMsg(null)
          }, 1500)
        }
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 
                      err.response?.data?.message || 
                      'Authentication failed. Please try again.'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setError(null)
    setSuccessMsg(null)
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setName('')
  }

  return (
    <div className="modal-overlay" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, backdropFilter: 'blur(4px)'
    }}>
      <div className="modal-content" style={{
        background: '#0d1117', border: '1px solid #333', padding: '2.5rem', width: '100%', maxWidth: '420px',
        animation: 'fade-up 0.3s ease-out', maxHeight: '90vh', overflowY: 'auto'
      }}>
        <h2 style={{ color: '#00ff88', marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: '800' }}>
          {isLogin ? '🔓 Login to StockQuery' : '✨ Create Your Account'}
        </h2>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', color: '#888', fontSize: '0.8rem', marginBottom: '0.5rem' }}>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{
                  width: '100%', background: '#161e28', border: '1px solid #333', padding: '0.8rem',
                  color: '#fff', outline: 'none', fontSize: '1rem', boxSizing: 'border-box'
                }}
                placeholder="e.g. John Doe"
                disabled={loading}
              />
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', color: '#888', fontSize: '0.8rem', marginBottom: '0.5rem' }}>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%', background: '#161e28', border: '1px solid #333', padding: '0.8rem',
                color: '#fff', outline: 'none', fontSize: '1rem', boxSizing: 'border-box'
              }}
              placeholder="e.g. user@example.com"
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', color: '#888', fontSize: '0.8rem', marginBottom: '0.5rem' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%', background: '#161e28', border: '1px solid #333', padding: '0.8rem',
                color: '#fff', outline: 'none', fontSize: '1rem', boxSizing: 'border-box'
              }}
              placeholder={isLogin ? 'Enter your password' : 'At least 6 characters'}
              disabled={loading}
            />
          </div>

          {!isLogin && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: '#888', fontSize: '0.8rem', marginBottom: '0.5rem' }}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={{
                  width: '100%', background: '#161e28', border: '1px solid #333', padding: '0.8rem',
                  color: '#fff', outline: 'none', fontSize: '1rem', boxSizing: 'border-box'
                }}
                placeholder="Confirm your password"
                disabled={loading}
              />
            </div>
          )}

          {error && (
            <div style={{ 
              background: '#3d1f1f', 
              color: '#ff6b2b', 
              fontSize: '0.85rem', 
              padding: '0.8rem', 
              borderRadius: '4px',
              marginBottom: '1rem',
              border: '1px solid #5a2a2a'
            }}>
              {error}
            </div>
          )}

          {successMsg && (
            <div style={{ 
              background: '#1f3d1f', 
              color: '#00ff88', 
              fontSize: '0.85rem', 
              padding: '0.8rem', 
              borderRadius: '4px',
              marginBottom: '1rem',
              border: '1px solid #2a5a2a'
            }}>
              ✓ {successMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', background: loading ? '#00cc66' : '#00ff88', border: 'none', padding: '1rem',
              color: '#080b0f', fontWeight: '700', fontSize: '1rem', cursor: loading ? 'not-allowed' : 'pointer',
              borderRadius: '4px', transition: 'background 0.2s', opacity: loading ? 0.7 : 1
            }}
            onMouseEnter={(e) => !loading && (e.target.style.background = '#00e67a')}
            onMouseLeave={(e) => !loading && (e.target.style.background = '#00ff88')}
          >
            {loading ? '⏳ ' + (isLogin ? 'Logging in...' : 'Creating account...') : (isLogin ? '🔓 Login' : '✨ Register')}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <p style={{ color: '#666', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
          </p>
          <button
            type="button"
            onClick={toggleMode}
            disabled={loading}
            style={{ 
              background: 'none', border: '1px solid #333', color: '#00ff88', cursor: loading ? 'not-allowed' : 'pointer',
              padding: '0.6rem 1.2rem', borderRadius: '4px', fontSize: '0.9rem', fontWeight: '600',
              transition: 'all 0.2s', opacity: loading ? 0.5 : 1
            }}
            onMouseEnter={(e) => !loading && (e.target.style.borderColor = '#00ff88')}
            onMouseLeave={(e) => !loading && (e.target.style.borderColor = '#333')}
          >
            {isLogin ? '✨ Create Account' : '🔓 Login'}
          </button>
        </div>

        {!isMandatory && (
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            style={{
              position: 'absolute', top: '1rem', right: '1rem', background: 'none',
              border: 'none', color: '#666', fontSize: '1.5rem', cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1
            }}
          >
            ×
          </button>
        )}
      </div>
    </div>
  )
}
