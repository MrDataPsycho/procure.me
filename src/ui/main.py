import streamlit as st
import os

from procureme.clients.ui_client import ChatSessionClient

# Init API client
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SESSION_ENDPOINT = os.path.join(BASE_URL, "sessions")

client = ChatSessionClient(base_url=SESSION_ENDPOINT)

st.set_page_config(page_title="Procure[.]Me", layout="wide")
st.title("📄💬 Procure[.]me Contract Assistant")

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
            updated = client.rename_session(session_id=active_id, new_label=new_name)
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
    
    for msg in session_data["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me a question...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        response = client.send_chat(session_id=session_data["id"], query=user_input)
        with st.chat_message("assistant"):
            st.markdown(response["response"])
        st.rerun()
else:
    st.info("No active session. Please create a new session to begin chatting.")
