import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { ChatAPI } from '../api/client'

export const sendChatMessage = createAsyncThunk(
  'chat/send',
  async ({ message, hcpId, sessionId }) => {
    const data = await ChatAPI.send({ message, hcp_id: hcpId, session_id: sessionId })
    return data
  },
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    sessionId: null,
    messages: [], // { role: 'user' | 'agent', content, toolCalls?, safetyFlags? }
    status: 'idle',
    error: null,
  },
  reducers: {
    resetSession(state) {
      state.sessionId = null
      state.messages = []
      state.status = 'idle'
      state.error = null
    },
    addUserMessage(state, action) {
      state.messages.push({ role: 'user', content: action.payload })
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.sessionId = action.payload.session_id
        state.messages.push({
          role: 'agent',
          content: action.payload.reply,
          toolCalls: action.payload.tool_calls,
          interactionId: action.payload.interaction_id,
          followups: action.payload.followups,
          safetyFlags: action.payload.safety_flags,
        })
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
        state.messages.push({ role: 'agent', content: `Error: ${action.error.message}` })
      })
  },
})

export const { resetSession, addUserMessage } = chatSlice.actions
export default chatSlice.reducer
