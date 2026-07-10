import { useEffect, useRef, useState } from 'react'
import { type ChatMessage } from '../types'
import './ChatPanel.css'

interface ChatPanelProps {
  messages: ChatMessage[]
  onSend: (message: string) => void
  isLoading?: boolean
  suggestions?: string[]
  placeholder?: string
  showEmptyGuide?: boolean
}

export default function ChatPanel({
  messages,
  onSend,
  isLoading = false,
  suggestions = [],
  placeholder = 'Describe interaction...',
  showEmptyGuide = false,
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const isSubmitting = useRef(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isSubmitting.current) return
    isSubmitting.current = true
    setInput('')
    onSend(trimmed)
  }

  function handleSuggestion(text: string) {
    if (isSubmitting.current) return
    onSend(text)
  }

  useEffect(() => {
    if (!isLoading) {
      isSubmitting.current = false
    }
  }, [isLoading, messages])

  return (
    <div className="chat-panel-inner">
      <div className="chat-header">
        <svg className="chat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a73e8" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a2 2 0 0 1 2 2v1h3a2 2 0 0 1 2 2v3h1a2 2 0 0 1 0 4h-1v3a2 2 0 0 1-2 2h-3v1a2 2 0 0 1-4 0v-1H7a2 2 0 0 1-2-2v-3H4a2 2 0 0 1 0-4h1V7a2 2 0 0 1 2-2h3V4a2 2 0 0 1 2-2z" fill="#1a73e8" />
        </svg>
        <div>
          <div className="chat-header-title">AI Assistant</div>
          <div className="chat-header-subtitle">Log Interaction via chat</div>
        </div>
      </div>

      <div className="chat-example-box">
        <p>Try: &quot;I met with Dr. Mehta and discussed CardioFlow&rsquo;s new efficacy data. She was positive and requested updated trial data by Friday.&quot;</p>
      </div>

      <div className="chat-messages">
        {showEmptyGuide ? (
          <div className="chat-empty">
            <p>Select an HCP from the header to start.</p>
          </div>
        ) : messages.length === 0 && !isLoading ? (
          <div className="chat-empty">
            {suggestions.length > 0 && (
              <div className="chat-suggestions">
                {suggestions.map((text) => (
                  <button
                    key={text}
                    type="button"
                    className="chat-suggestion-btn"
                    onClick={() => handleSuggestion(text)}
                  >
                    {text}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-msg chat-msg--${msg.role}`}>
                <span className="chat-msg-label">{msg.role === 'user' ? 'You:' : 'AI:'}</span>
                <span className="chat-msg-text">{msg.content}</span>
              </div>
            ))}
            {isLoading && (
              <div className="chat-msg chat-typing">
                <span className="chat-msg-label">AI:</span>
                <span className="chat-msg-text">Thinking&hellip;</span>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          aria-label="Chat message"
        />
        <button
          type="submit"
          className="chat-log-btn"
          disabled={!input.trim()}
        >
          Log
        </button>
      </form>
    </div>
  )
}
