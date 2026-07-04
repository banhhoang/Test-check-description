import streamlit as st
import requests
import json

# Thông tin API của bạn
CLIENT_ID = "GhisD3uPdgME76XnklG6L28VGe1ZBKdJxb1RfFs4VV5b3Kod"
CLIENT_SECRET = "dndU2Pad5yGcCIFw1uT7vwUhZOq55pSMGBYbQkYLfSHJi7fEaF3yP5ZzGPvi0XKa"

def get_token():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}
    try:
        r = requests.post(url, data=payload)
        return r.json().get("access_token")
    except: 
        return None

st.set_page_config(layout="wide")
st.title("🕷️ Máy Quét JSON DigiKey (Debug Tool)")
st.write("Công cụ này giúp nhìn xuyên thấu cấu trúc dữ liệu trả về từ DigiKey API.")

mpn_test = st.text_input("Nhập 1 Mã NSX bất kỳ đang bị lỗi N/A (Ví dụ: CGA6M3X7S2A475M200AB):")

if st.button("🚀 Quét Dữ Liệu"):
    with st.spinner("Đang kết nối..."):
        token = get_token()
        if not token:
            st.error("Không lấy được Token API!")
        else:
            headers = {
                "Authorization": f"Bearer {token}",
                "X-DIGIKEY-Client-Id": CLIENT_ID,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-DIGIKEY-Locale-Site": "US",
                "X-DIGIKEY-Locale-Language": "en",
                "X-DIGIKEY-Locale-Currency": "USD"
            }
            
            col1, col2 = st.columns(2)
            
            # --- 1. TEST KEYWORD SEARCH API ---
            with col1:
                st.subheader("1. Dữ liệu từ Keyword Search API")
                search_url = "https://api.digikey.com/products/v4/search/keyword"
                payload = {"Keywords": mpn_test}
                r1 = requests.post(search_url, headers=headers, data=json.dumps(payload))
                
                if r1.status_code == 200:
                    st.success("Thành công (200 OK)")
                    st.json(r1.json())
                else:
                    st.error(f"Lỗi {r1.status_code}")
                    st.write(r1.text)

            # --- 2. TEST PRODUCT DETAILS API ---
            with col2:
                st.subheader("2. Dữ liệu từ Product Details API")
                detail_url = f"https://api.digikey.com/products/v4/search/{mpn_test}/productdetails"
                r2 = requests.get(detail_url, headers=headers)
                
                if r2.status_code == 200:
                    st.success("Thành công (200 OK)")
                    st.json(r2.json())
                else:
                    st.error(f"Lỗi {r2.status_code}")
                    st.write(r2.text)
