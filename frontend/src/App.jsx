// App.jsx — StockQuery AI v2.0 — Terminal Command Center Design
import { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import MessageBubble from './components/MessageBubble'
import Sidebar from './components/Sidebar'

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
  const chatRef  = useRef(null)
  const inputRef = useRef(null)

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
  }, [input, loading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const hasMessages = messages.length > 0

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
                {activeNav === 'chat' ? 'Chat' : activeNav === 'explore' ? 'Explore' : 'History'}
              </span>
            </div>
          </div>
          <div className="topbar-right">
            <div className="model-badge">
              <span className="status-dot" />
              Llama-3.3-70B · Nebius
            </div>
            {hasMessages && (
              <button className="clear-btn" onClick={() => setMessages([])}>
                Clear Session
              </button>
            )}
          </div>
        </header>

        {/* ── Chat Area ── */}
        <main className="chat-area" ref={chatRef}>
          {!hasMessages ? (
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
                  <span className="wstat-num">25</span>
                  <span className="wstat-label">Products</span>
                </div>
                <div className="wstat-div" />
                <div className="wstat">
                  <span className="wstat-num">5</span>
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
