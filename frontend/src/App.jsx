// App.jsx — StockQuery AI v3.0 — Premium Dashboard
import { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import MessageBubble from './components/MessageBubble'
import Sidebar from './components/Sidebar'
import CsvUploadModal from './components/CsvUploadModal'
import Login from './components/Login'
import Register from './components/Register'

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

const UniqueLoader = () => {
  const [iconIndex, setIconIndex] = useState(0)
  const icons = ['🍎', '🥦', '🥕', '🥛', '🐟', '🥤', '🌾']
  
  useEffect(() => {
    const interval = setInterval(() => {
      setIconIndex((prev) => (prev + 1) % icons.length)
    }, 400)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="msg ai loader-msg">
      <div className="msg-avatar">AI</div>
      <div className="msg-body">
        <div className="scanner-container">
          <div className="scanner-ui">
            <div className="scanner-line" />
            <div className="scanner-icon-wrap">
              <span className="scanner-icon">{icons[iconIndex]}</span>
            </div>
          </div>
          <div className="scanner-content">
            <div className="scanner-label">SCANNING INVENTORY...</div>
            <div className="scanner-subtext">Searching database for relevant stock records</div>
            <div className="scanner-progress-track">
              <div className="scanner-progress-fill" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

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
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [authMode, setAuthMode] = useState('login')
  const chatRef  = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }, [token])

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setMessages([])
  }

  useEffect(() => {
    if (token) {
      axios.get('/me').catch((err) => {
        if (err.response?.status === 401) {
          handleLogout()
        }
      })
    }
  }, [token])

  const playTTS = async (text) => {
    try {
      const response = await axios.post('/tts', { text }, { responseType: 'blob' })
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
      const { data } = await axios.post('/query', { question })
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        content: data.answer,
        toolUsed: data.tool_used,
        data: data.data,
        userQuery: question,
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
      if (err.response?.status === 401) {
        handleLogout()
      }
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [input, loading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const hasMessages = messages.length > 0

  if (!token) {
    if (authMode === 'login') {
      return <Login onLogin={handleLogin} onSwitchToRegister={() => setAuthMode('register')} />
    } else {
      return <Register onRegister={handleLogin} onSwitchToLogin={() => setAuthMode('login')} />
    }
  }

  return (
    <div className="app-shell">

      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        onQuery={sendMessage}
        onUploadCSV={() => setIsCsvModalOpen(true)}
        onLogout={handleLogout}
        sidebarOpen={sidebarOpen}
        messageCount={messages.length}
      />

      <div className="main-panel">

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
              <span className="breadcrumb-root">StockQuery AI</span>
              <span className="breadcrumb-sep">/</span>
              <span className="breadcrumb-current">
                {activeNav === 'chat' ? 'Assistant' : activeNav === 'explore' ? 'Analytics' : 'History'}
              </span>
            </div>
          </div>
          <div className="topbar-right">
            <div className="model-badge">
              <span className="status-dot" />
              LLAMA-3.3-70B
            </div>
            {hasMessages && (
              <button className="clear-btn" onClick={() => setMessages([])}>
                Clear Session
              </button>
            )}
          </div>
        </header>

        <main className="chat-area" ref={chatRef}>
          {activeNav === 'history' ? (
            <div className="history-view">
              <div className="welcome-header">
                <div className="welcome-tag">SESSION LOGS</div>
                <h2 className="welcome-title">Your Recent Queries</h2>
              </div>
              
              {messages.filter(m => m.role === 'user').length === 0 ? (
                <div className="welcome-desc" style={{ marginTop: '2rem' }}>No queries have been made in this session yet.</div>
              ) : (
                <div className="category-list" style={{ marginTop: '2rem', maxWidth: '600px', marginInline: 'auto' }}>
                  {messages.filter(m => m.role === 'user').map(m => (
                    <button 
                      key={m.id} 
                      className="nav-item"
                      onClick={() => { setActiveNav('chat'); setInput(m.content); setTimeout(() => inputRef.current?.focus(), 50); }}
                    >
                      <span className="nav-icon">💬</span>
                      <span className="nav-label">{m.content}</span>
                      <span className="nav-badge">{new Date(m.timestamp).toLocaleTimeString()}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : !hasMessages ? (
            <div className="welcome">
              <div className="welcome-header">
                <div className="welcome-tag">INVENTORY INTELLIGENCE</div>
                <h1 className="welcome-title">
                  Ask your inventory anything.
                </h1>
                <p className="welcome-desc">
                  Natural language queries powered by Llama-3.3-70B.
                  Real-time SQLite data. Zero SQL required.
                </p>
                <div style={{ marginTop: '24px' }}>
                  <button 
                    className="primary-btn" 
                    onClick={() => setIsCsvModalOpen(true)}
                  >
                    📁 Upload Inventory CSV
                  </button>
                </div>
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
                    {q}
                    <span className="quick-arrow">→</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {loading && <UniqueLoader />}
            </>
          )}
        </main>

        <footer className="input-dock">
          <div className="input-wrap">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Query stock, prices, or categories..."
              rows={1}
              disabled={loading}
            />
            <div className="input-actions">
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
                title="Send"
              >
                {loading ? (
                  <div className="send-spinner" />
                ) : (
                  <SendIcon />
                )}
              </button>
            </div>
          </div>
        </footer>

      </div>
      <CsvUploadModal 
        isOpen={isCsvModalOpen} 
        onClose={() => setIsCsvModalOpen(false)} 
        onUploadSuccess={(insertedCount) => {
          setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'ai',
            content: `Successfully ingested ${insertedCount} products. You can now query your dataset!`,
            timestamp: new Date(),
          }])
        }}
      />
    </div>
  )
}

