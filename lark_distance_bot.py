# file: lark_distance_bot.py
from flask import Flask, request, jsonify
import math
import requests

app = Flask(__name__)

# ---- ĐỊA CHỈ CÔNG TY CỐ ĐỊNH ----
COMPANY_ADDRESS = "東京都世田谷区桜上水4-7-5"
# Google Maps API Key (bạn cần tạo 1 key miễn phí tại https://console.cloud.google.com/)
GOOGLE_API_KEY = "AIzaSyAND5r7rjGzT_b3nkSowZJ4gdzN-pMFoD8"

# Hàm chuyển địa chỉ thành tọa độ
def get_latlon(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address, 
        "key": GOOGLE_API_KEY,
        "language": "ja",  # ⚡ thêm ngôn ngữ Nhật
        "region": "jp"
    }
    res = requests.get(url, params=params).json()
    if not res["results"]:
        return None, None
    print(f"Geocode for {address}: {res['results'][0]['formatted_address']}")
    loc = res["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]

# Hàm tính khoảng cách (theo km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

@app.route("/distance", methods=["POST"])
def calc_distance():
    data = request.json
    site_address = data.get("address")

    # 1️⃣ Lấy tọa độ công ty (chỉ cần lấy 1 lần, có thể lưu sẵn)
    comp_lat, comp_lon = get_latlon(COMPANY_ADDRESS)
    if not comp_lat:
        return jsonify({"error": "Không tìm thấy địa chỉ công ty"}), 400

    # 2️⃣ Lấy tọa độ công trường
    site_lat, site_lon = get_latlon(site_address)
    if not site_lat:
        return jsonify({"error": "Không tìm thấy địa chỉ công trường"}), 400

    # 3️⃣ Tính khoảng cách
    distance_km = haversine(comp_lat, comp_lon, site_lat, site_lon)

    # 4️⃣ Trả kết quả về cho Lark Automation
    return jsonify({"distance": round(distance_km, 2)})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

