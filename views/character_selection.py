"""Screen 1: pick your fighter, then your opponent (each with a Yes/No confirmation)."""
import html

import streamlit as st

from core.ui import circle, page_title
from services import ai_client

SELECTION_ROLE = st.session_state.select_for          # "player" | "opponent"
CIRCLE_COLOR = "red" if SELECTION_ROLE == "player" else "blue"
BATTLE_PAGE = "views/battle.py"

with st.sidebar:
    st.markdown('<div class="side-title">Character<br>Selection</div>', unsafe_allow_html=True)


def _on_submit() -> None:
    """Runs when the user presses Enter in the text box."""
    text = st.session_state.char_input.strip()
    if text:
        st.session_state.submitted_query = text
    st.session_state.char_input = ""


def _confirm_yes() -> None:
    character = st.session_state.candidate
    st.session_state.candidate = None
    if st.session_state.select_for == "player":
        st.session_state.player = character
        st.session_state.select_for = "opponent"
    else:
        st.session_state.opponent = character
        st.session_state.start_battle = True


def _confirm_no() -> None:
    st.session_state.candidate = None


# Both fighters chosen -> go to the arena
if st.session_state.pop("start_battle", False):
    st.switch_page(BATTLE_PAGE)

# Resolve a freshly submitted query (this is the call that uses the AI)
query = st.session_state.submitted_query
if query:
    st.session_state.submitted_query = None
    try:
        with st.spinner("Looking up character..."):
            st.session_state.candidate = ai_client.resolve_character(query)
    except Exception as exc:  # noqa: BLE001 - show any AI/API failure to the user
        st.session_state.select_error = f"Couldn't look up that character: {exc}"
    st.rerun()

page_title()
_, middle, _ = st.columns([1, 3, 1])

with middle:
    st.markdown(f'<div style="margin-top:4rem">{circle(CIRCLE_COLOR)}</div>', unsafe_allow_html=True)

    candidate = st.session_state.candidate
    if candidate is None:
        # ---- input state ----
        st.markdown(
            '<div class="prompt">Enter a character (you can include the show/game they are from)</div>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Character",
            key="char_input",
            placeholder="e.g. Steve from Minecraft",
            label_visibility="collapsed",
            on_change=_on_submit,
        )
        if st.session_state.select_error:
            st.error(st.session_state.select_error)
            st.session_state.select_error = None
        step = "1 of 2: your fighter" if SELECTION_ROLE == "player" else "2 of 2: your opponent"
        st.markdown(f'<div class="step-note">Step {step}</div>', unsafe_allow_html=True)
    else:
        # ---- confirmation state ----
        label = f"{candidate.name} from {candidate.source}?" if candidate.source else f"{candidate.name}?"
        st.markdown(f'<div class="prompt">{html.escape(label)}</div>', unsafe_allow_html=True)
        no_col, _, yes_col = st.columns([1, 0.6, 1])
        no_col.button("No", key="btn_no", on_click=_confirm_no)
        yes_col.button("Yes", key="btn_yes", on_click=_confirm_yes)
