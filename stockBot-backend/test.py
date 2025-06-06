import yfinance as yf

apple = yf.Ticker("AAPL")
print(apple.info["longName"])
