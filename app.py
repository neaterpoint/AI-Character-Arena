"""Entrypoint. Run with:  streamlit run app.py

This file only does global setup (page config, state, CSS) and routing.
The actual screens live in views/.
"""
import streamlit as st

from core.state import init_state
from core.ui import SINGER, SWORDS, load_css

st.set_page_config(
    page_title="AI Character Arena",
    page_icon=SWORDS,
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
load_css()

# st.navigation + st.Page routing. position="hidden" hides the default nav menu
# because the app moves between screens itself with st.switch_page
# (requires Streamlit >= 1.46).
page = st.navigation(
    [
        st.Page("views/character_selection.py", title="Character Selection", icon=SINGER, default=True),
        st.Page("views/battle.py", title="Battle", icon=SWORDS),
    ],
    position="hidden",
)
page.run()