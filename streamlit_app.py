import time
import streamlit as st
from PIL import Image
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
st.caption("チャット入力欄からテキストと一緒に画像を直接添付できます。")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話を描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=300)
        if message.get("content"):
            st.markdown(message["content"])

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力してください。")
else:
    # チャット入力欄自体にファイル添付を統合 (accept_file=True)
    if prompt := st.chat_input(
        "メッセージを入力（＋ボタンで画像を添付可能）...",
        accept_file=True,
        file_type=["png", "jpg", "jpeg"],
    ):
        user_text = prompt.text
        uploaded_files = prompt.files

        img_obj = None
        if uploaded_files:
            img_obj = Image.open(uploaded_files[0])

        # ユーザーの発言を画面と履歴に保存
        user_msg = {"role": "user", "content": user_text}
        if img_obj:
            user_msg["image"] = img_obj

        st.session_state.messages.append(user_msg)

        with st.chat_message("user", avatar="👤"):
            if img_obj:
                st.image(img_obj, width=300)
            if user_text:
                st.markdown(user_text)

        # AI応答処理
        with st.chat_message("assistant", avatar="🤖"):
            try:
                client = genai.Client(api_key=gemini_api_key.strip())

                # 会話履歴（テキストのみ）を構築
                history = []
                for msg in st.session_state.messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    c_text = msg.get("content", "")
                    if c_text:
                        history.append(
                            types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=c_text)]
                            )
                        )

                # 送信データ（テキスト・画像）を準備
                contents = []
                if user_text:
                    contents.append(user_text)
                if img_obj:
                    contents.append(img_obj)
                if not contents:
                    contents = ["この画像について説明してください。"]

                models_to_try = ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
                response_stream = None
                last_error = None

                for model_name in models_to_try:
                    try:
                        chat = client.chats.create(
                            model=model_name,
                            history=history,
                        )
                        response_stream = chat.send_message_stream(contents)
                        break
                    except Exception as e:
                        last_error = e
                        if "503" in str(e) or "UNAVAILABLE" in str(e):
                            time.sleep(1)
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
                st.error(f"エラーが発生しました: {e}")
