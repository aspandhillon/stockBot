// src/features/stock/stockSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const BASE_URL =
  import.meta.env.MODE === 'development'
    ? 'http://localhost:5000' 
    : 'https://stockbot-backend-gkaw.onrender.com';

// Define an async thunk for fetching comparison data
export const fetchComparisonData = createAsyncThunk(
  'stock/fetchComparisonData',
  async (tickers, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/compare_stocks?tickers=${tickers.join(',')}`
      );
      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.error || 'Failed to fetch comparison data.');
      }
      return data;
    } catch (error) {
      console.error('Network error:', error);
      return rejectWithValue('Network error: Could not connect to the backend.');
    }
  }
);

const stockSlice = createSlice({
  name: 'stock',
  initialState: {
    tickersInput: '', // To hold the current input string for tickers
    comparisonResults: null,
    loading: false,
    error: null,
  },
  reducers: {
    // Reducer for when the ticker input changes
    setTickersInput: (state, action) => {
      state.tickersInput = action.payload;
    },
    // You could add other synchronous reducers here if needed
  },
  extraReducers: (builder) => {
    builder
      // When the async thunk starts
      .addCase(fetchComparisonData.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.comparisonResults = null;
      })
      // When the async thunk succeeds
      .addCase(fetchComparisonData.fulfilled, (state, action) => {
        state.loading = false;
        state.comparisonResults = action.payload;
        state.error = null;
      })
      // When the async thunk fails
      .addCase(fetchComparisonData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'An unknown error occurred.';
        state.comparisonResults = null;
      });
  },
});

export const { setTickersInput } = stockSlice.actions; // Export synchronous actions
export default stockSlice.reducer; // Export the reducer to be used in the store
