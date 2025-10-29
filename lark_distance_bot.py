from flask import Flask, request, jsonify
import math
import requests
import os

app = Flask(__name__)

# ---- CẤU HÌNH ----
COMPANY_ADDRESS = "東京都世田谷区桜上水4丁目7-5"
GOOGLE_API_KEY = "AIzaSyAND5r7rjGzT_b3nkSowZJ4gdzN-pMFoD8"

# ---- HÀM LẤY TOẠ ĐỘ GIỐNG KINTONE ----
def get_coordinates(address):
    """Giống y như code trên Kintone: lấy result[0].geometry.location"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY,
        "language": "ja",
        "region": "jp"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") == "OK":
        return data["results"][0]["geometry"]["location"]
    else:
        print(f"[Geocode ERROR] {address} → {data.get('status')}")
        return None

# ---- HÀM TÍNH KHOẢNG CÁCH (y hệt Kintone) ----
def calc_distance(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = (lat2 - lat1) * math.pi / 180
    dlng = (lng2 - lng1) * math.pi / 180
    a = math.sin(dlat / 2) ** 2 + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ---- ROUTE KIỂM TRA ----
@app.route("/", methods=["GET"])
def home():
    return "✅ Flask version of Kintone distance calculator is running!"

# ---- ROUTE CHÍNH ----
@app.route("/distance", methods=["POST"])
def calc_distance_api():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu JSON"}), 400

    address = data.get("住所") or data.get("address")
    if not address:
        return jsonify({"error": "Thiếu địa chỉ công trường"}), 400

    # Lấy toạ độ công ty
    base_coords = get_coordinates(COMPANY_ADDRESS)
    if not base_coords:
        return jsonify({"error": "Không tìm thấy địa chỉ công ty"}), 400

    # Lấy toạ độ công trường
    dest_coords = get_coordinates(address)
    if not dest_coords:
        return jsonify({"error": "Không tìm thấy địa chỉ công trường"}), 400

    # Tính khoảng cách
    distance = calc_distance(
        base_coords["lat"],
        base_coords["lng"],
        dest_coords["lat"],
        dest_coords["lng"]
    )

    print(f"🏢 {COMPANY_ADDRESS}: {base_coords}")
    print(f"🏗️ {address}: {dest_coords}")
    print(f"📏 Khoảng cách = {distance:.2f} km")

    return jsonify({
        "address_input": address,
        "distance_km": round(distance, 2),
        "company_address": COMPANY_ADDRESS,
        "company_lat": base_coords["lat"],
        "company_lng": base_coords["lng"],
        "site_lat": dest_coords["lat"],
        "site_lng": dest_coords["lng"]
    })

# ---- CHẠY TRÊN RENDER ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
