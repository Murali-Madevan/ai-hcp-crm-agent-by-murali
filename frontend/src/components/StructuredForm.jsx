import { useState } from 'react'
import { useDispatch } from 'react-redux'
import { createInteraction, fetchFollowups, fetchSafetyFlags } from '../store/interactionsSlice'
import './StructuredForm.css'

const INTERACTION_TYPES = ['Visit', 'Call', 'Email', 'Conference']
const CHANNELS = ['In-person', 'Phone', 'Video', 'Email']

const initialForm = {
  interaction_type: 'Visit',
  channel: 'In-person',
  raw_text: '',
  products_discussed: '',
  sentiment: '',
  samples_dropped: '',
  materials_shared: '',
  next_steps: '',
}

export default function StructuredForm({ hcp }) {
  const dispatch = useDispatch()
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setResult(null)
    try {
      const payload = { hcp_id: hcp.id, ...form }
      const created = await dispatch(createInteraction(payload)).unwrap()
      setResult(created)
      setForm(initialForm)
      dispatch(fetchFollowups())
      dispatch(fetchSafetyFlags())
    } catch (err) {
      setError(err.message || 'Something went wrong logging this interaction.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="structured-form" onSubmit={handleSubmit}>
      <div className="form-row two-col">
        <div className="field">
          <label>Interaction type</label>
          <select value={form.interaction_type} onChange={update('interaction_type')}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Channel</label>
          <select value={form.channel} onChange={update('channel')}>
            {CHANNELS.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="field">
        <label>Notes <span className="hint">— describe what happened; the agent will summarize and extract details</span></label>
        <textarea
          rows={5}
          placeholder="e.g. Discussed CardioFlow's updated dosing data. Dr. Mehta was receptive, asked for the latest trial results by Friday. Left 2 sample boxes."
          value={form.raw_text}
          onChange={update('raw_text')}
          required
        />
      </div>

      <div className="form-row two-col">
        <div className="field">
          <label>Products discussed <span className="hint">(optional override)</span></label>
          <input value={form.products_discussed} onChange={update('products_discussed')} placeholder="auto-extracted if left blank" />
        </div>
        <div className="field">
          <label>Sentiment <span className="hint">(optional override)</span></label>
          <select value={form.sentiment} onChange={update('sentiment')}>
            <option value="">Auto-detect</option>
            <option>Positive</option>
            <option>Neutral</option>
            <option>Negative</option>
          </select>
        </div>
      </div>

      <div className="form-row two-col">
        <div className="field">
          <label>Samples dropped</label>
          <input value={form.samples_dropped} onChange={update('samples_dropped')} placeholder="auto-extracted if left blank" />
        </div>
        <div className="field">
          <label>Materials shared</label>
          <input value={form.materials_shared} onChange={update('materials_shared')} placeholder="e.g. leave-behind brochure" />
        </div>
      </div>

      <div className="field">
        <label>Next steps</label>
        <input value={form.next_steps} onChange={update('next_steps')} placeholder="auto-extracted if left blank" />
      </div>

      <button type="submit" className="btn-primary" disabled={submitting}>
        {submitting ? 'Logging…' : 'Log interaction'}
      </button>

      {error && <div className="alert alert-error">{error}</div>}

      {result && (
        <div className="result-card">
          <div className="result-title">Interaction logged</div>
          <div className="result-grid">
            <div><span>Summary</span><p>{result.summary || '—'}</p></div>
            <div><span>Products</span><p>{result.products_discussed || '—'}</p></div>
            <div><span>Sentiment</span><p>{result.sentiment || '—'}</p></div>
            <div><span>Next steps</span><p>{result.next_steps || '—'}</p></div>
          </div>
        </div>
      )}
    </form>
  )
}
