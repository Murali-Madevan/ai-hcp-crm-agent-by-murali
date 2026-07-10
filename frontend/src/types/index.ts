export interface HCP {
  id: string
  name: string
  specialty: string
  institution: string
  segment: string
}

export interface FormField {
  key: string
  label: string
  value: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolCalls?: string[]
}

export interface InteractionFormData {
  hcpName: string
  date: string
  time?: string
  interactionType: string
  channel: string
  summary: string
  productsDiscussed: string
  sentiment: string
  samplesDropped: string
  materialsShared: string
  nextSteps: string
  attendees?: string
}
