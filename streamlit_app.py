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

# Secrets から API キーを取得（未設定時は空文字）
secrets_api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 設定")
    
    # Secrets に登録されている場合は自動読み込み
    if secrets_api_key:
        st.success("🔑 API キー（Secrets）を自動読み込みしました")
        gemini_api_key = secrets_api_key
    else:
        gemini_api_key = st.text_input(
            "Gemini API キー",
            type="password",
            placeholder="AIzaSy...",
            help="Streamlit Cloud の Secrets に GEMINI_API_KEY を設定すると手動入力が不要になります",
        )
        st.markdown("[🔑 APIキーの取得 (Google AI Studio)](https://aistudio.google.com/)")
    
    st.divider()
    
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.retry_trigger = False
        st.rerun()

st.title("🤖 AI アシスタント")
st.caption("チャット入力欄からテキストと一緒に画像を直接添付できます。")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 再送信フラグの初期化
if "retry_trigger" not in st.session_state:
    st.session_state.retry_trigger = False

# 過去の会話を描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=300)
        if message.get("content"):
            st.markdown(message["content"])

# AIに応答を生成させる共通関数
def process_ai_response(api_key):
    last_user_msg = st.session_state.messages[-1]
    user_text = last_user_msg.get("content", "")
    img_obj = last_user_msg.get("image", None)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            client = genai.Client(api_key=api_key.strip())

            # 過去の会話履歴（直前の発言を除くテキスト）を構築
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
            st.session_state.retry_trigger = False

        except Exception as e:
            st.error(f"通信エラーが発生しました: {e}")
            # 再送信ボタンの配置
            if st.button("🔄 もう一度送信する", use_container_width=True):
                st.session_state.retry_trigger = True
                st.rerun()

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力（または Secrets に登録）してください。")
else:
    # 1. 新規メッセージ入力時
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

        user_msg = {"role": "user", "content": user_text}
        if img_obj:
            user_msg["image"] = img_obj

        st.session_state.messages.append(user_msg)

        with st.chat_message("user", avatar="👤"):
            if img_obj:
                st.image(img_obj, width=300)
            if user_text:
                st.markdown(user_text)

        process_ai_response(gemini_api_key)

    # 2. 「もう一度送信する」ボタンが押されたときのリトライ実行
    elif st.session_state.retry_trigger and st.session_state.messages:
        process_ai_response(gemini_api_key)
