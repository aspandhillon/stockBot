from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

ALLOWED_ORIGINS = ["http://localhost:5173", "https://stockbot-frontend.onrender.com"]
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

def download_data(ticker_symbol, period="1y"):
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period=period)
        return data if not data.empty else None
    except Exception as e:
        print(f"Error downloading data for {ticker_symbol}: {e}")
        return None

def generate_candlestick_signal(data):
    signals = []
    if data.empty or not all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
        return signals

    for i in range(len(data)):
        open_price = data['Open'].iloc[i]
        high_price = data['High'].iloc[i]
        low_price = data['Low'].iloc[i]
        close_price = data['Close'].iloc[i]

        real_body = abs(close_price - open_price)
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)

        if real_body > 0 and lower_shadow >= 2 * real_body and upper_shadow < real_body * 0.2:
            signals.append({
                'date': data.index[i].strftime('%Y-%m-%d'),
                'type': 'Hammer',
                'message': 'Potential bullish reversal (Hammer candlestick detected).',
                'signal_type': 'Buy' if close_price > open_price else 'Hold'
            })

    return signals

@app.route('/api/compare_stocks', methods=['GET'])
def compare_stocks_api():
    tickers_str = request.args.get('tickers', '')
    ticker_list = [t.strip().upper() for t in tickers_str.split(',') if t.strip()]

    if not ticker_list:
        return jsonify({"error": "No ticker symbols provided."}), 400

    analysis_results = []
    all_data = {}

    for ticker in ticker_list:
        data = download_data(ticker)
        if data is None:
            analysis_results.append({
                "ticker": ticker,
                "message": f"Could not retrieve data for {ticker}.",
                "signal_type": "N/A"
            })
            continue

        all_data[ticker] = data['Close']
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        candlestick_signals = generate_candlestick_signal(data)

        current_rsi = data['RSI'].iloc[-1] if not data['RSI'].iloc[-1:].empty else None
        if current_rsi is None:
            rsi_message = "RSI data not available."
            rsi_signal_type = "Hold"
        elif current_rsi > 70:
            rsi_message = "Overbought (RSI > 70). Potential sell signal."
            rsi_signal_type = "Sell"
        elif current_rsi < 30:
            rsi_message = "Oversold (RSI < 30). Potential buy signal."
            rsi_signal_type = "Buy"
        else:
            rsi_message = "Neutral (RSI between 30 and 70)."
            rsi_signal_type = "Hold"

        full_message = f"RSI: {rsi_message}"
        for signal in candlestick_signals[-3:]:
            full_message += f"\n  - Candlestick: {signal['message']} (Date: {signal['date']})"
            if signal['signal_type'] == 'Buy' and rsi_signal_type != 'Sell':
                rsi_signal_type = 'Buy'
            elif signal['signal_type'] == 'Sell' and rsi_signal_type != 'Buy':
                rsi_signal_type = 'Sell'

        analysis_results.append({
            "ticker": ticker,
            "message": full_message,
            "signal_type": rsi_signal_type
        })

    base64_image = None
    if all_data:
        plt.figure(figsize=(12, 7))
        for ticker, series in all_data.items():
            normalized = (series / series.iloc[0]) * 100
            plt.plot(normalized.index, normalized, label=ticker)

        plt.title('Normalized Stock Price Comparison (Last 1 Year)')
        plt.xlabel('Date')
        plt.ylabel('Normalized Price (Start = 100)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        # Save image to buffer and convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        base64_image = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()

    return jsonify({
        "comparison_plot_base64": base64_image,
        "analysis_results": analysis_results
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
