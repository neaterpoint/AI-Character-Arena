"""Phase 3: combat engine regression tests (offline, no AI calls)."""
import random
import pytest
from core import engine
from core.models import Character


def make(name="A", **kw):
    base = dict(atk=6.0, atk_pct=100.0, defense=0.0, def_pct=0.0, crit_mult=2.0, crit_pct=0.0)
    base.update(kw)
    return Character(name=name, **base)


def test_attack_misses_when_atk_pct_zero():
    a, d = make(atk_pct=0), make("D")
    r = engine._attack(a, d)
    assert not r.hit and r.damage == 0 and d.hp == 100


def test_defending_full_block_when_def_pct_100():
    a, d = make(), make("D", def_pct=100)
    d.defending = True
    r = engine._attack(a, d)
    assert r.blocked and not r.hit and d.hp == 100


def test_block_only_applies_while_defending():
    a, d = make(), make("D", def_pct=100)
    r = engine._attack(a, d)
    assert r.hit and not r.blocked and d.hp < 100


@pytest.mark.parametrize("seed", range(50))
def test_base_damage_range_no_defense(seed):
    random.seed(seed)
    a, d = make(), make("D")
    r = engine._attack(a, d)
    assert 13 <= r.damage <= 17          # 6*2.5*[0.85,1.15] = 12.75..17.25
    assert d.hp == 100 - r.damage


@pytest.mark.parametrize("seed", range(50))
def test_crit_multiplies_damage(seed):
    random.seed(seed)
    a, d = make(crit_pct=100, crit_mult=2.0), make("D")
    r = engine._attack(a, d)
    assert r.crit and 26 <= r.damage <= 35


def test_mitigation_capped_at_80_percent():
    random.seed(1)
    a, d = make(atk=10), make("D", defense=100)
    d.defending = True
    r = engine._attack(a, d)
    assert r.damage <= round(10 * 2.5 * 1.15 * 0.2) + 1


def test_defending_reduces_more_than_not_defending():
    random.seed(3); a, d1 = make(), make("D", defense=10); r1 = engine._attack(a, d1)
    random.seed(3); a, d2 = make(), make("D", defense=10); d2.defending = True; r2 = engine._attack(a, d2)
    assert r2.damage < r1.damage


def test_min_damage_is_one_and_hp_never_negative():
    a, d = make(atk=0.1), make("D", defense=100); d.defending = True
    assert engine._attack(a, d).damage == 1
    d.hp = 1; a.atk = 10
    engine._attack(a, d)
    assert d.hp == 0


def test_tactic_boost_respects_cap():
    random.seed(5)
    a, t = make(atk_pct=97.5, def_pct=89.5, crit_pct=74.5), make("T")
    for _ in range(30):
        engine._tactic(a, t)
    assert a.atk_pct <= 98.0 and a.def_pct <= 90.0 and a.crit_pct <= 75.0


def test_tactic_boost_within_range_and_matches_stat():
    random.seed(7)
    a, t = make(atk_pct=50, def_pct=20, crit_pct=10), make("T")
    before = (a.atk_pct, a.def_pct, a.crit_pct)
    r = engine._tactic(a, t)
    after = (a.atk_pct, a.def_pct, a.crit_pct)
    idx = {"atk": 0, "def": 1, "crit": 2}[r.stat]
    assert 8 <= r.boost <= 15
    assert round(after[idx] - before[idx], 1) == r.boost
    assert [x for i, x in enumerate(after) if i != idx] == [x for i, x in enumerate(before) if i != idx]


def test_defend_flag_clears_on_next_action():
    a, t = make(), make("T")
    engine.perform_action(a, t, "defend"); assert a.defending
    engine.perform_action(a, t, "attack"); assert not a.defending


def test_sudden_death_lower_hp_loses():
    a, t = make("A"), make("T"); a.hp, t.hp = 60, 40
    r = engine._sudden_death(a, t)
    assert t.hp == 0 and a.hp == 60 and r.actor == "A"


def test_sudden_death_tie_non_actor_loses():
    a, t = make("A"), make("T")
    engine._sudden_death(a, t)
    assert t.hp == 0 and a.hp == 100


def test_sudden_death_triggers_at_action_50_only():
    a, t = make("A", atk_pct=0), make("T")
    assert len(engine.play_turn(a, t, "player", "attack", 49)) == 1
    res = engine.play_turn(a, t, "player", "attack", 50)
    assert res[-1].action == "sudden_death"


def test_narration_cannot_change_numbers_in_demo_mode():
    random.seed(11)
    a, d = make(), make("D")
    r = engine.perform_action(a, d, "attack")
    assert d.hp == 100 - r.damage
