// src/store/index.js
import { configureStore } from '@reduxjs/toolkit';
import stockReducer from '../features/stock/stockSlice'; // Import your stock slice reducer

export const store = configureStore({
  reducer: {
    stock: stockReducer, // Assign the stock slice reducer to the 'stock' key in your state
    // You can add more slices here for other parts of your app state
  },
});
