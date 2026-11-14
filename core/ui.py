"""Small HTML/CSS helpers so the views stay readable."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from core.models import Character

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"

# Written as escapes so they survive any file-encoding mix-up.
SWORDS = "\u2694\ufe0f"                 # crossed swords
TROPHY = "\U0001F3C6"                   # trophy
FLASK = "\U0001F9EA"                    # test tube
SINGER = "\U0001F9D1\u200d\U0001F3A4"   # singer


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_title() -> None:
    st.markdown(
        '<div class="app-title">AI Character Arena</div>',
        unsafe_allow_html=True,
    )


def circle(color: str) -> str:
    """Placeholder avatar. `color` is 'red' or 'blue'. Swap for an <img> later."""
    return f'<div class="circle {color}"></div>'


def hp_bar(char: Character) -> str:
    ratio = char.hp_ratio
    level = "ok" if ratio > 0.5 else "warn" if ratio > 0.25 else "low"
    return (
        '<div class="hp-row"><span class="hp-label">HP</span>'
        '<div class="hp-track">'
        f'<div class="hp-fill {level}" style="width:{ratio * 100:.0f}%"></div></div>'
        f'<span class="hp-value">{char.hp}/{char.max_hp}</span></div>'
    )


def fighter_card(char: Character, color: str, active: bool = True) -> str:
    """Render a fighter's arena HUD without changing character state."""
    side = "f1" if color == "red" else "f2"
    turn_label = "ACTIVE TURN" if active else "ON DECK"
    tactics = ", ".join(html.escape(move) for move in char.tactics_used) or "No tactic used"
    rows = [
        ("ATK", f"{char.atk:.1f}", f"{char.atk_pct:.1f}%"),
        ("DEF", f"{char.defense:.1f}", f"{char.def_pct:.1f}%"),
        ("CRIT", f"{char.crit_mult:.1f}x", f"{char.crit_pct:.1f}%"),
    ]
    cells = "".join(
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value}</span>'
        f'<span class="stat-chance">{chance}</span>'
        for label, value, chance in rows
    )
    return (
        f'<div class="fighter-card {side}{" active" if active else ""}">'
        '<div class="fighter-head">'
        f'<span class="fighter-index">Fighter {"1" if side == "f1" else "2"}</span>'
        f'<span class="fighter-turn{" " if active else " waiting"}">{turn_label}</span>'
        '</div>'
        f'<div class="fighter-name">{html.escape(char.name)}</div>'
        f'{hp_bar(char)}'
        f'<div class="stats-grid">{cells}</div>'
        '<div class="tactic-row"><span class="stat-label">TACTIC</span>'
        f'<span class="tactic-value">{tactics}</span></div>'
        '<div class="state-row"><span class="stat-label">STATE</span>'
        f'<span class="state-value">{html.escape(char.state)}</span></div>'
        '</div>'
    )


def stats_grid(char: Character) -> str:
    rows = [
        ("ATK", f"{char.atk:.1f}", f"{char.atk_pct:.1f}%"),
        ("DEF", f"{char.defense:.1f}", f"{char.def_pct:.1f}%"),
        ("CRIT", f"{char.crit_mult:.1f}x", f"{char.crit_pct:.1f}%"),
    ]
    cells = "".join(
        f'<span class="stat-label">{label}</span>'
        f'<span class="stat-value">{value}</span>'
        f'<span class="stat-chance">{chance}</span>'
        for label, value, chance in rows
    )
    return f'<div class="stats-grid">{cells}</div>'