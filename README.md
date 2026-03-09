# Recipe Manager

A recipe management app with Streamlit web UI and Telegram bot, using MotherDuck (cloud DuckDB) for persistent storage.

## Features

- Add recipes and ingredients
- Generate shopping lists from selected recipes
- Download shopping list as CSV
- Telegram bot with same functionality
- Data persists in MotherDuck cloud

## Setup

### 1. Get MotherDuck Token

1. Create free account at [motherduck.com](https://motherduck.com)
2. Go to Settings → Access Tokens → Create Token

### 2. Configure Secrets

Edit `.streamlit/secrets.toml`:
```toml
BOT_TOKEN = "your-telegram-bot-token"
MOTHERDUCK_TOKEN = "your-motherduck-token"
```

### 3. Install & Run

```bash
pip install -r requirements.txt
streamlit run recipe_app.py
```

Run the Telegram bot (separate terminal):
```bash
python telegram_bot.py
```

## Streamlit Cloud Deployment

1. Push to GitHub (secrets.toml is gitignored)
2. Connect repo to Streamlit Cloud
3. Add `BOT_TOKEN` and `MOTHERDUCK_TOKEN` in Streamlit Cloud secrets

## Telegram Bot Commands

- `/add_recipe <name>` - Add a new recipe
- `/add_ing <recipe|ingredient|quantity>` - Add ingredient to recipe
- `/list` - Show all recipes
- `/shop <recipe1,recipe2>` - Generate shopping list
