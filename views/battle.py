"""Screen 2: the arena. One person controls BOTH fighters; turns alternate until
someone reaches 0 HP or the action limit forces a sudden-death knockout."""
import html

import streamlit as st

from core import engine
from core.models import Character
from core.state import reset_game
from core.ui import fighter_card, page_title
from services import ai_client

SELECTION_PAGE = "views/character_selection.py"

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
                kind = (
                    "sudden" if result.action == "sudden_death"
                    else "tactic" if result.action == "tactic"
                    else "critical" if result.crit
                    else "normal"
                )
                st.session_state.logs.append(
                    {
                        "side": result.side,
                        "text": result.text,
                        "kind": kind,
                        "action": result.action,
                        "damage": result.damage,
                    }
                )
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

def is_shielded(side: str, character: Character) -> bool:
    """Keep the visual shield until a later incoming attack deals damage."""
    if not character.defending:
        return False
    defense_index = next(
        (
            index for index in range(len(st.session_state.logs) - 1, -1, -1)
            if st.session_state.logs[index].get("side") == side
            and st.session_state.logs[index].get("action") == "defend"
        ),
        -1,
    )
    return not any(
        entry.get("side") != side
        and entry.get("action") == "attack"
        and entry.get("damage", 0) > 0
        for entry in st.session_state.logs[defense_index + 1:]
    )


last_action = next(
    (
        entry for entry in reversed(st.session_state.logs)
        if entry.get("action") in {"attack", "defend", "tactic"}
    ),
    None,
)
player_effect = None
opponent_effect = None
player_motion = sum(
    1 for entry in st.session_state.logs
    if entry.get("side") == "player"
    and entry.get("action") in {"attack", "defend", "tactic"}
)
opponent_motion = sum(
    1 for entry in st.session_state.logs
    if entry.get("side") == "opponent"
    and entry.get("action") in {"attack", "defend", "tactic"}
)
if last_action is not None:
    if last_action["action"] == "defend":
        if last_action["side"] == "player":
            player_effect = "defend"
        else:
            opponent_effect = "defend"
    elif last_action["action"] == "tactic":
        if last_action["side"] == "player":
            player_effect = "tactic"
        else:
            opponent_effect = "tactic"
    else:
        if last_action["side"] == "player":
            player_effect = "attack"
            if last_action.get("damage", 0) > 0:
                opponent_effect = "hit"
        else:
            opponent_effect = "attack"
            if last_action.get("damage", 0) > 0:
                player_effect = "hit"


# ----------------------------- main area -----------------------------
page_title()
if game_over:
    loser = opponent if winner == "player" else player
    winner_color = "red" if winner == "player" else "blue"
    loser_color = "blue" if winner == "player" else "red"
    st.markdown(
        '<div class="victory-screen">'
        '<div class="victory-scanlines"></div>'
        '<div class="victory-stage">'
        f'<div class="victory-loser">{fighter_card(loser, loser_color, active=False, knocked_out=True)}</div>'
        '<div class="victory-champion">'
        '<div class="victory-banner">VICTORY</div>'
        f'{fighter_card(focus, winner_color, active=True, victorious=True)}'
        f'<div class="victory-name">{html.escape(focus.name)} WINS</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("Rematch", key="btn_again"):
        reset_game()
        st.switch_page(SELECTION_PAGE)
else:
    heading, reset = st.columns([5, 1])
    with heading:
        st.markdown(
            '<div class="screen-heading"><h1>Battle Arena</h1>'
            '<div class="eyebrow">Match in progress</div></div>',
            unsafe_allow_html=True,
        )
    with reset:
        if st.button("New Match", key="btn_reset"):
            reset_game()
            st.switch_page(SELECTION_PAGE)

    if ai_client.is_mock_mode():
        st.caption("DEMO MODE / Responses are simulated without an API key.")

    arena_col, logs_col = st.columns([2.1, 1], gap="large")

    with arena_col:
        left, versus, right = st.columns([1, 0.12, 1], gap="small")
        left.markdown(
            fighter_card(
                player,
                "red",
                active=focus_side == "player",
                effect=player_effect,
                effect_id=player_motion,
                defending=is_shielded("player", player),
            ),
            unsafe_allow_html=True,
        )
        with versus:
            st.markdown('<div class="arena-divider">VS</div>', unsafe_allow_html=True)
        right.markdown(
            fighter_card(
                opponent,
                "blue",
                active=focus_side == "opponent",
                effect=opponent_effect,
                effect_id=opponent_motion,
                defending=is_shielded("opponent", opponent),
            ),
            unsafe_allow_html=True,
        )

        number = min(st.session_state.action_count + 1, engine.MAX_ACTIONS)
        banner = (
            f"<strong>{html.escape(focus.name)}</strong> to act / "
            f"action {number} of {engine.MAX_ACTIONS}"
        )
        st.markdown(f'<div class="battle-banner">{banner}</div>', unsafe_allow_html=True)
        if st.session_state.action_count == engine.MAX_ACTIONS - 1:
            st.markdown(
                '<div class="sudden-warning">Sudden Death / Action 50 decides the match</div>',
                unsafe_allow_html=True,
            )

        fighter_label = "F1" if focus_side == "player" else "F2"
        st.markdown(
            f'<div class="action-caption">Fighter {fighter_label[-1]} / Choose your move</div>',
            unsafe_allow_html=True,
        )
        atk_col, def_col, tac_col = st.columns(3)
        atk_col.button(
            f"{fighter_label} / Attack", key="btn_attack", on_click=queue_action,
            args=("attack",),
        )
        def_col.button(
            f"{fighter_label} / Defend", key="btn_defend", on_click=queue_action,
            args=("defend",),
        )
        tac_col.button(
            f"{fighter_label} / Tactic", key="btn_tactic", on_click=queue_action,
            args=("tactic",),
            help="A random lore-based move that boosts Atk, Def or Crit chance.",
        )

        recap = st.session_state.recap
        body = (
            f'<div class="recap-text">{html.escape(recap)}</div>'
            if recap
            else '<div class="recap-empty">Choose an action to start the fight.</div>'
        )
        st.markdown(
            f'<div class="recap-panel"><div class="recap-heading">Last action</div>{body}</div>',
            unsafe_allow_html=True,
        )

    with logs_col:
        with st.container(height=640, key="logs_panel"):
            st.markdown(
                f'<div class="log-heading">Combat Log<span>{len(st.session_state.logs)} entries</span></div>',
                unsafe_allow_html=True,
            )
            logs = st.session_state.logs
            for index in range(len(logs) - 1, -1, -1):      # newest first
                entry = logs[index]
                text = entry["text"]
                lowered = text.lower()
                kind = entry.get("kind")
                if kind not in {"normal", "critical", "tactic", "sudden"}:
                    if "sudden death" in lowered:
                        kind = "sudden"
                    elif "chance +" in lowered or "chance is already at its maximum" in lowered:
                        kind = "tactic"
                    elif "critical" in lowered or "crit!" in lowered:
                        kind = "critical"
                    else:
                        kind = "normal"
                active_class = " active-log" if index == len(logs) - 1 else ""
                st.markdown(
                    f'<div class="log-line {entry["side"]} {kind}{active_class}">'
                    f'{html.escape(text)}</div>',
                    unsafe_allow_html=True,
                )
