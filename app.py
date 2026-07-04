import streamlit as st
import pandas as pd
import requests
import io
import json

# ==========================================
# 1. CẤU HÌNH & THƯ VIỆN MASTER RULES
# ==========================================
CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

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

MASTER_RULES = {
    "RES-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-VR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-SPECIAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-ARRAY": {"attrs": ["Giá trị", "Sai số", "Công suất", "Kích thước", "Đặc tính", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP ALUM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-CER,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP ALUM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP MICA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-MICA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-SUPER": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-ARRAY": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "DIODE-SWITCHING": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-SCHOTTKY": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-ARRAY": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-RECTIFIER": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-BRIDGE": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-SURGE ABSORBER": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-FAST": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-VAR": {"attrs": ["Điện áp", "Giá trị", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "DIODE-ZENER": {"attrs": ["Điện áp", "Công suất", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-BJT": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-POWER": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-DIGITAL": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "MOS-FET": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-BJT ARRAY": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-BJT Pre-Bias": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "MOS-FET ARRAY": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "RF-FET": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-RF": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "JFET": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "IC": {"attrs": ["Đặc tính", "Kích thước", "Điện áp"], "trunc": ["Đặc tính", "Kích thước"]},
    "LED-SMD": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "LED-DIP": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "LED-IR": {"attrs": ["Kích thước"], "trunc": ["Kích thước"]},
    "LED-MATRIX": {"attrs": ["Đặc tính", "Kích thước", "Điện áp"], "trunc": ["Kích thước"]},
    "LED-7SEG": {"attrs": ["Đặc tính", "Kích thước", "Điện áp"], "trunc": ["Kích thước"]},
    "FILTER-SMD": {"attrs": ["Đặc tính", "Giá trị", "Kích thước", "Điện áp"], "trunc": ["Kích thước", "Đặc tính"]},
    "FILTER-DIP": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "CRYSTAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "OSCILLATOR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "CONN-SMD": {"attrs": ["Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "CONN-DIP": {"attrs": ["Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "CONN-SPECIAL": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "SWITCH": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "PUSH-BUTTON": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "THERMISTOR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "IND-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Dòng điện", "Chuẩn"], "trunc": ["Chuẩn", "Kích thước"]},
    "IND-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Dòng điện", "Chuẩn"], "trunc": ["Chuẩn", "Kích thước"]},
    "IND-VR": {"attrs": ["Giá trị", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "IND-ARRAY": {"attrs": ["Giá trị", "Kích thước", "Dòng điện"], "trunc": ["Kích thước"]},
    "IND-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Số lượng"], "trunc": ["Sai số", "Số lượng"]},
    "RELAY": {"attrs": ["Dòng điện", "Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANSFORMER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "FUSE": {"attrs": ["Dòng điện", "Điện áp", "Kích thước"], "trunc": ["Kích thước"]},
    "FUSE-CLIP": {"attrs": ["Đặc tính", "Điện áp", "Kích thước"], "trunc": ["Kích thước"]},
    "FUSE-COVER": {"attrs": ["Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "ESD": {"attrs": ["Giá trị", "Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-DIODE": {"attrs": ["Công suất", "Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-HYRIST": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-VARISTOR": {"attrs": ["Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "FB": {"attrs": ["Giá trị", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "MODULE DIP": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "MODULE SMD": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "LCD MODULE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "MIC MODULE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "RECEIVER MODULE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "CAMERA MODULE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "SPEAKER MODULE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "CHOKE SMD": {"attrs": ["Giá trị", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "CHOKE DIP": {"attrs": ["Giá trị", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "ATTENUATOR": {"attrs": ["Đặc tính", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "THYRISTOR": {"attrs": ["Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "THERMOSTAT": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "FAN": {"attrs": ["Điện áp", "Công suất", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "LED HOLDER": {"attrs": ["Kích thước", "Đặc tính"], "trunc": ["Đặc tính"]},
    "LAMP": {"attrs": ["Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "MEMORY CARDS": {"attrs": ["Đặc tính", "Giá trị"], "trunc": ["Đặc tính"]},
    "CONTACTOR": {"attrs": ["Điện áp", "Dòng điện", "Đặc tính"], "trunc": ["Đặc tính"]},
    "AUXILLARY CONTACT": {"attrs": ["Đặc tính", "Số cực"], "trunc": ["Đặc tính"]},
    "MCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "MCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "RCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "ELCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "USB CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "BUNCHED CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "HIGHT FREQUENCY CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "CONT CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "COAXIAL CABLE": {"attrs": ["Giá trị", "Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "CONDUCTOR WIRE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "FERRITE": {"attrs": ["Kích thước", "Đặc tính"], "trunc": ["Đặc tính"]},
    "MOTOR": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "WINDOW": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "CHARGER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "EARPHONE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "ADAPTER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "ANTENNA": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "BARE PCB ARRAY": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "SMD FINAL": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "PHA FINAL": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "COMPRESSION TERMINAL": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "VINYL INSULATED TERMINAL": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]}
}

# ==========================================
# 2. HÀM XỬ LÝ DỮ LIỆU TỪ DIGIKEY API V4
# ==========================================
def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: 
        return None

def get_digikey_data(mpn, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-DIGIKEY-Client-Id": CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-DIGIKEY-Locale-Site": "US",
        "X-DIGIKEY-Locale-Language": "en",
        "X-DIGIKEY-Locale-Currency": "USD"
    }
    
    search_url = "https://api.digikey.com/products/v4/search/keyword"
    payload = {"Keywords": mpn}
    dk_part_num = mpn
    
    try:
        r = requests.post(search_url, headers=headers, data=json.dumps(payload))
        if r.status_code == 200:
            search_data = r.json()
            if search_data.get("ExactMatches") and len(search_data["ExactMatches"]) > 0:
                dk_part_num = search_data["ExactMatches"][0].get("DigiKeyProductNumber", mpn)
            elif search_data.get("Products") and len(search_data["Products"]) > 0:
                dk_part_num = search_data["Products"][0].get("DigiKeyProductNumber", mpn)
    except:
        pass
        
    detail_url = f"https://api.digikey.com/products/v4/search/{dk_part_num}/productdetails"
    try:
        r2 = requests.get(detail_url, headers=headers)
        if r2.status_code == 200:
            return r2.json()
    except:
        pass
        
    return None

def generate_standard_desc(data, prefix):
    if not data: return None
    
    # Ở API v4 ProductDetails, mọi thông số đều nằm trong object "Product"
    product_data = data.get("Product", data)
    params = product_data.get("Parameters", [])
    
    spec_dict = {}
    for p in params:
        # Lấy theo chuẩn ParameterText và ValueText như log bạn gửi
        key = p.get("ParameterText", "") or p.get("Parameter", "")
        if isinstance(key, dict): 
            key = key.get("Name", "")
            
        if key:
            val = p.get("ValueText", "") or p.get("Value", "")
            spec_dict[key.lower()] = str(val).replace(",", "")
            
    rule = MASTER_RULES.get(prefix)
    if not rule: return None
    
    values = []
    for attr in rule["attrs"]:
        found = "N/A"
        for key in NEXAR_MAPPING.get(attr, []):
            if key.lower() in spec_dict:
                found = spec_dict[key.lower()]
                break
        values.append(found)
        
    return f"{prefix};" + ",".join(values)

def get_suggestion(desc, prefix):
    return desc[:37] + "..." if len(desc) > 40 else desc

# ==========================================
# 3. GIAO DIỆN STREAMLIT
# ==========================================
st.title("🛠️ Check Description (DigiKey API)")

st.subheader("Trạng thái hệ thống")
status_col1, status_col2 = st.columns([1, 4])

with status_col1:
    if 'digikey_token' not in st.session_state:
        st.write("🟢 API: **Sẵn sàng**")
    else:
        st.write("🟢 API: **Đã kết nối**")

if st.button("🔄 Kiểm tra kết nối DigiKey"):
    with st.spinner("Đang thử kết nối..."):
        token = get_token()
        if token:
            st.session_state['digikey_token'] = token
            st.success("Kết nối thành công tới máy chủ DigiKey!")
        else:
            st.error("Kết nối thất bại. Kiểm tra lại Client ID và Secret!")

uploaded_file = st.file_uploader("Upload BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra"):
        token = get_token()
        status_list, api_desc_list, suggest_list, note_list = [], [], [], []
        
        for _, row in df.iterrows():
            desc_eng = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
            mpn = str(row.get('Mã NSX (Tham khảo hoặc tương đương)', '')).strip()
            
            prefix = desc_eng.split(";")[0].strip().upper() if ";" in desc_eng else ""
            
            if pd.isna(mpn) or mpn == 'nan' or mpn == "":
                status_list.append("🔴 FAIL"); api_desc_list.append("-"); suggest_list.append("-"); note_list.append("Dòng này bị bỏ trống Mã NSX nên không thể tra cứu API")
                continue
                
            if ";" not in desc_eng:
                status_list.append("🔴 FAIL"); api_desc_list.append("-"); suggest_list.append("-"); note_list.append("Lỗi format: Thiếu dấu chấm phẩy (;)")
                continue
                
            if prefix not in MASTER_RULES:
                status_list.append("🔴 FAIL"); api_desc_list.append("-"); suggest_list.append("-"); note_list.append(f"Sai chuẩn Tiền tố (Của bạn: {desc_eng.split(';')[0]})")
                continue
            
            data = get_digikey_data(mpn, token)
            
            if not data:
                status_list.append("🟡 UNVERIFIED"); api_desc_list.append("-"); suggest_list.append("-"); note_list.append("Không tìm thấy dữ liệu trên DigiKey (Check lại mã NSX)")
            else:
                std_desc = generate_standard_desc(data, prefix)
                if std_desc == desc_eng.upper():
                    if len(std_desc) <= 40:
                        status_list.append("🟢 PASS"); api_desc_list.append(std_desc); suggest_list.append(std_desc); note_list.append("Khớp 100% với dữ liệu hãng")
                    else:
                        status_list.append("🟡 WARNING"); api_desc_list.append(std_desc); suggest_list.append(get_suggestion(std_desc, prefix)); note_list.append("Mô tả đúng cấu trúc API nhưng vượt 40 ký tự.")
                else:
                    status_list.append("🔴 FAIL"); api_desc_list.append(std_desc); suggest_list.append("-"); note_list.append("Thông số mô tả không khớp với thông số thực tế của Mã NSX từ API")
        
        df["Status"] = status_list
        df["Mô tả API"] = api_desc_list
        df["Suggest"] = suggest_list
        df["Note"] = note_list
        
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Tải file BOM_Check_API_Result.xlsx", data=output, file_name="BOM_Check_API_Result.xlsx")
