import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { HcpAPI } from '../api/client'

export const fetchHcps = createAsyncThunk('hcps/fetch', async () => HcpAPI.list())

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: {
    items: [],
    selectedHcpId: null,
    status: 'idle',
    error: null,
  },
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
        if (!state.selectedHcpId && action.payload.length > 0) {
          state.selectedHcpId = action.payload[0].id
        }
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
  },
})

export const { selectHcp } = hcpSlice.actions
export default hcpSlice.reducer
