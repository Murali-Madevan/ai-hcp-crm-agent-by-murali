import { type HCP } from '../types'
import './Header.css'

interface HeaderProps {
  hcps: HCP[]
  selectedHcpId: string | null
  onHcpChange: (hcpId: string) => void
}

export default function Header({ hcps, selectedHcpId, onHcpChange }: HeaderProps) {
  return (
    <div className="page-header">
      <div className="header-left">
        <h1 className="header-title">Log HCP Interaction</h1>
        <p className="header-subtitle">Interaction Details</p>
      </div>
      <div className="header-right">
        <label htmlFor="hcp-picker">HCP</label>
        <select
          id="hcp-picker"
          value={selectedHcpId ?? ''}
          onChange={(e) => onHcpChange(e.target.value)}
        >
          <option value="" disabled>Select an HCP&hellip;</option>
          {hcps.map((hcp) => (
            <option key={hcp.id} value={hcp.id}>{hcp.name} &middot; {hcp.specialty}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
