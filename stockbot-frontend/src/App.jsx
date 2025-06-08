import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setTickersInput, fetchComparisonData } from './features/stock/stockSlice';

function App() {
  const dispatch = useDispatch();
  const input = useSelector(s => s.stock.tickersInput);
  const { comparison_plot_base64, analysis_results } = useSelector(s => s.stock.comparisonResults || {});
  const loading = useSelector(s => s.stock.loading);
  const error = useSelector(s => s.stock.error);
  const hasChart = comparison_plot_base64;

  const heading = () => {
    const count = input.split(',').filter(o => o.trim()).length;
    return count > 1 ? "Combined Price Chart" : count===1 ? "Price Chart" : "Stock Price Chart";
  };

  const handleChange = e => dispatch(setTickersInput(e.target.value));
  const handleSubmit = e => {
    e.preventDefault();
    const tickers = input.split(',').map(t=>t.trim()).filter(Boolean);
    if (tickers.length) dispatch(fetchComparisonData(tickers));
  };

  return (
    <div style={styles.container}>
      <div style={{
        ...styles.card,
        width: hasChart ? '90%' : '100%',
        maxWidth: hasChart ? '1000px' : '600px'
      }}>
        <h1 style={styles.header}>StockBot Analyzer</h1>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input value={input} onChange={handleChange} placeholder="TSLA, AAPL, GOOGL" style={styles.input} />
          <button type="submit" style={styles.button}>Analyze Stocks</button>
        </form>
        {loading && <p style={styles.text}>Loading...</p>}
        {error && <p style={{...styles.text, color:'red'}}>Error: {error}</p>}
        {hasChart && (
          <div style={{textAlign:'center'}}>
            <h3 style={styles.subheader}>{heading()}</h3>
            <img src={`data:image/png;base64,${comparison_plot_base64}`} alt="Chart"
               style={styles.chart}/>
            <div style={styles.analysisContainer}>
              {Object.entries(analysis_results).map(([t, r]) => (
                <div key={t} style={styles.analysisBlock}>
                  <strong>{t}:</strong> {r.message}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight:'100vh', minWidth:'100vw', display:'flex', justifyContent:'center', alignItems:'center', background:'#121212', padding:'20px', boxSizing:'border-box' },
  card: { background:'#fff', padding:'40px', borderRadius:12, boxShadow:'0 8px 24px rgba(0,0,0,0.2)', boxSizing:'border-box', transition:'width .4s ease' },
  header: { color:'#0d47a1', fontSize:28, fontWeight:600, textAlign:'center', marginBottom:25 },
  form: { display:'flex', gap:10, justifyContent:'center', flexWrap:'wrap', marginBottom:20 },
  input: { padding:'12px 16px', flex:'1 1 300px', fontSize:16, border:'1px solid #ccc', borderRadius:6 },
  button: { backgroundColor:'#1976d2', color:'#fff', padding:'12px 20px', border:'none', borderRadius:6, fontSize:16, cursor:'pointer' },
  text: { textAlign:'center', color:'#333' },
  subheader: { color:'#004d40', margin:'25px 0 15px' },
  chart: { maxWidth:'100%', height:'auto', borderRadius:8, boxShadow:'0 2px 12px rgba(0,0,0,0.1)' },
  // analysisContainer: { marginTop:20, textAlign:'left' },
  // analysisBlock: { background:'#f4f4f4', padding:12, borderRadius:6, marginBottom:10 }
};

export default App;
