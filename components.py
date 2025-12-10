import streamlit as st
import os
import time
import pandas as pd

def render_sidebar(poster):
    st.sidebar.title("Social Poster 🚀")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Post Content", "Login Management", "Settings"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Status")

    is_x_logged_in = "x" in poster.sessions
    st.sidebar.metric("X (Twitter)", "Connected" if is_x_logged_in else "Disconnected")
    return page

def render_dashboard(history, utils):
    st.title("Dashboard")
    st.markdown("Welcome to the **Social Poster** migration.")

    total, success, failed = utils.get_post_stats(history)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Posts", total)
    col2.metric("Success", success)
    col3.metric("Failed", failed)

    st.subheader("Recent Activity")
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)

        st.subheader("Posts Over Time")
        chart_data = utils.prepare_chart_data(history)
        if not chart_data.empty:
            st.bar_chart(chart_data)
    else:
        st.info("No posts yet.")

def render_login_management(poster, x_platform, save_sessions_func):
    st.title("Login Management")

    tab1, tab2 = st.tabs(["X (Twitter)", "Other Platforms"])

    with tab1:
        st.subheader("Connect to X")
        is_x_logged_in = "x" in poster.sessions
        if is_x_logged_in:
            st.success("You are currently logged in to X.")
            if st.button("Logout from X"):
                if "x" in poster.sessions:
                    del poster.sessions["x"]
                    save_sessions_func(poster.sessions)
                    st.rerun()
        else:
            with st.form("x_login_form"):
                username = st.text_input("Username / Email")
                password = st.text_input("Password", type="password")
                two_factor = st.text_input("2FA Code (if enabled)", help="Leave empty if not required")
                submit = st.form_submit_button("Login")

                if submit:
                    if not username or not password:
                        st.error("Please provide username and password.")
                    else:
                        with st.spinner("Logging in to X... (this may take a minute)"):
                            success, msg = x_platform.login(username, password, two_factor)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    with tab2:
        st.info("Other platforms (LinkedIn, TikTok, etc.) are under migration.")

def render_post_content(x_platform):
    st.title("Create New Post")

    with st.form("post_form"):
        platforms = st.multiselect("Select Platforms", ["X (Twitter)", "LinkedIn", "Facebook"], default=["X (Twitter)"])
        post_text = st.text_area("Post Content", height=150, max_chars=280)

        uploaded_file = st.file_uploader("Attach Media", type=['png', 'jpg', 'jpeg', 'mp4'])

        col1, col2 = st.columns([1, 4])
        with col1:
            schedule = st.checkbox("Schedule")
        with col2:
            schedule_time = st.date_input("Date") if schedule else None

        submit_post = st.form_submit_button("Post Now 🚀")

        if submit_post:
            if not platforms:
                st.error("Select at least one platform.")
                return None
            elif not post_text and not uploaded_file:
                st.error("Content cannot be empty.")
                return None
            else:
                # Process File
                media_path = None
                if uploaded_file:
                    media_dir = "temp_media"
                    if not os.path.exists(media_dir):
                        os.makedirs(media_dir)
                    media_path = os.path.join(media_dir, uploaded_file.name)
                    with open(media_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                results = []
                progress_bar = st.progress(0)

                for idx, platform in enumerate(platforms):
                    if platform == "X (Twitter)":
                        with st.spinner(f"Posting to {platform}..."):
                            success, msg = x_platform.post(post_text, [media_path] if media_path else None)
                            results.append({"Platform": platform, "Status": "Success" if success else "Failed", "Message": msg, "Time": time.strftime("%Y-%m-%d %H:%M:%S")})
                    else:
                        results.append({"Platform": platform, "Status": "Skipped", "Message": "Not implemented yet", "Time": time.strftime("%Y-%m-%d %H:%M:%S")})

                    progress_bar.progress((idx + 1) / len(platforms))

                if media_path and os.path.exists(media_path):
                    os.remove(media_path)

                return results
    return None

def render_settings():
    st.title("Settings")
    st.toggle("Headless Mode", value=True, help="Run browser in background")
    st.text_input("OpenAI API Key", type="password")
    if st.button("Save Settings"):
        st.success("Settings saved!")
