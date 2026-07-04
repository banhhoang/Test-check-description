import streamlit as st
import pandas as pd
import requests
import io

# ==========================================
# 1. CẤU HÌNH & THƯ VIỆN MASTER RULES
# ==========================================
CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

# [LƯU Ý]: Giữ nguyên danh sách MASTER_RULES và NEXAR_MAPPING như cũ...
# (Để code ngắn gọn tôi viết gọn, bạn copy đủ danh sách như trên nhé)
NEXAR_MAPPING = {
    "Giá trị": ["resistance", "capacitance", "inductance", "resistance (ohms)", "value"],
    "Sai số": ["tolerance"],
    "Kích thước": ["package / case", "case/package", "case code - mm", "size / dimension", "supplier device package"],
    "Công suất": ["power (watts)", "power rating", "power"],
    "Điện áp": ["voltage rating", "voltage - rated", "voltage - dc reverse (vr) (max)", "voltage"],
    "Đặc tính": ["temperature coefficient", "features", "temp coefficient", "description"],
    "ESR": ["equivalent series resistance"],
    "Dòng điện": ["current rating", "current - average rectified (io)", "current"],
    "Số lượng": ["quantity"],
    "Chuẩn": ["standard"],
    "Số cực": ["number of positions", "positions"]
}

# (Copy đầy đủ MASTER_RULES vào đây như file trước của bạn)

# ==========================================
# 2. HÀM XỬ LÝ API (ĐÃ NÂNG CẤP ĐỂ TÌM KIẾM MÃ)
# ==========================================
def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: return None

def get_digikey_data(mpn, token):
    # Bước 1: Tìm kiếm mã linh kiện (Search endpoint)
    search_url = f"https://api.digikey.com/products/v4/search/{mpn}/productdetails"
    headers = {"Authorization": f"Bearer {token}", "X-DIGIKEY-Client-Id": CLIENT_ID}
    
    # Thử gọi API chi tiết
    r = requests.get(search_url, headers=headers)
    
    if r.status_code == 200:
        return r.json()
    else:
        # Nếu không thấy, thử tìm kiếm lại bằng endpoint Search cơ bản
        search_url_2 = f"https://api.digikey.com/products/v4/search?keyword={mpn}&limit=1"
        r2 = requests.get(search_url_2, headers=headers)
        if r2.status_code == 200:
            data = r2.json()
            if "Products" in data and len(data["Products"]) > 0:
                # Nếu tìm thấy, trả về thông tin sản phẩm đầu tiên
                return data["Products"][0]
    return None

def generate_standard_desc(data, prefix):
    # Logic xử lý dữ liệu trả về (cần kiểm tra cả ProductParameters hoặc list parameters)
    params = data.get("ProductParameters", [])
    spec_dict = {p.get("Parameter", "").lower(): p.get("Value", "").replace(",", "") for p in params}
    
    rule = MASTER_RULES.get(prefix)
    if not rule: return None
    
    values = []
    for attr in rule["attrs"]:
        found = "N/A"
        for key in NEXAR_MAPPING.get(attr, []):
            if key in spec_dict:
                found = spec_dict[key]
                break
        values.append(found)
    return f"{prefix};" + ",".join(values)

# ==========================================
# 3. GIAO DIỆN & VÒNG LẶP KIỂM TRA
# ==========================================
st.title("🛠️ Check Description (DigiKey API)")
# Phần báo kết nối bạn viết ở đây (giờ nó sẽ không lỗi nữa)
if st.button("🔄 Kiểm tra kết nối DigiKey"):
    token = get_token() # Lúc này get_token đã được định nghĩa nên không lỗi
    if token:
        st.success("Kết nối thành công!")
    else:
        st.error("Kết nối thất bại!")
uploaded_file = st.file_uploader("Upload BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra"):
        token = get_token()
        status_list, api_desc_list, suggest_list, note_list = [], [], [], []
        
        for _, row in df.iterrows():
            desc_eng = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
            mpn = str(row.get('Mã NSX (Tham khảo)', '')).strip()
            
            # 1. Kiểm tra tiền tố chuẩn (phải chính xác tuyệt đối như trong MASTER_RULES)
            prefix = desc_eng.split(";")[0] if ";" in desc_eng else ""
            if prefix not in MASTER_RULES:
                status_list.append("🔴 FAIL"); api_desc_list.append("-"); suggest_list.append("-")
                note_list.append(f"Sai chuẩn Tiền tố (Của bạn: {prefix})")
                continue
            
            # 2. Tìm dữ liệu
            data = get_digikey_data(mpn, token)
            if not data:
                status_list.append("🟡 UNVERIFIED"); api_desc_list.append("-"); suggest_list.append("-")
                note_list.append("Hệ thống DigiKey không tìm thấy dữ liệu cho mã này")
            else:
                # 3. So sánh
                std_desc = generate_standard_desc(data, prefix)
                if std_desc and std_desc == desc_eng:
                    status_list.append("🟢 PASS"); api_desc_list.append(std_desc); suggest_list.append(std_desc); note_list.append("Khớp 100%")
                else:
                    status_list.append("🔴 FAIL"); api_desc_list.append(std_desc if std_desc else "-"); suggest_list.append("-")
                    note_list.append("Thông số mô tả không khớp")
        
        df["Status"] = status_list
        df["Mô tả API"] = api_desc_list
        df["Suggest"] = suggest_list
        df["Note"] = note_list
        st.dataframe(df)
