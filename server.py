from flask import Flask, jsonify
import sqlite3
import datetime
import pandas as pd
import ta
import tradingview_ta as tv
import pytz

app = Flask(__name__)
DB_FILE = "ticks.db"

# ---------- DB Setup ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp TEXT,
            price REAL,
            rsi REAL,
            macd REAL,
            ema REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Market Time (Saudi Time) ----------
def is_market_open():
    tz = pytz.timezone("Asia/Riyadh")
    now = datetime.datetime.now(tz).time()
    market_open = datetime.time(10, 0)
    market_close = datetime.time(15, 10)
    return market_open <= now <= market_close

# ---------- Fetch from TradingView ----------
def fetch_price(symbol="2222"):
    try:
        h = tv.TA_Handler(
            symbol=symbol,
            screener="saudi",
            exchange="TADAWUL",
            interval=tv.Interval.INTERVAL_1_MINUTE
        )
        analysis = h.get_analysis()
        price = analysis.indicators["close"]
        return float(price)
    except:
        return None

def calculate_indicators(prices: pd.Series):
    rsi = ta.momentum.RSIIndicator(prices).rsi().iloc[-1]
    macd = ta.trend.MACD(prices).macd().iloc[-1]
    ema = ta.trend.EMAIndicator(prices, window=14).ema_indicator().iloc[-1]
    return rsi, macd, ema

def store_tick(symbol, price, rsi, macd, ema):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO ticks (symbol, timestamp, price, rsi, macd, ema)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, datetime.datetime.utcnow().isoformat(), price, rsi, macd, ema))
    conn.commit()
    conn.close()

# ---------- API Routes ----------
@app.route("/tick/<symbol>", methods=["GET"])
def get_tick(symbol):
    if not is_market_open():
        return jsonify({"error": "Market closed (Saudi 10:00-15:10)"}), 403

    price = fetch_price(symbol)
    if price:
        prices = pd.Series([price] * 20)  # مؤقتاً لعدم توفر history مجاني
        rsi, macd, ema = calculate_indicators(prices)
        store_tick(symbol, price, rsi, macd, ema)
        return jsonify({
            "symbol": symbol,
            "price": price,
            "rsi": round(rsi, 2),
            "macd": round(macd, 2),
            "ema": round(ema, 2)
        })
    else:
        return jsonify({"error": "Failed to fetch price"}), 500

@app.route("/ticks/history/<symbol>", methods=["GET"])
def get_history(symbol):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, price, rsi, macd, ema
        FROM ticks
        WHERE symbol = ?
        ORDER BY id DESC
        LIMIT 2000
    """, (symbol,))
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# ---------- Clean Old Data ----------
def clean_old_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=2)).isoformat()
    c.execute("DELETE FROM ticks WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()

clean_old_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
