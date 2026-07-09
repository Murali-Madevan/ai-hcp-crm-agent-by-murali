import { useState } from 'react'
import StructuredForm from './StructuredForm'
import ChatPanel from './ChatPanel'
import './LogInteractionScreen.css'

export default function LogInteractionScreen({ hcp }) {
  const [mode, setMode] = useState('form') // 'form' | 'chat'

  return (
    <div className="log-screen">
      <div className="log-screen-header">
        <h1>Log Interaction</h1>
        <div className="mode-toggle" role="tablist" aria-label="Logging mode">
          <button
            role="tab"
            aria-selected={mode === 'form'}
            className={mode === 'form' ? 'active' : ''}
            onClick={() => setMode('form')}
          >
            Structured form
          </button>
          <button
            role="tab"
            aria-selected={mode === 'chat'}
            className={mode === 'chat' ? 'active' : ''}
            onClick={() => setMode('chat')}
          >
            Chat with agent
          </button>
        </div>
      </div>

      {!hcp && <p className="empty-hint">Select an HCP above to begin.</p>}
      {hcp && mode === 'form' && <StructuredForm hcp={hcp} />}
      {hcp && mode === 'chat' && <ChatPanel hcp={hcp} />}
    </div>
  )
}
