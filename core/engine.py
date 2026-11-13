"""Battle rules. All numbers/dice live here; the AI only supplies characters,
narration, tactic judgements and the opponent's decisions."""
from __future__ import annotations

import random
from dataclasses import dataclass

from core.models import Character
from services import ai_client

# Tunable balance knobs
DAMAGE_SCALE = 2.5          # atk 6.0 -> ~15 base damage
BASE_MITIGATION = 0.03      # defense * this = damage reduction when not defending
DEFEND_MITIGATION = 0.08    # defense * this = damage reduction when defending
MAX_MITIGATION = 0.80
TACTIC_MAX_DAMAGE = 25
TACTIC_MAX_HEAL = 15


@dataclass
class ActionResult:
    actor: str
    target: str
    action: str                 # "attack" | "defend" | "tactic"
    text: str = ""
    side: str = ""              # "player" | "opponent"
    damage: int = 0
    heal: int = 0
    hit: bool = True
    crit: bool = False
    blocked: bool = False
    detail: str = ""            # the typed tactic, if any


def _roll(percent: float) -> bool:
    return random.uniform(0, 100) < percent


def _attack(attacker: Character, defender: Character) -> ActionResult:
    result = ActionResult(attacker.name, defender.name, "attack")
    if not _roll(attacker.atk_pct):
        result.hit = False
        return result
    if defender.defending and _roll(defender.def_pct):
        result.hit, result.blocked = False, True
        return result

    damage = attacker.atk * DAMAGE_SCALE * random.uniform(0.85, 1.15)
    if _roll(attacker.crit_pct):
        result.crit = True
        damage *= attacker.crit_mult
    per_point = DEFEND_MITIGATION if defender.defending else BASE_MITIGATION
    damage *= 1 - min(MAX_MITIGATION, defender.defense * per_point)

    result.damage = max(1, round(damage))
    defender.hp = max(0, defender.hp - result.damage)
    return result


def _tactic(actor: Character, target: Character, tactic_text: str) -> ActionResult:
    outcome = ai_client.judge_tactic(actor, target, tactic_text)
    damage = max(0, min(TACTIC_MAX_DAMAGE, int(outcome.damage)))
    heal = max(0, min(TACTIC_MAX_HEAL, int(outcome.heal)))

    target.hp = max(0, target.hp - damage)
    actor.hp = min(actor.max_hp, actor.hp + heal)
    actor.defending = bool(outcome.defend)
    if outcome.actor_state:
        actor.state = outcome.actor_state
    if outcome.target_state:
        target.state = outcome.target_state

    return ActionResult(
        actor.name, target.name, "tactic",
        text=outcome.text, damage=damage, heal=heal, detail=tactic_text,
        hit=damage > 0,
    )


def perform_action(actor: Character, target: Character, action: str, detail: str | None = None) -> ActionResult:
    actor.defending = False          # a defence only lasts one round
    if action == "tactic":
        return _tactic(actor, target, detail or "improvise")

    if action == "defend":
        actor.defending = True
        result = ActionResult(actor.name, target.name, "defend")
    else:
        result = _attack(actor, target)

    narration = ai_client.narrate_action(actor, target, result)
    result.text = narration.text
    if narration.actor_state:
        actor.state = narration.actor_state
    if narration.target_state:
        target.state = narration.target_state
    return result


def play_round(player: Character, opponent: Character, action: str, detail: str | None = None) -> list[ActionResult]:
    """Player acts, then the opponent answers (if still standing)."""
    first = perform_action(player, opponent, action, detail)
    first.side = "player"
    results = [first]

    if opponent.alive:
        opp_action, opp_detail = ai_client.choose_action(opponent, player)
        second = perform_action(opponent, player, opp_action, opp_detail)
        second.side = "opponent"
        results.append(second)
    return results
