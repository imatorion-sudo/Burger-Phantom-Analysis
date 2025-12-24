import streamlit as st
import pydicom
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

# 画像の等倍表示を維持するCSS
st.markdown("""
    <style>
    .img-container {
        overflow: auto;
        border: 2px solid #333;
        background-color: #000;
        height: 80vh;
    }
    div[data-testid="stImage"] > img {
        max-width: none !important;
        width: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Burger Phantom 解析ツール")

# セッション状態の初期化
if "click_history" not in st.session_state:
    st.session_state.click_history = []

# --- サイドバー：規格設定 ---
st.sidebar.header("1. 規格設定")
d_min = st.sidebar.number_input("直径 最小(mm)", value=0.5, key="d_min")
d_max = st.sidebar.number_input("直径 最大(mm)", value=10.0, key="d_max")
d_num = st.sidebar.number_input("ステップ数", value=6, min_value=2, key="d_num_sb")
DIAMETERS = np.geomspace(d_min, d_max, d_num).tolist()

c_min = st.sidebar.number_input("コントラスト 最小", value=0.1, key="c_min")
c_max = st.sidebar.number_input("コントラスト 最大", value=5.0, key="c_max")
c_num = st.sidebar.number_input("ステップ数 ", value=6, min_value=2, key="c_num_sb")
CONTRASTS = np.geomspace(c_min, c_max, c_num).tolist()

uploaded_file = st.sidebar.file_uploader("DICOMアップロード", type=["dcm"])

if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    img_array = ds.pixel_array
    
    # 8bit正規化
    img_min, img_max = img_array.min(), img_array.max()
    img_norm = (img_array - img_min) / (img_max - img_min + 1e-5) * 255
    pil_img = Image.fromarray(img_norm.astype(np.uint8)).convert("RGB")
    
    # --- クリック履歴の描画 ---
    draw = ImageDraw.Draw(pil_img)
    for pos in st.session_state.click_history:
        if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
            px, py = pos['x'], pos['y']
            r = 10
            draw.ellipse([px-r, py-r, px+r, py+r], outline="red", width=3)

    col1, col2 = st.columns([1.5, 0.5])

    with col1:
        st.write("### 画像評価 (クリックでマーク)")
        if st.button("マークを全てクリア"):
            st.session_state.click_history = []
            st.rerun()

        # st.imageの戻り値を取得
        click_data = st.image(pil_img, use_container_width=False)
        
        # クリックイベントの検知
        if isinstance(click_data, dict) and 'x' in click_data and 'y' in click_data:
            if click_data not in st.session_state.click_history:
                st.session_state.click_history.append(click_data)
                st.rerun()

    with col2:
