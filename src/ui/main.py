import streamlit as st
import os
from PIL import Image
from pathlib import Path

from procureme.clients.ui_client import ChatSessionClient
from procureme.__about__ import __version__




# Init API client
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SESSION_ENDPOINT = os.path.join(BASE_URL, "sessions")

client = ChatSessionClient(base_url=SESSION_ENDPOINT)

logo_path = Path("static").joinpath("logo.png")
logo = Image.open(logo_path)

st.set_page_config(page_title="Procure[.]Me", layout="wide")
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image(logo, use_container_width=True)
st.markdown("<h5 style='text-align: center;'>AI-Powered Contracting & Procurement Intelligence</h5>", unsafe_allow_html=True)


# --- Init State ---
if "session_list" not in st.session_state:
    st.session_state.session_list = client.list_sessions()

if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = st.session_state.session_list[0]["id"] if st.session_state.session_list else None

# --- Sidebar: Session Management ---
st.sidebar.header("🗂 Chat Sessions")

# New session
with st.sidebar.expander("➕ Create New Session"):
    new_label = st.text_input("Session Label", key="new_label")
    if st.button("Create Session"):
        if new_label.strip():
            new_sess = client.create_session(label=new_label.strip())
            st.session_state.session_list.insert(0, {"id": new_sess["id"], "label": new_sess["label"]})
            st.session_state.active_session_id = new_sess["id"]
            st.rerun()
        else:
            st.warning("Please enter a session label.")

# Session list
for sess in st.session_state.session_list:
    sess_id = sess["id"]
    label = sess["label"]
    is_active = sess_id == st.session_state.active_session_id
    label_display = f"{'✅' if is_active else '📁'} {label}"
    if st.sidebar.button(label_display, key=f"session-{sess_id}"):
        st.session_state.active_session_id = sess_id
        st.rerun()

# Rename / Delete / Export
if st.session_state.active_session_id:
    active_id = st.session_state.active_session_id
    session_data = client.get_session(session_id=active_id)

    with st.sidebar.expander("🛠 Session Options"):
        new_name = st.text_input("Rename Session", value=session_data["label"], key="rename_input")
        if st.button("✏️ Rename"):
            updated = client.update_session_label(session_id=active_id, label=new_name)
            for sess in st.session_state.session_list:
                if sess["id"] == active_id:
                    sess["label"] = updated["label"]
            st.rerun()

        if st.button("🗑 Delete Session"):
            client.delete_session(session_id=active_id)
            st.session_state.session_list = [s for s in st.session_state.session_list if s["id"] != active_id]
            st.session_state.active_session_id = st.session_state.session_list[0]["id"] if st.session_state.session_list else None
            st.rerun()


# --- Main Chat UI ---
if st.session_state.active_session_id:
    session_data = client.get_session(session_id=st.session_state.active_session_id)
    st.subheader(f"💬 Chat: **{session_data['label']}** (`{session_data['id']}`)")

    messages = session_data["messages"]

    # Featured questions if no chat yet
    if not messages:
        st.info("Try asking one of the featured questions:")
        col1, col2, col3 = st.columns(3)
        featured_questions = [
            "What do you know about Supplier: Alpha Suppliers Inc. and what it supplies?",
            "what is the difference between the contract CW0307 and CW0343",
            "Provide me a long summery of the contract number CW0307"
        ]
        for i, col in enumerate((col1, col2, col3)):
            if col.button(featured_questions[i]):
                st.session_state.featured_input = featured_questions[i]
                st.rerun()

    # Display past messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Get user input (manual or from featured button)
    user_input = st.chat_input("Ask me a question...")
    if "featured_input" in st.session_state:
        user_input = st.session_state.pop("featured_input")

    # Process user input
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("Thinking..."):
            response = client.send_chat(session_id=session_data["id"], query=user_input)

        with st.chat_message("assistant"):
            st.markdown(response["response"])
        st.rerun()
else:
    st.info("No active session. Please create a new session to begin chatting.")

st.sidebar.markdown(
    f"""
    <hr style="margin-top: 50px;">
    <div style="text-align: center; font-size: 12px; color: grey;">
        Procure[.]Me • Version {__version__}
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.image(logo, width=100, use_container_width=True)