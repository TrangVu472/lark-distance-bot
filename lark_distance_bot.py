from flask import Flask, request, jsonify
import math
import requests
import os

app = Flask(__name__)

# ---- CẤU HÌNH CỐ ĐỊNH ----
COMPANY_LAT = 35.6641  # 東京都世田谷区桜上水4-7-5
COMPANY_LON = 139.6257

# ⚠️ Đừng để API key công khai trong code public repository
GOOGLE_API_KEY = "AIzaSyAND5r7rjGzT_b3nkSowZJ4gdzN-pMFoD8"

# ---- HÀM LẤY TỌA ĐỘ ĐỊA CHỈ ----
def get_latlon(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY,
        "language": "ja",
        "region": "jp"
    }
    res = requests.get(url, params=params).json()
    if not res.get("results"):
        print(f"[Geocode ERROR] No result for {address}")
        return None, None

    result = res["results"][0]
    formatted = result["formatted_address"]
    lat = result["geometry"]["location"]["lat"]
    lon = result["geometry"]["location"]["lng"]

    print(f"[Geocode OK] {address} → {formatted} | Lat: {lat}, Lon: {lon}")
    return lat, lon

# ---- HÀM TÍNH KHOẢNG CÁCH (km) ----
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

# ---- ROUTE KIỂM TRA (GET) ----
@app.route("/", methods=["GET"])
def home():
    return "✅ Lark Distance Bot is running on Render!"

@app.route("/distance", methods=["POST", "GET"])
def calc_distance():
    # Nếu người dùng mở GET /distance trên trình duyệt
    if request.method == "GET":
        return jsonify({
            "message": "Use POST method with JSON { 'address': '東京都新宿区...' }"
        })

    data = request.get_json(silent=True)
    if not data or "address" not in data:
        return jsonify({"error": "Thiếu địa chỉ công trường"}), 400

    site_address = data["address"]

    # Lấy tọa độ công trường
    site_lat, site_lon = get_latlon(site_address)
    if not site_lat or not site_lon:
        return jsonify({"error": "Không tìm thấy địa chỉ công trường"}), 400

    # Tính khoảng cách
    distance_km = haversine(COMPANY_LAT, COMPANY_LON, site_lat, site_lon)

    print("🏢 Công ty:", COMPANY_LAT, COMPANY_LON)
    print("🏗️ Công trường:", site_lat, site_lon)
    print(f"📏 Khoảng cách: {distance_km:.2f} km")

    return jsonify({"distance": round(distance_km, 2)})

# ---- KHỞI CHẠY APP (chỉ dùng khi chạy local) ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
