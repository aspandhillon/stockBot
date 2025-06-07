// src/App.jsx
import React from 'react';
import { useDispatch, useSelector } from 'react-redux'; // Import Redux hooks
import { setTickersInput, fetchComparisonData } from './features/stock/stockSlice'; // Import actions and thunk

// Get the API URL from environment variables for production, fallback to localhost for development
// Vite automatically exposes environment variables prefixed with VITE_
const FLASK_API_URL = import.meta.env.VITE_FLASK_API_URL || 'http://localhost:5000';

function App() {
  const dispatch = useDispatch(); // Get the dispatch function to send actions

  // Select relevant state from the Redux store
  const tickersInput = useSelector((state) => state.stock.tickersInput);
  const comparisonResults = useSelector((state) => state.stock.comparisonResults);
  const loading = useSelector((state) => state.stock.loading);
  const error = useSelector((state) => state.stock.error);

  // --- Dynamic Heading Logic ---
  // This function parses the input string to count active tickers
  const getTickerCount = () => {
    const tickers = tickersInput.split(',').map(t => t.trim()).filter(t => t);
    return tickers.length;
  };

  const tickerCount = getTickerCount();
  // Determine the chart heading based on the number of tickers
  const chartHeading =
    tickerCount > 1 // If more than one ticker, it's a "Combined" chart
      ? "Combined Price Chart"
      : tickerCount === 1 // If exactly one ticker, it's a "Price Chart"
        ? "Price Chart"
        : "Stock Price Chart"; // Default if no tickers are input yet, or for general display

  // --- Input Change Handler ---
  const handleInputChange = (e) => {
    // Dispatch the setTickersInput action to update the state in Redux
    dispatch(setTickersInput(e.target.value));
  };

  // --- Form Submission Handler ---
  const handleCompareSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior (page reload)

    const tickers = tickersInput.split(',').map(t => t.trim()).filter(t => t); // Clean and split tickers
    if (tickers.length === 0) {
      // Optionally, dispatch an error state or show a local message if no tickers are provided
      console.warn("No tickers entered. Please provide at least one ticker symbol.");
      return; // Do nothing if no tickers are entered
    }

    // Dispatch the asynchronous thunk to fetch comparison data from the backend
    // The thunk handles loading, error, and success states internally
    dispatch(fetchComparisonData(tickers));
  };

  return (
    <div style={{ fontFamily: 'sans-serif', margin: '40px', textAlign: 'center', backgroundColor: '#f4f4f4', color: '#333' }}>
      <div style={{ backgroundColor: '#fff', padding: '30px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', maxWidth: '800px', margin: 'auto' }}>
        <h1 style={{ color: '#0056b3', textAlign: 'center', marginBottom: '30px' }}>StockBot Analyzer (React Frontend)</h1>

        {/* Input Form */}
        <form onSubmit={handleCompareSubmit} style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <input
            type="text"
            value={tickersInput} // Input value is controlled by Redux state
            onChange={handleInputChange} // Input changes dispatch Redux action
            placeholder="Enter tickers (e.g., TSLA, GOOGL, AAPL)"
            required
            style={{ padding: '10px', marginRight: '10px', fontSize: '16px', flexGrow: 1, border: '1px solid #ddd', borderRadius: '4px' }}
          />
          <button
            type="submit"
            style={{ backgroundColor: '#007bff', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}
          >
            Analyze Stocks
          </button>
        </form>

        {/* Loading and Error Messages */}
        {loading && <p style={{ fontSize: '18px', color: '#007bff' }}>Analyzing...</p>}
        {error && <p style={{ color: 'red', fontSize: '18px' }}>Error: {error}</p>}

        {/* Display Results */}
        {comparisonResults && (
          <div style={{ marginTop: '20px' }}>
            {/* Display the combined comparison plot */}
            {comparisonResults.comparison_plot_url && (
              <div style={{ marginBottom: '30px' }}>
                <h3 style={{ color: '#0056b3', marginBottom: '15px' }}>{chartHeading}</h3>
                <img
                  // Construct the full URL for the plot image using the dynamic API URL
                  src={`${FLASK_API_URL}${comparisonResults.comparison_plot_url}`}
                  alt="Stock Comparison Chart"
                  style={{ maxWidth: '100%', height: 'auto', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
                />
              </div>
            )}

            {/* Display individual analysis results (text only, no separate plots) */}
            {/* {comparisonResults.analysis_results && (
              <div>
                <h3 style={{ color: '#0056b3', marginBottom: '15px' }}>Individual Analysis:</h3>
                {comparisonResults.analysis_results.map((result, index) => (
                  <div
                    key={index}
                    style={{
                      backgroundColor: '#e9ecef',
                      padding: '15px',
                      borderRadius: '8px',
                      fontSize: '16px',
                      fontWeight: 'bold',
                      marginBottom: '10px',
                      textAlign: 'left',
                      boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
                    }}
                  >
                    <p><strong>{result.ticker}:</strong> {result.message} (Signal: {result.signal_type})</p>
                  </div>
                ))}
              </div>
            )} */}
            {/* Message if no results or plot were available */}
            {!comparisonResults.comparison_plot_url && !comparisonResults.analysis_results && (
                  <p>No results or plot available for the entered tickers. Please check ticker symbols or try again.</p>
              )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
