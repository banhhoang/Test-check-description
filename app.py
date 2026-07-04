import streamlit as st
import requests
import json
import pandas as pd
import time

# CẤU HÌNH API
CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token") if r.status_code == 200 else None
    except:
        return None

def debug_digikey_part(mpn, token):
    headers = {
        "Authorization": f"Bearer {token}", 
        "X-DIGIKEY-Client-Id": CLIENT_ID, 
        "Content-Type": "application/json"
    }
    
    # 1. Tìm kiếm Part Number
    search_url = "https://api.digikey.com/products/v4/search/keyword"
    try:
        r = requests.post(search_url, headers=headers, data=json.dumps({"Keywords": mpn}))
        if r.status_code != 200: return f"Lỗi tìm kiếm: {r.status_code}"
        
        data = r.json()
        if not data.get("ExactMatches") and not data.get("Products"): return "Không tìm thấy linh kiện"
        
        dk_part = data["ExactMatches"][0]["DigiKeyProductNumber"] if data.get("ExactMatches") else data["Products"][0]["DigiKeyProductNumber"]
        
        # 2. Lấy chi tiết
        detail_url = f"https://api.digikey.com/products/v4/search/{dk_part}/productdetails"
        r2 = requests.get(detail_url, headers=headers)
        if r2.status_code != 200: return f"Lỗi lấy thông tin: {r2.status_code}"
        
        return r2.json()
    except Exception as e:
        return f"Lỗi hệ thống: {str(e)}"

# GIAO DIỆN
st.title("🔍 DigiKey Batch Debugger")
st.write("Nhập mã linh kiện (mỗi mã 1 dòng) để xem cấu trúc dữ liệu trả về từ DigiKey.")

input_text = st.text_area("Danh sách Mã NSX:", height=200)

if st.button("🚀 Lấy dữ liệu"):
    mpn_list = [line.strip() for line in input_text.split('\n') if line.strip()]
    token = get_token()
    
    if not mpn_list: 
        st.warning("Vui lòng nhập mã!")
    elif not token: 
        st.error("Lỗi xác thực Token! Vui lòng kiểm tra lại Client ID/Secret.")
    else:
        progress = st.progress(0)
        for i, mpn in enumerate(mpn_list):
            st.write(f"---")
            st.write(f"### Đang xử lý: {mpn}")
            
            # Đợi 1.5 giây để tránh bị chặn 429
            time.sleep(1.5) 
            
            result = debug_digikey_part(mpn, token)
            
            # Kiểm tra kết quả
            if isinstance(result, str):
                st.error(f"Lỗi: {result}")
            elif result is None:
                st.error(f"Không tìm thấy dữ liệu cho: {mpn}")
            else:
                with st.expander(f"Xem dữ liệu chi tiết: {mpn}"):
                    product_data = result.get("Product", {})
                    params = product_data.get("Parameters", [])
                    
                    if params:
                        # Hiển thị bảng thông số
                        debug_data = [{"ParameterName": p.get("ParameterText"), "Value": p.get("ValueText")} for p in params]
                        st.table(pd.DataFrame(debug_data))
                        
                        # Hiển thị JSON thô để copy
                        st.text("Dữ liệu thô (Copy phần này gửi cho tôi):")
                        st.json(params)
                    else:
                        st.warning("Tìm thấy linh kiện nhưng không có thông số (Parameters).")
            
            progress.progress((i + 1) / len(mpn_list))
        st.success("Đã hoàn tất kiểm tra!")
