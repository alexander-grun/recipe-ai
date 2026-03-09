# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit web app
streamlit run recipe_app.py

# Run Telegram bot (separate process)
python telegram_bot.py
```

## Architecture

This is a recipe management app with two interfaces sharing a cloud database:

```
┌─────────────────┐     ┌─────────────────┐
│  recipe_app.py  │     │ telegram_bot.py │
│   (Streamlit)   │     │  (python-tg-bot)│
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │    db.py    │
              │ (shared DB) │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │ MotherDuck  │
              │ (cloud DB)  │
              └─────────────┘
```

**db.py** - Database layer connecting to MotherDuck (cloud-hosted DuckDB). Contains all CRUD operations. Both interfaces import this module.

**Secrets** - Stored in `.streamlit/secrets.toml` (gitignored). Required keys: `BOT_TOKEN`, `MOTHERDUCK_TOKEN`. The code tries Streamlit secrets first, then falls back to reading the TOML file directly.

**DuckDB version** - Must use `duckdb==1.4.4` for MotherDuck compatibility. Newer versions are not yet supported.

## Database Schema

```sql
recipes(id INTEGER PK, name VARCHAR UNIQUE)
ingredients(id INTEGER PK, recipe_id FK, ingredient VARCHAR, quantity VARCHAR)
```
