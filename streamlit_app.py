import streamlit as st
from google import genai

# Title and description
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://aistudio.google.com/)."
)

# Ask user for their Gemini API key
gemini_api_key = st.text_input("Gemini API Key", type="password")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # APIキーの前後の空白・改行を自動除去
    clean_api_key = gemini_api_key.strip()

    # 新SDKのClient初期化
    client = genai.Client(api_key=clean_api_key)

    # Session state initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("What is up?"):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # 2026年最新モデル gemini-3.8-flash に変更
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            msg_text = response.text

            with st.chat_message("assistant"):
                st.markdown(msg_text)
            st.session_state.messages.append({"role": "assistant", "content": msg_text})
        except Exception as e:
            st.error(f"APIエラーが発生しました: {e}")
