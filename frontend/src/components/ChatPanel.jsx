import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { sendChatMessage, addUserMessage, resetSession } from '../store/chatSlice'
import { fetchInteractions, fetchFollowups, fetchSafetyFlags } from '../store/interactionsSlice'
import './ChatPanel.css'

const SUGGESTIONS = [
  "I met Dr. Mehta today, discussed CardioFlow's new dosing data — she was positive and asked for updated trial data by Friday.",
  'What did we last discuss with this HCP?',
  'Actually, change the sentiment on that last interaction to Positive.',
  'Remind me to follow up with a lunch-and-learn invite next month.',
]

export default function ChatPanel({ hcp }) {
  const dispatch = useDispatch()
  const { messages, sessionId, status } = useSelector((s) => s.chat)
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const lastHcpId = useRef(hcp?.id)

  useEffect(() => {
    if (lastHcpId.current !== hcp?.id) {
      dispatch(resetSession())
      lastHcpId.current = hcp?.id
    }
  }, [hcp?.id, dispatch])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text) => {
    const message = (text ?? input).trim()
    if (!message) return
    dispatch(addUserMessage(message))
    setInput('')
    const res = await dispatch(sendChatMessage({ message, hcpId: hcp.id, sessionId })).unwrap().catch(() => null)
    if (res) {
      dispatch(fetchInteractions(hcp.id))
      dispatch(fetchFollowups())
      dispatch(fetchSafetyFlags())
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Tell the agent about your visit in plain English. Try one of these:</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => handleSend(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            <div className="bubble-text">{m.content}</div>
            {m.role === 'agent' && m.toolCalls?.length > 0 && (
              <div className="tool-badges">
                {m.toolCalls.map((tc, j) => (
                  <span key={j} className="tool-badge">{tc}</span>
                ))}
              </div>
            )}
            {m.role === 'agent' && m.safetyFlags?.length > 0 && (
              <div className="safety-alert">
                ⚠ {m.safetyFlags.length} compliance flag(s) raised — see Safety &amp; Compliance panel
              </div>
            )}
          </div>
        ))}
        {status === 'loading' && <div className="chat-bubble agent typing">Thinking…</div>}
        <div ref={bottomRef} />
      </div>

      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault()
          handleSend()
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Message the agent about ${hcp.name}…`}
        />
        <button type="submit" className="btn-primary" disabled={status === 'loading'}>
          Send
        </button>
      </form>
    </div>
  )
}
