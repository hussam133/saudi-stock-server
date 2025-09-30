from flask import Flask, jsonify
import requests
import sqlite3
import pandas as pd
import datetime

app = Flask(__name__)

# =========================
# إعداد قاعدة البيانات
# =========================
DB_FILE = "ticks.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# دالة لجلب الأسعار من TradingView (كمثال)
# =========================
def fetch_tick(symbol="TADAWUL:TASI"):
    # ⚠️ هاي بس مثال باستخدام API وهمي من tradingview
    url = f"https://api.tradingview.com/symbols/{symbol}/"
    try:
        # هذا مثال، لاحقاً لازم نعدل حسب الاشتراك
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "symbol": symbol,
                "price": data.get("price", None),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
    except Exception as e:
        print("Error fetching tick:", e)
    return None

# =========================
# حفظ البيانات في SQLite
# =========================
def save_tick(symbol, price):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO ticks (symbol, price, timestamp) VALUES (?, ?, ?)",
              (symbol, price, datetime.datetime.utcnow()))
    conn.commit()
    conn.close()

# =========================
# مسارات API
# =========================

@app.route("/")
def home():
    return jsonify({"message": "Saudi Stock Server is running"})

@app.route("/tick/<symbol>")
def get_tick(symbol):
    tick = fetch_tick(symbol)
    if tick and tick["price"] is not None:
        save_tick(tick["symbol"], tick["price"])
        return jsonify(tick)
    else:
        return jsonify({"error": "Failed to fetch tick"}), 500

@app.route("/history/<symbol>")
def get_history(symbol):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM ticks WHERE symbol=? ORDER BY timestamp DESC LIMIT 2000",
        conn,
        params=(symbol,)
    )
    conn.close()
    return df.to_json(orient="records")

# =========================
# تشغيل السيرفر
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
