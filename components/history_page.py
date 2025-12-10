import streamlit as st
import plotly.express as px
from core.history_manager import HistoryManager

def render_history_page():
    st.title("📊 History & Analytics")

    hm = HistoryManager()
    stats = hm.get_stats()

    # Top metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Posts", stats["total_posts"])
    c2.metric("Success Rate", f"{stats['success_rate']}%")

    # Charts
    df = hm.get_history()
    if not df.empty:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("Success vs Failure")
            counts = df['success'].value_counts()
            # Map 1/0 to Label
            counts.index = counts.index.map({1: 'Success', 0: 'Failure'})
            fig = px.pie(values=counts.values, names=counts.index, hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            st.subheader("Posts per Platform")
            if 'platform' in df.columns:
                fig2 = px.bar(df, x='platform', title="Platform Distribution")
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Detailed Log")
        st.dataframe(df)
    else:
        st.info("No history available yet.")
