import streamlit as st
import asyncio
from core.session_manager import SessionManager

def render_login_management():
    st.title("🔐 Login Management")
    st.markdown("Manage your social media account connections here.")

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
    Triggers the interactive login flow using Local Browser (default).
    """
    status_container = st.empty()
    status_container.info(f"Opening browser for {platform_key}... Please check the new window.")

    # Force use of local browser for interactive login
    # We create a temporary platform instance with forced headless=False and use_browserless=False

    async def login_task():
        # Get the original options but override for local interactive
        original_platform = st.session_state.post_service.platforms.get(platform_key)
        if not original_platform:
            st.error("Platform not found")
            return

        # We need to ensure we don't accidentally use Browserless for this specific login action
        # even if it's enabled in settings.
        original_use_browserless = getattr(original_platform, 'use_browserless', False)
        original_platform.use_browserless = False

        try:
            success = await original_platform.login(options={"headless": False})
            return success
        finally:
            # Restore settings
            original_platform.use_browserless = original_use_browserless

    try:
        success = asyncio.run(login_task())
        if success:
            status_container.success(f"Successfully logged in to {platform_key}!")
            # Reload session manager
            st.session_state.session_manager = SessionManager()
            st.rerun()
        else:
            status_container.error(f"Login failed or timed out for {platform_key}.")
    except Exception as e:
        status_container.error(f"Error during login: {e}")
