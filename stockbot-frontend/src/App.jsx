// src/App.jsx
import React from 'react';
import { useDispatch, useSelector } from 'react-redux'; // Import Redux hooks
import { setTickersInput, fetchComparisonData } from './features/stock/stockSlice'; // Import actions and thunk

function App() {
  const dispatch = useDispatch(); // Get the dispatch function

  // Select state from the Redux store
  const tickersInput = useSelector((state) => state.stock.tickersInput);
  const comparisonResults = useSelector((state) => state.stock.comparisonResults);
  const loading = useSelector((state) => state.stock.loading);
  const error = useSelector((state) => state.stock.error);

  // --- NEW LOGIC FOR DYNAMIC HEADING ---
  // Derive the count of tickers from the input string
  const getTickerCount = () => {
    const tickers = tickersInput.split(',').map(t => t.trim()).filter(t => t);
    return tickers.length;
  };

  const tickerCount = getTickerCount();
  const chartHeading =
    tickerCount > 2
      ? "Combined Price Chart"
      : tickerCount > 0 // For 1 or 2 tickers, let's just call it a "Price Chart" or "Price Chart(s)"
        ? `${tickerCount === 1 ? 'Price Chart' : 'Price Charts'}`
        : "Price Chart"; // Default if no tickers are input yet
  // --- END NEW LOGIC ---

  const handleInputChange = (e) => {
    dispatch(setTickersInput(e.target.value)); // Dispatch action to update input state
  };

  const handleCompareSubmit = async (event) => {
    event.preventDefault();

    const tickers = tickersInput.split(',').map(t => t.trim()).filter(t => t);
    if (tickers.length === 0) {
      return; // No need to dispatch if no tickers
    }

    // Dispatch the async thunk to fetch data
    dispatch(fetchComparisonData(tickers));
  };

  return (
    <div style={{ fontFamily: 'sans-serif', margin: '40px', textAlign: 'center' }}>
      <h1>StockBot Analyzer (React Frontend)</h1>
      <form onSubmit={handleCompareSubmit} style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={tickersInput} // Value now comes from Redux store
          onChange={handleInputChange} // Dispatch action on change
          placeholder="Enter tickers (e.g., TSLA, GOOGL, AAPL)"
          required
          style={{ padding: '10px', marginRight: '10px', fontSize: '16px', width: '300px' }}
        />
        <button type="submit" style={{ padding: '10px 20px', fontSize: '16px' }}>Compare Stocks</button>
      </form>

      {loading && <p>Analyzing...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {comparisonResults && (
        <div style={{ marginTop: '20px' }}>
          {/* Display the combined comparison plot */}
          {comparisonResults.comparison_plot_url && (
            <div style={{ marginBottom: '30px' }}>
              {/* Use the dynamic heading here */}
              <h3>{chartHeading}:</h3>
              <img
                src={`http://localhost:5000${comparisonResults.comparison_plot_url}`}
                alt="Stock Comparison Chart"
                style={{ maxWidth: '100%', height: 'auto', border: '1px solid #ddd', borderRadius: '8px' }}
              />
            </div>
          )}

          {/* Display individual analysis results (text only) */}
          {/* {comparisonResults.analysis_results && (
            <div>
              <h3>Individual Analysis:</h3>
              {comparisonResults.analysis_results.map((result, index) => (
                <div key={index} style={{
                  backgroundColor: '#e9ecef',
                  padding: '15px',
                  borderRadius: '4px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  marginBottom: '10px',
                  textAlign: 'left'
                }}>
                  <p><strong>{result.ticker}:</strong> {result.message} (Signal: {result.signal_type})</p>
                </div>
              ))}
            </div>
          )} */}
           {!comparisonResults.comparison_plot_url && !comparisonResults.analysis_results && (
                <p>No results or plot available for the entered tickers.</p>
            )}
        </div>
      )}
    </div>
  );
}

export default App;
