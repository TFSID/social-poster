import streamlit as st
import asyncio
from core.session_manager import SessionManager
import time

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
                handle_browserless_login(platform_key)

def handle_browserless_login(platform_key: str):
    """Browserless interactive login flow."""
    status_container = st.empty()
    link_container = st.empty()

    platform = st.session_state.post_service.platforms.get(platform_key)
    if not platform:
        status_container.error("Platform not found.")
        return

    # Check for token (mandatory now)
    token = st.session_state.get("browserless_token")
    if not token:
        status_container.error("Browserless Token missing in Settings. Please configure it first.")
        return

    # Ensure platform has the token
    platform.browserless_token = token
    # Re-init service if needed (hacky but safe)
    from core.browserless import BrowserlessService
    platform.service = BrowserlessService(token)

    status_container.info(f"Starting Browserless session for {platform_key}...")

    async def start_session():
        return await platform.login_interactive_browserless()

    live_url, session_id, ws_url = asyncio.run(start_session())

    if not live_url:
        status_container.error("Failed to start Browserless session.")
        return

    link_container.markdown(f"### [🔴 Click here to Open Live Browser]({live_url})", unsafe_allow_html=True)
    status_container.info(f"Waiting for login... Please navigate to {platform.base_url} in the opened tab and log in.")

    # Polling loop
    async def poll_login():
        start_time = time.time()
        timeout = 300 # 5 mins

        try:
            while (time.time() - start_time) < timeout:
                if await platform.check_login_status(ws_url):
                    # Get cookies
                    cookies = await platform.service.get_cookies(ws_url)
                    if cookies:
                        # Save session
                        session_data = {
                            "cookies": cookies,
                            "lastValidated": asyncio.get_event_loop().time() # timestamp
                        }
                        # We need to adapt session manager to accept this format or normalize it
                        # For now, simplistic save
                        st.session_state.session_manager.set_session(platform_key, session_data)
                        return True
                await asyncio.sleep(5)
            return False
        finally:
            # Cleanup
            if session_id:
                 await platform.service.stop_session(session_id)

    success = asyncio.run(poll_login())

    if success:
        status_container.success(f"Successfully logged in to {platform_key}!")
        link_container.empty()
        # Force reload session manager
        st.session_state.session_manager = SessionManager()
        st.rerun()
    else:
        status_container.error("Login timed out.")
        link_container.empty()
