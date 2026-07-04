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

# DANH SÁCH CÁC THÔNG SỐ TÙY CHỌN (Được phép thiếu ở cuối chuỗi mà không báo lỗi)
OPTIONAL_ATTRS = [
    "Chuẩn", "Special Info", "Đặc tính", "ESR", 
    "Color", "Internal Connection", "Length", "Version", "Model"
]

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
    "Số cực": ["number of positions", "positions"],
    "Số lượng điện trở": ["number of resistors"],
    "Function": ["logic type", "function", "description"],
    "Temperature": ["operating temperature", "temperature"],
    "Special Info": ["features", "packaging", "description"],
    "Voltage": ["voltage rating", "voltage - rated", "voltage"],
    "Current": ["current rating", "current", "current rating (amps)"],
    "Dimension": ["size / dimension", "package / case", "dimension"],
    "Color": ["color"],
    "Configuration": ["configuration"],
    "Internal Connection": ["internal connection"],
    "Loại Filter": ["filter type", "type"],
    "Frequency center": ["frequency - center", "frequency"],
    "Loại": ["connector type", "type"],
    "Male/Female": ["gender", "contact type"],
    "DCR": ["dc resistance (dcr)"],
    "Series inductance": ["inductance"],
    "Sort": ["type", "category"],
    "I hold": ["current - hold (ih) (max)", "hold current"],
    "Rated Voltage": ["voltage rating", "voltage - rated"],
    "Type": ["type"],
    "Fuse Size": ["size / dimension", "package / case"],
    "Termination Style": ["termination style", "mounting type"],
    "Maximum DC Voltage": ["maximum dc voltage", "voltage - working"],
    "Maximum AC Voltage": ["maximum ac voltage", "voltage - clamping"],
    "Current Surge": ["current - surge"],
    "Specification": ["specifications", "description"],
    "Switching Temperature": ["switching temperature"],
    "Memory Size": ["memory size"],
    "Length": ["length"],
    "Diameter": ["diameter"],
    "Impedance": ["impedance"],
    "AWG": ["wire gauge", "awg"],
    "Outer Diameter": ["outer diameter"],
    "Info": ["description", "features"],
    "Size": ["size / dimension"],
    "Model": ["series"],
    "Version": ["version"],
    "Name": ["description", "productdescription", "name", "series"]
}

MASTER_RULES = {
    "RES-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-VR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-SPECIAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Công suất", "Số lượng", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "RES-ARRAY": {"attrs": ["Giá trị", "Sai số", "Số lượng điện trở", "Kích thước", "Công suất", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-CER,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-TA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-TA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-ALUM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-ALUM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "ESR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn", "ESR"]},
    "CAP-CER,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Đặc tính", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-MICA,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-MICA,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-VR,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-FILM,DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-SUPER": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-ARRAY": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Điện áp", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "CAP-KITS": {"attrs": ["Giá trị", "Kích thước", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
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
    "TRANS-BJT,ARRAY": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-BJT,Pre-Bias": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "MOS-FET,ARRAY": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "RF-FET": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "TRANS-RF": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "JFET": {"attrs": ["Đặc tính", "Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "IC": {"attrs": ["Function", "Kích thước", "Temperature", "Special Info"], "trunc": ["Kích thước", "Special Info"]},
    "LED-SMD": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "LED-DIP": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "LED-IR": {"attrs": ["Voltage", "Current", "Dimension", "Color"], "trunc": ["Dimension", "Color"]},
    "LED-MATRIX": {"attrs": ["Configuration", "Dimension", "Color", "Voltage", "Internal Connection"], "trunc": ["Dimension", "Color"]},
    "LED-7SEG": {"attrs": ["Configuration", "Dimension", "Voltage", "Current", "Color"], "trunc": ["Dimension", "Current"]},
    "FILTER-SMD": {"attrs": ["Loại Filter", "Dimension", "Frequency center", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "FILTER-DIP": {"attrs": ["Loại Filter", "Dimension", "Frequency center", "Special Info"],"trunc": ["Dimension", "Special Info"]},
    "CRYSTAL": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "OSCILLATOR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "CONN-SMD": {"attrs": ["Loại", "Male/Female", "Dimension", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "CONN-DIP": {"attrs": ["Loại", "Male/Female", "Dimension", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "CONN-SPECIAL": {"attrs": ["Loại", "Male/Female", "Dimension", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "SWITCH": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "PUSH-BUTTON": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "THERMISTOR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "IND-SMD": {"attrs": ["Giá trị", "Sai số", "Kích thước", "DCR", "Dòng điện", "Chuẩn"], "trunc": ["Kích thước","Chuẩn"]},
    "IND-DIP": {"attrs": ["Giá trị", "Sai số", "Kích thước", "DCR", "Dòng điện", "Chuẩn"], "trunc": ["Kích thước","Chuẩn"]},
    "IND-VR": {"attrs": ["Giá trị", "Sai số", "Kích thước", "DCR", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "IND-ARRAY": {"attrs": ["Giá trị", "Series inductance", "DCR", "Kích thước", "Chuẩn"], "trunc": ["Kích thước", "Chuẩn"]},
    "IND-KITS": {"attrs": ["Giá trị", "Sai số", "Kích thước", "Số lượng"], "trunc": ["Sai số", "Số lượng"]},
    "RELAY": {"attrs": ["Voltage", "Current", "Dimension", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "TRANSFORMER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính", "Kích thước"]},
    "FUSE": {"attrs": ["Sort", "I hold", "Rated Voltage", "Dimension", "Type"], "trunc": ["Dimension", "Type"]},
    "FUSE-CLIP": {"attrs": ["Fuse Size", "Termination Style", "Current", "Dimension"], "trunc": ["Dimension", "Current"]},
    "FUSE-COVER": {"attrs": ["Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "ESD": {"attrs": ["Giá trị", "Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-DIODE": {"attrs": ["Công suất", "Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-HYRIST": {"attrs": ["Điện áp", "Dòng điện", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "TVS-VARISTOR": {"attrs": ["Maximum DC Voltage", "Maximum AC Voltage", "Current Surge", "Dimension", "Special Info"], "trunc": ["Dimension", "Special Info"]},
    "FERRITE BEAD": {"attrs": ["Giá trị", "Dòng điện", "Kích thước", "DCR"], "trunc": ["Kích thước", "DCR"]},
    "MODULE DIP": {"attrs": ["Name","Dimension","Special Info"], "trunc": ["Special Info","Dimension"]},
    "MODULE SMD": {"attrs": ["Name","Dimension","Special Info"], "trunc": ["Special Info","Dimension"]},
    "CHOKE SMD": {"attrs": ["Giá trị", "Dòng điện", "Kích thước", "DCR"], "trunc": ["Kích thước", "DCR"]},
    "CHOKE DIP": {"attrs": ["Giá trị", "Dòng điện", "Kích thước", "DCR"], "trunc": ["Kích thước", "DCR"]},
    "ATTENUATOR": {"attrs": ["Specification", "Special Info"], "trunc": ["Special Info"]},
    "THYRISTOR": {"attrs": ["Điện áp", "Dòng điện", "Kích thước"], "trunc": ["Kích thước"]},
    "THERMOSTAT": {"attrs": ["Switching Temperature", "Dimension"], "trunc": ["Dimension"]},
    "FAN": {"attrs": ["Điện áp", "Công suất", "Kích thước", "Đặc tính"], "trunc": ["Đặc tính", "Kích thước"]},
    "LED HOLDER": {"attrs": ["Dimension", "Color", "Special Info"], "trunc": ["Special Info"]},
    "LAMP": {"attrs": ["Điện áp", "Kích thước", "Đặc tính"], "trunc": ["Kích thước"]},
    "MEMORY CARDS": {"attrs": ["Sort", "Memory Size", "Special Info"], "trunc": ["Special Info"]},
    "CONTACTOR": {"attrs": ["Điện áp", "Dòng điện", "Đặc tính"], "trunc": ["Đặc tính"]},
    "AUXILLARY CONTACT": {"attrs": ["Đặc tính", "Số cực"], "trunc": ["Đặc tính"]},
    "MCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "MCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "RCCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "ELCB": {"attrs": ["Điện áp", "Dòng điện", "Số cực", "Đặc tính"], "trunc": ["Đặc tính"]},
    "USB CABLE": {"attrs": ["Sort", "Length", "Special Info"], "trunc": ["Special Info"]},
    "BUNCHED CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "HIGHT FREQUENCY CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "CONT CABLE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Đặc tính"]},
    "COAXIAL CABLE": {"attrs": ["Diameter", "Impedance", "Length", "Special Info"], "trunc": ["Special Info", "Length"]},
    "CONDUCTOR WIRE": {"attrs": ["Type", "AWG", "Outer Diameter", "Color", "Special Info"], "trunc": ["Color", "Special Info"]},
    "FERRITE": {"attrs": ["Kích thước", "Đặc tính"], "trunc": ["Đặc tính"]},
    "MOTOR": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "WINDOW": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "CHARGER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "EARPHONE": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "ADAPTER": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "ANTENNA": {"attrs": ["Đặc tính", "Kích thước"], "trunc": ["Kích thước"]},
    "BARE PCB ARRAY": {"attrs": ["Model", "Version"], "trunc": ["Version"]},
    "SMD FINAL": {"attrs": ["Model", "Version"], "trunc": ["Version"]},
    "PBA FINAL": {"attrs": ["Model", "Version"], "trunc": ["Version"]},
    "COMPRESSION TERMINAL": {"attrs": ["Model", "Special Info", "Kích thước"], "trunc": ["Special Info"]},
    "VINYL-RING": {"attrs": ["Type", "Model", "Kích thước", "Special Info"], "trunc": ["Special Info"]},
    "VINYL-PORK": {"attrs": ["Type", "Model", "Kích thước", "Special Info"], "trunc": ["Special Info"]},
    "VINYL-CORD": {"attrs": ["Type", "Model", "Kích thước", "Special Info"], "trunc": ["Special Info"]}
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

def get_1000pcs_price(data):
    if not data: return ""
    try:
        product_data = data.get("Product", data)
        variations = product_data.get("ProductVariations", [])
        for var in variations:
            pricing = var.get("StandardPricing", [])
            for p in pricing:
                if p.get("BreakQuantity") == 1000:
                    return f"${p.get('UnitPrice')}"
    except:
        pass
    return ""

def clean_digikey_value(val):
    if pd.isna(val) or not val or val == "N/A":
        return "N/A"
    
    val = str(val).replace(",", ".").replace("±", "").replace("µ", "u")
    
    if " (" in val:
        val = val.split(" (")[0]
        
    val = val.replace("C0G. NP0", "C0G/NP0").replace("C0G.NP0", "C0G/NP0")
    val = val.replace("C0G, NP0", "C0G/NP0").replace("C0G,NP0", "C0G/NP0")
    val = val.replace(" ", "")
    
    val = val.replace("kOhms", "KOHM").replace("Ohms", "OHM").replace("ohms", "OHM")
    val = val.replace("Ohm", "OHM").replace("ohm", "OHM").replace("mOhms", "mOHM")
    
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
                val_clean = clean_digikey_value(spec_dict[key.lower()])
                if attr == "Chuẩn" and val_clean != "Auto":
                    val_clean = "N/A"
                found = val_clean
                break
        values.append(found)
        
    # TỰ ĐỘNG ẨN THÔNG SỐ TÙY CHỌN Ở CUỐI CHUỖI
    while values and (values[-1] == "N/A" or values[-1] == "") and rule["attrs"][len(values)-1] in OPTIONAL_ATTRS:
        values.pop()
        
    return f"{prefix};" + ",".join(values)

# ==========================================
# 3. GIAO DIỆN STREAMLIT
# ==========================================
st.title("🛠️ BOM Checker & DigiKey Sync")

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
        
        format_status_list = []
        format_template_list = []
        suggest_list = []
        note_list = []
        digikey_status_list = []
        api_desc_list = []
        price_1000_list = []
        
        for _, row in df.iterrows():
            desc_eng = str(row.get('Mô tả/Yêu cầu kỹ thuật', '')).strip()
            mpn = str(row.get('Mã NSX (Tham khảo hoặc tương đương)', '')).strip()
            
            # --- 1. LOCAL FORMAT CHECK THÔNG MINH ---
            parts = desc_eng.split(";")
            prefix = parts[0].strip().upper() if len(parts) > 0 else ""
            user_params = [p.strip() for p in parts[1].split(",")] if len(parts) > 1 else []
            
            format_status = "🟢 Hợp lệ"
            format_correct_template = desc_eng
            user_parsed = {}
            
            if ";" not in desc_eng:
                format_status = "🔴 Lỗi: Thiếu dấu chấm phẩy (;) phân cách Tiền tố"
                if prefix in MASTER_RULES:
                    format_correct_template = f"{prefix};" + ",".join(MASTER_RULES[prefix]["attrs"])
                else:
                    format_correct_template = "-"
            elif prefix not in MASTER_RULES:
                possible_matches = [k for k in MASTER_RULES.keys() if k.startswith(prefix + "-") or k.startswith(prefix + ",") or k.startswith(prefix + " ")]
                
                if possible_matches:
                    suffixes = [k.replace(prefix, "") for k in possible_matches]
                    format_status = f"🔴 Lỗi: Tiền tố '{prefix}' chung chung, hãy thêm hậu tố: {', '.join(suffixes)}"
                    templates = [f"{m};..." for m in possible_matches[:2]]
                    format_correct_template = " HOẶC ".join(templates) + ("..." if len(possible_matches) > 2 else "")
                else:
                    format_status = f"🔴 Sai Tiền tố: '{prefix}' không hợp lệ"
                    format_correct_template = "-"
            else:
                rule = MASTER_RULES[prefix]
                expected_attrs = rule["attrs"]
                
                missing_all = [expected_attrs[i] for i in range(len(user_params), len(expected_attrs))]
                missing_strict = [m for m in missing_all if m not in OPTIONAL_ATTRS]
                extra = user_params[len(expected_attrs):]
                
                if missing_strict or extra:
                    err_msg = []
                    if missing_strict: err_msg.append(f"Thiếu: {', '.join(missing_strict)}")
                    if extra: err_msg.append(f"Dư: {', '.join(extra)}")
                    format_status = f"🔴 Lỗi: {'; '.join(err_msg)}"
                    
                    filled_params = user_params[:len(expected_attrs)] + ["N/A"] * len(missing_all)
                    while filled_params and filled_params[-1] == "N/A" and expected_attrs[len(filled_params)-1] in OPTIONAL_ATTRS:
                        filled_params.pop()
                        
                    format_correct_template = f"{prefix};" + ",".join(filled_params)
                else: 
                    for i, attr in enumerate(expected_attrs[:len(user_params)]):
                        user_parsed[attr] = user_params[i]

            format_status_list.append(format_status)
            format_template_list.append(format_correct_template)

            # --- 2. GỌT ĐỘ DÀI TRUNC (OFFLINE) ---
            suggestion = "-"
            if format_status == "🟢 Hợp lệ":
                if len(desc_eng) <= 40:
                    suggestion = "Độ dài đã chuẩn (<=40)"
                else:
                    current_dict = user_parsed.copy()
                    rule = MASTER_RULES[prefix]
                    temp_desc = desc_eng
                    
                    for attr_to_drop in rule["trunc"]:
                        if attr_to_drop in current_dict:
                            del current_dict[attr_to_drop]
                            rebuilt_params = [current_dict[a] for a in rule["attrs"] if a in current_dict]
                            temp_desc = f"{prefix};" + ",".join(rebuilt_params)
                            
                            if len(temp_desc) <= 40:
                                break
                                
                    if len(temp_desc) > 40:
                        suggestion = temp_desc[:37] + "..."
                    else:
                        suggestion = temp_desc
            
            suggest_list.append(suggestion)

            # --- 3. DIGIKEY API ĐỘC LẬP ---
            digikey_status = "-"
            api_desc = "-"
            current_price = ""
            
            if pd.isna(mpn) or mpn == 'nan' or mpn == "":
                digikey_status = "⚪ Trống Mã NSX"
            else:
                data = get_digikey_data(mpn, token)
                if not data:
                    digikey_status = "🔴 Không tìm thấy"
                else:
                    digikey_status = "🟢 Tồn tại"
                    current_price = get_1000pcs_price(data)
                    if prefix in MASTER_RULES:
                        api_desc = generate_standard_desc(data, prefix)
            
            digikey_status_list.append(digikey_status)
            api_desc_list.append(api_desc)
            price_1000_list.append(current_price)
            
            # --- 4. ĐỐI CHIẾU ---
            if format_status != "🟢 Hợp lệ":
                note_list.append("Cần sửa lỗi Format trước khi đối chiếu dữ liệu")
            elif digikey_status == "🟢 Tồn tại" and api_desc != "-":
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
                note_list.append("-")
        
        # --- XUẤT EXCEL ---
        df["Format Status"] = format_status_list
        df["Mô tả đúng format"] = format_template_list
        df["Đề xuất cắt (<40 ký tự)"] = suggest_list
        df["Note"] = note_list
        df["DigiKey Status"] = digikey_status_list
        df["Mô tả API"] = api_desc_list
        df["Quantity Required"] = ""
        df["1000pcs Price"] = price_1000_list
        
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Tải file BOM_Check_API_Result.xlsx", data=output, file_name="BOM_Check_API_Result.xlsx")
