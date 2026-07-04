import streamlit as st
import requests
import json

CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    r = requests.post(url, data=payload)
    return r.json().get("access_token") if r.status_code == 200 else None

def debug_digikey_part(mpn, token):
    headers = {"Authorization": f"Bearer {token}", "X-DIGIKEY-Client-Id": CLIENT_ID, "Content-Type": "application/json"}
    
    # 1. Tìm kiếm Part Number
    search_url = "https://api.digikey.com/products/v4/search/keyword"
    r = requests.post(search_url, headers=headers, data=json.dumps({"Keywords": mpn}))
    
    if r.status_code != 200: return f"Lỗi kết nối tìm kiếm: {r.text}"
    data = r.json()
    
    if not data.get("ExactMatches") and not data.get("Products"): return "Không tìm thấy linh kiện!"
    
    dk_part = data["ExactMatches"][0]["DigiKeyProductNumber"] if data.get("ExactMatches") else data["Products"][0]["DigiKeyProductNumber"]
    
    # 2. Lấy chi tiết
    detail_url = f"https://api.digikey.com/products/v4/search/{dk_part}/productdetails"
    r2 = requests.get(detail_url, headers=headers)
    if r2.status_code != 200: return f"Lỗi lấy thông tin: {r2.text}"
    
    return r2.json()

st.title("🔍 DigiKey Parameter Debugger")
mpn = st.text_input("Nhập Mã NSX (MPN) để debug:")

if st.button("🚀 Lấy dữ liệu thô"):
    token = get_token()
    if not token: st.error("Token lỗi!")
    else:
        result = debug_digikey_part(mpn, token)
        if isinstance(result, str): st.error(result)
        else:
            st.success("Đã lấy được dữ liệu! Đây là danh sách các thông số trả về:")
            params = result.get("Product", {}).get("Parameters", [])
            
            # Hiển thị dạng bảng cho dễ copy
            debug_data = []
            for p in params:
                debug_data.append({"ParameterName": p.get("ParameterText"), "Value": p.get("ValueText")})
            
            st.table(pd.DataFrame(debug_data))
            
            # Hiển thị JSON thô để bạn copy
            st.subheader("Dữ liệu thô (Để copy cho tôi):")
            st.json(params)
