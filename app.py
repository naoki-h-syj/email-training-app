import streamlit as st
from google import genai
import pandas as pd

st.set_page_config(page_title="ビジネスメール書き換え訓練", layout="centered")
st.title("📧 ビジネスメール書き換え訓練")
st.caption("後輩・同僚と共有できるトレーニングツールです。")

# 1. API設定
api_key = st.secrets.get("GOOGLE_API_KEY", None)
client = None

if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"APIの初期化に失敗しました: {e}")
else:
    st.error("APIキーが設定されていないか、無効です。Secretsを確認してください。")

# 2. 問題データの読み込み（ttl=0 でキャッシュの自動クリアを有効化）
@st.cache_data(ttl=0)
def load_data():
    try:
        data = pd.read_excel('problems.xlsx')
    except FileNotFoundError:
        st.error("problems.xlsx が見つかりません。ファイル名が正確か確認してください。")
        return pd.DataFrame(columns=['ID', 'Situation', 'OriginalText'])
    except Exception as e:
        st.error(f"Excelファイルの読み込みエラー: {e}")
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
        if not client:
            st.error("APIキーが読み込めていないため採点できません。")
        elif user_answer:
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
                try:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )
                    st.subheader("採点結果とフィードバック")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"採点中にエラーが発生しました: {e}")
        else:
            st.error("文章を入力してください。")
else:
    st.write("現在、問題が登録されていません。Excelファイルをアップロードしてください。")
