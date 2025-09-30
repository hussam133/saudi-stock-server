from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "data.db"


# ================= Database Setup =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # جدول الأسعار
    c.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            timestamp DATETIME
        )
    """)

    # جدول المؤشرات
    c.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            indicator TEXT,
            value REAL,
            timestamp DATETIME
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= Helper Functions =================
def save_price(symbol, price, timestamp):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO prices (symbol, price, timestamp) VALUES (?, ?, ?)",
              (symbol, price, timestamp))
    conn.commit()
    conn.close()


def save_indicator(symbol, indicator, value, timestamp):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO indicators (symbol, indicator, value, timestamp) VALUES (?, ?, ?, ?)",
              (symbol, indicator, value, timestamp))
    conn.commit()
    conn.close()


def cleanup_old_data():
    """يحذف البيانات الأقدم من 7 أيام"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    week_ago = datetime.utcnow() - timedelta(days=7)
    c.execute("DELETE FROM prices WHERE timestamp < ?", (week_ago,))
    c.execute("DELETE FROM indicators WHERE timestamp < ?", (week_ago,))
    conn.commit()
    conn.close()


def get_prices_df(symbol):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT price, timestamp FROM prices WHERE symbol = ? ORDER BY timestamp ASC"
    df = pd.read_sql(query, conn, params=(symbol,))
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
    return df


# ================= Indicators =================
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_ema(prices, period=9):
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line


def calculate_vwap(df):
    # هنا بنفترض أنه جاي من TradingView بسعر الإغلاق فقط
    # فإذا بدنا دقة أعلى لازم يرسلوا كمان حجم التداول (volume)
    df["cum_price"] = (df["price"]).cumsum()
    df["cum_vol"] = range(1, len(df) + 1)  # volume افتراضي = 1
    vwap = df["cum_price"] / df["cum_vol"]
    return vwap


# ================= Endpoints =================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data or "symbol" not in data or "price" not in data:
        return jsonify({"error": "invalid payload"}), 400

    symbol = data["symbol"]
    price = float(data["price"])
    timestamp = datetime.utcnow()

    # تخزين السعر
    save_price(symbol, price, timestamp)
    cleanup_old_data()

    # نحضر كل الأسعار لهالرمز
    df = get_prices_df(symbol)
    if df.empty:
        return jsonify({"status": "saved price only"})

    df["RSI"] = calculate_rsi(df["price"])
    df["EMA9"] = calculate_ema(df["price"], 9)
    df["EMA21"] = calculate_ema(df["price"], 21)
    macd, signal = calculate_macd(df["price"])
    df["MACD"] = macd
    df["MACD_signal"] = signal
    df["VWAP"] = calculate_vwap(df)

    latest = df.iloc[-1]

    # نخزن آخر القيم
    save_indicator(symbol, "RSI", float(latest["RSI"]), timestamp)
    save_indicator(symbol, "EMA9", float(latest["EMA9"]), timestamp)
    save_indicator(symbol, "EMA21", float(latest["EMA21"]), timestamp)
    save_indicator(symbol, "MACD", float(latest["MACD"]), timestamp)
    save_indicator(symbol, "MACD_signal", float(latest["MACD_signal"]), timestamp)
    save_indicator(symbol, "VWAP", float(latest["VWAP"]), timestamp)

    return jsonify({
        "symbol": symbol,
        "price": price,
        "RSI": float(latest["RSI"]),
        "EMA9": float(latest["EMA9"]),
        "EMA21": float(latest["EMA21"]),
        "MACD": float(latest["MACD"]),
        "MACD_signal": float(latest["MACD_signal"]),
        "VWAP": float(latest["VWAP"]),
        "timestamp": timestamp.isoformat()
    })


@app.route("/prices")
def get_prices():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT symbol, price, timestamp FROM prices WHERE symbol = ? ORDER BY timestamp DESC", (symbol,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"symbol": r[0], "price": r[1], "timestamp": r[2]} for r in rows
    ])


@app.route("/indicators")
def get_indicators():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT symbol, indicator, value, timestamp FROM indicators WHERE symbol = ? ORDER BY timestamp DESC",
              (symbol,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"symbol": r[0], "indicator": r[1], "value": r[2], "timestamp": r[3]} for r in rows
    ])


# ================= Local Run =================
if __name__ == "__main__":
    app.run(debug=True)
