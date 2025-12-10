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
                handle_interactive_login_click(platform_key)

def handle_interactive_login_click(platform_key: str):
    """Handle login click, dispatching to local or browserless flow."""
    use_browserless = st.session_state.get("use_browserless", False)

    if use_browserless:
        handle_browserless_login(platform_key)
    else:
        handle_local_login(platform_key)

def handle_local_login(platform_key: str):
    """Legacy local interactive login."""
    status_container = st.empty()
    status_container.info(f"Opening local browser for {platform_key}...")

    async def login_task():
        platform = st.session_state.post_service.platforms.get(platform_key)
        if not platform: return False

        # Force local settings
        orig_headless = platform.headless
        orig_browserless = platform.use_browserless

        platform.headless = False
        platform.use_browserless = False

        try:
            success = await platform.login(options={"headless": False})
            return success
        finally:
            platform.headless = orig_headless
            platform.use_browserless = orig_browserless

    try:
        success = asyncio.run(login_task())
        if success:
            status_container.success(f"Successfully logged in to {platform_key}!")
            st.session_state.session_manager = SessionManager()
            st.rerun()
        else:
            status_container.error("Login failed/timed out.")
    except Exception as e:
        status_container.error(f"Error: {e}")

def handle_browserless_login(platform_key: str):
    """Browserless interactive login flow."""
    status_container = st.empty()
    link_container = st.empty()

    platform = st.session_state.post_service.platforms.get(platform_key)
    if not platform:
        status_container.error("Platform not found.")
        return

    # Check for token
    token = st.session_state.get("browserless_token")
    if not token:
        status_container.error("Browserless Token missing in Settings.")
        return

    # Ensure platform has the token
    platform.browserless_token = token

    status_container.info(f"Starting Browserless session for {platform_key}...")

    async def start_session():
        return await platform.login_interactive_browserless()

    debugger_url, browser, page = asyncio.run(start_session())

    if not debugger_url:
        status_container.error("Failed to start Browserless session.")
        return

    link_container.markdown(f"### [🔴 Click here to Open Interactive Login]({debugger_url})", unsafe_allow_html=True)
    status_container.info("Waiting for login... (Please login in the opened tab)")

    # Polling loop
    # We need to run the polling in an async loop
    async def poll_login():
        start_time = time.time()
        timeout = 300 # 5 mins

        try:
            while (time.time() - start_time) < timeout:
                if await platform.is_logged_in(page):
                    await platform.save_session(page, platform_key)
                    return True
                await asyncio.sleep(2)
            return False
        finally:
            # Cleanup
            if browser:
                await browser.close()
                # Also explicitly stop session via API if needed, but close() might handle connection
                if platform.browserless_session_id:
                     await platform.stop_browserless_session(platform.browserless_session_id, token)

    success = asyncio.run(poll_login())

    if success:
        status_container.success(f"Successfully logged in to {platform_key}!")
        link_container.empty()
        st.session_state.session_manager = SessionManager()
        st.rerun()
    else:
        status_container.error("Login timed out.")
        link_container.empty()
