import streamlit as st
import pydicom
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

st.title("Burger Phantom 解析ツール")
st.caption("規格範囲を入力してステップを自動生成します")

# --- サイドバー：規格の自動生成設定 ---
st.sidebar.header("1. 規格ステップの自動生成")

def generate_steps(min_val, max_val, num_steps, mode):
    if mode == "線形 (等間隔)":
        return np.linspace(min_val, max_val, num_steps).tolist()
    else:  # 対数 (等比間隔)
        return np.geomspace(min_val, max_val, num_steps).tolist()

# 直径の設定
st.sidebar.subheader("直径 (Diameter) 設定")
d_min = st.sidebar.number_value("直径 最小値", value=0.5, format="%.2f")
d_max = st.sidebar.number_value("直径 最大値", value=10.0, format="%.2f")
d_num = st.sidebar.number_input("直径のステップ数", value=6, min_value=2)
d_mode = st.sidebar.selectbox("直径の変化方式", ["対数 (等比)", "線形 (等間隔)"])

# コントラストの設定
st.sidebar.subheader("コントラスト (Contrast) 設定")
c_min = st.sidebar.number_value("コントラスト 最小値", value=0.1, format="%.2f")
c_max = st.sidebar.number_value("コントラスト 最大値", value=5.0, format="%.2f")
c_num = st.sidebar.number_input("コントラストのステップ数", value=6, min_value=2)
c_mode = st.sidebar.selectbox("コントラストの変化方式", ["対数 (等比)", "線形 (等間隔)"])

# ステップの生成
DIAMETERS = generate_steps(d_min, d_max, d_num, d_mode)
CONTRASTS = generate_steps(c_min, c_max, c_num, c_mode)

st.sidebar.write("---")
st.sidebar.write("**生成された直径:**", [round(x, 2) for x in DIAMETERS])
st.sidebar.write("**生成されたコントラスト:**", [round(x, 2) for x in CONTRASTS])

st.sidebar.header("2. 画像の読み込み")
uploaded_file = st.sidebar.file_uploader("DICOMファイルをアップロード", type=["dcm"])

# --- メインコンテンツ ---
if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    img = ds.pixel_array
    
    st.subheader("視覚評価入力")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### 対象画像")
        fig_img, ax_img = plt.subplots(figsize=(5, 5))
        ax_img.imshow(img, cmap='gray')
        ax_img.axis('off')
        st.pyplot(fig_img)

    with col2:
        st.write("### 判定入力")
        st.info("各直径において識別できた「最小コントラスト」を選択。")
        
        results = {}
        # 自動生成された直径リストに基づいて入力を作成
        for d in sorted(DIAMETERS, reverse=True):
            d_label = round(d, 2)
            results[d_label] = st.selectbox(
                f"直径 {d_label} mm の列：",
                options=[None] + [round(x, 2) for x in CONTRASTS],
                key=f"sel_{d_label}"
            )

    if st.button("CDダイヤグラム表示 & IQF算出", type="primary"):
        detected_d = []
        detected_c = []
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
                ax_cd.plot(detected_d, detected_c, marker='o', markersize=8, color='#1f77b4')
                ax_cd.set_xscale('log')
                ax_cd.set_yscale('log')
                ax_cd.set_xlabel("Diameter (mm)")
                ax_cd.set_ylabel("Contrast")
                ax_cd.invert_yaxis()
                ax_cd.grid(True, which="both", ls="-", alpha=0.5)
                st.pyplot(fig_cd)

            with res_col2:
                st.write("### 算出結果")
                st.metric(label="IQF (Image Quality Figure)", value=f"{iqf_sum:.3f}")
                
                # CSVダウンロード機能の追加
                csv_data = "Diameter(mm),MinContrast\n" + "\n".join([f"{d},{c}" for d, c in zip(detected_d, detected_c)])
                st.download_button(
                    label="結果をCSVでダウンロード",
                    data=csv_data,
                    file_name="iqf_result.csv",
                    mime="text/csv"
                )
        else:
            st.warning("評価を入力してください。")
