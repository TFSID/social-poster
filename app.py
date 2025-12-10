import streamlit as st
import nest_asyncio

from core.post_service import PostService
from core.ai_service import AIService
from core.session_manager import SessionManager

# Import Components
from components.dashboard import render_dashboard
from components.post_content import render_post_page
from components.post_management import render_batch_page
from components.login_management import render_login_management
from components.settings import render_settings
from components.history import render_history_page

# Patch asyncio for Streamlit
nest_asyncio.apply()

# Initialize services
if "post_service" not in st.session_state:
    st.session_state.post_service = PostService()
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "ai_service" not in st.session_state:
    st.session_state.ai_service = AIService()

# Initialize settings state
if "browserless_token" not in st.session_state:
    st.session_state.browserless_token = ""
if "use_browserless" not in st.session_state:
    st.session_state.use_browserless = False

st.set_page_config(page_title="Social Poster", layout="wide", page_icon="🚀")

def main():
    st.sidebar.title("🚀 Social Poster")

    # Navigation
    page = st.sidebar.radio("Menu", [
        "Dashboard",
        "Post Content",
        "Post Management",
        "Login Management",
        "Settings",
        "History"
    ])

    if page == "Dashboard":
        render_dashboard()
    elif page == "Post Content":
        render_post_page()
    elif page == "Post Management":
        render_batch_page()
    elif page == "Login Management":
        render_login_management()
    elif page == "Settings":
        render_settings()
    elif page == "History":
        render_history_page()

if __name__ == "__main__":
    main()
