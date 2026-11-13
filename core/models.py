"""Plain data classes shared by the engine, the AI client and the views."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Character:
    name: str
    source: str = ""            # show/game they are from
    description: str = ""
    max_hp: int = 100
    hp: int = 100
    atk: float = 6.0            # damage power
    atk_pct: float = 75.0       # chance for an attack to land (%)
    defense: float = 6.0        # damage reduction power
    def_pct: float = 30.0       # chance to fully block while defending (%)
    crit_mult: float = 2.0      # critical hit multiplier (x)
    crit_pct: float = 20.0      # critical hit chance (%)
    state: str = "Fresh and ready"   # short status text shown in the sidebar
    defending: bool = False

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def hp_ratio(self) -> float:
        return max(0.0, min(1.0, self.hp / self.max_hp)) if self.max_hp else 0.0


@dataclass
class Narration:
    """What the AI says about an attack/defend result."""
    text: str
    actor_state: str | None = None
    target_state: str | None = None


@dataclass
class TacticOutcome:
    """What the AI decides a free-form tactic does. The engine clamps these numbers."""
    text: str
    damage: int = 0
    heal: int = 0
    defend: bool = False
    actor_state: str | None = None
    target_state: str | None = None
