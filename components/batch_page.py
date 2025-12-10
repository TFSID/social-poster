import streamlit as st
import pandas as pd
import asyncio

def render_batch_page():
    st.title("📦 Batch Posting")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())

        col_text = st.selectbox("Select Text Column", df.columns)
        col_link = st.selectbox("Select Link Column (Optional)", ["None"] + list(df.columns))

        platforms = st.session_state.post_service.get_supported_platforms()
        selected_platforms = st.multiselect("Target Platforms", platforms)

        if st.button("Start Batch Process"):
            if not selected_platforms:
                st.error("Select platforms first.")
                return

            progress_bar = st.progress(0)
            status_text = st.empty()
            results_table = st.empty()

            results_data = []

            for index, row in df.iterrows():
                status_text.text(f"Processing row {index + 1}/{len(df)}...")

                content = {"text": str(row[col_text])}
                if col_link != "None":
                    content["link"] = str(row[col_link])

                async def batch_task():
                     return await st.session_state.post_service.post_to_multiple(selected_platforms, content)

                row_res = asyncio.run(batch_task())

                display_res = {"Row": index + 1, "Content": content["text"][:30] + "..."}
                for p, r in row_res.items():
                    display_res[p] = "✅" if r["success"] else "❌"

                results_data.append(display_res)
                results_table.dataframe(pd.DataFrame(results_data))

                progress_bar.progress((index + 1) / len(df))

            st.success("Batch processing complete!")
