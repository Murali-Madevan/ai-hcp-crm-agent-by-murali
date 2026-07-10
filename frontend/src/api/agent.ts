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
  const result: Record<string, string> = {}
  for (const [snakeKey, camelKey] of Object.entries(SNAKE_TO_CAMEL)) {
    const raw = snake[snakeKey]
    const val = (raw as string | undefined) ?? ''
    result[camelKey] = val
  }
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

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Agent API error ${res.status}: ${text}`)
  }

  const json = await res.json()

  const formData = snakeToCamel(json.form_data)

  return {
    reply: json.reply,
    formData,
    sessionId: json.session_id,
    toolCalls: json.tool_calls ?? [],
  }
}
