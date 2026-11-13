"""Small HTML/CSS helpers so the views stay readable."""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from core.models import Character

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_title() -> None:
    st.markdown('<div class="app-title">⚔️ AI CHARACTER ARENA</div>', unsafe_allow_html=True)


def circle(color: str) -> str:
    """Placeholder avatar. `color` is 'red' or 'blue'. Swap for an <img> later."""
    return f'<div class="circle {color}"></div>'


def hp_bar(char: Character) -> str:
    ratio = char.hp_ratio
    level = "ok" if ratio > 0.5 else "warn" if ratio > 0.25 else "low"
    return (
        '<div class="hp-row"><span>HP:</span>'
        '<div class="hp-track">'
        f'<div class="hp-fill {level}" style="width:{ratio * 100:.0f}%"></div></div>'
        f"<span>{char.hp}/{char.max_hp}</span></div>"
    )


def fighter_card(char: Character, color: str) -> str:
    return (
        '<div class="fighter">'
        f"{circle(color)}"
        f'<div class="fighter-name">{html.escape(char.name)}</div>'
        f"{hp_bar(char)}</div>"
    )


def stats_grid(char: Character) -> str:
    rows = [
        ("Atk", f"{char.atk:.1f}", f"{char.atk_pct:.1f}%"),
        ("Def", f"{char.defense:.1f}", f"{char.def_pct:.1f}%"),
        ("Crit%", f"{char.crit_mult:.1f}x", f"{char.crit_pct:.1f}%"),
    ]
    cells = "".join(f"<span>{a}</span><span>{b}</span><span>{c}</span>" for a, b, c in rows)
    return f'<div class="stats-grid">{cells}</div>'
