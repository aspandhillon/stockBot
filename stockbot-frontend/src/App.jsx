import React, { useState } from 'react';

function App() {
  const [tickersInput, setTickersInput] = useState('');
  const [comparisonResults, setComparisonResults] = useState(null); // This will hold the response from /api/compare_stocks
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCompareSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setComparisonResults(null); // Clear previous results
    setError(null);

    const tickers = tickersInput.split(',').map(t => t.trim()).filter(t => t); // Split and clean
    if (tickers.length === 0) {
      setError("Please enter at least one ticker.");
      setLoading(false);
      return;
    }

    try {
      // ONLY make the call to the comparison API endpoint
      const response = await fetch(`http://localhost:5000/api/compare_stocks?tickers=${tickers.join(',')}`);
      const data = await response.json();

      if (response.ok) {
        setComparisonResults(data); // Store the entire response
      } else {
        setError(data.error || 'An error occurred during comparison.');
      }
    } catch (err) {
      setError('Failed to connect to the comparison service. Is the Flask backend running?');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: 'sans-serif', margin: '40px', textAlign: 'center' }}>
      <h1>StockBot Analyzer (React Frontend)</h1>
      <form onSubmit={handleCompareSubmit} style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={tickersInput}
          onChange={(e) => setTickersInput(e.target.value)}
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
              <h3>Combined Price Chart:</h3>
              <img
                src={`http://localhost:5000${comparisonResults.comparison_plot_url}`}
                alt="Stock Comparison Chart"
                style={{ maxWidth: '100%', height: 'auto', border: '1px solid #ddd', borderRadius: '8px' }}
              />
            </div>
          )}

          {/* Display individual analysis results (text only) */}
          {/* This section ONLY iterates through analysis_results to display text */}
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
