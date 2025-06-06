from flask import Flask, jsonify, request, url_for
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import os

# --- Stock Analysis Functions (Keep these as they are) ---
# ... (your existing download_data, generate_candlestick_signal, analyze_stock functions) ...
# I'll just put a placeholder for them here for brevity but they should be in your file
# from app.py
def download_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            return None
        data.dropna(inplace=True)
        if data.empty or len(data) < 14:
            return None
        return data
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return None

def generate_candlestick_signal(df):
    if len(df) < 2:
        return "Neutral"
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    prev_close = prev["Close"].item()
    prev_open = prev["Open"].item()
    curr_close = curr["Close"].item()
    curr_open = curr["Open"].item()
    if prev_close < prev_open and curr_close > curr_open and curr_close > prev_close:
        return "Bullish"
    elif prev_close > prev_open and curr_close < curr_open and curr_close < prev_close:
        return "Bearish"
    else:
        return "Neutral"

def analyze_stock(ticker_symbol):
    DATA_PERIOD = "1y"
    DATA_INTERVAL = "1wk"
    data = download_data(ticker_symbol, DATA_PERIOD, DATA_INTERVAL)
    if data is None:
        return ticker_symbol, "Skip", "No sufficient data or error downloading."
    candlestick_signal = generate_candlestick_signal(data)
    rsi_indicator = ta.momentum.RSIIndicator(close=data["Close"].squeeze(), window=14)
    rsi_value = rsi_indicator.rsi().iloc[-1]
    if rsi_value < 30 and candlestick_signal == "Bullish":
        return ticker_symbol, "Buy", f"🔼 Buy Signal (Bullish candlestick + RSI {rsi_value:.2f})"
    elif rsi_value > 70 and candlestick_signal == "Bearish":
        return ticker_symbol, "Sell", f"🔽 Sell Signal (Bearish candlestick + RSI {rsi_value:.2f})"
    else:
        return ticker_symbol, "Hold", f"🟡 Hold/Neutral (Signal: {candlestick_signal}, RSI: {rsi_value:.2f})"


# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

if not os.path.exists('static'):
    os.makedirs('static')

# Existing API endpoint for single stock analysis
@app.route("/api/analyze/<ticker_symbol>", methods=["GET"])
def analyze_stock_api(ticker_symbol):
    ticker, signal_type, message = analyze_stock(ticker_symbol.upper())

    if signal_type == "Skip":
        return jsonify({"error": message}), 400

    plot_url = None
    data = download_data(ticker_symbol.upper(), "1y", "1wk")
    if data is not None and not data.empty:
        plt.figure(figsize=(10, 6))
        plt.plot(data.index, data["Close"], label=f"{ticker_symbol.upper()} Close Price")
        plt.title(f"{ticker_symbol.upper()} Weekly Close Price")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        plot_filename = f"{ticker_symbol.upper()}_price_plot.png"
        plot_path = os.path.join('static', plot_filename)
        plt.savefig(plot_path)
        plt.close()

        plot_url = url_for('static', filename=plot_filename)

    return jsonify({
        "ticker": ticker,
        "signal_type": signal_type,
        "message": message,
        "plot_url": plot_url
    })


# --- NEW API ENDPOINT for Comparing Multiple Stocks ---
@app.route("/api/compare_stocks", methods=["GET"])
def compare_stocks_api():
    tickers_param = request.args.get('tickers') # Get tickers from query parameter like ?tickers=TSLA,GOOGL
    if not tickers_param:
        return jsonify({"error": "Please provide a comma-separated list of tickers using the 'tickers' query parameter."}), 400

    tickers = [t.strip().upper() for t in tickers_param.split(',')]
    if not tickers:
        return jsonify({"error": "No valid tickers provided."}), 400

    all_stock_data = {}
    analysis_results = []
    DATA_PERIOD = "1y" # Use same period for comparison
    DATA_INTERVAL = "1wk"

    plt.figure(figsize=(12, 7)) # Larger figure for multiple lines

    for ticker_symbol in tickers:
        data = download_data(ticker_symbol, DATA_PERIOD, DATA_INTERVAL)
        if data is not None and not data.empty:
            # Store data for plotting
            all_stock_data[ticker_symbol] = data["Close"]

            # Perform analysis for each stock and store results
            _, signal_type, message = analyze_stock(ticker_symbol)
            analysis_results.append({
                "ticker": ticker_symbol,
                "signal_type": signal_type,
                "message": message
            })
            plt.plot(data.index, data["Close"], label=f"{ticker_symbol} Close Price")
        else:
            analysis_results.append({
                "ticker": ticker_symbol,
                "signal_type": "Skip",
                "message": "No sufficient data or error downloading."
            })

    if not all_stock_data: # If no data was successfully downloaded for any stock
        return jsonify({"error": "Could not retrieve data for any of the specified tickers."}), 400

    # Finalize plot settings
    plt.title(f"Weekly Close Prices Comparison ({', '.join(tickers)})")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    plt.legend() # This will now show all ticker labels
    plt.tight_layout()

    # Define plot filename (unique based on tickers)
    plot_filename = f"comparison_plot_{'_'.join(sorted(tickers))}.png"
    plot_path = os.path.join('static', plot_filename)

    plt.savefig(plot_path)
    plt.close()

    compare_plot_url = url_for('static', filename=plot_filename)

    return jsonify({
        "comparison_plot_url": compare_plot_url,
        "analysis_results": analysis_results # Return analysis for all stocks
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
