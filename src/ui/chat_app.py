import streamlit as st
import requests

# API endpoint
API_URL = "http://localhost:8000/chat"  # Adjust if hosted remotely

st.set_page_config(page_title="Procure.me Chat", layout="wide")
st.title("📄💬 Procure.me Contract Assistant")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat display
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Ask me a question about your contracts...")

if user_input:
    # Add user input to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("Processing...", show_time=True):
            response = requests.post(API_URL, json={"query": user_input})
        response.raise_for_status()
        result = response.json()

        answer = result.get("response", "⚠️ No response")
        success = result.get("success", False)
        sources = result.get("sources", [])

        answer_markdown = f"**Answer:**\n\n{answer}"
        if success and sources:
            answer_markdown += "\n\n---\n**Sources:**"
            for src in sources:
                title = src.get("document_title", "Unknown")
                section = src.get("section_text", "")
                answer_markdown += f"\n- *{title}*: `{section}`"

        st.session_state.chat_history.append({"role": "assistant", "content": answer_markdown})
        with st.chat_message("assistant"):
            st.markdown(answer_markdown)

    except requests.RequestException as e:
        st.error(f"❌ API request failed: {e}")