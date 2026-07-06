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
    
    search_url = "https://api.digikey.com/products/v4/search/keyword"
    
    for attempt in range(3):
        try:
            r = requests.post(search_url, headers=headers, data=json.dumps({"Keywords": mpn}))
            
            if r.status_code == 429:
                st.warning(f"Bị chặn (429). Đang chờ 5s để thử lại lần {attempt+1}...")
                time.sleep(5)
                continue
            
            if r.status_code != 200: return f"Lỗi tìm kiếm: {r.status_code}"
            
            data = r.json()
            
            # Lấy object sản phẩm đầu tiên tìm thấy
            product_node = None
            if data.get("ExactMatches") and len(data["ExactMatches"]) > 0:
                product_node = data["ExactMatches"][0]
            elif data.get("Products") and len(data["Products"]) > 0:
                product_node = data["Products"][0]
                
            if not product_node:
                return "Không tìm thấy dữ liệu (Danh sách rỗng)"
            
            # Nếu API trả thẳng Parameters ở đây, bọc lại và trả về luôn!
            if "Parameters" in product_node:
                return {"Product": product_node}
                
            # Nếu không có Parameters, tìm mã PartNumber để gọi API chi tiết
            dk_part = product_node.get("DigiKeyPartNumber") or product_node.get("ManufacturerPartNumber")
            
            if not dk_part:
                # Vẫn không có mã? Trả thẳng data thô ra giao diện để Debug
                return {"Product": product_node, "IS_RAW": True}
                
            detail_url = f"https://api.digikey.com/products/v4/search/{dk_part}/productdetails"
            r2 = requests.get(detail_url, headers=headers)
            
            if r2.status_code != 200: return f"Lỗi lấy chi tiết: {r2.status_code}"
            return r2.json()
            
        except Exception as e:
            return f"Lỗi hệ thống: {str(e)}"
            
    return "Lỗi: Quá nhiều yêu cầu (429), thử lại sau."

# GIAO DIỆN
st.title("🔍 DigiKey Debugger (Trùm Cuối)")
input_text = st.text_area("Nhập danh sách Mã NSX:", height=200)

if st.button("🚀 Lấy dữ liệu"):
    mpn_list = [line.strip() for line in input_text.split('\n') if line.strip()]
    token = get_token()
    
    if not mpn_list: 
        st.warning("Vui lòng nhập mã!")
    elif not token: 
        st.error("Lỗi xác thực Token!")
    else:
        for mpn in mpn_list:
            st.write(f"---")
            st.write(f"### Đang xử lý: {mpn}")
            time.sleep(2)
            
            result = debug_digikey_part(mpn, token)
            
            if isinstance(result, str):
                st.error(f"Kết quả: {result}")
            elif result is None:
                st.error(f"Không nhận được dữ liệu cho: {mpn}")
            else:
                with st.expander(f"Dữ liệu thô: {mpn}"):
                    product_data = result.get("Product", {})
                    
                    if result.get("IS_RAW"):
                        st.warning("Đây là dữ liệu thô (Không có Parameters chuẩn):")
                        st.json(product_data)
                    else:
                        params = product_data.get("Parameters", [])
                        if params:
                            st.table(pd.DataFrame([{"Parameter": p.get("ParameterText"), "Value": p.get("ValueText")} for p in params]))
                            st.json(params)
                        else:
                            st.warning("Linh kiện hợp lệ nhưng hãng không cung cấp thông số (Parameters).")
                            st.json(product_data) # In ra để xem có trường nào khác thay thế không
