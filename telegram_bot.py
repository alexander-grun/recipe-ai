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
        "/add_recipe <name> - Add a new recipe\n"
        "/add_ing <recipe|ingredient|quantity> - Add ingredient\n"
        "/list - Show all recipes\n"
        "/shop <recipe1,recipe2> - Generate shopping list"
    )


async def add_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_recipe <recipe name>")
        return

    name = " ".join(context.args)
    try:
        recipe_id = db.add_recipe(name)
        await update.message.reply_text(f"Added recipe: {name}")
    except Exception as e:
        if "UNIQUE" in str(e) or "Duplicate" in str(e):
            await update.message.reply_text("Recipe already exists!")
        else:
            await update.message.reply_text(f"Error: {e}")


async def add_ingredient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add_ing <recipe|ingredient|quantity>")
        return

    text = " ".join(context.args)
    parts = text.split("|")
    if len(parts) != 3:
        await update.message.reply_text("Usage: /add_ing <recipe|ingredient|quantity>")
        return

    recipe_name, ingredient, quantity = [p.strip() for p in parts]
    recipe = db.get_recipe_by_name(recipe_name)
    if not recipe:
        await update.message.reply_text(f"Recipe '{recipe_name}' not found")
        return

    db.add_ingredient(recipe[0], ingredient, quantity)
    await update.message.reply_text(f"Added {quantity} {ingredient} to {recipe_name}")


async def list_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipes = db.get_recipes()
    if not recipes:
        await update.message.reply_text("No recipes yet. Add one with /add_recipe")
        return

    text = "Recipes:\n" + "\n".join(f"- {name}" for _, name in recipes)
    await update.message.reply_text(text)


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /shop <recipe1,recipe2,...>")
        return

    recipe_names = [n.strip() for n in " ".join(context.args).split(",")]
    recipe_ids = []

    for name in recipe_names:
        recipe = db.get_recipe_by_name(name)
        if recipe:
            recipe_ids.append(recipe[0])
        else:
            await update.message.reply_text(f"Recipe '{name}' not found")
            return

    shopping_list = db.generate_shopping_list(recipe_ids)
    if not shopping_list:
        await update.message.reply_text("No ingredients found")
        return

    text = "Shopping List:\n" + "\n".join(
        f"- {ingredient}: {quantities}" for ingredient, quantities in shopping_list
    )
    await update.message.reply_text(text)


def main():
    token = get_bot_token()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("add_recipe", add_recipe))
    app.add_handler(CommandHandler("add_ing", add_ingredient))
    app.add_handler(CommandHandler("list", list_recipes))
    app.add_handler(CommandHandler("shop", shop))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
