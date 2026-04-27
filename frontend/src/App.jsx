// App.jsx — StockQuery AI v3.0 — With Auth Routing
import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LandingPage    from './pages/LandingPage'
import LoginPage      from './pages/LoginPage'
import SignupPage     from './pages/SignupPage'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword  from './pages/ResetPassword'
import VerifyEmail    from './pages/VerifyEmail'
import Dashboard      from './pages/Dashboard'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('sq_token')
  return token ? children : <Navigate to="/login" replace />
}

function GuestRoute({ children }) {
  const token = localStorage.getItem('sq_token')
  return token ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  const [user, setUser] = useState(() => {
    const email = localStorage.getItem('sq_email')
    const token = localStorage.getItem('sq_token')
    return token && email ? { email, token } : null
  })

  const login = (token, email) => {
    localStorage.setItem('sq_token', token)
    localStorage.setItem('sq_email', email)
    setUser({ token, email })
  }

  const logout = () => {
    localStorage.removeItem('sq_token')
    localStorage.removeItem('sq_email')
    setUser(null)
  }

  return (
    <Routes>
      <Route path="/"               element={<GuestRoute><LandingPage /></GuestRoute>} />
      <Route path="/login"          element={<GuestRoute><LoginPage onLogin={login} /></GuestRoute>} />
      <Route path="/signup"         element={<GuestRoute><SignupPage /></GuestRoute>} />
      <Route path="/forgot-password" element={<GuestRoute><ForgotPassword /></GuestRoute>} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/verify-email"   element={<VerifyEmail />} />
      <Route path="/dashboard"      element={<PrivateRoute><Dashboard user={user} onLogout={logout} /></PrivateRoute>} />
      <Route path="*"               element={<Navigate to="/" replace />} />
    </Routes>
  )
}
