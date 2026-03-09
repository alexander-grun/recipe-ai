import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db.init_db()


def get_bot_token() -> str:
    try:
        import streamlit as st
        return st.secrets["BOT_TOKEN"]
    except Exception:
        pass
    try:
        import tomllib
        from pathlib import Path
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets["BOT_TOKEN"]
    except Exception as e:
        raise ValueError(f"Could not load BOT_TOKEN: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Recipe Bot Commands:\n"
        "/list - Show all recipes with IDs\n"
        "/view <id> - View recipe ingredients by ID"
    )


async def list_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipes = db.get_recipes()
    if not recipes:
        await update.message.reply_text("No recipes yet.")
        return

    text = "Recipes:\n" + "\n".join(f"{id}. {name}" for id, name in recipes)
    await update.message.reply_text(text)


async def view_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /view <id>")
        return

    try:
        recipe_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid recipe ID (number)")
        return

    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        await update.message.reply_text(f"Recipe with ID {recipe_id} not found")
        return

    ingredients = db.get_recipe_ingredients(recipe[0])
    if not ingredients:
        await update.message.reply_text(f"{recipe[1]} has no ingredients yet")
        return

    lines = [f"{recipe[1]}:"]
    for _, ing_name, quantity in ingredients:
        lines.append(f"- {ing_name}: {quantity}")
    await update.message.reply_text("\n".join(lines))


def main():
    token = get_bot_token()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("list", list_recipes))
    app.add_handler(CommandHandler("view", view_recipe))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
