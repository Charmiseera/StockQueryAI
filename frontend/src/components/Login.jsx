import { useState } from 'react';
import axios from 'axios';

export default function Login({ onLogin, onSwitchToRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Email/Username and password are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post('/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      onLogin(response.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="brand-icon" style={{ display: 'inline-flex', marginBottom: '10px' }}>
            <svg viewBox="0 0 24 24" fill="none" width="32" height="32">
              <rect x="2" y="3" width="20" height="14" rx="1" stroke="#00ff88" strokeWidth="1.5"/>
              <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M6 7h4M6 13h6" stroke="#00ff88" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </div>
          <h1>Welcome Back to <span className="welcome-accent">StockQuery</span></h1>
          <p>Login to access your inventory</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label>Email or Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter email or username"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
            />
          </div>

          <button type="submit" className="primary-btn auth-submit" disabled={loading}>
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        <div className="auth-toggle">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToRegister} className="text-btn">
            Register Here
          </button>
        </div>
      </div>
    </div>
  );
}
