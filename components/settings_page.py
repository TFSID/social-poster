import streamlit as st
import asyncio
from core.session_manager import SessionManager

def render_settings_page():
    st.title("⚙️ Settings & Accounts")

    # OpenAI Config
    with st.expander("AI Configuration", expanded=True):
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.ai_service.api_key or "")
        if st.button("Save API Key"):
            st.session_state.ai_service.set_api_key(api_key)
            st.success("API Key saved!")

    st.divider()

    # Account Connections
    st.subheader("Connect Accounts")

    col1, col2 = st.columns(2)

    with col1:
        render_platform_login_card("x", "X (Twitter)")

    with col2:
        render_platform_login_card("facebook", "Facebook")

def render_platform_login_card(platform_key: str, platform_label: str):
    """Render a card for platform login status and action."""
    sm = st.session_state.session_manager
    is_connected = sm.is_session_valid(platform_key)

    with st.container(border=True):
        st.markdown(f"### {platform_label}")
        if is_connected:
            st.success("✅ Connected")
            if st.button(f"Disconnect {platform_label}"):
                sm.clear_session(platform_key)
                st.rerun()
        else:
            st.warning("⚠️ Not Connected")
            if st.button(f"Login to {platform_label} (Interactive)"):
                handle_interactive_login(platform_key)

def handle_interactive_login(platform_key: str):
    """
    Triggers the interactive login flow.
    """
    status_container = st.empty()
    status_container.info(f"Opening browser for {platform_key}... Please check the new window.")

    # We run this asynchronously
    async def login_task():
        platform_instance = st.session_state.post_service.platforms.get(platform_key)
        if not platform_instance:
            st.error("Platform not found")
            return

        # Launch login with headless=False
        success = await platform_instance.login(options={"headless": False})
        return success

    try:
        success = asyncio.run(login_task())
        if success:
            status_container.success(f"Successfully logged in to {platform_key}!")
            # Reload session manager to pick up new file
            st.session_state.session_manager = SessionManager()
            st.rerun()
        else:
            status_container.error(f"Login failed or timed out for {platform_key}.")
    except Exception as e:
        status_container.error(f"Error during login: {e}")
