"""Screen 1: pick the first fighter, then the second.

Each typed name is verified Yes/No against up to MAX_ORIGIN_CANDIDATES possible
shows/games. Pressing No shows the next possible origin.
"""
import html

import streamlit as st

from core.ui import page_title
from services import ai_client

SELECTION_ROLE = st.session_state.select_for          # "player" | "opponent"
BATTLE_PAGE = "views/battle.py"


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
st.markdown(
    '<div class="screen-heading"><h1>Select your fighters</h1>'
    '<div class="eyebrow">Two picks. One arena.</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="selection-board"><div class="eyebrow">Choose your contenders</div></div>',
    unsafe_allow_html=True,
)

fighter_one, versus, fighter_two = st.columns([1, 0.14, 1], gap="small")

def render_slot(column, side: str, label: str, role: str, character) -> None:
    is_active = SELECTION_ROLE == role
    with column:
        with st.container(key=f"slot_{side}"):
            st.markdown(
                f'<div class="slot-kicker">{"FIGHTER 1 / RED CORNER" if side == "f1" else "FIGHTER 2 / BLUE CORNER"}</div>'
                f'<div class="slot-title">{label}</div>',
                unsafe_allow_html=True,
            )
            if character is not None:
                st.markdown(
                    f'<div class="slot-state ready"><strong>{html.escape(character.name)}</strong>'
                    'Selection locked. Ready for the arena.</div>',
                    unsafe_allow_html=True,
                )
            elif not is_active:
                st.markdown(
                    '<div class="slot-state waiting"><strong>Awaiting contender</strong>'
                    'This side is next in the selection order.</div>',
                    unsafe_allow_html=True,
                )
            elif st.session_state.candidates:
                candidates = st.session_state.candidates
                idx = st.session_state.candidate_idx
                current = candidates[idx]
                candidate_name = html.escape(current["name"])
                origin = html.escape(current["origin"])
                prompt = f"{candidate_name} from {origin}?" if origin else f"{candidate_name}?"
                st.markdown(
                    f'<div class="selection-prompt"><small>Confirm match {idx + 1} of {len(candidates)}</small>{prompt}</div>',
                    unsafe_allow_html=True,
                )
                no_col, yes_col = st.columns(2, gap="small")
                no_col.button("No", key="btn_no", on_click=_confirm_no)
                yes_col.button("Yes", key="btn_yes", on_click=_confirm_yes)
                hint = "More matches available." if idx + 1 < len(candidates) else "Last available match."
                st.markdown(f'<div class="step-note">{hint}</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="selection-prompt"><small>Enter a character</small>'
                    'Include a show or game to narrow the match.</div>',
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
                    st.markdown(
                        f'<div class="selection-error">{html.escape(st.session_state.select_error)}</div>',
                        unsafe_allow_html=True,
                    )
                    st.session_state.select_error = None
                st.markdown(
                    '<div class="step-note">Press enter to search. You control both fighters.</div>',
                    unsafe_allow_html=True,
                )


render_slot(fighter_one, "f1", "Fighter 1", "player", st.session_state.player)
with versus:
    st.markdown('<div class="selection-vs"><span>VS</span></div>', unsafe_allow_html=True)
render_slot(fighter_two, "f2", "Fighter 2", "opponent", st.session_state.opponent)