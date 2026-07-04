import streamlit as st
import requests
import json
import pandas as pd

CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    r = requests.post(url, data=payload)
    return r.json().get("access_token") if r.status_code == 200 else None

def debug_digikey_part(mpn, token):
    headers = {"Authorization": f"Bearer {token}", "X-DIGIKEY-Client-Id": CLIENT_ID, "Content-Type": "application/json"}
    
    # 1. Search
    search_url = "https://api.digikey.com/products/v4/search/keyword"
    r = requests.post(search_url, headers=headers, data=json.dumps({"Keywords": mpn}))
    if r.status_code != 200: return f"Lỗi tìm kiếm: {r.status_code}"
    
    data = r.json()
    if not data.get("ExactMatches") and not data.get("Products"): return None
    
    dk_part = data["ExactMatches"][0]["DigiKeyProductNumber"] if data.get("ExactMatches") else data["Products"][0]["DigiKeyProductNumber"]
    
    # 2. Get Detail
    detail_url = f"https://api.digikey.com/products/v4/search/{dk_part}/productdetails"
    r2 = requests.get(detail_url, headers=headers)
    return r2.json() if r2.status_code == 200 else None

st.title("🔍 DigiKey Batch Debugger")
input_text = st.text_area("Nhập danh sách Mã NSX (mỗi mã 1 dòng):", height=200)

if st.button("🚀 Lấy dữ liệu hàng loạt"):
    mpn_list = [line.strip() for line in input_text.split('\n') if line.strip()]
    token = get_token()
    
    if not mpn_list: st.warning("Vui lòng nhập mã!")
    elif not token: st.error("Lỗi xác thực Token!")
    else:
        progress = st.progress(0)
        for i, mpn in enumerate(mpn_list):
            st.write(f"### Đang xử lý: {mpn}")
            result = debug_digikey_part(mpn, token)
            
            if not result:
                st.error(f"Không tìm thấy dữ liệu cho: {mpn}")
            else:
                with st.expander(f"Xem dữ liệu thô: {mpn}"):
                    params = result.get("Product", {}).get("Parameters", [])
                    debug_data = [{"ParameterName": p.get("ParameterText"), "Value": p.get("ValueText")} for p in params]
                    st.table(pd.DataFrame(debug_data))
                    st.json(params)
            
            progress.progress((i + 1) / len(mpn_list))
        st.success("Đã hoàn tất!")
