import streamlit as st

st.set_page_config(page_title="Recipe Manager", layout="wide")

import db
import telegram_sender

db.init_db()

# todo create a backup logic for DB
# todo create login with a pin



def home_page():
    st.title("Shopping List")

    recipes = db.get_recipes()

    if not recipes:
        st.info("No recipes yet. Go to 'Create' to add your first recipe!")
        return

    # Shopping list generator - main content
    recipe_options = {name: id for id, name in recipes}
    selected_recipes = st.multiselect(
        "Select recipes",
        options=list(recipe_options.keys()),
        placeholder="Choose recipes..."
    )

    if selected_recipes:
        selected_ids = [recipe_options[name] for name in selected_recipes]
        shopping_list = db.generate_shopping_list(selected_ids)

        if shopping_list:
            # Group by store if available
            all_ingredients = {name: (cat_id, cat_name, store_id, store_name)
                              for _, name, cat_id, cat_name, store_id, store_name in db.get_all_ingredients()}

            # Build text output grouped by store
            by_store = {}
            for ingredient, quantities in shopping_list:
                info = all_ingredients.get(ingredient, (None, None, None, None))
                store_name = info[3] or "Any store"
                if store_name not in by_store:
                    by_store[store_name] = []
                by_store[store_name].append(f"- {ingredient}: {quantities}")

            text_lines = [f"Shopping List: {', '.join(selected_recipes)}", ""]
            for store in sorted(by_store.keys(), key=lambda x: (x == "Any store", x)):
                text_lines.append(f"**{store}**")
                text_lines.extend(by_store[store])
                text_lines.append("")

            with st.container(border=True):
                st.markdown("\n".join(text_lines))

            # Copy-friendly text
            plain_text = "\n".join(text_lines).replace("**", "")

            # Action buttons stacked for mobile
            st.download_button("Download List", plain_text, "shopping_list.txt", "text/plain", width="stretch")

            user_count = db.get_telegram_user_count()
            if user_count == 0:
                st.button("Send to Telegram", disabled=True, help="No users registered. Start the bot and send /start", width="stretch")
            elif st.button("Send to Telegram", width="stretch"):
                success, fail = telegram_sender.send_to_all_users(plain_text)
                if success > 0:
                    st.success(f"Sent to {success} user(s)")
                if fail > 0:
                    st.error(f"Failed for {fail} user(s)")


# Define pages
pg = st.navigation(
    [
        st.Page(home_page, title="Shop", icon=":material/shopping_cart:"),
        st.Page("pages/1_Recipes.py", title="Recipes", icon=":material/menu_book:"),
        st.Page("pages/2_Data.py", title="Data", icon=":material/database:"),
    ],
    position="top",
)
pg.run()
