import yfinance as yf
import pandas as pd
import ta
import time # To add delays for rate limiting if needed

# --- Configuration ---
# You'd typically get a list of tickers from an API or a pre-defined file
# For demonstration, let's use a small list of well-known tech stocks
TICKERS_TO_ANALYZE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", "JPM", "V", "PG", "KO"]
DATA_PERIOD = "6mo" # For weekly data, 6 months should be enough for 14-period RSI
DATA_INTERVAL = "1wk" # Weekly data for longer-term signals

# --- Existing Functions (slightly modified for robustness) ---
def download_data(ticker, period, interval):
    """Downloads historical stock data."""
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            print(f"Warning: No data downloaded for {ticker}. Skipping.")
            return None
        data.dropna(inplace=True)
        if data.empty or len(data) < 14: # Need enough data for RSI
            print(f"Warning: Not enough data for {ticker} after dropping NaNs. Skipping.")
            return None
        return data
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return None

def generate_candlestick_signal(df):
    """Generates a bullish, bearish, or neutral candlestick signal."""
    if len(df) < 2:
        return "Neutral"

    prev = df.iloc[-2]  # last week's candle
    curr = df.iloc[-1]  # this week's candle

    # Ensure scalar values are extracted
    prev_close = prev["Close"].item() if isinstance(prev["Close"], pd.Series) else prev["Close"]
    prev_open = prev["Open"].item() if isinstance(prev["Open"], pd.Series) else prev["Open"]
    curr_close = curr["Close"].item() if isinstance(curr["Close"], pd.Series) else curr["Close"]
    curr_open = curr["Open"].item() if isinstance(curr["Open"], pd.Series) else curr["Open"]

    # Basic bullish/bearish engulfing or strong continuation check
    # Bullish: Previous candle was down, current candle is up and closes above previous close
    if prev_close < prev_open and curr_close > curr_open and curr_close > prev_close:
        return "Bullish"
    # Bearish: Previous candle was up, current candle is down and closes below previous close
    elif prev_close > prev_open and curr_close < curr_open and curr_close < prev_close:
        return "Bearish"
    else:
        return "Neutral"

def analyze_stock(ticker):
    """
    Analyzes a single stock and returns a signal.
    Returns (ticker, signal_type, message)
    """
    data = download_data(ticker, DATA_PERIOD, DATA_INTERVAL)
    if data is None:
        return ticker, "Skip", "No sufficient data"

    candlestick_signal = generate_candlestick_signal(data)

    # RSI (Relative Strength Index)
    # Ensure 'close' series is correctly passed
    rsi_indicator = ta.momentum.RSIIndicator(close=data["Close"].squeeze(), window=14)
    rsi_value = rsi_indicator.rsi().iloc[-1] # .iloc[-1] is robust

    # Combine analysis
    if rsi_value < 30 and candlestick_signal == "Bullish":
        return ticker, "Buy", f"🔼 Buy Signal (Bullish candlestick + RSI {rsi_value:.2f})"
    elif rsi_value > 70 and candlestick_signal == "Bearish":
        return ticker, "Sell", f"🔽 Sell Signal (Bearish candlestick + RSI {rsi_value:.2f})"
    else:
        return ticker, "Hold", f"🟡 Hold/Neutral (Signal: {candlestick_signal}, RSI: {rsi_value:.2f})"

# --- Main Market Analysis Loop ---
def analyze_market(tickers_list):
    """Analyzes a list of tickers and prints signals."""
    buy_signals = []
    sell_signals = []
    hold_signals = []
    skipped_stocks = []

    print(f"Starting market analysis for {len(tickers_list)} tickers...\n")

    for ticker in tickers_list:
        print(f"Analyzing {ticker}...")
        ticker_result, signal_type, message = analyze_stock(ticker)

        if signal_type == "Buy":
            buy_signals.append(f"{ticker_result}: {message}")
        elif signal_type == "Sell":
            sell_signals.append(f"{ticker_result}: {message}")
        elif signal_type == "Hold":
            hold_signals.append(f"{ticker_result}: {message}")
        else: # Skip
            skipped_stocks.append(f"{ticker_result}: {message}")

        # Be polite to yfinance/APIs - add a small delay
        time.sleep(1) # 1 second delay between ticker downloads

    print("\n--- Market Analysis Summary ---")
    print("\nBUY SIGNALS:")
    if buy_signals:
        for signal in buy_signals:
            print(signal)
    else:
        print("No immediate Buy signals found.")

    print("\nSELL SIGNALS:")
    if sell_signals:
        for signal in sell_signals:
            print(signal)
    else:
        print("No immediate Sell signals found.")

    print("\nHOLD/NEUTRAL SIGNALS:")
    if hold_signals:
        for signal in hold_signals:
            print(signal)
    else:
        print("No immediate Hold/Neutral signals found.")

    if skipped_stocks:
        print("\nSKIPPED (Insufficient Data/Error):")
        for skipped in skipped_stocks:
            print(skipped)

# --- Run the market analysis ---
if __name__ == "__main__":
    analyze_market(TICKERS_TO_ANALYZE)
