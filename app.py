import streamlit as st
import pandas as pd
from core_logic import SocialPoster, XPlatform, save_sessions
import components
import utils

# Page Config
st.set_page_config(
    page_title="Social Poster",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State & Resources ---
@st.cache_resource
def get_poster():
    return SocialPoster(headless=True)

poster = get_poster()
x_platform = XPlatform(poster)

if 'post_history' not in st.session_state:
    st.session_state.post_history = []

# --- Main App Logic ---
page = components.render_sidebar(poster)

if page == "Dashboard":
    components.render_dashboard(st.session_state.post_history, utils)

elif page == "Login Management":
    components.render_login_management(poster, x_platform, save_sessions)

elif page == "Post Content":
    results = components.render_post_content(x_platform)
    if results:
        st.success("Operation Complete!")
        res_df = pd.DataFrame(results)
        st.table(res_df)
        st.session_state.post_history.extend(results)

elif page == "Settings":
    components.render_settings()

# Footer
st.markdown("---")
st.markdown("Migrated to Streamlit by Jules.")
