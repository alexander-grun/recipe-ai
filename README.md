# Recipe Manager

A recipe management app with Streamlit web UI and Telegram bot, using MotherDuck (cloud DuckDB) for persistent storage.

## Features

- Create and manage recipes with ingredients
- Organize ingredients by category and store
- Generate shopping lists grouped by store
- Send lists to Telegram or download as text
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

- `/start` or `/help` - Show available commands
- `/list` - Show all recipes
- `/view <recipe>` - View recipe ingredients with shopping list option
