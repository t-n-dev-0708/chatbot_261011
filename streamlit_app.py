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

secrets_api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 設定")
    
    if secrets_api_key:
        st.success("🔑 API キー（Secrets）自動読み込み完了")
        gemini_api_key = secrets_api_key
    else:
        gemini_api_key = st.text_input(
            "Gemini API キー",
            type="password",
            placeholder="AIzaSy...",
        )
        st.markdown("[🔑 APIキーの取得 (Google AI Studio)](https://aistudio.google.com/)")
    
    st.divider()

    # 手動モデル選択肢
    selected_model = st.selectbox(
        "優先モデル",
        ["auto (自動フォールバック)", "gemini-1.5-flash", "gemini-2.5-flash", "gemini-3.8-flash"],
        index=0,
        help="autoの場合は gemini-3.8-flash -> 1.5-flash -> 2.5-flash の順で自動切替します"
    )
    
    st.divider()
    
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.retry_trigger = False
        st.rerun()

st.title("🤖 AI アシスタント")
st.caption("テキストおよび画像の添付に対応したチャットボットです。")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_trigger" not in st.session_state:
    st.session_state.retry_trigger = False

# 過去ログ描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=300)
        if message.get("content"):
            st.markdown(message["content"])

def process_ai_response(api_key, model_option):
    last_user_msg = st.session_state.messages[-1]
    user_text = last_user_msg.get("content", "")
    img_obj = last_user_msg.get("image", None)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            client = genai.Client(api_key=api_key.strip())

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

            # モデル選択ロジック（autoの場合は3.8->1.5->2.5の順で試し、503や429が出たら切り替え）
            if model_option == "auto (自動フォールバック)":
                models_to_try = ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
            else:
                models_to_try = [model_option, "gemini-1.5-flash", "gemini-2.5-flash"]

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
                    err_str = str(e)
                    # 503 (混雑) または 429 / RESOURCE_EXHAUSTED (利用枠上限) の場合は別モデルへ回避
                    if any(k in err_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "Quota exceeded"]):
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
            if st.button("🔄 もう一度送信する", use_container_width=True):
                st.session_state.retry_trigger = True
                st.rerun()

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力（または Secrets に登録）してください。")
else:
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

        process_ai_response(gemini_api_key, selected_model)

    elif st.session_state.retry_trigger and st.session_state.messages:
        process_ai_response(gemini_api_key, selected_model)
