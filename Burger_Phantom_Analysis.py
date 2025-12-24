import streamlit as st
import pydicom
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

# CSSで画像を100%サイズで表示し、スクロール可能にする設定
st.markdown("""
    <style>
    .scroll-container {
        width: 100%;
        height: 600px;
        overflow: auto;
        border: 1px solid #ddd;
    }
    /* streamlit-image-coordinates のコンテナを強制的に等倍にする設定 */
    div[data-testid="stMarkdownContainer"] img {
        max-width: none !important;
        width: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Burger Phantom 解析ツール (等倍表示モード)")

if "clicks" not in st.session_state:
    st.session_state.clicks = []

# --- サイドバー：規格設定 ---
st.sidebar.header("1. 規格設定")
d_min = st.sidebar.number_input("直径 最小(mm)", value=0.5)
d_max = st.sidebar.number_input("直径 最大(mm)", value=10.0)
d_num = st.sidebar.number_input("ステップ数", value=6, min_value=2)
DIAMETERS = np.geomspace(d_min, d_max, d_num).tolist()

c_min = st.sidebar.number_input("コントラスト 最小", value=0.1)
c_max = st.sidebar.number_input("コントラスト 最大", value=5.0)
c_num = st.sidebar.number_input("ステップ数 ", value=6, min_value=2)
CONTRASTS = np.geomspace(c_min, c_max, c_num).tolist()

uploaded_file = st.sidebar.file_uploader("DICOMアップロード", type=["dcm"])

if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    img_array = ds.pixel_array
    
    # 画質調整（10bit/12bit -> 8bit）
    img_min, img_max = img_array.min(), img_array.max()
    img_norm = (img_array - img_min) / (img_max - img_min) * 255
    base_img = Image.fromarray(img_norm.astype(np.uint8)).convert("RGB")
    
    # 元画像のサイズを取得
    width, height = base_img.size

    col1, col2 = st.columns([1.5, 0.5])

    with col1:
        st.write(f"### 画像表示 (サイズ: {width}x{height} px)")
        st.caption("スクロールして微細なターゲットを確認してください。クリックでマーク。")
        
        if st.button("マークをリセット"):
            st.session_state.clicks = []
            st.rerun()

        # クリック済みの場所に赤丸を描画
        draw_img = base_img.copy()
        draw = ImageDraw.Draw(draw_img)
        for click in st.session_state.clicks:
            r = 15  # 100%表示に合わせて少し大きめの半径に設定
            draw.ellipse([click['x']-r, click['y']-r, click['x']+r, click['y']+r], outline="red", width=3)

        # スクロール可能なエリアを作成
        with st.container():
            # 画像を等倍(width=None)で表示するためのコンポーネント呼び出し
            value = streamlit_image_coordinates(
                draw_img,
                key="phantom_img",
                use_column_width=False # ここをFalseにすることで等倍表示を維持
            )
        
        if value is not None:
            new_click = {"x": value["x"], "y": value["y"]}
            if new_click not in st.session_state.clicks:
                st.session_state.clicks.append(new_click)
                st.rerun()

    with col2:
        st.write("### 判定入力")
        results = {}
        for d in sorted(DIAMETERS, reverse=True):
            d_label = round(d, 2)
            results[d_label] = st.selectbox(
                f"直径 {d_label} mm：",
                options=[None] + [round(x, 2) for x in CONTRASTS],
                key=f"sel_{d_label}"
            )
        
        # IQF算出
        if st.button("IQF算出", type="primary"):
            iqf = sum(d * c for d, c in results.items() if c is not None)
            st.metric("IQF値", f"{iqf:.3f}")
