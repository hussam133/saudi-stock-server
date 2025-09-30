from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return {"status": "ok", "message": "Saudi Stock Server Running"}

@app.route("/price", methods=["GET"])
def get_price():
    symbol = request.args.get("symbol")  # مثال: 2222.SR
    if not symbol:
        return {"error": "Missing symbol"}, 400

    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        latest = data.tail(1)
        price = float(latest["Close"].iloc[0])
        return {"symbol": symbol, "price": price}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/indicators", methods=["GET"])
def get_indicators():
    symbol = request.args.get("symbol")
    if not symbol:
        return {"error": "Missing symbol"}, 400

    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d", interval="5m")

        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["RSI"] = 100 - (100 / (1 + (data["Close"].pct_change().add(1).rolling(14).apply(lambda x: (x[x > 0].sum()) / abs(x[x < 0].sum()) if abs(x[x < 0].sum()) > 0 else 0))))

        latest = data.tail(1).to_dict(orient="records")[0]
        return {"symbol": symbol, "indicators": latest}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
