// App.jsx — StockQuery AI v2.0 — Terminal Command Center Design
import { useState, useRef, useEffect, useCallback } from 'react'
import api from './services/api'
import MessageBubble from './components/MessageBubble'
import Sidebar from './components/Sidebar'
import AlertsDashboard from './components/AlertsDashboard'
import AuthModal from './components/AuthModal'

const SAMPLE_QUESTIONS = [
  'Which products are low in stock?',
  'Show me all Dairy products',
  'What categories do you have?',
  'Show me all Electronics',
  'What is the price of Basmati Rice?',
  'Which snacks are available?',
  'List products under ₹100',
  'What items need restocking?',
]

const TypingIndicator = () => (
  <div className="msg ai">
    <div className="msg-avatar">AI</div>
    <div className="msg-body">
      <div className="typing">
        <span /><span /><span />
        <span className="typing-label">Querying inventory...</span>
      </div>
    </div>
  </div>
)

const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const MicIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" x2="12" y1="19" y2="22" />
  </svg>
)

export default function App() {
  const [messages, setMessages]   = useState([])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [activeNav, setActiveNav] = useState('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isListening, setIsListening] = useState(false)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [user, setUser] = useState(null)
  const chatRef  = useRef(null)
  const inputRef = useRef(null)

  const playTTS = async (text) => {
    try {
      const response = await api.post('/tts', { text }, { responseType: 'blob' })
      const audioUrl = URL.createObjectURL(response.data)
      const audio = new Audio(audioUrl)
      audio.play()
    } catch (err) {
      console.error("TTS Error:", err)
    }
  }

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert("Your browser does not support Speech Recognition.")
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => setIsListening(true)
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      sendMessage(transcript, true)
    }
    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error)
      setIsListening(false)
    }
    recognition.onend = () => setIsListening(false)
    recognition.start()
  }

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('token')
    const email = localStorage.getItem('email')
    if (token && email) {
      setUser({ email, token })
    } else {
      // Show auth modal if no token
      setIsAuthModalOpen(true)
    }
  }, [])

  const fetchHistory = useCallback(async (token) => {
    try {
      const { data } = await api.get('/history', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (Array.isArray(data)) {
        const historyMsgs = []
        data.forEach(h => {
          historyMsgs.push({
            id: `h-q-${h.id}`,
            role: 'user',
            content: h.question,
            timestamp: new Date(h.timestamp)
          })
          historyMsgs.push({
            id: `h-a-${h.id}`,
            role: 'ai',
            content: h.answer,
            toolUsed: h.tool_used,
            timestamp: new Date(h.timestamp)
          })
        })
        setMessages(historyMsgs)
      }
    } catch (err) {
      console.error("Failed to fetch history:", err)
    }
  }, [])

  useEffect(() => {
    if (user?.token) {
      fetchHistory(user.token)
    }
  }, [user, fetchHistory])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages, loading])

  const sendMessage = useCallback(async (questionText, wasVoice = false) => {
    const question = (typeof questionText === 'string' ? questionText : input).trim()
    if (!question || loading) return

    setInput('')
    setLoading(true)
    setActiveNav('chat')

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    }])

    try {
      const headers = user?.token ? { Authorization: `Bearer ${user.token}` } : {}
      const { data } = await api.post('/query', { question }, { headers })
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer,
        toolUsed: data.tool_used,
        data: data.data,
        userQuery: question, // Store original question to detect intent
        timestamp: new Date(),
      }])
      if (wasVoice === true) {
        playTTS(data.answer)
      }
    } catch (err) {
      const detail = err.response?.data?.detail || 'Query failed. Check backend connection.'
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: detail,
        timestamp: new Date(),
        error: true,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [input, loading, user])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('email')
    setUser(null)
    setMessages([])
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const hasMessages = messages.length > 0

  if (!user) {
    return (
      <div className="auth-page-container" style={{
        height: '100vh', width: '100vw', background: '#080b0f',
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <AuthModal 
          isOpen={true} 
          onClose={() => {}} 
          onAuthSuccess={(data) => setUser({ email: data.email, token: data.access_token })}
          isMandatory={true}
        />
      </div>
    )
  }

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        onQuery={sendMessage}
        sidebarOpen={sidebarOpen}
        messageCount={messages.length}
      />

      {/* ── Main Panel ── */}
      <div className="main-panel">
        {/* ── Top Bar ── */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(o => !o)}
              title="Toggle sidebar"
            >
              <span /><span /><span />
            </button>
            <div className="topbar-breadcrumb">
              <span className="breadcrumb-root">StockQuery</span>
              <span className="breadcrumb-sep">/</span>
              <span className="breadcrumb-current">
                {activeNav === 'chat' ? 'Chat' : activeNav === 'alerts' ? 'Alerts' : 'History'}
              </span>
            </div>
          </div>
          <div className="topbar-right">
            <div className="model-badge">
              <span className="status-dot" />
              Llama-3.3-70B · Nebius
            </div>
            {user ? (
              <div className="user-profile">
                <span className="user-name">{user.email}</span>
                <button className="clear-btn" onClick={handleLogout}>Logout</button>
              </div>
            ) : (
              <button className="clear-btn" onClick={() => setIsAuthModalOpen(true)}>Login</button>
            )}
            {hasMessages && (
              <button className="clear-btn" onClick={() => setMessages([])}>
                Clear Session
              </button>
            )}
          </div>
        </header>

        <main className="chat-area" ref={chatRef}>
          {activeNav === 'history' ? (
            <div className="history-view" style={{ padding: '2rem' }}>
              <h2 style={{ color: '#fff', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Session History</h2>
              {messages.filter(m => m.role === 'user').length === 0 ? (
                <p style={{ color: '#888' }}>No queries have been made in this session yet.</p>
              ) : (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {messages.filter(m => m.role === 'user').map(m => (
                    <li 
                      key={m.id} 
                      className="history-item"
                      style={{ padding: '1rem', borderBottom: '1px solid #222', color: '#00ff88', cursor: 'pointer', transition: 'background 0.2s' }} 
                      onClick={() => { setActiveNav('chat'); setInput(m.content); setTimeout(() => inputRef.current?.focus(), 50); }}
                      onMouseOver={(e) => e.currentTarget.style.background = '#111'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <span style={{ fontSize: '1.1rem' }}>{m.content}</span>
                      <span style={{ color: '#666', fontSize: '0.85rem', marginLeft: '15px', float: 'right' }}>
                        {new Date(m.timestamp).toLocaleTimeString()}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : activeNav === 'alerts' ? (
            <AlertsDashboard />
          ) : !hasMessages ? (
            <div className="welcome">
              <div className="welcome-header">
                <div className="welcome-tag">INVENTORY INTELLIGENCE</div>
                <h1 className="welcome-title">
                  Ask your inventory<br />
                  <span className="welcome-accent">anything.</span>
                </h1>
                <p className="welcome-desc">
                  Natural language queries powered by Llama-3.3-70B.
                  Real-time SQLite data. Zero SQL required.
                </p>
              </div>

              <div className="quick-grid">
                {SAMPLE_QUESTIONS.map((q, i) => (
                  <button
                    key={q}
                    className="quick-btn"
                    onClick={() => sendMessage(q)}
                    disabled={loading}
                    style={{ animationDelay: `${i * 0.05}s` }}
                  >
                    <span className="quick-arrow">→</span>
                    {q}
                  </button>
                ))}
              </div>

              <div className="welcome-stats">
                <div className="wstat">
                  <span className="wstat-num">990</span>
                  <span className="wstat-label">Products</span>
                </div>
                <div className="wstat-div" />
                <div className="wstat">
                  <span className="wstat-num">7</span>
                  <span className="wstat-label">Categories</span>
                </div>
                <div className="wstat-div" />
                <div className="wstat">
                  <span className="wstat-num">5</span>
                  <span className="wstat-label">AI Tools</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {loading && <TypingIndicator />}
            </>
          )}
        </main>

        {/* ── Input Dock ── */}
        <footer className="input-dock">
          <div className="input-wrap">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about stock levels, prices, categories..."
              rows={1}
              disabled={loading}
            />
            <div className="input-actions">
              <span className="input-hint-key">↵ Enter</span>
              <button
                className={`mic-btn ${isListening ? 'listening' : ''}`}
                onClick={startListening}
                disabled={loading || isListening}
                title="Voice Input"
              >
                {isListening ? <span className="mic-spinner" /> : <MicIcon />}
              </button>
              <button
                className="send-btn"
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                title="Send (Enter)"
              >
                {loading ? (
                  <span className="send-spinner" />
                ) : (
                  <SendIcon />
                )}
              </button>
            </div>
          </div>
          <div className="dock-footer">
            <span>Shift+Enter for new line</span>
            <span className="dock-dot">·</span>
            <span>Connected to <code>inventory.db</code></span>
          </div>
        </footer>

      </div>
    </div>
  )
}
