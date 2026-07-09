import { useState } from 'react'
import { useSelector } from 'react-redux'
import EditInteractionModal from './EditInteractionModal'
import './InteractionList.css'

const sentimentClass = (s) => {
  if (s === 'Positive') return 'chip positive'
  if (s === 'Negative') return 'chip negative'
  return 'chip neutral'
}

export default function InteractionList({ hcp }) {
  const { items, followups, safetyFlags } = useSelector((s) => s.interactions)
  const [editing, setEditing] = useState(null)

  const hcpFollowups = followups.filter((f) => f.hcp_id === hcp?.id)
  const interactionIds = new Set(items.map((i) => i.id))
  const relevantFlags = safetyFlags.filter((f) => interactionIds.has(f.interaction_id))

  return (
    <div className="sidebar">
      {hcp && (
        <div className="hcp-card">
          <div className="hcp-card-name">{hcp.name}</div>
          <div className="hcp-card-meta">{hcp.specialty} &middot; {hcp.institution}</div>
          <span className={`segment-chip segment-${hcp.segment}`}>Segment {hcp.segment}</span>
        </div>
      )}

      {relevantFlags.length > 0 && (
        <div className="section">
          <h2>Safety &amp; compliance</h2>
          {relevantFlags.map((f) => (
            <div key={f.id} className="flag-card">
              <div className="flag-head">
                <span>{f.flag_type}</span>
                <span className={`severity severity-${f.severity?.toLowerCase()}`}>{f.severity}</span>
              </div>
              <p>{f.detail}</p>
              {f.requires_pv_escalation && <div className="pv-tag">Escalate to pharmacovigilance</div>}
            </div>
          ))}
        </div>
      )}

      <div className="section">
        <h2>Follow-ups</h2>
        {hcpFollowups.length === 0 && <p className="muted">No open follow-ups.</p>}
        {hcpFollowups.map((f) => (
          <div key={f.id} className="followup-row">
            <span className={`status-dot status-${f.status.toLowerCase()}`} />
            <div>
              <div className="followup-task">{f.task}</div>
              {f.due_date && <div className="followup-due">Due {new Date(f.due_date).toLocaleDateString()}</div>}
            </div>
          </div>
        ))}
      </div>

      <div className="section">
        <h2>Recent interactions</h2>
        {items.length === 0 && <p className="muted">No interactions logged yet.</p>}
        {items.map((it) => (
          <div key={it.id} className="interaction-card">
            <div className="interaction-head">
              <span className="interaction-type">{it.interaction_type}</span>
              <span className={sentimentClass(it.sentiment)}>{it.sentiment || 'Neutral'}</span>
            </div>
            <p className="interaction-summary">{it.summary}</p>
            {it.products_discussed && <div className="meta-line"><strong>Products:</strong> {it.products_discussed}</div>}
            {it.next_steps && <div className="meta-line"><strong>Next:</strong> {it.next_steps}</div>}
            <div className="interaction-footer">
              <span>{new Date(it.interaction_date).toLocaleString()}</span>
              <button onClick={() => setEditing(it)}>Edit</button>
            </div>
          </div>
        ))}
      </div>

      {editing && <EditInteractionModal interaction={editing} onClose={() => setEditing(null)} />}
    </div>
  )
}
