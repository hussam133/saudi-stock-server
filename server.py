from flask import Flask, jsonify

app = Flask(__name__)

# المسار الأساسي للتأكد إن السيرفر شغال
@app.route('/')
def home():
    return jsonify({"message": "Saudi Stock Server is running"})

# مسار الأسعار اللحظية (تيك)
@app.route('/tick')
def tick():
    # هون رح نجيب بيانات الأسعار من TradingView لاحقاً
    data = {
        "symbol": "TASI",
        "price": 11000.25,
        "time": "2025-09-30T10:30:00"
    }
    return jsonify(data)

# مسار المؤشرات
@app.route('/indicators')
def indicators():
    indicators_data = {
        "RSI": 55.3,
        "MACD": {"signal": 1.2, "hist": -0.3},
        "SMA_20": 10980.5,
        "EMA_50": 11020.8
    }
    return jsonify(indicators_data)

# مسار البيانات التاريخية (مثلاً يومين)
@app.route('/history')
def history():
    history_data = [
        {"time": "2025-09-28", "close": 10950},
        {"time": "2025-09-29", "close": 11010}
    ]
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
