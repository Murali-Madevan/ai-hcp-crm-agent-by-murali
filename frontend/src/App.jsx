import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHcps, selectHcp } from './store/hcpSlice'
import { fetchInteractions, fetchFollowups, fetchSafetyFlags } from './store/interactionsSlice'
import LogInteractionScreen from './components/LogInteractionScreen'
import InteractionList from './components/InteractionList'
import './App.css'

export default function App() {
  const dispatch = useDispatch()
  const { items: hcps, selectedHcpId } = useSelector((s) => s.hcps)

  useEffect(() => {
    dispatch(fetchHcps())
    dispatch(fetchFollowups())
    dispatch(fetchSafetyFlags())
  }, [dispatch])

  useEffect(() => {
    if (selectedHcpId) dispatch(fetchInteractions(selectedHcpId))
  }, [dispatch, selectedHcpId])

  const selectedHcp = hcps.find((h) => h.id === selectedHcpId)

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 21s-7.5-4.6-10-9.2C.5 8.4 2.4 4.5 6 4c2-.3 3.7.6 6 3 2.3-2.4 4-3.3 6-3 3.6.5 5.5 4.4 4 7.8C19.5 16.4 12 21 12 21z"
                stroke="var(--accent)"
                strokeWidth="1.6"
              />
              <path d="M4 12h3.2l1.6-3 2.2 6 1.6-3H20" stroke="var(--brand)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <div>
            <div className="brand-title">MedTouch CRM</div>
            <div className="brand-subtitle">HCP Module &middot; Log Interaction</div>
          </div>
        </div>

        <div className="hcp-select">
          <label htmlFor="hcp-picker">Healthcare Professional</label>
          <select
            id="hcp-picker"
            value={selectedHcpId || ''}
            onChange={(e) => dispatch(selectHcp(e.target.value))}
          >
            {hcps.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} &middot; {h.specialty}
              </option>
            ))}
          </select>
        </div>
      </header>

      <main className="app-main">
        <section className="panel panel-primary">
          <LogInteractionScreen hcp={selectedHcp} />
        </section>
        <section className="panel panel-secondary">
          <InteractionList hcp={selectedHcp} />
        </section>
      </main>
    </div>
  )
}
