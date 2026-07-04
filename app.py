import streamlit as st
import pandas as pd
import requests
import io
import json
import re

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
    "Điện áp": ["voltage rating", "voltage - rated", "voltage - dc reverse (vr) (max)", "voltage", "drain to source voltage (vdss)", "voltage - breakdown (min)", "voltage - zener (nom) (vz)"],
    "Đặc tính": ["temperature coefficient", "features", "temp coefficient", "description", "fet type", "diode type", "transistor type"],
    "ESR": ["equivalent series resistance", "esr (equivalent series resistance)", "dc resistance (dcr)"],
    "Dòng điện": ["current rating", "current rating (amps)", "current - average rectified (io)", "current", "current - continuous drain (id) @ 25°c", "current - max"],
    "Số lượng": ["quantity"],
    "Chuẩn": ["standard", "ratings"],
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

def clean_digikey_value(val):
    if pd.isna(val) or not val or val == "N/A":
        return "N/A"
    
    val = str(val)
    val = val.replace(",", ".")
    val = val.replace("±", "").replace("µ", "u")
    
    if " (" in val:
        val = val.split(" (")[0]
        
    val = val.replace("C0G. NP0", "C0G/NP0").replace("C0G.NP0", "C0G/NP0")
    val = val.replace("C0G, NP0", "C0G/NP0").replace("C0G,NP0", "C0G/NP0")
    val = val.replace(" ", "")
    
    val = val.replace("kOhms", "KOHM").replace("Ohms", "OHM").replace("ohms", "OHM")
    val = val.replace("Ohm", "OHM").replace("ohm", "OHM")
    val = val.replace("mOhms", "mOHM")
    
    if val == "AEC-Q200":
        return "Auto"
        
    match = re.match(r"^([\d\.]+)([a-zA-Z]+)$", val)
    if match:
        num_str = match.group(1)
        unit = match.group(2).upper()
        try:
            num = float(num_str)
            if unit == "PF" and num >= 1000:
                num = num / 1000
                unit = "NF"
            elif unit == "NF" and num >= 1000:
                num = num / 1000
                unit = "UF"
            elif unit == "V" and num >= 1000:
                num = num / 1000
                unit = "KV"
            
            if num.is_integer():
                num_str = str(int(num))
            else:
                num_str = str(num)
            
            if unit == "PF": unit = "pF"
            elif unit == "NF": unit = "nF"
            elif unit == "UF": unit = "uF"
            elif unit == "KV": unit = "kV"
            elif unit == "V": unit = "V"
            
            val = num_str + unit
        except ValueError:
            pass

    return val

def generate_standard_desc(data, prefix):
    if not data: return None
    
    product_data = data.get("Product", data)
    params = product_data.get("Parameters", [])
    
    spec_dict = {}
    for p in params:
        key = p.get("ParameterText", "") or p.get("Parameter", "")
        if isinstance(key, dict): 
            key = key.get("Name", "")
            
        if key:
            val = p.get("ValueText", "") or p.get("Value", "")
            spec_dict[key.lower()] = val
            
    rule = MASTER_RULES.get(prefix)
    if not rule: return None
    
    values = []
    for attr in rule["attrs"]:
        found = "N/A"
        for key in NEXAR_MAPPING.get(attr, []):
            if key.lower() in spec_dict:
                found = clean_digikey_value(spec_dict[key.lower()])
                break
        values.append(found)
        
    return f"{prefix};" + ",".join(values)

# ==========================================
# 3. GIAO DIỆN STREAMLIT
# ==========================================
st.title("🛠️ Check Description & DigiKey API")

st.subheader("Trạng thái kết nối API")
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
    if st.button("🚀 Chạy kiểm tra toàn diện"):
        token = get_token()
        
        # Tạo danh sách chứa kết quả cho các cột mới
        format_status_list = []
        digikey_status_list = []
        api_desc_list = []
        suggest_list = []
        note_list = []
        
        for _, row in df.iterrows():
            desc_eng = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
            mpn = str(row.get('Mã NSX (Tham khảo hoặc tương đương)', '')).strip()
            
            # -------------------------------------------------------------
            # BƯỚC 1: KIỂM TRA ĐỊNH DẠNG MÔ TẢ (LOCAL - KHÔNG DÙNG API)
            # -------------------------------------------------------------
            format_status = "🟢 Hợp lệ"
            format_note = ""
            user_parsed = {}
            prefix = ""
            
            if ";" not in desc_eng:
                format_status = "🔴 Sai cấu trúc"
                format_note = "Thiếu dấu chấm phẩy (;) phân cách Tiền tố"
            else:
                parts = desc_eng.split(";")
                prefix = parts[0].strip().upper()
                params_str = parts[1]
                
                if prefix not in MASTER_RULES:
                    format_status = "🔴 Sai Tiền tố"
                    format_note = f"Tiền tố '{prefix}' không tồn tại trong Rules"
                else:
                    rule = MASTER_RULES[prefix]
                    expected_attrs = rule["attrs"]
                    user_params = [p.strip() for p in params_str.split(",")]
                    
                    if len(user_params) != len(expected_attrs):
                        format_status = "🔴 Dư/Thiếu thông số"
                        format_note = f"Yêu cầu {len(expected_attrs)} thông số ({', '.join(expected_attrs)}). Của bạn có {len(user_params)}."
                    else:
                        # Map thông số của user thành Dict để dành cho bước Gọt độ dài
                        for i, attr in enumerate(expected_attrs):
                            user_parsed[attr] = user_params[i]
                            
            format_status_list.append(format_status)

            # -------------------------------------------------------------
            # BƯỚC 2: GỌT ĐỘ DÀI MÔ TẢ THEO TRUNC RULES (DÙNG DỮ LIỆU CỦA BẠN)
            # -------------------------------------------------------------
            suggestion = "-"
            if format_status == "🟢 Hợp lệ":
                if len(desc_eng) <= 40:
                    suggestion = desc_eng
                else:
                    current_dict = user_parsed.copy()
                    rule = MASTER_RULES[prefix]
                    temp_desc = desc_eng
                    
                    # Lần lượt xóa từng thuộc tính nằm trong danh sách trunc
                    for attr_to_drop in rule["trunc"]:
                        if attr_to_drop in current_dict:
                            del current_dict[attr_to_drop]
                            # Xếp lại chuỗi mô tả sau khi xóa
                            rebuilt_params = [current_dict[a] for a in rule["attrs"] if a in current_dict]
                            temp_desc = f"{prefix};" + ",".join(rebuilt_params)
                            
                            # Nếu độ dài đã đạt chuẩn <= 40 thì dừng thuật toán
                            if len(temp_desc) <= 40:
                                break
                                
                    # Nếu xóa hết list trunc mà vẫn > 40 thì đặt dấu ...
                    if len(temp_desc) > 40:
                        suggestion = temp_desc[:37] + "..."
                    else:
                        suggestion = temp_desc
            
            suggest_list.append(suggestion)

            # -------------------------------------------------------------
            # BƯỚC 3: CHECK DIGIKEY API ĐỘC LẬP
            # -------------------------------------------------------------
            digikey_status = "-"
            api_desc = "-"
            
            if pd.isna(mpn) or mpn == 'nan' or mpn == "":
                digikey_status = "⚪ Trống Mã NSX"
            else:
                data = get_digikey_data(mpn, token)
                if not data:
                    digikey_status = "🔴 Không tìm thấy"
                else:
                    digikey_status = "🟢 Tồn tại"
                    if prefix in MASTER_RULES:
                        api_desc = generate_standard_desc(data, prefix)
                    else:
                        api_desc = "Lỗi Tiền tố (Không thể render format)"
            
            digikey_status_list.append(digikey_status)
            api_desc_list.append(api_desc)
            
            # -------------------------------------------------------------
            # BƯỚC 4: TỔNG HỢP GHI CHÚ
            # -------------------------------------------------------------
            if format_status != "🟢 Hợp lệ":
                note_list.append(format_note)
            elif digikey_status == "🟢 Tồn tại" and "Lỗi Tiền tố" not in api_desc:
                # Đối chiếu dữ liệu của bạn và API
                clean_desc_eng = desc_eng.replace(" ", "").upper()
                clean_api_desc = str(api_desc).replace(" ", "").upper()
                
                is_match = False
                if "C0G/NP0" in clean_api_desc:
                    alt_desc_1 = clean_api_desc.replace("C0G/NP0", "C0G")
                    alt_desc_2 = clean_api_desc.replace("C0G/NP0", "NP0")
                    if (clean_api_desc == clean_desc_eng) or (alt_desc_1 == clean_desc_eng) or (alt_desc_2 == clean_desc_eng):
                        is_match = True
                else:
                    is_match = (clean_api_desc == clean_desc_eng)

                if is_match:
                    note_list.append("Khớp 100% với dữ liệu hãng DigiKey")
                else:
                    note_list.append("Cảnh báo: Thông số BOM và thông số API lệch nhau")
            else:
                note_list.append("Chưa có đủ dữ liệu DigiKey để đối chiếu")
        
        # Add Columns to DataFrame
        df["Format Status"] = format_status_list
        df["DigiKey Status"] = digikey_status_list
        df["Mô tả API"] = api_desc_list
        df["Suggest (<40 ký tự)"] = suggest_list
        df["Note"] = note_list
        
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Tải file BOM_Check_API_Result.xlsx", data=output, file_name="BOM_Check_API_Result.xlsx")
