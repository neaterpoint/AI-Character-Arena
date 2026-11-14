# AI Character Arena

Turn-based battles between any two characters, powered by AI.
You control **both** fighters: pick them, then take turns choosing Attack,
Defend or Tactic for whoever's turn it is.

- **Smart character entry:** type `Goku` and the AI offers up to 5 possible
  shows/games one by one (Yes/No). Type `Goku from Dragon Ball` to skip the guessing.
- **Stats:** Atk, Def and Crit, each with a multiplier and a success chance.
- **Tactic:** a random, lore-accurate move that boosts the chance of Atk, Def or Crit.
- **Sudden death:** after 50 actions the fighter with less HP is knocked out.
- The engine handles dice and damage; the AI creates stats, narrates the fight and
  invents the tactic flavour.

## Run locally

```bash
# inside an activated virtual environment
pip install -r requirements.txt
streamlit run app.py
```

## Configure the AI

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Put your API key in `AI_API_KEY`, and set `AI_MODEL` / `AI_BASE_URL`.

`secrets.toml` is git-ignored. Never put real keys in the `.example` file. If you
deploy on Streamlit Community Cloud, paste the same contents into the app's
**Secrets** settings instead.

Without a key the app runs in an offline **demo mode** with simulated responses.

## Project layout

| Path | Purpose |
| --- | --- |
| `app.py` | Entry point: page config, CSS, navigation |
| `views/` | The two screens (character selection, battle) |
| `core/` | Game rules, data models, session state, UI helpers |
| `services/ai_client.py` | All AI access (live and demo mode) |
| `assets/style.css` | Styling |