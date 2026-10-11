import streamlit as st
import google.generativeai as genai

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://aistudio.google.com/)."
)

# Ask user for their Gemini API key via `st.text_input`.
gemini_api_key = st.text_input("Gemini API Key", type="password")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:

    # Configure Gemini API client.
    genai.configure(api_key=gemini_api_key)
    # モデル名を最新の安定版指定に変更
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the Gemini API.
        response = model.generate_content(prompt)
        msg_text = response.text

        # Display the response and store it in session state.
        with st.chat_message("assistant"):
            st.markdown(msg_text)
        st.session_state.messages.append({"role": "assistant", "content": msg_text})
