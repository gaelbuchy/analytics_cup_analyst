import streamlit as st

st.title("⚽ Player Passing Decision Quality Analysis")

st.markdown("---")

st.markdown("""
This project is an interactive dashboard for analyzing player passing decisions. With new metrics and event data available for player possessions, we can now add context when evaluating passes and uncover new insights.

A common way to compare player decisions is looking at the xThreat created by each pass. But very different situations can produce the same xThreat values. One player might be choosing the best available option while another misses out on a more threatening pass.

Using SkillCorner's Dynamic Events Data and analyzing all available options in each pass situation, this dashboard provides tools to identify and compare how players make use of their passing opportunities.
""")

with st.expander("💡 Simple Example"):
    st.markdown("""
    **Player A:** Creates 2.5 xThreat per 90  
    **Player B:** Creates 2.5 xThreat per 90  
    
    Those seem similar, but ..
    
    **Player A:** Had 2.6 xThreat available → **96% efficiency**
    **Player B:** Had 4.0 xThreat available → **63% efficiency**
    
    The added context gives us more insights.
    """)

st.markdown("---")

st.subheader("🔬 Methodology")

st.markdown("""
We use SkillCorner's Dynamic Events Data and specifically **Player Possession Events** and **Passing Option Events**. 

From those, we can extract the `xthreat` (threat value) and `xpass_completion` (pass completion probability) available for each option.

By comparing all of the passing options, we can create new metrics for each player possession, that are then used in the dashboard for analysis.
""")

st.markdown("---")

st.subheader("📊 Key Metrics Explained")

st.markdown("**xThreat Available**")
st.caption("The highest xThreat from all the passing options, only considering options with a ≥40% completion probability.")

st.markdown("**Decision Efficiency**")
st.caption("The ratio of xThreat created to xThreat available.")

st.markdown("**Good Passing Opportunity**")
st.caption(
    "A pass that is helpful to the attack, defined by a completion probability ≥80% and that is threatening (having a xThreat value in the top 25% of all passes).")

st.markdown("**Safest Passing option**")
st.caption("Passing option with the highest completion probability.")

st.markdown("---")

st.subheader("Explore the Dashboard")

st.markdown("""
Use the sidebar to navigate through three analysis views:
""")

col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    st.page_link(
        "src/views/overview.py",
        label="📊 **Overview**",
    )
    st.caption("Global patterns, top performers, and decision profiles")

with col_nav2:
    st.page_link(
        "src/views/player_profile.py",
        label="👤 **Player Profile**",
    )
    st.caption(
        "Dive into individual player decision-making")

with col_nav3:
    st.page_link(
        "src/views/comparison.py",
        label="⚖️ **Comparison**",
    )
    st.caption("Head-to-head comparison")
