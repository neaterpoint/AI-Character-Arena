"""All AI access lives in this file.

=====================  PLACEHOLDER MODE  =====================
The professor's API key (ChatGPT 6 "Luna") has not been issued yet, so while
no real key is configured every function below returns FAKE, locally generated
data and the app shows a "placeholder mode" badge in the sidebar.

TO GO LIVE (3 steps):
  1. Copy .streamlit/secrets.toml.example -> .streamlit/secrets.toml
     and paste the real key into AI_API_KEY.
  2. Set MODEL_NAME (and API_BASE_URL if the professor gives one) below.
  3. Implement `_call_llm_json()` at the bottom of the "REAL AI" section
     (an OpenAI-style example is already written in the comments).
Nothing else in the project needs to change.
===============================================================
"""
from __future__ import annotations

import json
import os
import random
import re

import streamlit as st

from core.models import Character, Narration, TacticOutcome

# ---- TODO: confirm these with the professor ---------------------------------
MODEL_NAME = "gpt-6-luna"        # TODO: replace with the exact model id
API_BASE_URL: str | None = None  # TODO: set if the API isn't the default OpenAI URL
# -----------------------------------------------------------------------------


# ============================ configuration ================================
def get_api_key() -> str | None:
    """Return the key from .streamlit/secrets.toml or the AI_API_KEY env var."""
    key = None
    try:
        key = st.secrets.get("AI_API_KEY")
    except Exception:  # no secrets.toml yet
        pass
    key = key or os.getenv("AI_API_KEY")
    if not key or str(key).strip().upper().startswith("PASTE"):
        return None
    return str(key).strip()


def is_mock_mode() -> bool:
    return get_api_key() is None


def _clamp(value, low, high, default):
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return default


# ============================ public functions =============================
def resolve_character(query: str) -> Character:
    """Turn free text ("Steve from Minecraft") into a Character with stats."""
    if is_mock_mode():
        return _mock_resolve_character(query)

    data = _call_llm_json(
        system=(
            "You design balanced turn-based battle stats for fictional characters. "
            "Reply with JSON only."
        ),
        user=(
            f'Character request: "{query}"\n'
            'Return: {"name": str, "source": str, "description": str (max 25 words), '
            '"atk": 3-10, "atk_pct": 50-95, "defense": 3-10, "def_pct": 10-60, '
            '"crit_mult": 1.2-3.0, "crit_pct": 5-45, "state": str (2-4 words)}'
        ),
    )
    return _character_from_dict(data, fallback_name=query)


def narrate_action(actor: Character, target: Character, result) -> Narration:
    """Short, fun battle-log sentence for an attack/defend result."""
    if is_mock_mode():
        return _mock_narrate(actor, target, result)

    data = _call_llm_json(
        system=(
            "You are the narrator of a comedic turn-based arena. Reply with JSON only: "
            '{"text": one sentence in character, "actor_state": 2-4 words, "target_state": 2-4 words}'
        ),
        user=json.dumps(
            {
                "actor": actor.name, "source": actor.source,
                "target": target.name, "target_source": target.source,
                "action": result.action, "hit": result.hit, "crit": result.crit,
                "blocked": result.blocked, "damage": result.damage,
                "actor_hp": f"{actor.hp}/{actor.max_hp}",
                "target_hp": f"{target.hp}/{target.max_hp}",
            }
        ),
    )
    return Narration(
        text=str(data.get("text", f"{actor.name} acted.")),
        actor_state=data.get("actor_state"),
        target_state=data.get("target_state"),
    )


def judge_tactic(actor: Character, target: Character, tactic_text: str) -> TacticOutcome:
    """Decide what a free-form tactic typed by the player actually does."""
    if is_mock_mode():
        return _mock_tactic(actor, target, tactic_text)

    data = _call_llm_json(
        system=(
            "You are the referee of a turn-based arena. Judge the tactic fairly using the "
            "characters' abilities and lore. Reply with JSON only: "
            '{"text": one sentence, "damage": 0-25, "heal": 0-15, "defend": bool, '
            '"actor_state": 2-4 words, "target_state": 2-4 words}'
        ),
        user=json.dumps(
            {"actor": actor.name, "source": actor.source, "target": target.name,
             "target_source": target.source, "tactic": tactic_text}
        ),
    )
    return TacticOutcome(
        text=str(data.get("text", f"{actor.name} tried {tactic_text}.")),
        damage=int(_clamp(data.get("damage"), 0, 25, 0)),
        heal=int(_clamp(data.get("heal"), 0, 15, 0)),
        defend=bool(data.get("defend", False)),
        actor_state=data.get("actor_state"),
        target_state=data.get("target_state"),
    )


def choose_action(actor: Character, target: Character) -> tuple[str, str | None]:
    """The AI opponent picks its move: ("attack" | "defend" | "tactic", tactic_text)."""
    if is_mock_mode():
        return _mock_choose_action(actor, target)

    data = _call_llm_json(
        system=(
            "You control a fighter in a turn-based arena. Reply with JSON only: "
            '{"action": "attack"|"defend"|"tactic", "tactic": str or null}'
        ),
        user=json.dumps(
            {"you": actor.name, "source": actor.source, "enemy": target.name,
             "your_hp": actor.hp, "enemy_hp": target.hp}
        ),
    )
    action = data.get("action")
    if action not in {"attack", "defend", "tactic"}:
        action = "attack"
    return action, data.get("tactic") if action == "tactic" else None


# ============================ REAL AI (TODO) ===============================
def _call_llm_json(system: str, user: str) -> dict:
    """Send one prompt and return the parsed JSON reply.

    TODO: implement when the API key arrives. Example for an OpenAI-compatible API
    (also add `openai` to requirements.txt and `pip install openai`):

        from openai import OpenAI
        client = OpenAI(api_key=get_api_key(), base_url=API_BASE_URL)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(response.choices[0].message.content)
    """
    raise NotImplementedError(
        "A key is configured but _call_llm_json() in services/ai_client.py is not implemented yet."
    )


def _character_from_dict(data: dict, fallback_name: str) -> Character:
    return Character(
        name=str(data.get("name") or fallback_name).strip().title(),
        source=str(data.get("source") or "").strip(),
        description=str(data.get("description") or ""),
        atk=round(_clamp(data.get("atk"), 3, 10, 6.0), 1),
        atk_pct=round(_clamp(data.get("atk_pct"), 50, 95, 75.0), 1),
        defense=round(_clamp(data.get("defense"), 3, 10, 6.0), 1),
        def_pct=round(_clamp(data.get("def_pct"), 10, 60, 30.0), 1),
        crit_mult=round(_clamp(data.get("crit_mult"), 1.2, 3.0, 2.0), 1),
        crit_pct=round(_clamp(data.get("crit_pct"), 5, 45, 20.0), 1),
        state=str(data.get("state") or "Fresh and ready"),
    )


# ============================ PLACEHOLDER MODE =============================
def _mock_resolve_character(query: str) -> Character:
    match = re.match(r"^\s*(.+?)\s+(?:from|of)\s+(.+?)\s*$", query, flags=re.IGNORECASE)
    name, source = (match.group(1), match.group(2)) if match else (query.strip(), "")
    rng = random.Random(name.lower())  # same name -> same stats
    return Character(
        name=name.title(),
        source=source.title(),
        description="Placeholder character (no AI connected yet).",
        atk=round(rng.uniform(4, 9), 1),
        atk_pct=round(rng.uniform(65, 95), 1),
        defense=round(rng.uniform(4, 9), 1),
        def_pct=round(rng.uniform(20, 50), 1),
        crit_mult=round(rng.uniform(1.5, 3.0), 1),
        crit_pct=round(rng.uniform(10, 40), 1),
    )


def _state_from_hp(char: Character) -> str:
    ratio = char.hp_ratio
    if ratio > 0.75:
        return "Fresh and ready"
    if ratio > 0.5:
        return "Winded but fighting"
    if ratio > 0.25:
        return "Tired, hurting"
    if ratio > 0:
        return "Barely standing"
    return "Knocked out"


def _mock_narrate(actor: Character, target: Character, result) -> Narration:
    if result.action == "defend":
        text = f"{actor.name} braced for the next hit."
    elif result.blocked:
        text = f"{target.name} blocked {actor.name}'s attack."
    elif not result.hit:
        text = f"{actor.name} swung at {target.name} but missed."
    elif result.crit:
        text = f"CRITICAL! {actor.name} smashed {target.name} for {result.damage} damage."
    else:
        text = f"{actor.name} hit {target.name} for {result.damage} damage."
    return Narration(text, _state_from_hp(actor), _state_from_hp(target))


def _mock_tactic(actor: Character, target: Character, tactic_text: str) -> TacticOutcome:
    worked = random.random() < 0.7
    damage = random.randint(4, 14) if worked else 0
    heal = random.randint(0, 5) if worked else 0
    text = (
        f"{actor.name} used a tactic: {tactic_text}. It worked for {damage} damage."
        if worked
        else f"{actor.name} tried a tactic: {tactic_text}. It fizzled."
    )
    return TacticOutcome(text, damage=damage, heal=heal)


def _mock_choose_action(actor: Character, target: Character) -> tuple[str, str | None]:
    action = random.choices(["attack", "defend", "tactic"], weights=[60, 20, 20])[0]
    return action, ("improvised a trick" if action == "tactic" else None)
