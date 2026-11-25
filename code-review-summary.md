| # | Finding | Bug? | Why |
|---|---------|------|-----|
| 1 | Narrate action number validation | No | UX degradation (fallback narration), not broken logic |
| 2 | Generate tactic missing actor_state/target_state | Yes | Battle state becomes stale — subsequent logic uses wrong state |
| 3 | Mentions origin skips short franchise names | Yes (security) | Franchise names leak in output — privacy/integrity issue |
| 4 | Unused target parameter | No | Dead code only |
| 6 | Clean move pool silent drops | Yes | Legitimate moves disappear from character move sets |
| 7 | Spanish over-match ("Ignorant Hero") | Yes | False positive flags valid character names/titles |
| 8 | Default moveset allocates per call | No | Minor perf overhead only |
| 9 | Tactic repeat avoidance lost | Yes | AI repeats tactics instead of varying — degraded behavior |
| 10 | Clean output str false positives on lore | Yes | Legitimate narrative text ("ignores the pain") incorrectly filtered |

**Summary**: 6 bugs (#2, #3, #6, #7, #9, #10), 1 security leak (#3), 3 non-bugs (#1, #4, #8).
The highest-impact bugs are #2 (state corruption in battles) and #6 (moves silently disappearing).

---

## Additional Note: reload_sensitive_figures() Helper

| Item | Bug? |
|------|------|
| reload_sensitive_figures() helper | ❌ No (optional suggestion) |

### The reload_sensitive_figures() Function

One Minor Improvement (Optional)

The `_setting()` function reads secrets at module import time. If you change `SENSITIVE_FIGURES` in `secrets.toml`, you need a process restart to pick it up. For a Streamlit app, that's usually fine (restart on config change), but you could add a cache-clear helper if you want live reload:

```python
# Optional: add to ai_client.py if you want live config reload without restart
def reload_sensitive_figures() -> None:
    global _SENSITIVE_FIGURE_NAMES
    _SENSITIVE_FIGURE_NAMES = _get_sensitive_figures()
```

Bottom line: The current architecture is solid. All user text passes through `ai_client.py`'s validation pipeline before ever reaching the LLM. No other files need injection defenses.