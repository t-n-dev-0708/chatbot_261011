import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI アシスタントチャット",
    page_icon="🤖",
    layout="wide",
)

with st.sidebar:
    st.header("⚙️ 設定")
    gemini_api_key = st.text_input(
        "Gemini API キー",
        type="password",
        placeholder="AIzaSy...",
    )
    st.markdown("[🔑 APIキーの取得 (Google AI Studio)](https://aistudio.google.com/)")
    st.divider()
    
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🤖 AI アシスタント")
st.caption("文脈を理解する対話型チャットボットです。")

# 画面表示およびAPI送信用の会話履歴
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話を描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力してください。")
else:
    if prompt := st.chat_input("メッセージを入力してください..."):
        # ユーザーの発言を画面と履歴に追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AIの返答処理
        with st.chat_message("assistant", avatar="🤖"):
            try:
                # 毎リクエスト時に Client を新規作成（クローズエラーを防ぐ）
                client = genai.Client(api_key=gemini_api_key.strip())

                # これまでの全履歴（今回送信するプロンプトを除く）を Gemini 用の形式に変換
                history = []
                for msg in st.session_state.messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )

                # 過去履歴を持ったチャットセッションをその場で作成
                chat = client.chats.create(
                    model="gemini-3.8-flash",
                    history=history,
                )

                # メッセージ送信（文脈を維持したストリーミング返答）
                response_stream = chat.send_message_stream(prompt)
                
                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text

                full_response = st.write_stream(stream_generator)
                
                # AIの返答を履歴に保存
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
