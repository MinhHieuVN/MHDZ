import hashlib
import requests
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Cấu hình chuẩn từ hệ thống Garena
APP_ID = "100067"
LOCALE = "vi-VN"
REGION = "VN"

def call_post(url, payload):
    """Hàm gọi API Garena với log chi tiết"""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=20)
        # Nếu Garena trả về lỗi hệ thống (4xx, 5xx)
        if response.status_code != 200:
            return {"error": f"Garena Server Error {response.status_code}", "raw": response.text}
        return response.json()
    except Exception as e:
        return {"error": f"Lỗi kết nối máy chủ: {str(e)}", "result": -1}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/info", methods=["GET"])
def bind_info():
    access_token = request.args.get("access_token")
    if not access_token:
        return jsonify({"error": "Thiếu access_token"}), 400
    
    url = f"https://100067.connect.garena.com/game/account_security/bind:get_bind_info?app_id={APP_ID}&access_token={access_token}"
    try:
        resp = requests.get(url, timeout=15)
        return resp.json()
    except Exception as e:
        return jsonify({"error": f"Không thể lấy thông tin: {str(e)}"}), 500

@app.route("/send_otp", methods=["GET"])
def send_otp():
    access_token = request.args.get("access_token")
    email = request.args.get("email")
    if not access_token or not email:
        return jsonify({"error": "Thiếu email hoặc token"}), 400

    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    payload = {
        "email": email, 
        "app_id": APP_ID, 
        "access_token": access_token, 
        "locale": LOCALE, 
        "region": REGION
    }
    return jsonify(call_post(url, payload))

@app.route("/unbind", methods=["GET"])
def unbind_otp():
    access_token = request.args.get("access_token")
    email = request.args.get("email")
    otp = request.args.get("otp")
    
    if not all([access_token, email, otp]):
        return jsonify({"error": "Thiếu thông tin OTP hoặc Email"}), 400

    # Bước 1: Xác thực OTP để lấy identity_token
    res_identity = call_post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_identity",
        {"email": email, "app_id": APP_ID, "access_token": access_token, "otp": otp}
    )
    
    identity_token = res_identity.get("identity_token")
    if not identity_token:
        return jsonify({"error": "Xác thực OTP thất bại", "detail": res_identity}), 400

    # Bước 2: Gửi yêu cầu hủy liên kết
    return jsonify(call_post(
        "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request",
        {"app_id": APP_ID, "access_token": access_token, "identity_token": identity_token}
    ))

@app.route("/unbind_secondary", methods=["GET"])
def unbind_secondary():
    access_token = request.args.get("access_token")
    security_code = request.args.get("securitycode")
    
    if not access_token or not security_code:
        return jsonify({"error": "Thiếu Token hoặc Pass 2"}), 400

    # Mã hóa Pass 2 theo chuẩn SHA256
    secondary_password = hashlib.sha256(security_code.encode()).hexdigest().upper()

    res_identity = call_post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_identity",
        {"secondary_password": secondary_password, "app_id": APP_ID, "access_token": access_token}
    )
    
    identity_token = res_identity.get("identity_token")
    if not identity_token:
        return jsonify({"error": "Sai Mật khẩu cấp 2", "detail": res_identity}), 400

    return jsonify(call_post(
        "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request",
        {"app_id": APP_ID, "access_token": access_token, "identity_token": identity_token}
    ))

@app.route("/cancel", methods=["GET"])
def cancel():
    access_token = request.args.get("access_token")
    url = "https://100067.connect.gopapi.io/game/account_security/bind:cancel_request"
    return jsonify(call_post(url, {"app_id": APP_ID, "access_token": access_token}))

if __name__ == "__main__":
    app.run(debug=True)
    
