import streamlit as st
import pydicom
import numpy as np
from PIL import Image, ImageDraw

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

# 画像が勝手に縮小されないようにCSSで固定
st.markdown("""
    <style>
    /* 画像を等倍で表示し、はみ出た分はスクロールさせる */
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

# クリック履歴をセッションに保持
if "click_history" not in st.session_state:
    st.session_state.click_history = []

# --- サイドバー：規格設定 ---
st.sidebar.header("1. 規格設定")
d_min = st.sidebar.number_input("直径 最小(mm)", value=0.5, key="d_min")
d_max = st.sidebar.number_input("直径 最大(mm)", value=10.0, key="d_max")
d_num = st.sidebar.number_input("ステップ数", value=6, min_value=2, key="d_num")
DIAMETERS = np.geomspace(d_min, d_max, d_num).tolist()

c_min = st.sidebar.number_input("コントラスト 最小", value=0.1, key="c_min")
c_max = st.sidebar.number_input("コントラスト 最大", value=5.0, key="c_max")
c_num = st.sidebar.number_input("ステップ数 ", value=6, min_value=2, key="c_num")
CONTRASTS = np.geomspace(c_min, c_max, c_num).tolist()

uploaded_file = st.sidebar.file_uploader("DICOMアップロード", type=["dcm"])

if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    img_array = ds.pixel_array
    
    # 8bit正規化
    img_min, img_max = img_array.min(), img_array.max()
    img_norm = (img_array - img_min) / (img_max - img_min + 1e-5) * 255
    pil_img = Image.fromarray(img_norm.astype(np.uint8)).convert("RGB")
    
    # クリックされた座標に赤丸を描画する
    draw = ImageDraw.Draw(pil_img)
    for click in st.session_state.click_history:
        r = 8  # マーカーの半径
        draw.ellipse([click[0]-r, click[1]-r, click[0]+r, click[1]+r], outline="red", width=3)

    col1, col2 = st.columns([1.5, 0.5])

    with col1:
        st.write("### 画像評価 (クリックしてマーク)")
        if st.button("マークを全てクリア"):
            st.session_state.click_history = []
            st.rerun()

        # st.imageのクリックイベントを利用（最新機能）
        # label=Trueにすると座標が表示されます
        event = st.image(pil_img, use_container_width=False)
        
        # クリックされた時の処理
        # st.imageをクリックすると、その座標が辞書形式で返ってきます
        if event is not None and hasattr(event, "x") and hasattr(event, "y"):
            pos = (event.x, event.y)
            if pos not in st.session_state.click_history:
                st.session_state.click_history.append(pos)
                st.rerun()

    with col2:
        st.write("### 判定入力")
        results = {}
        for d in sorted(DIAMETERS, reverse=True):
            d_val = round(d, 2)
            results[d_val] = st.selectbox(
                f"直径 {d_val} mm：",
                options=[None] + [round(x, 2) for x in CONTRASTS],
                key=f"sel_{d_val}"
            )
        
        st.divider()
        if st.button("IQF算出", type="primary"):
            valid = [(d, c) for d, c in results.items() if c is not None]
            if valid:
                iqf = sum(d * c for d, c in valid)
                st.metric("算出結果 IQF", f"{iqf:.3f}")
                st.write(f"プロット数: {len(st.session_state.click_history)}")
            else:
                st.warning("値を入力してください")
