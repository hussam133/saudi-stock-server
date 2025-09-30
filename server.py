from flask import Flask, request, jsonify

app = Flask(__name__)

# صفحة افتراضية للتأكد إن السيرفر شغال
@app.route("/")
def home():
    return "✅ Saudi Stock Server is running"

# Endpoint لاستقبال تنبيهات TradingView
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # هنا مؤقتاً منطبع البيانات
    print("📩 Webhook data:", data)

    return jsonify({"status": "success", "received": data}), 200

# Endpoint بسيط لتجربة API
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
