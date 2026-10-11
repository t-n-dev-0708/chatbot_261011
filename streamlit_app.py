import time
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

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力してください。")
else:
    if prompt := st.chat_input("メッセージを入力してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            try:
                client = genai.Client(api_key=gemini_api_key.strip())

                history = []
                for msg in st.session_state.messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )

                # 混雑時に試すモデルの候補リスト（順次フォールバック）
                models_to_try = ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
                response_stream = None
                last_error = None

                for model_name in models_to_try:
                    try:
                        chat = client.chats.create(
                            model=model_name,
                            history=history,
                        )
                        response_stream = chat.send_message_stream(prompt)
                        break  # 成功したらループを抜け出す
                    except Exception as e:
                        last_error = e
                        if "503" in str(e) or "UNAVAILABLE" in str(e):
                            time.sleep(1)  # 1秒待って次のモデルを試す
                            continue
                        raise e

                if response_stream is None:
                    raise last_error

                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text

                full_response = st.write_stream(stream_generator)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error("現在GoogleのAPIサーバーが世界的に大変混雑しています。10〜20秒ほど置いて再度メッセージをお送りください。")
