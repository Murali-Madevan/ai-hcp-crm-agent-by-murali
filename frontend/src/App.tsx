import { useState, useCallback, useRef } from 'react'
import Header from './components/Header'
import InteractionForm from './components/InteractionForm'
import ChatPanel from './components/ChatPanel'
import { type HCP, type ChatMessage, type InteractionFormData } from './types'
import { sendChatMessage, type ChatResponse } from './api/agent'
import './App.css'

const DEMO_HCPS: HCP[] = [
  { id: '1', name: 'Dr. Anjali Mehta', specialty: 'Cardiology', institution: 'City Hospital', segment: 'A' },
  { id: '2', name: 'Dr. Ravi Kumar', specialty: 'Neurology', institution: 'Neurocare Clinic', segment: 'B' },
  { id: '3', name: 'Dr. Sarah Chen', specialty: 'Oncology', institution: 'Cancer Center', segment: 'A' },
  { id: '4', name: 'Dr. James Wilson', specialty: 'General Medicine', institution: 'Community Health', segment: 'C' },
]

const DEMO_SUGGESTIONS = [
  "Today I met Dr. Mehta and discussed CardioFlow's new efficacy data. She was very positive and asked for updated trial data by Friday. I left 2 sample boxes and the new brochure.",
  'What did we last discuss with this HCP?',
  'Actually, change the sentiment to Negative.',
  'Save this interaction.',
]

const EMPTY_FORM: InteractionFormData = {
  hcpName: '',
  date: '',
  time: '',
  interactionType: '',
  channel: 'In-person',
  summary: '',
  productsDiscussed: '',
  sentiment: '',
  samplesDropped: '',
  materialsShared: '',
  nextSteps: '',
  attendees: '',
}

type FormStatus = 'idle' | 'loading' | 'error' | 'submitted'

export default function App() {
  const [selectedHcpId, setSelectedHcpId] = useState<string | null>(null)
  const [formData, setFormData] = useState<InteractionFormData>(EMPTY_FORM)
  const [formStatus, setFormStatus] = useState<FormStatus>('idle')
  const [formError, setFormError] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)

  const msgIdRef = useRef(1)

  function handleHcpChange(hcpId: string) {
    console.log('[App] HCP changed to:', hcpId)
    msgIdRef.current = 1
    setSelectedHcpId(hcpId)
    setChatMessages([])
    setFormData(EMPTY_FORM)
    setFormStatus('idle')
    setFormError(null)
    setSessionId(null)
  }

  const handleChatSend = useCallback(async (message: string) => {
    const hcpId = selectedHcpId ?? ''
    console.log('[App] ===== handleChatSend called =====')
    console.log('[App] message:', message.slice(0, 200))
    console.log('[App] hcpId:', hcpId)
    console.log('[App] sessionId:', sessionId)

    const userMsg: ChatMessage = {
      id: String(msgIdRef.current++),
      role: 'user',
      content: message,
    }

    setChatMessages((prev) => [...prev, userMsg])
    setFormStatus('loading')
    setFormError(null)

    try {
      console.log('[App] Calling sendChatMessage...')
      const res: ChatResponse = await sendChatMessage(message, sessionId, hcpId)
      console.log('[App] ===== Response received =====')
      console.log('[App] res.reply:', res.reply)
      console.log('[App] res.formData:', JSON.stringify(res.formData, null, 2))
      console.log('[App] res.sessionId:', res.sessionId)
      console.log('[App] res.toolCalls:', res.toolCalls)

      const assistantMsg: ChatMessage = {
        id: String(msgIdRef.current++),
        role: 'assistant',
        content: res.reply,
        toolCalls: res.toolCalls.length > 0 ? res.toolCalls : undefined,
      }

      setChatMessages((prev) => [...prev, assistantMsg])
      console.log('[App] Merging form data EMPTY_FORM + res.formData')
      const merged = { ...EMPTY_FORM, ...res.formData }
      console.log('[App] Merged formData for state update:', JSON.stringify(merged, null, 2))
      setFormData(merged)
      setSessionId(res.sessionId)
      setFormStatus('idle')
      console.log('[App] ===== State update complete =====')
    } catch (err) {
      console.error('[App] Error:', err)
      const errorMsg = err instanceof Error ? err.message : 'Request failed'
      setFormError(errorMsg)
      setFormStatus('error')
    }
  }, [selectedHcpId, sessionId])

  console.log('[App] Render - formData:', formData)

  return (
    <div className="app">
      <div className="app-container">
        <Header
          hcps={DEMO_HCPS}
          selectedHcpId={selectedHcpId}
          onHcpChange={handleHcpChange}
        />

        <div className="cards-layout">
          <div className="card card-left">
            <InteractionForm
              data={formData}
              status={formStatus}
              error={formError}
            />
          </div>

          <div className="card card-right">
            <ChatPanel
              messages={chatMessages}
              onSend={handleChatSend}
              suggestions={DEMO_SUGGESTIONS}
              isLoading={formStatus === 'loading'}
              showEmptyGuide={false}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
