// Sidebar.jsx — Navigation panel with stats and quick-access categories
import { useState, useEffect } from 'react'
import api from '../services/api'

const NAV_ITEMS = [
  { id: 'chat',    label: 'Chat',    icon: '◈' },
  { id: 'history', label: 'History', icon: '◷' },
]

const CATEGORY_QUERIES = {
  'Fruits & Veg':    'Show me all Fruits & Vegetables',
  'Dairy':           'Show me all Dairy products',
  'Grains & Pulses': 'Show me all Grains & Pulses',
  'Seafood':         'Show me all Seafood',
  'Beverages':       'Show me all Beverages',
  'Bakery':          'Show me all Bakery products',
  'Oils & Fats':     'Show me all Oils & Fats',
}

const CATEGORY_COLORS = {
  'Fruits & Veg':    '#39ff14',
  'Dairy':           '#00ff88',
  'Grains & Pulses': '#ffd700',
  'Seafood':         '#00d4ff',
  'Beverages':       '#ff4488',
  'Bakery':          '#ff9944',
  'Oils & Fats':     '#cc88ff',
}

export default function Sidebar({ activeNav, setActiveNav, onQuery, sidebarOpen, messageCount, userEmail, onLogout }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.get('/health')
      .then(r => setHealth(r.data))
      .catch(() => setHealth(null))
  }, [])

  if (!sidebarOpen) return null

  return (
    <aside className="sidebar">
      {/* ── Brand ── */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18">
            <rect x="2" y="3" width="20" height="14" rx="1" stroke="#00ff88" strokeWidth="1.5"/>
            <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M6 7h4M6 10h8M6 13h6" stroke="#00ff88" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <div className="brand-name">StockQuery</div>
          <div className="brand-tag">AI</div>
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

      <div className="sidebar-divider" />

      {/* ── Categories ── */}
      <div className="sidebar-section">
        <div className="section-label">CATEGORIES</div>
        <div className="category-list">
          {Object.entries(CATEGORY_QUERIES).map(([cat, query]) => (
            <button
              key={cat}
              className="cat-item"
              onClick={() => onQuery(query)}
              title={`Browse ${cat}`}
            >
              <span className="cat-dot" style={{ background: CATEGORY_COLORS[cat] }} />
              <span className="cat-name">{cat}</span>
              <span className="cat-arrow">→</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-divider" />

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
          <button className="action-btn" onClick={() => onQuery('Show me the most expensive products')}>
            <span className="action-icon accent">↑</span>
            Top Priced
          </button>
        </div>
      </div>

      {/* ── Status Footer ── */}
      <div className="sidebar-footer">
        {userEmail && (
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{userEmail[0].toUpperCase()}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-email">{userEmail}</div>
              <button className="sidebar-logout" onClick={onLogout}>Sign out</button>
            </div>
          </div>
        )}
        <div className="status-row">
          <span className={`status-indicator ${health ? 'online' : 'offline'}`} />
          <span className="status-text">{health ? 'API Connected' : 'API Offline'}</span>
        </div>
        <div className="db-info">
          <span className="db-icon">◉</span>
          inventory.db · 990 products
        </div>
      </div>
    </aside>
  )
}
