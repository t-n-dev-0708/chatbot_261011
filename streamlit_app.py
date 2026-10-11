import streamlit as st
from google import genai

# ページ設定
st.set_page_config(
    page_title="AI アシスタントチャット",
    page_icon="🤖",
    layout="wide",
)

# サイドバー: 設定パネル
with st.sidebar:
    st.header("⚙️ 設定")
    
    gemini_api_key = st.text_input(
        "Gemini API キー",
        type="password",
        placeholder="AIzaSy...",
        help="Google AI Studioで発行したAPIキーを入力してください",
    )
    
    st.markdown("[🔑 APIキーの取得はこちら (Google AI Studio)](https://aistudio.google.com/)")
    
    st.divider()
    
    # 会話履歴クリアボタン
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# メインヘッダー
st.title("🤖 AI アシスタント")
st.caption("Google Gemini を搭載した対話型チャットボットです。")

# セッション状態（履歴）の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話履歴を描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# APIキー未入力時の案内
if not gemini_api_key:
    st.info("👈 左側のサイドバーに Gemini API キーを入力するとチャットを開始できます。")
else:
    # クライアント初期化
    client = genai.Client(api_key=gemini_api_key.strip())

    # 入力フォーム
    if prompt := st.chat_input("メッセージを入力してください..."):
        # ユーザーの発言を記録・表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AIの返答をストリーミング生成・表示
        with st.chat_message("assistant", avatar="🤖"):
            try:
                response_stream = client.models.generate_content_stream(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )
                
                # ストリーミング書き出し
                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text

                full_response = st.write_stream(stream_generator)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
