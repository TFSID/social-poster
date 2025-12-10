import streamlit as st
import asyncio

def render_post_page():
    st.title("✍️ Create Post")

    col_main, col_ai = st.columns([2, 1])

    with col_ai:
        st.subheader("🤖 AI Assistant")
        ai_prompt = st.text_area("What do you want to post about?")
        ai_style = st.selectbox("Style", ["viral", "professional", "casual"])
        if st.button("Generate Content"):
            with st.spinner("Generating..."):
                res = st.session_state.ai_service.generate_viral_post(prompt=ai_prompt, style=ai_style)
                if res["success"]:
                    st.session_state.generated_content = res["content"]["text"]
                else:
                    st.error(res.get("error"))

    with col_main:
        with st.form("post_form"):
            default_text = st.session_state.get("generated_content", "")
            text_content = st.text_area("Post Content", value=default_text, height=150)
            link_content = st.text_input("Link (Optional)")

            st.subheader("Select Platforms")
            platforms = st.session_state.post_service.get_supported_platforms()
            selected_platforms = []
            cols = st.columns(len(platforms))
            for i, p in enumerate(platforms):
                if cols[i].checkbox(p.capitalize()):
                    selected_platforms.append(p)

            submitted = st.form_submit_button("Post Now 🚀")

            if submitted:
                if not text_content and not link_content:
                    st.error("Please provide text or a link.")
                    return
                if not selected_platforms:
                    st.error("Please select at least one platform.")
                    return

                with st.spinner("Posting..."):
                    async def post_task():
                        return await st.session_state.post_service.post_to_multiple(
                            selected_platforms,
                            {"text": text_content, "link": link_content}
                        )

                    results = asyncio.run(post_task())

                    for p, res in results.items():
                        if res["success"]:
                            st.success(f"✅ Posted to {p}!")
                        else:
                            st.error(f"❌ Failed {p}: {res.get('error')}")
