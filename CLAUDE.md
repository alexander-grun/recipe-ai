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

## Streamlit Rules

- Avoid deprecated `use_container_width` param (use `width='stretch'` or `width='content'`)
- Navigation: `st.navigation()` with `position="top"` for horizontal menu
- Use `st.container(border=True)` to group sections, `st.expander()` for secondary actions
- Mobile-first: single-column layouts, avoid multi-column for main content

## Page Structure

3 pages: **Shop** (shopping list) | **Recipes** (View/Create tabs) | **Data** (Categories/Stores/Ingredients tabs)

## Database Schema

```sql
recipes(id, name UNIQUE)
ingredients(id, name UNIQUE, category_id FK, store_id FK)
recipe_ingredients(id, recipe_id FK, ingredient_id FK, quantity, UNIQUE(recipe_id, ingredient_id))
categories(id, name UNIQUE)
stores(id, name UNIQUE)
telegram_users(chat_id PK, username, first_name)
```
