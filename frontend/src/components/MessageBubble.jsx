// MessageBubble.jsx — Renders a single chat message with tool tag and data table
import DataTable from './DataTable'

const formatTime = (date) =>
  date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export default function MessageBubble({ message }) {
  const { role, content, toolUsed, data, timestamp, error } = message

  return (
    <div className={`msg ${role} ${error ? 'msg-error' : ''}`}>
      <div className="msg-avatar">{role === 'user' ? 'U' : 'AI'}</div>
      <div className="msg-body">
        <div className="msg-bubble">
          <p>{content}</p>
          {data && data.length > 0 && <DataTable data={data} />}
        </div>
        <div className="msg-meta">
          <span className="msg-time">{formatTime(timestamp)}</span>
          {toolUsed && (
            <span className="tool-tag">
              <span className="tool-tag-dot" />
              {toolUsed}()
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
