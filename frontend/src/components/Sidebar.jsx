// Sidebar.jsx — Navigation panel with stats and quick-access categories
import { useState, useEffect } from 'react'
import axios from 'axios'

const NAV_ITEMS = [
  { id: 'chat',    label: 'Chat',    icon: '◈' },
  { id: 'history', label: 'History', icon: '◷' },
]

const CATEGORIES = [
  { id: 'fruits',   label: 'Fruits & Veg',   icon: '🍎', query: 'Can you show me all our fruits and vegetables?', color: '#39ff14' },
  { id: 'dairy',    label: 'Dairy',          icon: '🥛', query: 'Show me all the dairy products we have.',       color: '#00ff88' },
  { id: 'grains',   label: 'Grains & Pulses', icon: '🌾', query: 'What grains and pulses do we have in stock?',     color: '#ffd700' },
  { id: 'seafood',  label: 'Seafood',        icon: '🐟', query: 'Can you list all the seafood products?',             color: '#00d4ff' },
  { id: 'beverages',label: 'Beverages',      icon: '🥤', query: 'Show me all of our beverages.',           color: '#ff4488' },
]

export default function Sidebar({ activeNav, setActiveNav, onQuery, onUploadCSV, onLogout, sidebarOpen, messageCount }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    axios.get('/health')
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
  }, [])

  if (!sidebarOpen) return null

  return (
    <aside className="sidebar">

      {/* ── Brand ── */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="#00ff88" strokeWidth="2"/>
            <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="2" strokeLinecap="round"/>
            <path d="M6 7h4M6 10h8M6 13h6" stroke="#00ff88" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <div className="brand-name">StockQuery</div>
          <div className="brand-tag">AI DASHBOARD</div>
        </div>
      </div>

      {/* ── Nav ── */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activeNav === item.id ? 'nav-active' : ''}`}
            onClick={() => setActiveNav(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
            {item.id === 'chat' && messageCount > 0 && (
              <span className="nav-badge">{messageCount}</span>
            )}
          </button>
        ))}
      </nav>

      {/* ── Categories ── */}
      <div className="sidebar-section">
        <div className="section-label">CATEGORIES</div>
        <div className="category-list">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className="cat-item"
              onClick={() => onQuery(cat.query)}
              title={`Browse ${cat.label}`}
            >
              <div className="cat-icon-wrapper">
                <span className="cat-mini-icon">{cat.icon}</span>
                <span
                  className="cat-dot-pulse"
                  style={{ background: cat.color }}
                />
              </div>
              <span className="cat-name">{cat.label}</span>
              <span className="cat-arrow">→</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Quick Queries ── */}
      <div className="sidebar-section">
        <div className="section-label">QUICK ACTIONS</div>
        <div className="quick-actions">
          <button className="action-btn" onClick={() => onQuery('Which products are low in stock?')}>
            <span className="action-icon warning">!</span>
            Low Stock Alert
          </button>
          <button className="action-btn" onClick={() => onQuery('Please show me a list of all product categories available in the database')}>
            <span className="action-icon info">≡</span>
            All Categories
          </button>
          <button className="action-btn" onClick={onUploadCSV}>
            <span className="action-icon upload">📁</span>
            Upload CSV
          </button>
        </div>
      </div>

      {/* ── Status Footer ── */}
      <div className="sidebar-footer">
        <div className="status-row">
          <span className={`status-indicator ${health ? 'online' : 'offline'}`} />
          <span className="status-text">
            {health ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </span>
        </div>
        <div className="db-info">
          <span className="db-icon">◉</span>
          inventory.db · 990 units
        </div>
        <button className="clear-btn" onClick={onLogout} style={{ marginTop: '16px', width: '100%' }}>
          Logout
        </button>
      </div>
    </aside>
  )
}
