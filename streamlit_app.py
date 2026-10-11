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

                chat = client.chats.create(
                    model="gemini-3.8-flash",
                    history=history,
                )

                # 503エラー対策：最大3回自動リトライ
                response_stream = None
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response_stream = chat.send_message_stream(prompt)
                        break
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(2)  # 2秒待って再試行
                            continue
                        raise e
                
                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text

                full_response = st.write_stream(stream_generator)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"エラーが発生しました（少し時間を置いて再度お試しください）: {e}")
