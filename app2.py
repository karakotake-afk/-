from datetime import datetime
import os
import pandas as pd
import streamlit as st

# 自動保存先のCSVファイル名
CSV_FILE = "accounting_data.csv"


# ------------------------------------
# CSVの読み込み・書き出し（保存）関数
# ------------------------------------
def load_data():
  """CSVファイルが存在すれば読み込み、なければ空のデータを作成"""
  if os.path.exists(CSV_FILE):
    return pd.read_csv(CSV_FILE, dtype={"備考(領収書番号等)": str})
  else:
    return pd.DataFrame(
        columns=["日付", "区分", "項目名", "金額", "備考(領収書番号等)"]
    )


def save_data(df):
  """データフレームをCSVファイルに自動書き出し（保存）"""
  df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


# ページの基本設定
st.set_page_config(page_title="Web会計管理ソフト", layout="wide")

# ------------------------------------
# ★ カスタムCSSによる文字サイズ拡大設定
# ------------------------------------
st.markdown(
    """
    <style>
    /* 1. 入力項目の見出しラベル（「収支区分」「日付」など） */
    .stWidgetLabel, label, div[data-testid="stWidgetLabel"] p {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
    }

    /* 2. 入力ボックス内部のテキスト（文字・数字・日付入力欄） */
    input {
        font-size: 1.2rem !important;
        height: 2.8rem !important;
    }

    /* 3. ドロップダウン（セレクトボックス）内のテキスト */
    div[data-baseweb="select"] {
        font-size: 1.2rem !important;
    }

    /* 4. ラジオボタンの選択肢（「収入」「支出」） */
    div[role="radiogroup"] label p {
        font-size: 1.2rem !important;
    }

    /* 5. 「登録する」ボタンのテキスト */
    div[data-testid="stFormSubmitButton"] button {
        font-size: 1.3rem !important;
        font-weight: bold !important;
        padding: 0.6rem 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💰 Webベース 会計管理アプリ")

# アプリ起動時にCSVファイルからデータを自動読み込み
if "data" not in st.session_state:
  st.session_state.data = load_data()

# ------------------------------------
# 1. データの入力エリア
# ------------------------------------
st.header("📝 データの入力")

with st.form("accounting_form", clear_on_submit=True):
  col1, col2 = st.columns(2)

  with col1:
    trans_type = st.radio("収支区分", ["収入", "支出"], horizontal=True)
    trans_date = st.date_input("日付", datetime.now())

    category_options = [
        "売上",
        "給与収入",
        "雑収入",
        "仕入",
        "旅費交通費",
        "通信費",
        "消耗品費",
        "接待交際費",
        "水道光熱費",
        "地代家賃",
        "雑費",
        "その他（手入力）",
    ]
    selected_category = st.selectbox("項目名（カテゴリ）", category_options)

    if selected_category == "その他（手入力）":
      item_name = st.text_input("自由入力（項目名）", placeholder="例: 会議費")
    else:
      item_name = selected_category

  with col2:
    amount = st.number_input("金額 (円)", min_value=0, step=100)
    memo = st.text_input(
        "備考欄（領収書・レシート番号、メモなど）", placeholder="例: 10023"
    )

  submit_button = st.form_submit_button("登録する")

# 登録ボタンが押されたとき
if submit_button:
  if amount > 0:
    final_item_name = item_name if item_name.strip() != "" else "未設定"

    new_data = pd.DataFrame([{
        "日付": trans_date.strftime("%Y-%m-%d"),
        "区分": trans_type,
        "項目名": final_item_name,
        "金額": amount,
        "備考(領収書番号等)": memo,
    }])

    st.session_state.data = pd.concat(
        [st.session_state.data, new_data], ignore_index=True
    )
    save_data(st.session_state.data)

    st.success("登録し、CSVファイルに保存しました！")
  else:
    st.warning("金額を入力してください。")

st.divider()

# ------------------------------------
# 2. 合計と収支の確認エリア
# ------------------------------------
st.header("📊 収支状況（現時点の合計）")

df = st.session_state.data

if not df.empty:
  total_income = df[df["区分"] == "収入"]["金額"].sum()
  total_expense = df[df["区分"] == "支出"]["金額"].sum()
else:
  total_income = 0
  total_expense = 0

balance = total_income - total_expense

col_inc, col_exp, col_bal = st.columns(3)
col_inc.metric("収入合計", f"{total_income:,} 円")
col_exp.metric("支出合計", f"{total_expense:,} 円")
col_bal.metric(
    "収支差額 (収入 - 支出)",
    f"{balance:,} 円",
    delta=f"{balance:,} 円",
    delta_color="normal" if balance >= 0 else "inverse",
)

# ------------------------------------
# 3. 履歴の確認・項目別集計・ダウンロード
# ------------------------------------
st.subheader("📋 入力履歴一覧")
if not df.empty:
  st.dataframe(df, use_container_width=True)

  with st.expander("💡 項目ごとの合計金額を見る"):
    summary_df = (
        df.groupby(["区分", "項目名"])["金額"]
        .sum()
        .reset_index()
        .sort_values(by=["区分", "金額"], ascending=[False, False])
    )
    st.dataframe(summary_df, use_container_width=True)

  csv = df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      label="📥 CSV形式でダウンロード（手動出力用）",
      data=csv,
      file_name=f"accounting_{datetime.now().strftime('%Y%m%d')}.csv",
      mime="text/csv",
  )
else:
  st.info("まだデータが登録されていません。")