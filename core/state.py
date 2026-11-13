"""Single place that owns st.session_state keys."""
import streamlit as st


def _defaults() -> dict:
    return {
        "select_for": "player",     # which fighter is being chosen: "player" | "opponent"
        "candidate": None,          # Character awaiting Yes/No confirmation
        "submitted_query": None,    # text typed in the selection box
        "select_error": None,
        "player": None,
        "opponent": None,
        "turn": "player",
        "logs": [],                 # [{"side": "player"|"opponent", "text": str}]
        "recap": None,              # the opponent's latest move
        "winner": None,             # None | "player" | "opponent"
        "queued_action": None,      # (action, detail) set by the buttons
    }


def init_state() -> None:
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)


def reset_game() -> None:
    for key, value in _defaults().items():
        st.session_state[key] = value
