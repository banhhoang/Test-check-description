import streamlit as st
import pandas as pd
import requests
import io
import re

# ==========================================
# 1. CẤU HÌNH & QUY TẮC (MASTER RULES)
# ==========================================
CLIENT_ID = "b0B8QFDQ7AjTD4JKkAPRtCXLeczroWN0RIstnSMak4H6lIWg"
CLIENT_SECRET = "NYMdqqKvoshhFoVYYtuMZ2NitAkcMPFiBHkm7pInrlcXR6jJU2lk3HhmXupEKNfx"

NEXAR_MAPPING = {
    "Giá trị": ["resistance", "capacitance", "inductance", "resistance (ohms)"],
    "Sai số": ["tolerance"],
    "Kích thước": ["package / case", "case/package", "case code - mm", "size / dimension", "supplier device package"],
    "Công suất": ["power (watts)", "power rating", "power"],
    "Điện áp": ["voltage rating", "voltage - rated", "voltage - dc reverse (vr) (max)", "voltage"],
    "Đặc tính": ["temperature coefficient", "features", "temp coefficient"],
    "ESR": ["equivalent series resistance"],
    "Dòng điện": ["current rating", "current - average rectified (io)", "current"],
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
# 2. HÀM XỬ LÝ DIGIKEY API
# ==========================================
def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: return None

def get_digikey_data(mpn, token):
    url = f"https://api.digikey.com/products/v4/search/{mpn}/productdetails"
    headers = {"Authorization": f"Bearer {token}", "X-DIGIKEY-Client-Id": CLIENT_ID}
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else None
    except: return None

# ==========================================
# 3. GIAO DIỆN STREAMLIT
# ==========================================
st.title("🛠️ SMT BOM Checker (DigiKey API)")
uploaded_file = st.file_uploader("Upload BOM Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if st.button("🚀 Chạy kiểm tra"):
        token = get_token()
        results = []
        for _, row in df.iterrows():
            desc = str(row.get('Mô tả/Yêu cầu kỹ thuật', ''))
            mpn = str(row.get('Mã NSX (Tham khảo)', ''))
            
            prefix = desc.split(";")[0] if ";" in desc else ""
            rule = MASTER_RULES.get(prefix)
            
            if not rule:
                results.append("Sai tiền tố")
                continue
                
            data = get_digikey_data(mpn, token)
            results.append("🟢 PASS" if data else "🔴 FAIL API")
            
        df["Result"] = results
        st.dataframe(df)
