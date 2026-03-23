import hashlib
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Cấu hình mặc định
APP_ID = "100067"
LOCALE = "vi-VN"
REGION = "VN"

def call_post(url, payload):
    """Hàm bổ trợ thực hiện yêu cầu POST đến hệ thống Garena"""
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": f"Lỗi kết nối: {str(e)}", "result": -1}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/info", methods=["GET"])
def bind_info():
    access_token = request.args.get("access_token")
    if not access_token:
        return jsonify({"error": "access_token required"}), 400
    url = f"https://100067.connect.garena.com/game/account_security/bind:get_bind_info?app_id={APP_ID}&access_token={access_token}"
    try:
        resp = requests.get(url)
        return resp.json()
    except:
        return jsonify({"error": "Failed to fetch bind info"}), 500

@app.route("/send_otp", methods=["GET"])
def send_otp():
    access_token = request.args.get("access_token")
    email = request.args.get("email")
    if not access_token or not email:
        return jsonify({"error": "access_token and email required"}), 400
    url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    payload = {"email": email, "app_id": APP_ID, "access_token": access_token, "locale": LOCALE, "region": REGION}
    return call_post(url_send, payload)

@app.route("/unbind", methods=["GET"])
def unbind_otp():
    access_token = request.args.get("access_token")
    email = request.args.get("email")
    otp = request.args.get("otp")
    if not all([access_token, email, otp]):
        return jsonify({"error": "access_token, email, otp required"}), 400
    res_identity = call_post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_identity",
        {"email": email, "app_id": APP_ID, "access_token": access_token, "otp": otp}
    )
    identity_token = res_identity.get("identity_token")
    if not identity_token:
        return jsonify({"error": "identity verification failed", "raw": res_identity}), 400
    return call_post(
        "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request",
        {"app_id": APP_ID, "access_token": access_token, "identity_token": identity_token}
    )

@app.route("/unbind_secondary", methods=["GET"])
def unbind_secondary():
    access_token = request.args.get("access_token")
    security_code = request.args.get("securitycode")
    if not access_token or not security_code:
        return jsonify({"error": "access_token and securitycode required"}), 400
    secondary_password = hashlib.sha256(security_code.encode()).hexdigest().upper()
    res_identity = call_post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_identity",
        {"secondary_password": secondary_password, "app_id": APP_ID, "access_token": access_token}
    )
    identity_token = res_identity.get("identity_token")
    if not identity_token:
        return jsonify({"error": "identity verification failed", "raw": res_identity}), 400
    return call_post(
        "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request",
        {"app_id": APP_ID, "access_token": access_token, "identity_token": identity_token}
    )

@app.route("/cancel", methods=["GET"])
def cancel():
    access_token = request.args.get("access_token")
    if not access_token:
        return jsonify({"error": "access_token required"}), 400
    return call_post(
        "https://100067.connect.gopapi.io/game/account_security/bind:cancel_request",
        {"app_id": APP_ID, "access_token": access_token}
    )

if __name__ == "__main__":
    app.run(debug=True)
    
