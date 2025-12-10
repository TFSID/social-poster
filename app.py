import streamlit as st
import nest_asyncio

from core.post_service import PostService
from core.ai_service import AIService
from core.session_manager import SessionManager
from components.post_page import render_post_page
from components.batch_page import render_batch_page
from components.history_page import render_history_page
from components.settings_page import render_settings_page

# Patch asyncio for Streamlit
nest_asyncio.apply()

# Initialize services
if "post_service" not in st.session_state:
    st.session_state.post_service = PostService()
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "ai_service" not in st.session_state:
    st.session_state.ai_service = AIService()

st.set_page_config(page_title="Social Poster", layout="wide", page_icon="🚀")

def main():
    st.sidebar.title("🚀 Social Poster")
    page = st.sidebar.radio("Navigation", ["Post", "Batch", "History", "Settings"])

    if page == "Post":
        render_post_page()
    elif page == "Batch":
        render_batch_page()
    elif page == "History":
        render_history_page()
    elif page == "Settings":
        render_settings_page()

if __name__ == "__main__":
    main()
