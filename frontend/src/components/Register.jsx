import { useState } from 'react';
import axios from 'axios';

export default function Register({ onRegister, onSwitchToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !email.trim() || !password.trim()) {
      setError('Username, email, and password are required');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await axios.post('/register', { username, email, password });
      
      // Automatically log in after successful registration
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post('/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      onRegister(response.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
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
          <h1>Create an <span className="welcome-accent">Account</span></h1>
          <p>Join StockQuery AI to manage your inventory</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label>Choose Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter a new username"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label>Choose Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a strong password"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label>Confirm Password</label>
            <input 
              type="password" 
              value={confirmPassword} 
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              disabled={loading}
            />
          </div>

          <button type="submit" className="primary-btn auth-submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className="auth-toggle">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="text-btn">
            Login Here
          </button>
        </div>
      </div>
    </div>
  );
}
