from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Get latest price
@app.route("/price", methods=["GET"])
def price():
    symbol = request.args.get("symbol", "AAPL")
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        return jsonify({"error": "No data"}), 404
    last_price = data["Close"].iloc[-1]
    return jsonify({"symbol": symbol, "price": round(last_price, 2)})

# SMA (Simple Moving Average)
@app.route("/sma", methods=["GET"])
def sma():
    symbol = request.args.get("symbol", "AAPL")
    fast = int(request.args.get("fast", 10))
    slow = int(request.args.get("slow", 30))
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="3mo")
    if data.empty:
        return jsonify({"error": "No data"}), 404
    data["SMA_fast"] = data["Close"].rolling(window=fast).mean()
    data["SMA_slow"] = data["Close"].rolling(window=slow).mean()
    return jsonify({
        "symbol": symbol,
        "sma_fast": round(data["SMA_fast"].iloc[-1], 2),
        "sma_slow": round(data["SMA_slow"].iloc[-1], 2)
    })

# RSI
@app.route("/rsi", methods=["GET"])
def rsi():
    symbol = request.args.get("symbol", "AAPL")
    period = int(request.args.get("period", 14))
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="3mo")
    if data.empty:
        return jsonify({"error": "No data"}), 404
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi_value = 100 - (100 / (1 + rs.iloc[-1]))
    return jsonify({"symbol": symbol, "rsi": round(rsi_value, 2)})

# MACD
@app.route("/macd", methods=["GET"])
def macd():
    symbol = request.args.get("symbol", "AAPL")
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="6mo")
    if data.empty:
        return jsonify({"error": "No data"}), 404
    short_ema = data["Close"].ewm(span=12, adjust=False).mean()
    long_ema = data["Close"].ewm(span=26, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return jsonify({
        "symbol": symbol,
        "macd": round(macd_line.iloc[-1], 2),
        "signal": round(signal.iloc[-1], 2)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
