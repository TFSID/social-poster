import streamlit as st

def render_settings():
    st.title("⚙️ Settings")

    # OpenAI Config
    with st.expander("AI Configuration", expanded=True):
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.ai_service.api_key or "")
        if st.button("Save API Key"):
            st.session_state.ai_service.set_api_key(api_key)
            st.success("API Key saved!")

    st.divider()

    # Browserless Config
    with st.expander("Browserless Configuration", expanded=True):
        st.markdown("Use Browserless for cloud-based automation (Persistent Sessions).")

        # Load current config if exists in session state or service
        # For simplicity, we store this in session state for now, ideally persist to config file

        current_token = st.session_state.get("browserless_token", "")
        use_browserless = st.session_state.get("use_browserless", False)

        browserless_token = st.text_input("Browserless API Token", type="password", value=current_token)
        enable_browserless = st.checkbox("Enable Browserless Automation", value=use_browserless)

        if st.button("Save Browserless Settings"):
            st.session_state.browserless_token = browserless_token
            st.session_state.use_browserless = enable_browserless

            # Update all platform instances
            if "post_service" in st.session_state:
                for platform in st.session_state.post_service.platforms.values():
                    platform.options["browserless_token"] = browserless_token
                    platform.options["use_browserless"] = enable_browserless
                    # Also update instance attributes directly as they might be initialized
                    platform.browserless_token = browserless_token
                    platform.use_browserless = enable_browserless

            st.success("Browserless settings saved!")
