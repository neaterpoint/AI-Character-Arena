"""Single place that owns st.session_state keys."""
import streamlit as st


def _defaults() -> dict:
    return {
        # --- character selection ---
        "select_for": "player",     # which fighter is being chosen: "player" | "opponent"
        "submitted_query": None,    # text typed in the selection box
        "candidates": [],           # [{"name": str, "origin": str}] possible matches to confirm
        "candidate_idx": 0,         # which candidate is currently being asked about
        "confirmed_pick": None,     # candidate the user said Yes to (stats get built next)
        "select_error": None,
        # --- battle ---
        "player": None,             # Fighter 1 (red)
        "opponent": None,           # Fighter 2 (blue)
        "turn": "player",           # whose turn it is: "player" | "opponent"
        "action_count": 0,          # actions taken so far (sudden death at the limit)
        "logs": [],                 # [{"side": "player"|"opponent", "text": str}]
        "recap": None,              # the latest action's outcome
        "winner": None,             # None | "player" | "opponent"
        "queued_action": None,      # "attack" | "defend" | "tactic", set by the buttons
    }


def init_state() -> None:
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)


def reset_game() -> None:
    for key, value in _defaults().items():
        st.session_state[key] = value