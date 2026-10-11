import streamlit as st
import google.generativeai as genai

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

    # Configure API key
    genai.configure(api_key=gemini_api_key)
    
    # Model specification
    model = genai.GenerativeModel("gemini-1.5-flash")

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

        # Generate response
        response = model.generate_content(prompt)
        msg_text = response.text

        with st.chat_message("assistant"):
            st.markdown(msg_text)
        st.session_state.messages.append({"role": "assistant", "content": msg_text})
