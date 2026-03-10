import streamlit as st

st.set_page_config(page_title="Recipe Manager", layout="wide")

import db
import telegram_sender

db.init_db()

# todo create a backup logic for DB
# todo create login with a pin
# todo add a gallery with pics to browse recepies




def home_page():
    st.title("Shopping List")

    # Initialize extra items session state
    if "extra_items" not in st.session_state:
        st.session_state["extra_items"] = []  # List of ingredient IDs

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

    # Extra items section - for one-off items not in recipes
    all_ingredients = db.get_all_ingredients()
    ingredient_lookup = {ing_id: (name, cat_id, cat_name, store_id, store_name)
                        for ing_id, name, cat_id, cat_name, store_id, store_name in all_ingredients}

    with st.expander("Add extra items"):
        # Filter out already-added catalog ingredients
        added_ids = [x for x in st.session_state["extra_items"] if isinstance(x, int)]
        available = [(ing_id, name) for ing_id, name, *_ in all_ingredients
                    if ing_id not in added_ids]

        # Catalog selection
        if available:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_extra = st.selectbox(
                    "Select ingredient",
                    options=available,
                    format_func=lambda x: x[1],
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("Add"):
                    if selected_extra:
                        st.session_state["extra_items"].append(selected_extra[0])
                        st.rerun()

        # Free text input
        col1, col2 = st.columns([3, 1])
        with col1:
            custom_item = st.text_input("Or type custom item", label_visibility="collapsed", placeholder="Type custom item...")
        with col2:
            if st.button("Add", key="add_custom"):
                if custom_item and custom_item.strip():
                    st.session_state["extra_items"].append(custom_item.strip())
                    st.rerun()

        # Show current extras with remove buttons
        if st.session_state["extra_items"]:
            st.caption("Extra items:")
            for idx, item in enumerate(st.session_state["extra_items"]):
                if isinstance(item, int) and item in ingredient_lookup:
                    name = ingredient_lookup[item][0]
                else:
                    name = str(item)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(name)
                with col2:
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state["extra_items"].pop(idx)
                        st.rerun()

    if selected_recipes or st.session_state["extra_items"]:
        selected_ids = [recipe_options[name] for name in selected_recipes]
        shopping_list = db.generate_shopping_list(selected_ids) if selected_ids else []

        # Build text output grouped by category, then by store
        by_cat_store = {}  # {category: {store: [items]}}

        # Add recipe items
        for ingredient, total_qty, occurrences in shopping_list:
            info = ingredient_lookup.get(
                next((ing_id for ing_id, data in ingredient_lookup.items() if data[0] == ingredient), None),
                (ingredient, None, "Other", None, "")
            )
            cat_name = info[2] or "Other"
            store_name = info[4] or ""

            if total_qty > 0:
                item_text = f"- {ingredient}: {total_qty}"
            elif occurrences > 1:
                item_text = f"- {ingredient} x{occurrences}"
            else:
                item_text = f"- {ingredient}"

            if cat_name not in by_cat_store:
                by_cat_store[cat_name] = {}
            if store_name not in by_cat_store[cat_name]:
                by_cat_store[cat_name][store_name] = []
            by_cat_store[cat_name][store_name].append(item_text)

        # Add extra items (can be int IDs or string free-text)
        for item in st.session_state["extra_items"]:
            if isinstance(item, int) and item in ingredient_lookup:
                name, _, cat_name, _, store_name = ingredient_lookup[item]
                cat_name = cat_name or "Other"
                store_name = store_name or ""
            else:
                name = str(item)
                cat_name = "Other"
                store_name = ""
            item_text = f"- {name}"

            if cat_name not in by_cat_store:
                by_cat_store[cat_name] = {}
            if store_name not in by_cat_store[cat_name]:
                by_cat_store[cat_name][store_name] = []
            by_cat_store[cat_name][store_name].append(item_text)

        if by_cat_store:
            # Build recipes message (if any recipes selected)
            recipes_text = ""
            if selected_recipes:
                recipes_lines = ["Recipes:"]
                for recipe in selected_recipes:
                    recipes_lines.append(f"- {recipe}")
                recipes_text = "\n".join(recipes_lines)

            # Build shopping list message
            list_lines = ["Shopping List:", ""]
            for cat in sorted(by_cat_store.keys(), key=lambda x: (x == "Other", x)):
                list_lines.append(f"**{cat}**")
                stores = by_cat_store[cat]
                # Sort: empty store (any) first, then alphabetical
                for store in sorted(stores.keys(), key=lambda x: (x != "", x)):
                    if store:
                        list_lines.append(f"  @ {store}:")
                    list_lines.extend(f"    {item}" if store else f"  {item}" for item in stores[store])
                list_lines.append("")

            # Display combined view
            display_lines = []
            if recipes_text:
                display_lines.append(recipes_text)
                display_lines.append("")
            display_lines.extend(list_lines)

            with st.container(border=True):
                st.markdown("\n".join(display_lines))

            # Plain text versions for Telegram
            recipes_plain = recipes_text
            list_plain = "\n".join(list_lines).replace("**", "")

            user_count = db.get_telegram_user_count()
            if user_count == 0:
                st.button(":material/send: Send to Telegram", disabled=True, type="primary", help="No users registered. Start the bot and send /start")
            elif st.button(":material/send: Send to Telegram", type="primary"):
                total_success = 0
                total_fail = 0
                # Send recipes first (if any)
                if recipes_plain:
                    success, fail = telegram_sender.send_to_all_users(recipes_plain)
                    total_success = max(total_success, success)
                    total_fail = max(total_fail, fail)
                # Send shopping list
                success, fail = telegram_sender.send_to_all_users(list_plain)
                total_success = max(total_success, success)
                total_fail = max(total_fail, fail)
                if total_success > 0:
                    st.success(f"Sent to {total_success} user(s)")
                if total_fail > 0:
                    st.error(f"Failed for {total_fail} user(s)")


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
