"""Screen 2: the arena. Player acts, the AI opponent answers, repeat until someone hits 0 HP."""
import html

import streamlit as st

from core import engine
from core.state import reset_game
from core.ui import fighter_card, page_title, stats_grid
from services import ai_client

SELECTION_PAGE = "views/character_selection.py"

player = st.session_state.player
opponent = st.session_state.opponent
if player is None or opponent is None:       # opened directly / state lost
    st.switch_page(SELECTION_PAGE)


# ----------------------------- actions -----------------------------
def queue_action(action: str, detail: str | None = None) -> None:
    st.session_state.queued_action = (action, detail)


@st.dialog("Choose a tactic")
def tactic_dialog() -> None:
    st.write(f"Describe what {player.name} does. Be creative and use their abilities.")
    text = st.text_input(
        "Tactic",
        placeholder=f"e.g. Pull {opponent.name} closer with a fishing rod",
        max_chars=140,
        label_visibility="collapsed",
    )
    if st.button("Use tactic", key="btn_exec", disabled=not text.strip()):
        queue_action("tactic", text.strip())
        st.rerun()   # full rerun closes the dialog


# Resolve a queued action BEFORE drawing, so the screen shows fresh numbers
queued = st.session_state.queued_action
if queued is not None:
    st.session_state.queued_action = None
    if st.session_state.winner is None:
        action, detail = queued
        try:
            with st.spinner("Resolving turn..."):
                results = engine.play_round(player, opponent, action, detail)
        except Exception as exc:  # noqa: BLE001
            st.error(f"The AI couldn't resolve that turn: {exc}")
        else:
            for result in results:
                st.session_state.logs.append({"side": result.side, "text": result.text})
            st.session_state.recap = results[-1].text
            if not opponent.alive:
                st.session_state.winner = "player"
            elif not player.alive:
                st.session_state.winner = "opponent"

winner = st.session_state.winner
game_over = winner is not None


# ----------------------------- sidebar -----------------------------
with st.sidebar:
    turn_tag = "" if game_over else '<span class="turn-tag">Current Turn</span>'
    st.markdown('<div class="side-label">Character</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-name">{html.escape(player.name)}{turn_tag}</div>', unsafe_allow_html=True)
    st.markdown(stats_grid(player), unsafe_allow_html=True)
    st.markdown(
        '<div class="state-box"><div class="state-title">Character State</div>'
        f"{html.escape(player.state)}</div>",
        unsafe_allow_html=True,
    )
    if ai_client.is_mock_mode():
        st.caption("🧪 AI placeholder mode: no API key set, responses are fake.")
    if st.button("New match", key="btn_reset"):
        reset_game()
        st.switch_page(SELECTION_PAGE)


# ----------------------------- main area -----------------------------
page_title()
arena_col, logs_col = st.columns([2.3, 1.2], gap="large")

with arena_col:
    left, right = st.columns(2)
    left.markdown(fighter_card(player, "red"), unsafe_allow_html=True)
    right.markdown(fighter_card(opponent, "blue"), unsafe_allow_html=True)

    atk_col, def_col, tac_col = st.columns(3)
    atk_col.button("Attack", key="btn_attack", on_click=queue_action, args=("attack",), disabled=game_over)
    def_col.button("Defend", key="btn_defend", on_click=queue_action, args=("defend",), disabled=game_over)
    if tac_col.button("Tactic", key="btn_tactic", disabled=game_over):
        tactic_dialog()

    if game_over:
        champion = player if winner == "player" else opponent
        st.markdown(f'<div class="banner">🏆 {html.escape(champion.name)} wins!</div>', unsafe_allow_html=True)
        if st.button("Play again", key="btn_again"):
            reset_game()
            st.switch_page(SELECTION_PAGE)

    recap = st.session_state.recap
    body = (
        f'<div class="recap-text">{html.escape(recap)}</div>'
        if recap
        else '<div class="recap-empty">Pick an action to start the fight.</div>'
    )
    st.markdown(f'<div class="panel"><div class="panel-title">Recap</div>{body}</div>', unsafe_allow_html=True)

with logs_col:
    with st.container(height=640, key="logs_panel"):
        st.markdown('<div class="panel-title">Battle Logs</div>', unsafe_allow_html=True)
        for entry in reversed(st.session_state.logs):      # newest first
            st.markdown(
                f'<div class="log-line {entry["side"]}">{html.escape(entry["text"])}</div>',
                unsafe_allow_html=True,
            )
