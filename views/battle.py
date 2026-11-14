"""Screen 2: the arena. One person controls BOTH fighters; turns alternate until
someone reaches 0 HP or the action limit forces a sudden-death knockout."""
import html

import streamlit as st

from core import engine
from core.state import reset_game
from core.ui import FLASK, TROPHY, fighter_card, page_title, stats_grid
from services import ai_client

SELECTION_PAGE = "views/character_selection.py"
SIDE_HEX = {"player": "#ff3b3b", "opponent": "#38b6ff"}   # fighter 1 = red, fighter 2 = blue

player = st.session_state.player
opponent = st.session_state.opponent
if player is None or opponent is None:       # opened directly / state lost
    st.switch_page(SELECTION_PAGE)


def fighters_for(turn: str):
    """Return (acting fighter, other fighter) for the given side."""
    return (player, opponent) if turn == "player" else (opponent, player)


# ----------------------------- actions -----------------------------
def queue_action(action: str) -> None:
    st.session_state.queued_action = action


# Resolve a queued action BEFORE drawing, so the screen shows fresh numbers
queued = st.session_state.queued_action
if queued is not None:
    st.session_state.queued_action = None
    if st.session_state.winner is None:
        turn = st.session_state.turn
        actor, target = fighters_for(turn)
        action_number = st.session_state.action_count + 1
        try:
            with st.spinner("Resolving turn..."):
                results = engine.play_turn(actor, target, turn, queued, action_number)
        except Exception as exc:  # noqa: BLE001 - show any AI/API failure to the player
            st.error(f"The AI couldn't resolve that turn, please try again. ({exc})")
        else:
            st.session_state.action_count = action_number
            for result in results:
                st.session_state.logs.append({"side": result.side, "text": result.text})
            st.session_state.recap = results[-1].text
            if not opponent.alive:
                st.session_state.winner = "player"
            elif not player.alive:
                st.session_state.winner = "opponent"
            else:
                st.session_state.turn = "opponent" if turn == "player" else "player"

winner = st.session_state.winner
game_over = winner is not None
focus_side = winner if game_over else st.session_state.turn     # whose card/stats to highlight
focus = player if focus_side == "player" else opponent


# ----------------------------- sidebar -----------------------------
with st.sidebar:
    turn_tag = "" if game_over else '<span class="turn-tag">Current Turn</span>'
    st.markdown('<div class="side-label">Character</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="side-name" style="color:{SIDE_HEX[focus_side]}">{html.escape(focus.name)}{turn_tag}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(stats_grid(focus), unsafe_allow_html=True)
    st.markdown(
        '<div class="state-box"><div class="state-title">Character State</div>'
        f"{html.escape(focus.state)}</div>",
        unsafe_allow_html=True,
    )
    if ai_client.is_mock_mode():
        st.caption(f"{FLASK} Demo mode: no API key set, responses are simulated.")
    if st.button("New match", key="btn_reset"):
        reset_game()
        st.switch_page(SELECTION_PAGE)


# ----------------------------- main area -----------------------------
page_title()
arena_col, logs_col = st.columns([2.3, 1.2], gap="large")

with arena_col:
    left, right = st.columns(2)
    left.markdown(fighter_card(player, "red", active=focus_side == "player"), unsafe_allow_html=True)
    right.markdown(fighter_card(opponent, "blue", active=focus_side == "opponent"), unsafe_allow_html=True)

    if game_over:
        banner = f"{TROPHY} {focus.name} wins!"
    else:
        number = min(st.session_state.action_count + 1, engine.MAX_ACTIONS)
        banner = f"{focus.name}'s turn - action {number} of {engine.MAX_ACTIONS}"
    st.markdown(f'<div class="banner">{html.escape(banner)}</div>', unsafe_allow_html=True)

    atk_col, def_col, tac_col = st.columns(3)
    atk_col.button("Attack", key="btn_attack", on_click=queue_action, args=("attack",), disabled=game_over)
    def_col.button("Defend", key="btn_defend", on_click=queue_action, args=("defend",), disabled=game_over)
    tac_col.button(
        "Tactic", key="btn_tactic", on_click=queue_action, args=("tactic",), disabled=game_over,
        help="A random lore-based move that boosts Atk, Def or Crit chance.",
    )

    if game_over and st.button("Play again", key="btn_again"):
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