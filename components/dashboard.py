import streamlit as st
from core.history_manager import HistoryManager

def render_dashboard():
    st.title("📊 Dashboard")

    hm = HistoryManager()
    stats = hm.get_stats()

    # Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Posts", stats.get("total_posts", 0))
    col2.metric("Success Rate", f"{stats.get('success_rate', 0)}%")

    # Recent Activity
    st.subheader("Recent Activity")
    df = hm.get_history()
    if not df.empty:
        st.dataframe(df.head(5))
    else:
        st.info("No recent activity.")
