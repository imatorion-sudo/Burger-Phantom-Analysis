import streamlit as st
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

st.title("Burger Phantom 解析ツール (クリック・マーカー機能付)")

# --- セッション状態の初期化 (クリック座標保存用) ---
if "clicks" not in st.session_state:
    st.session_state.clicks = []

# --- サイドバー：規格の自動生成設定 ---
st.sidebar.header("1. 規格ステップの自動生成")

def generate_steps(min_val, max_val, num_steps, mode):
    if num_steps < 2: return [min_val]
    if mode == "線形 (等間隔)":
        return np.linspace(min_val, max_val, num_steps).tolist()
    else:
        if min_val <= 0: min_val = 0.01
        return np.geomspace(min_val, max_val, num_steps).tolist()

d_min = st.sidebar.number_input("直径 最小値", value=0.5, format="%.2f", key="d_min")
d_max = st.sidebar.number_input("直径 最大値", value=10.0, format="%.2f", key="d_max")
d_num = st.sidebar.number_input("直径のステップ数", value=6, min_value=2, key="d_num")
d_mode = st.sidebar.selectbox("直径の変化方式", ["対数 (等比)", "線形 (等間隔)"], key="d_mode")

c_min = st.sidebar.number_input("コントラスト 最小値", value=0.1, format="%.2f", key="c_min")
c_max = st.sidebar.number_input("コントラスト 最大値", value=5.0, format="%.2f", key="c_max")
c_num = st.sidebar.number_input("コントラストのステップ数", value=6, min_value=2, key="c_num")
c_mode = st.sidebar.selectbox("コントラストの変化方式", ["対数 (等比)", "線形 (等間隔)"], key="c_mode")

DIAMETERS = generate_steps(d_min, d_max, d_num, d_mode)
CONTRASTS = generate_steps(c_min, c_max, c_num, c_mode)

st.sidebar.header("2. 画像の読み込み")
uploaded_file = st.sidebar.file_uploader("DICOMファイルをアップロード", type=["dcm"])

if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    # DICOMを閲覧用画像(PIL)に変換
    img_array = ds.pixel_array
    img_min, img_max = img_array.min(), img_array.max()
    img_norm = (img_array - img_min) / (img_max - img_min) * 255
    pil_img = Image.fromarray(img_norm.astype(np.uint8)).convert("RGB")

    st.subheader("視覚評価入力")
    col1, col2 = st.columns([1.2, 0.8])

    with col1:
        st.write("### 対象画像 (クリックしてマーカーを設置)")
        # クリックをリセットするボタン
        if st.button("マーカーをすべて消去"):
            st.session_state.clicks = []
            st.rerun()

        # 画像上に既存のクリック位置を描画して表示
        fig, ax = plt.subplots()
        ax.imshow(img_norm, cmap='gray')
        for click in st.session_state.clicks:
            circle = plt.Circle((click['x'], click['y']), 15, color='red', fill=False, linewidth=2)
            ax.add_patch(circle)
        ax.axis('off')
        
        # 座標取得コンポーネント
        value = streamlit_image_coordinates(pil_img, key="pil")

        if value is not None:
            new_click = {"x": value["x"], "y": value["y"]}
            if new_click not in st.session_state.clicks:
                st.session_state.clicks.append(new_click)
                st.rerun()

    with col2:
        st.write("### 判定入力")
        results = {}
        sorted_diameters = sorted(DIAMETERS, reverse=True)
        for d in sorted_diameters:
            d_label = round(d, 2)
            results[d_label] = st.selectbox(
                f"直径 {d_label} mm の列：",
                options=[None] + [round(x, 2) for x in CONTRASTS],
                key=f"sel_{d_label}"
            )

    # --- 解析実行セクション ---
    if st.button("CDダイヤグラム表示 & IQF算出", type="primary"):
        detected_d, detected_c = [], []
        iqf_sum = 0
        for d_label in sorted(results.keys()):
            c = results[d_label]
            if c is not None:
                detected_d.append(d_label)
                detected_c.append(c)
                iqf_sum += d_label * c

        if detected_d:
            st.divider()
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.write("### CDダイヤグラム")
                fig_cd, ax_cd = plt.subplots()
                ax_cd.plot(detected_d, detected_c, marker='o', color='#1f77b4')
                ax_cd.set_xscale('log'); ax_cd.set_yscale('log')
                ax_cd.invert_yaxis()
                ax_cd.grid(True, which="both", alpha=0.5)
                st.pyplot(fig_cd)

            with res_col2:
                st.write("### 算出結果")
                st.metric(label="IQF", value=f"{iqf_sum:.3f}")
                st.dataframe({"直径(D)": detected_d, "最小コントラスト(C)": detected_c})
