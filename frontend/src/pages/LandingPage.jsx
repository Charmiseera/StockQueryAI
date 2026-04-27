// LandingPage.jsx — Premium hero landing page
import { useNavigate } from 'react-router-dom'

const FEATURES = [
  { icon: '🧠', title: 'AI-Powered Queries', desc: 'Ask anything in plain English. No SQL needed.' },
  { icon: '⚡', title: 'Real-Time Data', desc: 'Instant answers from your live SQLite inventory.' },
  { icon: '📊', title: 'Visual Analytics', desc: 'Charts, breakdowns, and trends at a glance.' },
  { icon: '🔒', title: 'Secure & Private', desc: 'JWT authentication with per-user data isolation.' },
  { icon: '🎙️', title: 'Voice Input', desc: 'Speak your queries with speech recognition.' },
  { icon: '📧', title: 'Smart Alerts', desc: 'Email alerts for low stock and critical events.' },
]

const STATS = [
  { num: '990+', label: 'Products Indexed' },
  { num: '8',    label: 'Categories' },
  { num: '<1s',  label: 'Query Response' },
  { num: '70B',  label: 'Model Parameters' },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="landing">
      {/* ── Nav ── */}
      <nav className="landing-nav">
        <div className="landing-logo">
          <div className="logo-icon-wrap">
            <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
              <rect x="2" y="3" width="20" height="14" rx="1.5" stroke="#00ff88" strokeWidth="1.8"/>
              <path d="M8 21h8M12 17v4" stroke="#00ff88" strokeWidth="1.8" strokeLinecap="round"/>
              <path d="M6 7h4M6 10h9M6 13h6" stroke="#00ff88" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
          </div>
          <span>StockQuery <strong>AI</strong></span>
        </div>
        <div className="landing-nav-actions">
          <button className="nav-link" onClick={() => navigate('/login')}>Sign In</button>
          <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started →</button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-badge">Powered by Llama-3.3-70B · Nebius AI</div>
        <h1 className="hero-title">
          Your inventory,<br />
          <span className="hero-gradient">understood.</span>
        </h1>
        <p className="hero-desc">
          Ask questions in plain English. Get instant answers from your real inventory data.<br />
          No dashboards to build. No SQL to write. Just ask.
        </p>
        <div className="hero-actions">
          <button className="btn-primary btn-lg" onClick={() => navigate('/signup')}>
            Start for Free →
          </button>
          <button className="btn-ghost btn-lg" onClick={() => navigate('/login')}>
            Sign In
          </button>
        </div>

        {/* Query Preview */}
        <div className="hero-preview">
          <div className="preview-bar">
            <span className="preview-dot red"/><span className="preview-dot yellow"/><span className="preview-dot green"/>
            <span className="preview-title">StockQuery AI</span>
          </div>
          <div className="preview-body">
            <div className="preview-msg user">Which Dairy products are low in stock?</div>
            <div className="preview-msg ai">
              <span className="preview-badge">AI</span>
              Found 12 Dairy products with stock ≤ 20. Showing top 12 results in the table below.
            </div>
            <div className="preview-table-hint">
              <span>📊 Data table rendered • 12 rows • sorted by stock ↑</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="landing-stats">
        {STATS.map(s => (
          <div key={s.label} className="landing-stat">
            <div className="lstat-num">{s.num}</div>
            <div className="lstat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* ── Features ── */}
      <section className="features">
        <div className="section-tag">CAPABILITIES</div>
        <h2 className="section-title">Everything you need to manage inventory</h2>
        <div className="features-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feature-card">
              <div className="feature-icon">{f.icon}</div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="landing-cta">
        <h2 className="cta-title">Ready to query smarter?</h2>
        <p className="cta-desc">Create a free account and start asking questions in seconds.</p>
        <button className="btn-primary btn-lg" onClick={() => navigate('/signup')}>
          Create Free Account →
        </button>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-logo">
          <span>StockQuery <strong>AI</strong></span>
        </div>
        <div className="footer-links">
          <button className="footer-link" onClick={() => navigate('/login')}>Sign In</button>
          <button className="footer-link" onClick={() => navigate('/signup')}>Sign Up</button>
        </div>
        <p className="footer-copy">© 2026 StockQuery AI. Powered by Nebius · Llama-3.3-70B</p>
      </footer>
    </div>
  )
}
