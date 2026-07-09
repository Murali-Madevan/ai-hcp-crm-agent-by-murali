import { useState } from 'react'
import { useDispatch } from 'react-redux'
import { updateInteraction, fetchInteractions } from '../store/interactionsSlice'
import './EditInteractionModal.css'

const FIELDS = [
  { key: 'sentiment', label: 'Sentiment', type: 'select', options: ['Positive', 'Neutral', 'Negative'] },
  { key: 'products_discussed', label: 'Products discussed', type: 'text' },
  { key: 'samples_dropped', label: 'Samples dropped', type: 'text' },
  { key: 'next_steps', label: 'Next steps', type: 'text' },
  { key: 'summary', label: 'Summary', type: 'textarea' },
]

export default function EditInteractionModal({ interaction, onClose }) {
  const dispatch = useDispatch()
  const [values, setValues] = useState(
    Object.fromEntries(FIELDS.map((f) => [f.key, interaction[f.key] || ''])),
  )
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)

  const update = (key) => (e) => setValues((v) => ({ ...v, [key]: e.target.value }))

  const handleSave = async () => {
    setSaving(true)
    const payload = {}
    FIELDS.forEach((f) => {
      if (values[f.key] !== (interaction[f.key] || '')) payload[f.key] = values[f.key]
    })
    payload.reason = reason || 'Edited via structured form'
    if (Object.keys(payload).length > 1) {
      await dispatch(updateInteraction({ id: interaction.id, payload })).unwrap()
      dispatch(fetchInteractions(interaction.hcp_id))
    }
    setSaving(false)
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Edit interaction</h3>
        <p className="modal-sub">Uses the same <code>edit_interaction</code> tool the chat agent uses. Every change is recorded in the audit trail.</p>

        {FIELDS.map((f) => (
          <div className="field" key={f.key}>
            <label>{f.label}</label>
            {f.type === 'select' && (
              <select value={values[f.key]} onChange={update(f.key)}>
                <option value="">—</option>
                {f.options.map((o) => (
                  <option key={o}>{o}</option>
                ))}
              </select>
            )}
            {f.type === 'text' && <input value={values[f.key]} onChange={update(f.key)} />}
            {f.type === 'textarea' && <textarea rows={3} value={values[f.key]} onChange={update(f.key)} />}
          </div>
        ))}

        <div className="field">
          <label>Reason for edit</label>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. rep clarified over the phone" />
        </div>

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
