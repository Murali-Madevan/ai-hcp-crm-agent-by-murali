import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

export const HcpAPI = {
  list: () => api.get('/api/hcps/').then((r) => r.data),
  create: (payload) => api.post('/api/hcps/', payload).then((r) => r.data),
}

export const InteractionAPI = {
  list: (hcpId) => api.get('/api/interactions/', { params: hcpId ? { hcp_id: hcpId } : {} }).then((r) => r.data),
  create: (payload) => api.post('/api/interactions/', payload).then((r) => r.data),
  update: (id, payload) => api.patch(`/api/interactions/${id}`, payload).then((r) => r.data),
  history: (id) => api.get(`/api/interactions/${id}/history`).then((r) => r.data),
  followups: () => api.get('/api/interactions/followups/all').then((r) => r.data),
  safetyFlags: () => api.get('/api/interactions/safety-flags/all').then((r) => r.data),
}

export const ChatAPI = {
  send: (payload) => api.post('/api/chat/', payload).then((r) => r.data),
}
