import streamlit as st
import db
import telegram_sender

db.init_db()


def home_page():
    st.title("Recipe Manager")

    recipes = db.get_recipes()

    if not recipes:
        st.info("No recipes yet. Go to 'Create Recipe' to add your first recipe!")
        return

    # Shopping list generator
    st.subheader("Quick Shopping List")
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

            st.markdown("\n".join(text_lines))

            # Copy-friendly text
            plain_text = "\n".join(text_lines).replace("**", "")

            col_dl, col_tg = st.columns(2)
            with col_dl:
                st.download_button("Download List", plain_text, "shopping_list.txt", "text/plain")
            with col_tg:
                user_count = db.get_telegram_user_count()
                if user_count == 0:
                    st.button("Send to Telegram", disabled=True, help="No users registered. Start the bot and send /start")
                elif st.button("Send to Telegram"):
                    success, fail = telegram_sender.send_to_all_users(plain_text)
                    if success > 0:
                        st.success(f"Sent to {success} user(s)")
                    if fail > 0:
                        st.error(f"Failed for {fail} user(s)")

    st.divider()

    # Stats row
    stats = db.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recipes", stats["recipe_count"])
    col2.metric("Ingredients", stats["ingredient_count"])
    col3.metric("Categories", stats["category_count"])
    col4.metric("Stores", stats["store_count"])

    st.divider()

    # Recipe list
    st.subheader("Your Recipes")
    for recipe_id, name in recipes:
        ingredients = db.get_recipe_ingredients(recipe_id)
        ing_count = len(ingredients)
        st.write(f"- **{name}** ({ing_count} ingredient{'s' if ing_count != 1 else ''})")


# Define pages
pg = st.navigation(
    [
        st.Page(home_page, title="Home", icon=":material/home:"),
        st.Page("pages/1_View_Recipes.py", title="Recipes", icon=":material/menu_book:"),
        st.Page("pages/2_Create_Recipe.py", title="Create", icon=":material/add_circle:"),
        st.Page("pages/6_Manage_Ingredients.py", title="Ingredients", icon=":material/egg:"),
        st.Page("pages/4_Manage_Categories.py", title="Categories", icon=":material/category:"),
        st.Page("pages/5_Manage_Stores.py", title="Stores", icon=":material/store:"),
    ],
    position="top",
)
pg.run()
