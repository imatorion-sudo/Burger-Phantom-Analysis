import streamlit as st
import pydicom
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Burger Phantom Analysis")

st.title("Burger Phantom 解析ツール")
st.caption("直径とコントラストの規格を自由設定してIQFを算出できます")

# --- サイドバー設定 ---
st.sidebar.header("1. 規格の設定")

# 直径の入力を受け付ける（デフォルト値を設定）
d_input = st.sidebar.text_input("直径のステップ (mm) [カンマ区切り]", "0.3, 0.5, 1.0, 2.0, 4.0, 7.0")
# コントラスト（深さ）の入力を受け付ける
c_input = st.sidebar.text_input("コントラスト/深さのステップ [カンマ区切り]", "0.1, 0.2, 0.5, 1.0, 2.0, 5.0")

# 入力文字列を数値リストに変換
try:
    DIAMETERS = sorted([float(x.strip()) for x in d_input.split(",")], reverse=True)
    CONTRASTS = sorted([float(x.strip()) for x in c_input.split(",")])
except ValueError:
    st.sidebar.error("数値とカンマのみを入力してください。")
    st.stop()

st.sidebar.header("2. 画像の読み込み")
uploaded_file = st.sidebar.file_uploader("DICOMファイルをアップロード", type=["dcm"])

# --- メインコンテンツ ---
if uploaded_file:
    ds = pydicom.dcmread(uploaded_file)
    # 窓幅・窓レベルの適用（簡易版）
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
        st.write("### 判定入力マトリクス")
        st.info("各直径において、識別できた「最小のコントラスト値」を選択してください。")
        
        results = {}
        # 入力された規格に基づいて入力フォームを動的に生成
        for d in sorted(DIAMETERS):
            results[d] = st.selectbox(
                f"直径 {d} mm の列：",
                options=[None] + CONTRASTS,
                format_func=lambda x: "未選択 (見えない)" if x is None else f"最小コントラスト: {x}",
                key=f"sel_{d}"
            )

    # --- 解析ボタン ---
    if st.button("CDダイヤグラム表示 & IQF算出", type="primary"):
        detected_d = []
        detected_c = []
        iqf_sum = 0

        for d in sorted(DIAMETERS):
            c = results[d]
            if c is not None:
                detected_d.append(d)
                detected_c.append(c)
                iqf_sum += d * c

        if detected_d:
            st.divider()
            res_col1, res_col2 = st.columns(2)

            with res_col1:
                st.write("### CDダイヤグラム")
                fig_cd, ax_cd = plt.subplots()
                ax_cd.plot(detected_d, detected_c, marker='o', markersize=8, linestyle='-', linewidth=2, color='#1f77b4')
                
                # 両軸対数グラフ
                ax_cd.set_xscale('log')
                ax_cd.set_yscale('log')
                
                ax_cd.set_xlabel("Diameter (mm) [Log scale]")
                ax_cd.set_ylabel("Contrast Step [Log scale]")
                ax_cd.invert_yaxis()  # 低コントラスト（数値が小さい）を上に
                ax_cd.grid(True, which="both", ls="-", alpha=0.5)
                
                st.pyplot(fig_cd)

            with res_col2:
                st.write("### 算出結果")
                st.metric(label="IQF (Image Quality Figure)", value=f"{iqf_sum:.3f}")
                
                # 詳細データテーブル
                summary_data = {"直径(D)": detected_d, "最小コントラスト(C)": detected_c}
                st.table(summary_data)
                
                # 簡単な判定評価
                st.write("**解析メモ:**")
                st.write(f"- 解析に使用したステップ数: {len(detected_d)} / {len(DIAMETERS)}")
                st.write("- IQFは、各直径での最小可視コントラストの積の総和です。")

        else:
            st.warning("評価データが入力されていません。マトリクスから選択してください。")
else:
    st.info("サイドバーからDICOMファイルをアップロードしてください。")
