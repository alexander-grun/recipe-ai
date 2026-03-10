import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import db
from utils import get_secret

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db.init_db()


def save_user(update: Update):
    """Save user info to database for sending messages from web app."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    db.save_telegram_user(chat_id, user.username if user else None, user.first_name if user else None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update)
    await update.message.reply_text(
        "Recipe Bot Commands:\n"
        "/list - Show all recipes with IDs\n"
        "/view <id> - View recipe ingredients by ID\n\n"
        "You're now registered to receive shopping lists from the web app!"
    )


async def list_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update)
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
        if quantity:
            lines.append(f"- {ing_name}: {quantity}")
        else:
            lines.append(f"- {ing_name}")
    await update.message.reply_text("\n".join(lines))


def main():
    token = get_secret("BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("list", list_recipes))
    app.add_handler(CommandHandler("view", view_recipe))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
