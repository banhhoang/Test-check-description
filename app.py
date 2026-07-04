import streamlit as st
import requests
import json
import pandas as pd
import time  # 1. Thêm thư viện time

# ... (Giữ nguyên các hàm CLIENT_ID, get_token, debug_digikey_part như cũ) ...

# Giao diện
st.title("🔍 DigiKey Batch Debugger")
input_text = st.text_area("Nhập danh sách Mã NSX (mỗi mã 1 dòng):", height=200)

if st.button("🚀 Lấy dữ liệu hàng loạt"):
    mpn_list = [line.strip() for line in input_text.split('\n') if line.strip()]
    token = get_token()
    
    if not mpn_list: 
        st.warning("Vui lòng nhập mã!")
    elif not token: 
        st.error("Lỗi xác thực Token!")
    else:
        progress = st.progress(0)
        for i, mpn in enumerate(mpn_list):
            st.write(f"### Đang xử lý: {mpn}")
            
            # 2. Thêm độ trễ 1.5 giây giữa các lần gọi API
            time.sleep(1.5) 
            
            result = debug_digikey_part(mpn, token)
            
            # Xử lý kết quả an toàn
            if isinstance(result, str):
                st.error(f"Lỗi: {result}")
            elif result is None:
                st.error(f"Không tìm thấy dữ liệu cho: {mpn}")
            else:
                with st.expander(f"Xem dữ liệu thô: {mpn}"):
                    product_data = result.get("Product", {})
                    params = product_data.get("Parameters", [])
                    
                    if params:
                        debug_data = [{"ParameterName": p.get("ParameterText"), "Value": p.get("ValueText")} for p in params]
                        st.table(pd.DataFrame(debug_data))
                        st.json(params)
                    else:
                        st.warning("Tìm thấy linh kiện nhưng không có thông số kỹ thuật (Parameters).")
            
            progress.progress((i + 1) / len(mpn_list))
        st.success("Đã hoàn tất!")
