from flask import Flask, request, jsonify
import math
import requests
import os

app = Flask(__name__)

# ---- CẤU HÌNH CỐ ĐỊNH ----
COMPANY_LAT = 35.6641  # 東京都世田谷区桜上水4-7-5
COMPANY_LON = 139.6257
GOOGLE_API_KEY = "AIzaSyAND5r7rjGzT_b3nkSowZJ4gdzN-pMFoD8"

# ---- HÀM CHUẨN HÓA ĐỊA CHỈ ----
def normalize_address(addr: str):
    """Đảm bảo địa chỉ có chứa '日本' để Google hiểu rõ"""
    addr = addr.strip()
    if "日本" not in addr:
        addr = "日本 " + addr
    return addr

# ---- HÀM LẤY TỌA ĐỘ CHÍNH XÁC ----
def get_latlon(address):
    if not address:
        return None, None

    address = normalize_address(address)
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY,
        "language": "ja",
        "components": "country:JP"
    }

    res = requests.get(url, params=params).json()
    if not res.get("results"):
        print(f"[❌ Geocode ERROR] Không tìm thấy: {address}")
        return None, None

    result = res["results"][0]
    geometry = result["geometry"]
    loc_type = geometry.get("location_type", "UNKNOWN")

    # Nếu có viewport → lấy trung bình (khi địa chỉ là khu vực)
    if "viewport" in geometry:
        ne = geometry["viewport"]["northeast"]
        sw = geometry["viewport"]["southwest"]
        lat = (ne["lat"] + sw["lat"]) / 2
        lon = (ne["lng"] + sw["lng"]) / 2
    else:
        lat = geometry["location"]["lat"]
        lon = geometry["location"]["lng"]

    formatted = result.get("formatted_address", "")
    print(f"[📍Geocode OK] {address} → {formatted} | Type: {loc_type} | Lat: {lat:.6f}, Lon: {lon:.6f}")

    # Cảnh báo nếu Google cho kết quả ước lượng
    if loc_type not in ["ROOFTOP", "RANGE_INTERPOLATED"]:
        print(f"[⚠️ Warning] Địa chỉ không cụ thể ({loc_type}) → Sai số có thể lớn")

    return lat, lon

# ---- HÀM TÍNH KHOẢNG CÁCH (km) ----
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

# ---- ROUTE KIỂM TRA ----
@app.route("/", methods=["GET"])
def home():
    return "✅ Lark Distance Bot is running and optimized for Japan!"

# ---- ROUTE TÍNH KHOẢNG CÁCH ----
@app.route("/distance", methods=["POST", "GET"])
def calc_distance():
    if request.method == "GET":
        return jsonify({"message": "Use POST with JSON {'住所': '東京都新宿区...'}"})

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Thiếu dữ liệu JSON"}), 400

    # Hỗ trợ cả '住所' (từ Lark) và 'address' (test local)
    site_address = data.get("住所") or data.get("address")
    if not site_address:
        return jsonify({"error": "Thiếu địa chỉ công trường"}), 400

    # Lấy tọa độ
    site_lat, site_lon = get_latlon(site_address)
    if not site_lat or not site_lon:
        return jsonify({"error": "Không tìm thấy địa chỉ công trường"}), 400

    # Kiểm tra hợp lệ
    if abs(site_lat) < 1 and abs(site_lon) < 1:
        return jsonify({"error": "Địa chỉ không hợp lệ (tọa độ quá nhỏ)"}), 400

    # Tính khoảng cách
    distance_km = haversine(COMPANY_LAT, COMPANY_LON, site_lat, site_lon)
    print(f"🏢 Công ty: ({COMPANY_LAT}, {COMPANY_LON}) | 🏗️ Công trường: ({site_lat}, {site_lon})")
    print(f"📏 Khoảng cách: {distance_km:.2f} km\n")

    return jsonify({
        "address_input": site_address,
        "distance_km": round(distance_km, 2)
    })

# ---- KHỞI CHẠY APP (Render) ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
