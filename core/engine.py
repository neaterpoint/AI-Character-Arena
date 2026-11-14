"""Battle rules. All numbers and dice live here; the AI only supplies character
origins/stats, narration and lore-accurate flavour for tactics."""
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
MAX_ACTIONS = 50            # sudden death once this many actions have been taken

TACTIC_BOOST = (8.0, 15.0)  # random boost (percentage points) a tactic gives
# stat key -> (Character attribute, label shown in the log, cap for that chance)
TACTIC_STATS = {
    "atk": ("atk_pct", "Atk chance", 98.0),
    "def": ("def_pct", "Def chance", 90.0),
    "crit": ("crit_pct", "Crit chance", 75.0),
}


@dataclass
class ActionResult:
    actor: str
    target: str
    action: str                 # "attack" | "defend" | "tactic" | "sudden_death"
    text: str = ""
    side: str = ""              # "player" | "opponent" (who acted)
    damage: int = 0
    hit: bool = True
    crit: bool = False
    blocked: bool = False
    stat: str = ""              # tactic: which chance was boosted ("atk" | "def" | "crit")
    boost: float = 0.0          # tactic: how many percentage points it added
    detail: str = ""            # tactic: name of the move


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


def _tactic(actor: Character, target: Character) -> ActionResult:
    """A random lore-based move whose main effect is boosting Atk, Def or Crit chance."""
    stat = random.choice(list(TACTIC_STATS))
    attr, label, cap = TACTIC_STATS[stat]
    outcome = ai_client.generate_tactic(actor, target, stat)

    old = getattr(actor, attr)
    boost = round(max(0.0, min(cap, old + random.uniform(*TACTIC_BOOST)) - old), 1)
    setattr(actor, attr, round(old + boost, 1))

    if outcome.move:
        actor.tactics_used = (actor.tactics_used + [outcome.move])[-5:]
    if outcome.actor_state:
        actor.state = outcome.actor_state
    if outcome.target_state:
        target.state = outcome.target_state

    suffix = f"({label} +{boost:.1f}%)" if boost > 0 else f"({label} is already at its maximum)"
    return ActionResult(
        actor.name, target.name, "tactic",
        text=f"{outcome.text} {suffix}", stat=stat, boost=boost, detail=outcome.move, hit=False,
    )


def perform_action(actor: Character, target: Character, action: str) -> ActionResult:
    actor.defending = False          # a defence only lasts until the actor's next action
    if action == "tactic":
        return _tactic(actor, target)

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


def _sudden_death(actor: Character, target: Character) -> ActionResult:
    """Action limit reached: the fighter with less HP is knocked out (tie: the one who didn't act)."""
    loser = target if target.hp <= actor.hp else actor
    winner = actor if loser is target else target
    loser.hp = 0
    loser.state = "Knocked out"
    return ActionResult(
        winner.name, loser.name, "sudden_death",
        text=f"Sudden death! After {MAX_ACTIONS} actions the arena gives way and {loser.name} is knocked out.",
        hit=False,
    )


def play_turn(actor: Character, target: Character, side: str, action: str, action_number: int) -> list[ActionResult]:
    """One fighter acts. `action_number` is this action's number (1-based) in the match."""
    first = perform_action(actor, target, action)
    first.side = side
    results = [first]

    if actor.alive and target.alive and action_number >= MAX_ACTIONS:
        final = _sudden_death(actor, target)
        final.side = side
        results.append(final)
    return results