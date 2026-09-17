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

# 2. 問題データの読み込み
@st.cache_data(ttl=0)
def load_data():
    try:
        data = pd.read_excel('problems.xlsx')
    except FileNotFoundError:
        st.error("problems.xlsx が見つかりません。")
        return pd.DataFrame(columns=['ID', 'Situation', 'OriginalText'])
    except Exception as e:
        st.error(f"Excelファイルの読み込みエラー: {e}")
        return pd.DataFrame(columns=['ID', 'Situation', 'OriginalText'])
    return data

df = load_data()

# 3. アプリ画面の構成
if not df.empty:
    options = [f"{row['ID']} {row['Situation']}" for _, row in df.iterrows()]
    selected_option = st.selectbox("練習問題を選択してください", options)
    
    selected_index = options.index(selected_option)
    target_row = df.iloc[selected_index]

    st.info(f"**【状況設定】**\n\n{target_row['Situation']}")
    st.warning(f"**【修正前の原文】**\n\n{target_row['OriginalText']}")

    # keyに問題IDを含めることで、問題を切り替えた際に入力内容がクリアされるように設定
    user_answer = st.text_area(
        "ビジネスで使用できる内容に変換してください（書き換え・返信のどちらでも可）",
        height=200,
        key=f"user_answer_{target_row['ID']}"
    )

    if st.button("採点する", key=f"btn_{target_row['ID']}"):
        if not client:
            st.error("APIキーが読み込めていないため採点できません。")
        elif user_answer:
            with st.spinner('AIが採点中...'):
                prompt = f"""
                あなたは企業の教育担当者です。
                受講者が作成した文章（「修正後の文」）を採点してください。
                なお、受講者の回答は「修正前原文のトゲを抜いた書き換え文」または「修正前原文に対するプロフェッショナルな返信文」のいずれかの形式で入力されます。どちらの形式であっても適切に評価してください。

                【状況設定】: {target_row['Situation']}
                【修正前の原文】: {target_row['OriginalText']}
                【ユーザーの入力文】: {user_answer}

                【採点・フィードバックの基準】
                1. 感情の抑制：相手を責めたり突き放したりするニュアンスが消え、冷静かつ礼儀正しいか
                2. 意図の明確化：具体的かつ失礼のない表現で目的や要望が伝わっているか
                3. 建設的な提案・配慮：解決に向けた前向きな姿勢、代替案、または返信としての配慮（挨拶・労い等）が含まれているか

                【出力フォーマット】
                - 総合評価（例：A / B / C または 100点満点中の点数）
                - 良かった点
                - 改善できる点・アドバイス
                - より良い表現例（書き換え例または返信例）
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
