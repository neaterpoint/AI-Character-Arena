# AI Character Arena

Turn-based battles between any two characters, powered by AI.
You control **both** fighters: pick them, then take turns choosing Attack,
Defend or Tactic for whoever's turn it is.

Built with [Streamlit](https://streamlit.io) and any OpenAI-compatible API.
Runs fully offline in **demo mode** if no API key is configured.

## How it works

1. **Pick fighters.** Type a character (`Goku`) and the AI offers up to 5
   possible shows/games one at a time (Yes/No). Type `Goku from Dragon Ball`
   to skip the guessing. Fighter 1 (red) is chosen first, then Fighter 2 (blue).
2. **Stats are generated.** Once you confirm a match, the AI builds lore-based
   stats: Atk, Def and Crit, each with a power value and a success chance.
3. **Fight.** Players alternate turns choosing:
   - **Attack:** roll to land, then damage with a possible critical hit.
   - **Defend:** until that fighter's next action, incoming hits that land can
     be fully blocked (Def chance) and take extra damage reduction.
   - **Tactic:** a random, lore-accurate move that permanently boosts the
     chance of Atk, Def or Crit for the rest of the match.
4. **Win.** Reduce the other fighter to 0 HP. After 50 total actions, sudden
   death knocks out the fighter with less HP.

**Division of labor:** the engine (`core/engine.py`) owns all dice, damage and
balance numbers. The AI only supplies character origins and stats, battle
narration, and tactic flavour text. It never decides who wins a roll.

### Combat rules at a glance

| Rule | Value |
| --- | --- |
| Starting HP | 100 |
| Base damage | `atk x 2.5 x random(0.85-1.15)` |
| Critical hit | Multiplies damage by the fighter's `crit_mult` |
| Damage reduction | `defense x 0.03` normally, `defense x 0.08` while defending (max 80%) |
| Tactic boost | +8 to +15 percentage points (caps: Atk 98%, Def 90%, Crit 75%) |
| Tactic memory | Last 5 tactics are passed to the AI to avoid repeats |
| Sudden death | At action 50, lower HP loses (tie: the fighter who didn't act loses) |

Balance knobs live at the top of `core/engine.py`.

## Run locally

```bash
# inside an activated virtual environment
pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows PowerShell, run the same two commands one per line (`&&` is not
supported in Windows PowerShell 5.1). Using `python -m streamlit` guarantees
Streamlit runs with the active virtual environment's packages.

Requires Python 3.10+ and Streamlit 1.46+ (needed for `st.navigation` and
`st.switch_page`).

## Configure the AI

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Fill in the values:

| Setting | Purpose |
| --- | --- |
| `AI_API_KEY` | Your API key. Empty (or starting with `PASTE`) means demo mode. |
| `AI_MODEL` | Model id. Defaults to the value of `DEFAULT_MODEL` in `services/ai_client.py`. |
| `AI_BASE_URL` | Optional. Base URL for OpenAI-compatible providers. |

Settings are read from `secrets.toml` first, then from environment variables of
the same name. `secrets.toml` is git-ignored. Never put real keys in the
`.example` file. On Streamlit Community Cloud, paste the same contents into the
app's **Secrets** settings instead.

### Demo mode

With no API key the app still works end to end. Origins come from a small
built-in list (Goku, Steve, Mario, Link) or placeholder "Demo Universe"
entries, stats are generated deterministically from the name, and narration is
template text. A "DEMO MODE" caption shows on the battle screen.

### How AI responses are requested

All AI access lives in `services/ai_client.py`. There are four calls: origin
lookup, character stats, battle narration, and tactic generation.

- Each call asks for **structured JSON** using a per-call JSON schema
  (`response_format=json_schema`).
- If the provider rejects schema mode with a 400 error, the client falls back
  to plain `json_object` mode and remembers that for the rest of the session.
- Replies are parsed leniently (code fences and stray text are tolerated) and
  stats are clamped to valid ranges in code, so a bad model reply cannot
  produce out-of-range numbers.
- If narration or tactic generation fails mid-battle, the turn still
  completes using simple template text. Character lookup and stat-building
  failures are shown on the selection screen so the player can retry.

### Input safety

- Typed names have `<` and `>` stripped and are capped at 80 characters.
- Empty, symbol-only, and zero-width-only names are rejected. Prompt-control
  phrases are checked after Unicode normalization, separator removal, common
  leetspeak/Cyrillic-confusable normalization, and selected multilingual checks.
- User text is passed to the model as untrusted data, and the prompts tell the
  model not to follow instructions found in it.
- AI output is length-limited and sanitized; instruction-like output and
  franchise-name leakage in battle text fall back to local templates. Stat
  values are finite-checked and clamped, and narration damage numbers are
  checked against the engine's result.
- Real-world figures associated with atrocities, extremist movements,
  terrorism, or notorious violent or sexual crimes are not accepted as
  fighters; the AI is also instructed to avoid glorifying these harms or
  demeaning protected groups.
- Everything rendered into HTML goes through `html.escape`.
- These are defense-in-depth checks, not a guarantee against every possible
  prompt-injection phrasing or behavior from an external model. The battle
  engine remains authoritative for rolls, damage, and win conditions.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Entry point: page config, CSS, navigation |
| `views/character_selection.py` | Screen 1: name entry and Yes/No origin confirmation |
| `views/battle.py` | Screen 2: arena, action buttons, combat log, victory screen |
| `core/engine.py` | Battle rules, dice and balance constants |
| `core/models.py` | Dataclasses: `Character`, `Narration`, `TacticOutcome` |
| `core/state.py` | Owns all `st.session_state` keys and reset logic |
| `core/ui.py` | HTML/CSS helpers (fighter cards, HP bars) |
| `services/ai_client.py` | All AI access, JSON schemas, and offline demo mode |
| `assets/style.css` | Arcade-style theme, animations and victory screen |

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `Couldn't look up that character: No module named 'openai'` | Dependencies not installed in the active environment. Run `pip install -r requirements.txt` and start with `python -m streamlit run app.py`. |
| App always in demo mode | `AI_API_KEY` is missing or still a placeholder in `.streamlit/secrets.toml`. |
| `400` errors from the provider | Usually the provider not supporting schema mode or the chosen model. The client falls back automatically; if it still fails, check `AI_MODEL` and `AI_BASE_URL`. |

## Status and known issues

The core loop (select fighters, battle, victory, rematch) is implemented, and
the AI JSON handling has been reworked to tolerate providers without schema
support. Novel multilingual prompt-injection phrasing and model-specific
behavior remain possible.

## Contributing

- Work on a feature branch and open a pull request into `main`.
- Do not commit `.streamlit/secrets.toml`, `.venv/` or `.DS_Store`.
- Keep game numbers in `core/engine.py` and AI calls in `services/ai_client.py`.