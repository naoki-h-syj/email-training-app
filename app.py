import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. API設定
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("APIキーが設定されていないか、無効です。")

st.set_page_config(page_title="ビジネスメール書き換え訓練", layout="centered")
st.title("📧 ビジネスメール書き換え訓練")
st.caption("後輩・同僚と共有できるトレーニングツールです。")

# 2. 問題データの読み込み（メンテナンス性重視）
@st.cache_data
def load_data():
    # CSVを読み込み。ファイルがない場合は空のデータを作成
    try:
        data = pd.read_csv('problems.csv', encoding='utf-8')
    except FileNotFoundError:
        st.error("problems.csvが見つかりません。")
        return pd.DataFrame(columns=['ID', 'Situation', 'OriginalText'])
    return data

df = load_data()

# 3. アプリ画面の構成
if not df.empty:
    selected_id = st.selectbox("練習問題を選択してください", df['ID'].tolist())
    target_row = df[df['ID'] == selected_id].iloc[0]

    st.info(f"**【状況設定】**\n\n{target_row['Situation']}")
    st.warning(f"**【修正前のトゲがある文】**\n\n{target_row['OriginalText']}")

    user_answer = st.text_area("修正後のプロフェッショナルな文章を入力してください", height=200)

    if st.button("採点する"):
        if user_answer:
            with st.spinner('AIが採点中...'):
                prompt = f"""
                あなたは企業の教育担当者です。
                「修正前の文」に含まれる感情的なトゲを抜き、ビジネスとして適切な「修正後の文」に書き換えられているか採点してください。

                【採点基準】
                1. 感情の抑制：相手を責めたり突き放したりするニュアンスが消え、冷静か
                2. 意図の明確化：具体的かつ失礼のない表現で要望が伝わるか
                3. 建設的な提案：解決に向けた前向きな姿勢や代替案が含まれているか

                【修正前の文】: {target_row['OriginalText']}
                【修正後の文】: {user_answer}
                """
                response = model.generate_content(prompt)
                st.subheader("採点結果とフィードバック")
                st.write(response.text)
        else:
            st.error("文章を入力してください。")
else:
    st.write("現在、問題が登録されていません。CSVファイルをアップロードしてください。")
