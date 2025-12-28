import streamlit as st


st.set_page_config(
    page_title="Player Passing Decision Quality",
    page_icon="⚽",
    layout="wide"
)

pg = st.navigation([
    st.Page("src/views/presentation.py", title="Presentation"),
    st.Page("src/views/overview.py", title="Overview"),
    st.Page("src/views/player_profile.py", title="Player Profile"),
    st.Page("src/views/comparison.py", title="Players Comparison")])
pg.run()

st.space(size="large")
st.markdown("---")
st.caption("SkillCorner X PySport Analytics Cup - Data powered by SkillCorner")
st.caption("10 Matches of Australian A-League 2024/2025 Season")
