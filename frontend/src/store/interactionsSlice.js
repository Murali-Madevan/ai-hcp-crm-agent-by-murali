import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { InteractionAPI } from '../api/client'

export const fetchInteractions = createAsyncThunk('interactions/fetch', async (hcpId) =>
  InteractionAPI.list(hcpId),
)

export const createInteraction = createAsyncThunk('interactions/create', async (payload) =>
  InteractionAPI.create(payload),
)

export const updateInteraction = createAsyncThunk('interactions/update', async ({ id, payload }) => {
  await InteractionAPI.update(id, payload)
  return { id }
})

export const fetchFollowups = createAsyncThunk('interactions/fetchFollowups', async () => InteractionAPI.followups())

export const fetchSafetyFlags = createAsyncThunk('interactions/fetchSafetyFlags', async () =>
  InteractionAPI.safetyFlags(),
)

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    items: [],
    followups: [],
    safetyFlags: [],
    status: 'idle',
    error: null,
    editingId: null,
  },
  reducers: {
    setEditingId(state, action) {
      state.editingId = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.items.unshift(action.payload)
      })
      .addCase(fetchFollowups.fulfilled, (state, action) => {
        state.followups = action.payload
      })
      .addCase(fetchSafetyFlags.fulfilled, (state, action) => {
        state.safetyFlags = action.payload
      })
  },
})

export const { setEditingId } = interactionsSlice.actions
export default interactionsSlice.reducer
