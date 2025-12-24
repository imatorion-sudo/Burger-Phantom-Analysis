import streamlit as st
import pydicom
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

# 等倍表示を維持するためのCSS
st.markdown("""
    <style>
    .stCanvasContainer {
        border: 2px solid #444;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("Burger Phantom 解析ツール (サクサク判定モード)")

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
    
    # 8bit変換
    img_min, img_max = img_array.min(), img_array.max()
    img_norm = (img_array - img_min) / (img_max - img_min) * 255
    bg_image = Image.fromarray(img_norm.astype(np.uint8)).convert("RGB")
    width, height = bg_image.size

    col1, col2 = st.columns([1.5, 0.5])

    with col1:
        st.write("### 画像評価エリア")
        st.caption("クリックでマーク。リロードなしで連続入力可能です。")
        
        # キャンバスの設定（ここが重要）
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",  # 半透明の赤
            stroke_width=2,
            stroke_color="#ff0000",
            background_image=bg_image,
            update_streamlit=True,
            height=height,
            width=width,
            drawing_mode="point", # ポイント（点）を打つモード
            point_display_radius=10,
            key="canvas",
        )

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
        
        if st.button("IQF算出", type="primary"):
            iqf = sum(d * c for d, c in results.items() if c is not None)
            st.metric("IQF値", f"{iqf:.3f}")
            
            # マークした箇所の数を確認
            if canvas_result.json_data is not None:
                n_marks = len(canvas_result.json_data["objects"])
                st.write(f"マークした数: {n_marks} 箇所")
