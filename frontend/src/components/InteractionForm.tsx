import { type InteractionFormData } from '../types'
import './InteractionForm.css'

interface InteractionFormProps {
  data: InteractionFormData
  status?: 'idle' | 'loading' | 'error' | 'submitted'
  error?: string | null
}

export default function InteractionForm({
  data,
  status = 'idle',
  error = null,
}: InteractionFormProps) {
  console.log('[InteractionForm] Received data prop:', JSON.stringify(data))
  console.log('[InteractionForm] hcpName:', data.hcpName)
  console.log('[InteractionForm] date:', data.date)
  console.log('[InteractionForm] time:', data.time)
  console.log('[InteractionForm] interactionType:', data.interactionType)
  console.log('[InteractionForm] productsDiscussed:', data.productsDiscussed)
  console.log('[InteractionForm] sentiment:', data.sentiment)
  console.log('[InteractionForm] summary:', data.summary)
  console.log('[InteractionForm] nextSteps:', data.nextSteps)
  console.log('[InteractionForm] attendees:', data.attendees)
  console.log('[InteractionForm] materialsShared:', data.materialsShared)
  const hcnName = data.hcpName ?? ''
  const intType = data.interactionType ?? ''
  const dt = data.date ?? ''
  const tm = data.time ?? ''
  const att = data.attendees ?? ''
  const topics = data.productsDiscussed ?? ''
  const sentiment = data.sentiment ?? ''
  const outcomes = data.summary ?? ''
  const followUp = data.nextSteps ?? ''
  const materialItems: string[] = data.materialsShared
    ? data.materialsShared.split(',').map((s) => s.trim()).filter(Boolean)
    : []

  const suggestedFollowups = [
    'Schedule follow-up meeting in 2 weeks',
    'Send OncoBoost Phase III PDF',
    'Add Dr. Sharma to advisory board invite list',
  ]

  return (
    <div className="interaction-form">
      {/* HCP Name + Interaction Type */}
      <div className="form-row-two">
        <div className="form-group">
          <label className="form-label">HCP Name</label>
          <input
            type="text"
            className="form-input"
            value={hcnName}
            onChange={() => {}}
            placeholder="Search HCP..."
          />
        </div>
        <div className="form-group">
          <label className="form-label">Interaction Type</label>
          <select className="form-select" value={intType} onChange={() => {}}>
            <option value="">Select...</option>
            <option value="Visit">Visit</option>
            <option value="Call">Call</option>
            <option value="Email">Email</option>
            <option value="Meeting">Meeting</option>
          </select>
        </div>
      </div>

      {/* Date + Time */}
      <div className="form-row-two">
        <div className="form-group">
          <label className="form-label">Date</label>
          <input
            type="date"
            className="form-input"
            value={dt}
            onChange={() => {}}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Time</label>
          <input
            type="time"
            className="form-input"
            value={tm}
            onChange={() => {}}
          />
        </div>
      </div>

      {/* Attendees */}
      <div className="form-group">
        <label className="form-label">Attendees</label>
        <input
          type="text"
          className="form-input"
          value={att}
          onChange={() => {}}
          placeholder="Enter attendees..."
        />
      </div>

      {/* Topics Discussed */}
      <div className="form-group">
        <div className="form-label-row">
          <label className="form-label">Topics Discussed</label>
          <div className="form-label-icons">
            <button type="button" className="icon-btn" title="Microphone">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <button type="button" className="icon-btn" title="Edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
          </div>
        </div>
        <textarea
          className="form-textarea"
          value={topics}
          onChange={() => {}}
          rows={2}
          placeholder="Topics discussed..."
        />
      </div>

      {/* Voice Note Button */}
      <button type="button" className="voice-note-btn">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
        Summarize from Voice Note (Requires Consent)
      </button>

      {/* Materials Shared + Samples Distributed */}
      <div className="form-row-two">
        <div className="mini-card">
          <div className="mini-card-header">
            <span className="mini-card-title">Materials Shared</span>
            <button type="button" className="mini-card-btn">Search/Add</button>
          </div>
          <div className="mini-card-body">
            {status === 'loading' ? (
              <span className="mini-card-loading">Loading...</span>
            ) : materialItems.length > 0 ? (
              <div className="material-list">
                {materialItems.map((item, i) => (
                  <span key={i} className="material-chip">{item}</span>
                ))}
              </div>
            ) : (
              'No materials added.'
            )}
          </div>
        </div>
        <div className="mini-card">
          <div className="mini-card-header">
            <span className="mini-card-title">Samples Distributed</span>
            <button type="button" className="mini-card-btn">Add Sample</button>
          </div>
          <div className="mini-card-body">No samples added.</div>
        </div>
      </div>

      {/* Sentiment */}
      <div className="form-group">
        <label className="form-label">Observed/Inferred HCP Sentiment</label>
        <div className="sentiment-group">
          <label className="sentiment-option">
            <input
              type="radio"
              name="sentiment"
              value="Positive"
              checked={sentiment === 'Positive'}
              onChange={() => {}}
              className="sentiment-radio"
            />
            <span>🙂</span>
            <span>Positive</span>
          </label>
          <label className="sentiment-option">
            <input
              type="radio"
              name="sentiment"
              value="Neutral"
              checked={sentiment === 'Neutral'}
              onChange={() => {}}
              className="sentiment-radio"
            />
            <span>😐</span>
            <span>Neutral</span>
          </label>
          <label className="sentiment-option">
            <input
              type="radio"
              name="sentiment"
              value="Negative"
              checked={sentiment === 'Negative'}
              onChange={() => {}}
              className="sentiment-radio"
            />
            <span>☹</span>
            <span>Negative</span>
          </label>
        </div>
      </div>

      {/* Outcomes */}
      <div className="form-group">
        <label className="form-label">Outcomes</label>
        <textarea
          className="form-textarea"
          value={outcomes}
          onChange={() => {}}
          rows={2}
          placeholder="Outcomes..."
        />
      </div>

      {/* Follow-up Actions */}
      <div className="form-group">
        <label className="form-label">Follow-up Actions</label>
        <textarea
          className="form-textarea"
          value={followUp}
          onChange={() => {}}
          rows={2}
          placeholder="Follow-up actions..."
        />
      </div>

      {/* AI Suggested Follow-ups */}
      <div className="ai-followups">
        <div className="ai-followups-label">AI Suggested Follow-ups</div>
        <div className="ai-followups-list">
          {suggestedFollowups.map((item, i) => (
            <a key={i} className="ai-followup-link" href="#">{item}</a>
          ))}
        </div>
      </div>

      {/* Status */}
      <div className="form-status-bar">
        {status === 'loading' && (
          <div className="form-status-inline">
            <div className="loading-dot" />
            <span>AI is processing...</span>
          </div>
        )}
        {status === 'error' && error && (
          <div className="form-status-inline form-status-inline--error">
            <span>{error}</span>
          </div>
        )}
        {status === 'submitted' && (
          <div className="form-status-inline form-status-inline--success">
            <span>Interaction logged successfully!</span>
          </div>
        )}
      </div>
    </div>
  )
}
