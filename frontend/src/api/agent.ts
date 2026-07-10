import type { InteractionFormData } from '../types'

const API_BASE = '/api/agent'

const SNAKE_TO_CAMEL: Record<string, keyof InteractionFormData> = {
  hcp_name: 'hcpName',
  interaction_type: 'interactionType',
  channel: 'channel',
  interaction_date: 'date',
  interaction_time: 'time',
  summary: 'summary',
  products_discussed: 'productsDiscussed',
  sentiment: 'sentiment',
  samples_dropped: 'samplesDropped',
  materials_shared: 'materialsShared',
  next_steps: 'nextSteps',
  attendees: 'attendees',
}

function snakeToCamel(snake: Record<string, string>): InteractionFormData {
  console.log('[API] snakeToCamel INPUT:', JSON.stringify(snake, null, 2))
  const result: Record<string, string> = {}
  for (const [snakeKey, camelKey] of Object.entries(SNAKE_TO_CAMEL)) {
    const raw = snake[snakeKey]
    const val = (raw as string | undefined) ?? ''
    if (val) {
      console.log(`[API]   Mapping ${snakeKey} -> ${camelKey} = "${val}"`)
    }
    result[camelKey] = val
  }
  console.log('[API] snakeToCamel OUTPUT:', JSON.stringify(result, null, 2))
  return result as unknown as InteractionFormData
}

export interface ChatResponse {
  reply: string
  formData: InteractionFormData
  sessionId: string
  toolCalls: string[]
}

export async function sendChatMessage(
  message: string,
  sessionId: string | null,
  hcpId: string,
): Promise<ChatResponse> {
  const body = JSON.stringify({
    message,
    session_id: sessionId,
    hcp_id: hcpId,
  })
  console.log('[API] ===== SENDING REQUEST =====')
  console.log('[API] URL:', `${API_BASE}/chat`)
  console.log('[API] Body:', body)

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })

  console.log('[API] Response status:', res.status)
  if (!res.ok) {
    const text = await res.text()
    console.error('[API] Response error:', res.status, text)
    throw new Error(`Agent API error ${res.status}: ${text}`)
  }

  const json = await res.json()
  console.log('[API] ===== RESPONSE RECEIVED =====')
  console.log('[API] Raw JSON:', JSON.stringify(json, null, 2))
  console.log('[API] json.form_data:', JSON.stringify(json.form_data))
  console.log('[API] json.form_data keys:', Object.keys(json.form_data || {}))
  console.log('[API] json.reply:', json.reply)

  const formData = snakeToCamel(json.form_data)
  console.log('[API] Final formData for App:', JSON.stringify(formData, null, 2))
  console.log('[API] ==============================')

  return {
    reply: json.reply,
    formData,
    sessionId: json.session_id,
    toolCalls: json.tool_calls ?? [],
  }
}
 