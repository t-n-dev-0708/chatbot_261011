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
    
    # リセット時にチャットセッションも消去する
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        st.rerun()

st.title("🤖 AI アシスタント")
st.caption("文脈を理解する対話型チャットボットです。")

# 画面表示用の履歴
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
    client = genai.Client(api_key=gemini_api_key.strip())

    # --- 文脈保持用（Chat Session）の初期化 ---
    if "chat_session" not in st.session_state:
        # Streamlit再起動時に画面履歴(messages)からAPI用の履歴(History)を復元する
        api_history = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            api_history.append(types.Content(role=role, parts=[types.Part.from_text(msg["content"])]))
        
        # 履歴を持った状態でセッションを作成
        st.session_state.chat_session = client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                temperature=0.7,
            ),
            history=api_history
        )

    if prompt := st.chat_input("メッセージを入力してください..."):
        # 画面にユーザーの発言を追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AIの返答処理（send_message_streamを使うことで文脈が維持される）
        with st.chat_message("assistant", avatar="🤖"):
            try:
                response_stream = st.session_state.chat_session.send_message_stream(prompt)
                
                def stream_generator():
                    for chunk in response_stream:
                        yield chunk.text

                full_response = st.write_stream(stream_generator)
                
                # 画面用の履歴に保存
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
