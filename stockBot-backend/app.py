# app.py
from flask import Flask, jsonify, request, url_for, send_from_directory
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import os
import io
import base64

app = Flask(__name__)

# --- PRODUCTION CORS SETUP ---
# IMPORTANT: Replace 'https://your-react-app-url.com' with the actual URL of your deployed React frontend.
# For development, you can add "http://localhost:5173" (or whatever port your React dev server uses)
# to the list of allowed origins if you need to test locally while this app is deployed.
ALLOWED_ORIGINS = ["http://localhost:5173", "https://your-react-app-url.com"] # Add your deployed frontend URL here
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})


# Directory for saving plots
PLOTS_DIR = 'static/plots'
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

def download_data(ticker_symbol, period="1y"):
    """Downloads historical stock data."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period=period)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"Error downloading data for {ticker_symbol}: {e}")
        return None

def generate_candlestick_signal(data):
    """Generates candlestick signals (e.g., Hammer, Doji)."""
    # Example: Simple Hammer detection
    # A hammer is a bullish reversal candlestick pattern.
    # It occurs after a downtrend and consists of a small real body
    # (open and close are close to each other) at the upper end of the trading range
    # and a long lower shadow that is at least twice the length of the real body.
    # It has little or no upper shadow.

    signals = []
    if data.empty:
        return signals

    # Ensure data has necessary columns
    if 'Open' not in data.columns or 'High' not in data.columns or \
       'Low' not in data.columns or 'Close' not in data.columns:
        return signals

    for i in range(len(data)):
        open_price = data['Open'].iloc[i]
        high_price = data['High'].iloc[i]
        low_price = data['Low'].iloc[i]
        close_price = data['Close'].iloc[i]

        real_body = abs(close_price - open_price)
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)

        # Conditions for a Hammer (approximate):
        # 1. Small real body
        # 2. Lower shadow at least twice the real body
        # 3. Little or no upper shadow
        if real_body > 0 and lower_shadow >= 2 * real_body and upper_shadow < real_body * 0.2:
            signals.append({
                'date': data.index[i].strftime('%Y-%m-%d'),
                'type': 'Hammer',
                'message': 'Potential bullish reversal (Hammer candlestick detected).',
                'signal_type': 'Buy' if close_price > open_price else 'Hold' # Green body suggests stronger buy
            })

    return signals


def analyze_stock(ticker_symbol):
    """Analyzes stock data for RSI and candlestick patterns."""
    data = download_data(ticker_symbol)
    if data is None or data.empty:
        return {
            "ticker": ticker_symbol,
            "message": f"Could not retrieve data for {ticker_symbol}. It might be an invalid ticker symbol or data is unavailable.",
            "signal_type": "N/A",
            "plot_url": None
        }

    # Calculate RSI
    data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()

    # Generate Candlestick Signals
    candlestick_signals = generate_candlestick_signal(data)

    rsi_message = ""
    rsi_signal_type = "Hold"

    if not data['RSI'].iloc[-1:].empty:
        current_rsi = data['RSI'].iloc[-1]
        if current_rsi > 70:
            rsi_message = "Overbought (RSI > 70). Potential sell signal."
            rsi_signal_type = "Sell"
        elif current_rsi < 30:
            rsi_message = "Oversold (RSI < 30). Potential buy signal."
            rsi_signal_type = "Buy"
        else:
            rsi_message = "Neutral (RSI between 30 and 70)."
            rsi_signal_type = "Hold"
    else:
        rsi_message = "RSI data not available."


    # Combine messages
    full_message = f"{ticker_symbol} - RSI: {rsi_message}"
    if candlestick_signals:
        for signal in candlestick_signals[-3:]: # Show last 3 signals
            full_message += f"\n  - Candlestick: {signal['message']} (Date: {signal['date']})"
            # If any recent strong buy/sell candlestick signal, override RSI for overall signal
            if signal['signal_type'] == 'Buy' and rsi_signal_type != 'Sell':
                rsi_signal_type = 'Buy'
            elif signal['signal_type'] == 'Sell' and rsi_signal_type != 'Buy':
                rsi_signal_type = 'Sell'


    # Generate plot
    plot_filename = f"{ticker_symbol}_price_chart.png"
    plot_path = os.path.join(PLOTS_DIR, plot_filename)
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.title(f'{ticker_symbol} Close Price (Last 1 Year)')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close() # Close the plot to free memory

    plot_url = url_for('static_files', filename=f'plots/{plot_filename}')

    return {
        "ticker": ticker_symbol,
        "message": full_message,
        "signal_type": rsi_signal_type,
        "plot_url": plot_url
    }

@app.route('/static/plots/<filename>')
def static_files(filename):
    """Serves static plot images."""
    return send_from_directory(PLOTS_DIR, filename)

@app.route('/api/analyze/<ticker_symbol>', methods=['GET'])
def analyze_single_stock_api(ticker_symbol):
    """API endpoint for single stock analysis."""
    result = analyze_stock(ticker_symbol.upper())
    return jsonify(result)

@app.route('/api/compare_stocks', methods=['GET'])
def compare_stocks_api():
    """API endpoint for comparing multiple stocks."""
    tickers_str = request.args.get('tickers', '')
    ticker_list = [t.strip().upper() for t in tickers_str.split(',') if t.strip()]

    if not ticker_list:
        return jsonify({"error": "No ticker symbols provided."}), 400

    analysis_results = []
    all_data = {}

    for ticker in ticker_list:
        data = download_data(ticker)
        if data is None or data.empty:
            analysis_results.append({
                "ticker": ticker,
                "message": f"Could not retrieve data for {ticker}. It might be an invalid ticker symbol or data is unavailable.",
                "signal_type": "N/A"
            })
            continue # Skip to next ticker if data is not available

        all_data[ticker] = data['Close'] # Store closing prices for comparison plot

        # Perform individual analysis for text results
        # Note: We're not generating individual plots here as per the user's requirement.
        # We reuse part of analyze_stock's logic for text analysis.
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        candlestick_signals = generate_candlestick_signal(data)

        rsi_message = ""
        rsi_signal_type = "Hold"

        if not data['RSI'].iloc[-1:].empty:
            current_rsi = data['RSI'].iloc[-1]
            if current_rsi > 70:
                rsi_message = "Overbought (RSI > 70). Potential sell signal."
                rsi_signal_type = "Sell"
            elif current_rsi < 30:
                rsi_message = "Oversold (RSI < 30). Potential buy signal."
                rsi_signal_type = "Buy"
            else:
                rsi_message = "Neutral (RSI between 30 and 70)."
                rsi_signal_type = "Hold"
        else:
            rsi_message = "RSI data not available."

        full_message = f"RSI: {rsi_message}"
        if candlestick_signals:
            for signal in candlestick_signals[-3:]: # Show last 3 signals
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


    # Generate comparison plot if valid data exists for at least one ticker
    comparison_plot_url = None
    if all_data:
        plt.figure(figsize=(12, 7))
        for ticker, series in all_data.items():
            # Normalize data to start at 100 for better comparison of percentage change
            normalized_series = (series / series.iloc[0]) * 100
            plt.plot(normalized_series.index, normalized_series, label=ticker)

        plt.title('Normalized Stock Price Comparison (Last 1 Year)')
        plt.xlabel('Date')
        plt.ylabel('Normalized Price (Start = 100)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        comparison_plot_filename = f"compare_{'_'.join(ticker_list)}_price_chart.png"
        comparison_plot_path = os.path.join(PLOTS_DIR, comparison_plot_filename)
        plt.savefig(comparison_plot_path)
        plt.close()

        comparison_plot_url = url_for('static_files', filename=f'plots/{comparison_plot_filename}')


    return jsonify({
        "comparison_plot_url": comparison_plot_url,
        "analysis_results": analysis_results
    })

# --- Gunicorn will use the 'app' object directly in production ---
if __name__ == "__main__":
    # This block is for local development only. Gunicorn will run the 'app' object in production.
    # Set debug=True only for development.
    app.run(debug=True, port=5000)
