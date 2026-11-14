"""Screen 1: pick the first fighter, then the second.

Each typed name is verified Yes/No against up to MAX_ORIGIN_CANDIDATES possible
shows/games. Pressing No shows the next possible origin.
"""
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
    state = st.session_state
    state.confirmed_pick = state.candidates[state.candidate_idx]
    state.candidates = []
    state.candidate_idx = 0


def _confirm_no() -> None:
    state = st.session_state
    next_idx = state.candidate_idx + 1
    if next_idx < len(state.candidates):
        state.candidate_idx = next_idx            # ask about the next possible origin
    else:
        state.candidates = []
        state.candidate_idx = 0
        state.select_error = (
            "That was the last match I could find. Try adding the show or game, "
            "e.g. 'Goku from Dragon Ball'."
        )


# Both fighters chosen -> go to the arena
if st.session_state.pop("start_battle", False):
    st.switch_page(BATTLE_PAGE)

# The user said Yes to a match -> now build that character's stats
pick = st.session_state.confirmed_pick
if pick:
    st.session_state.confirmed_pick = None
    try:
        with st.spinner("Building character stats..."):
            character = ai_client.build_character(pick["name"], pick["origin"])
    except Exception as exc:  # noqa: BLE001 - show any AI/API failure to the user
        st.session_state.select_error = f"Couldn't build that character: {exc}"
    else:
        if st.session_state.select_for == "player":
            st.session_state.player = character
            st.session_state.select_for = "opponent"
        else:
            st.session_state.opponent = character
            st.session_state.start_battle = True
    st.rerun()

# A freshly typed name -> look up its possible origins
query = st.session_state.submitted_query
if query:
    st.session_state.submitted_query = None
    try:
        with st.spinner("Looking up character..."):
            st.session_state.candidates = ai_client.find_origins(query)
            st.session_state.candidate_idx = 0
    except Exception as exc:  # noqa: BLE001 - show any AI/API failure to the user
        st.session_state.select_error = f"Couldn't look up that character: {exc}"
    st.rerun()

page_title()
_, middle, _ = st.columns([1, 3, 1])

with middle:
    st.markdown(f'<div style="margin-top:4rem">{circle(CIRCLE_COLOR)}</div>', unsafe_allow_html=True)

    candidates = st.session_state.candidates
    if not candidates:
        # ---- input state ----
        st.markdown(
            '<div class="prompt">Enter a character (you can include the show/game they are from)</div>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Character",
            key="char_input",
            placeholder="e.g. Steve from Minecraft",
            max_chars=80,
            label_visibility="collapsed",
            on_change=_on_submit,
        )
        if st.session_state.select_error:
            st.error(st.session_state.select_error)
            st.session_state.select_error = None
        step = "1 of 2: first fighter (red)" if SELECTION_ROLE == "player" else "2 of 2: second fighter (blue)"
        st.markdown(f'<div class="step-note">Step {step}. You control both fighters.</div>', unsafe_allow_html=True)
    else:
        # ---- confirmation state ----
        idx = st.session_state.candidate_idx
        current = candidates[idx]
        label = f"{current['name']} from {current['origin']}?" if current["origin"] else f"{current['name']}?"
        st.markdown(f'<div class="prompt">{html.escape(label)}</div>', unsafe_allow_html=True)
        no_col, _, yes_col = st.columns([1, 0.6, 1])
        no_col.button("No", key="btn_no", on_click=_confirm_no)
        yes_col.button("Yes", key="btn_yes", on_click=_confirm_yes)
        hint = "Press No to see the next match." if idx + 1 < len(candidates) else "This is the last match."
        st.markdown(
            f'<div class="step-note">Match {idx + 1} of {len(candidates)}. {hint}</div>',
            unsafe_allow_html=True,
        )