import yfinance as yf
import ta
import pandas as pd

import csv

portfolio = []
with open("portfolio.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        portfolio.append({
            "ticker": row["ticker"].strip().upper(),
            "buy_price": float(row["buy_price"]),
            "shares": int(row["shares"])
        })


def analyze_stock(ticker):
    df = yf.download(ticker, period='6mo', interval='1d', progress=False, auto_adjust=True)
    print(f"\n>>> Downloaded {ticker} data: {len(df)} rows")
    if df.empty:
        return None

    df['rsi'] = ta.momentum.RSIIndicator(close=df['Close'].squeeze()).rsi()
    latest = df.iloc[-1]

    rsi_value = latest['rsi'].item()
    signal = "Hold"
    if rsi_value < 30:
        signal = "Buy"
    elif rsi_value > 70:
        signal = "Avoid"

    return latest['Close'].item(), rsi_value, signal

print("\n📊 Portfolio Tracker:\n")
for stock in portfolio:
    ticker = stock["ticker"]
    buy_price = stock["buy_price"]
    shares = stock["shares"]

    result = analyze_stock(ticker)
    if result:
        current_price, rsi, signal = result
        total_cost = buy_price * shares
        current_value = current_price * shares
        pnl = current_value - total_cost
        pnl_percent = (pnl / total_cost) * 100
        total_pl = (current_price - buy_price) * shares
        print(f"  P/L: ₹{total_pl:.2f} ({pnl_percent:.2f}%) on {shares} shares")
        print(f"{ticker}: {signal}")
        print(f"  Buy Price: ₹{buy_price} | Current: ₹{current_price:.2f} | RSI: {rsi:.2f}")
        print(f"  P/L: ₹{pnl:.2f} ({pnl_percent:.2f}%)\n")
    else:
        print(f"{ticker}: No data available.\n")
