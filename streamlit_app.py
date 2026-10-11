import time
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI アシスタントチャット (画像認識対応)",
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

st.title("🤖 AI アシスタント (画像認識対応)")
st.caption("テキストによる会話と、画像の読み取りができるチャットボットです。")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話履歴を描画
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        # 画像が含まれている場合は表示
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=300)
        st.markdown(message["content"])

if not gemini_api_key:
    st.info("👈 サイドバーに API キーを入力してください。")
else:
    # --- 画像アップロード欄 ---
    uploaded_file = st.file_uploader("🖼️ 解析したい画像をアップロード（任意）", type=["png", "jpg", "jpeg"])
    
    if prompt := st.chat_input("メッセージを入力してください..."):
        
        # ユーザーの発言を保存・表示
        user_message_data = {"role": "user", "content": prompt}
        
        img_obj = None
        if uploaded_file is not None:
            # 画像をPillow形式で読み込み
            img_obj = Image.open(uploaded_file)
            user_message_data["image"] = img_obj
            
        st.session_state.messages.append(user_message_data)
        
        with st.chat_message("user", avatar="👤"):
            if img_obj:
                st.image(img_obj, width=300)
            st.markdown(prompt)

        # AIの返答処理
        with st.chat_message("assistant", avatar="🤖"):
            try:
                client = genai.Client(api_key=gemini_api_key.strip())

                # 文脈履歴の構築（画像は最新のプロンプトで送るため、履歴のテキストのみ抽出）
                history = []
                for msg in st.session_state.messages[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg["content"])]
                        )
                    )

                models_to_try = ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
                response_stream = None
                last_error = None

                for model_name in models_to_try:
                    try:
                        chat = client.chats.create(
                            model=model_name,
                            history=history,
                        )
                        
                        # 画像がある場合は、テキストと画像をリストにして送信
                        if img_obj:
                            response_stream = chat.send_message_stream([prompt, img_obj])
                        else:
                            response_stream = chat.send_message_stream(prompt)
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
