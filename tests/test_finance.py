import yfinance as yf

ticker = yf.Ticker("DEC.PA")
info = ticker.info

print("Company:", info.get("longName"))
print("Market Cap:", info.get("marketCap"))
print("Revenue:", info.get("totalRevenue"))