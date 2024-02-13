from openai import OpenAI, RateLimitError
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
import time

load_dotenv()

st.title("Streamlit Chatbot Interface")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("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"))

# Ensure openai_model is initialized in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])

# Display chat messages
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Main chat interface
def call_api_with_rate_limit(client, openai_model, messages):
    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=messages,
            stream=True
        )
        return response.choices
    except RateLimitError as e:
        print("Rate limit exceeded. Waiting for some time before retrying.")
        time.sleep(10)  # Wait for 60 seconds before retrying
        return None

# Process user input and generate responses
if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        response = call_api_with_rate_limit(client, st.session_state["openai_model"], st.session_state["messages"])
        if response is not None:
            full_response = ""
            for choice in response:
                full_response += choice.delta.content or ""
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                st.markdown(full_response)

# Save chat history after each interaction
save_chat_history(st.session_state.messages)
