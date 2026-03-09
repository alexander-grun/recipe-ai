import streamlit as st
import db

db.init_db()

st.title("Recipes")

# Display any pending success messages
if msg := st.session_state.pop("recipe_success_msg", None):
    st.success(msg)

# Initialize session state for new recipe
if "new_recipe_ingredients" not in st.session_state:
    st.session_state["new_recipe_ingredients"] = []

# === Tabs: View | Create ===
tab_view, tab_create = st.tabs(["View", "Create"])

# =============================================================================
# VIEW TAB
# =============================================================================
with tab_view:
    # Undo deleted ingredient
    if deleted := st.session_state.get("last_deleted_ing"):
        st.info(f"Removed '{deleted['ing_name']}' from recipe")
        if st.button("Undo", width="stretch", key="view_undo"):
            db.add_ingredient_to_recipe(deleted["recipe_id"], deleted["ing_id"], deleted["quantity"])
            st.session_state.pop("last_deleted_ing")
            st.session_state["recipe_success_msg"] = f"Restored '{deleted['ing_name']}'"
            st.rerun()

    recipes = db.get_recipes()

    if not recipes:
        st.info("No recipes yet. Switch to 'Create' tab to add one!")
    else:
        # Recipe selector
        recipe_options = {name: id for id, name in recipes}
        selected_name = st.selectbox("Select Recipe", options=list(recipe_options.keys()), key="view_recipe_select")
        recipe_id = recipe_options[selected_name]

        # Recipe Detail
        with st.container(border=True):
            st.subheader(selected_name)

            ingredients = db.get_recipe_ingredients(recipe_id)

            if not ingredients:
                st.info("No ingredients yet. Add some below!")
            else:
                for ing_id, ing_name, quantity in ingredients:
                    st.write(f"- **{ing_name}**: {quantity}")

                    # Inline edit/delete
                    if st.session_state.get("editing_ing") == ing_id:
                        new_qty = st.text_input("New quantity", value=quantity, key=f"view_edit_qty_{ing_id}")
                        col_save, col_del, col_cancel = st.columns(3)
                        with col_save:
                            if st.button("Save", key=f"view_save_{ing_id}", width="stretch"):
                                if new_qty.strip() and new_qty != quantity:
                                    db.update_recipe_ingredient(recipe_id, ing_id, new_qty.strip())
                                    st.session_state["recipe_success_msg"] = "Quantity updated!"
                                st.session_state.pop("editing_ing", None)
                                st.rerun()
                        with col_del:
                            if st.button("Remove", key=f"view_del_{ing_id}", type="secondary", width="stretch"):
                                st.session_state["confirm_del_ing"] = {"id": ing_id, "name": ing_name, "quantity": quantity}
                        with col_cancel:
                            if st.button("Cancel", key=f"view_cancel_{ing_id}", width="stretch"):
                                st.session_state.pop("editing_ing", None)
                                st.rerun()

                        # Confirm delete
                        if st.session_state.get("confirm_del_ing", {}).get("id") == ing_id:
                            st.warning(f"Remove '{ing_name}'?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes", key=f"view_confirm_yes_{ing_id}", type="primary", width="stretch"):
                                    db.remove_ingredient_from_recipe(recipe_id, ing_id)
                                    st.session_state.pop("confirm_del_ing")
                                    st.session_state.pop("editing_ing", None)
                                    st.session_state["last_deleted_ing"] = {
                                        "recipe_id": recipe_id,
                                        "ing_id": ing_id,
                                        "ing_name": ing_name,
                                        "quantity": quantity
                                    }
                                    st.rerun()
                            with col_no:
                                if st.button("No", key=f"view_confirm_no_{ing_id}", width="stretch"):
                                    st.session_state.pop("confirm_del_ing")
                                    st.rerun()
                    else:
                        if st.button("Edit", key=f"view_edit_btn_{ing_id}", width="stretch"):
                            st.session_state["editing_ing"] = ing_id
                            st.rerun()

        # Add Ingredient
        with st.expander("Add Ingredient"):
            all_ingredients = db.get_all_ingredients()
            existing_ing_ids = {ing_id for ing_id, _, _ in ingredients}
            available_ingredients = [(id, name, cat_name, store_name)
                                     for id, name, _, cat_name, _, store_name in all_ingredients
                                     if id not in existing_ing_ids]

            view_tab_existing, view_tab_new = st.tabs(["From Catalog", "Create New"])

            with view_tab_existing:
                if available_ingredients:
                    def format_display(name, cat_name, store_name):
                        parts = []
                        if cat_name:
                            parts.append(cat_name)
                        if store_name:
                            parts.append(f"@ {store_name}")
                        return f"{name} ({', '.join(parts)})" if parts else name

                    ing_display = [format_display(name, cat_name, store_name)
                                   for _, name, cat_name, store_name in available_ingredients]
                    ing_map = {display: (id, name) for display, (id, name, _, _)
                               in zip(ing_display, available_ingredients)}
                    selected_display = st.selectbox("Select Ingredient", options=ing_display, key="view_add_existing_select")
                    selected_id, selected_name_val = ing_map[selected_display]
                    quantity = st.text_input("Quantity", key="view_existing_qty")
                    if st.button("Add to Recipe", key="view_add_existing", width="stretch"):
                        if quantity.strip():
                            db.add_ingredient_to_recipe(recipe_id, selected_id, quantity.strip())
                            st.session_state["recipe_success_msg"] = f"Added {selected_name_val}"
                            st.rerun()
                        else:
                            st.warning("Please enter a quantity")
                else:
                    st.info("All catalog ingredients are in this recipe.")

            with view_tab_new:
                new_ing_name = st.text_input("New Ingredient Name", key="view_new_ing_name")
                new_ing_qty = st.text_input("Quantity", key="view_new_qty")

                categories = db.get_categories()
                cat_options = ["No category"] + [name for _, name in categories]
                cat_map = {name: id for id, name in categories}
                selected_cat = st.selectbox("Category (optional)", options=cat_options, key="view_new_ing_cat")

                stores = db.get_stores()
                store_options = ["Any store"] + [name for _, name in stores]
                store_map = {name: id for id, name in stores}
                selected_store = st.selectbox("Sold at (optional)", options=store_options, key="view_new_ing_store")

                if st.button("Create & Add", key="view_add_new", width="stretch"):
                    if new_ing_name.strip() and new_ing_qty.strip():
                        cat_id = cat_map.get(selected_cat) if selected_cat != "No category" else None
                        store_id = store_map.get(selected_store) if selected_store != "Any store" else None
                        ing_id = db.get_or_create_ingredient(new_ing_name.strip(), cat_id, store_id)
                        if ing_id in existing_ing_ids:
                            st.error("This ingredient is already in the recipe!")
                        else:
                            db.add_ingredient_to_recipe(recipe_id, ing_id, new_ing_qty.strip())
                            st.session_state["recipe_success_msg"] = f"Added {new_ing_name}"
                            st.rerun()
                    else:
                        st.warning("Please enter both ingredient name and quantity")

        # Recipe Settings
        with st.expander("Recipe Settings"):
            new_name = st.text_input("Rename recipe", value=selected_name, key="view_rename_input")
            if st.button("Save Name", width="stretch", key="view_save_name"):
                if new_name.strip() and new_name.strip() != selected_name:
                    try:
                        db.update_recipe_name(recipe_id, new_name.strip())
                        st.session_state["recipe_success_msg"] = "Recipe renamed!"
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e) or "Duplicate" in str(e):
                            st.error("A recipe with that name already exists!")
                        else:
                            st.error(f"Error: {e}")

            st.divider()

            if st.button("Delete Recipe", type="secondary", width="stretch", key="view_delete"):
                st.session_state["confirm_delete"] = True

            if st.session_state.get("confirm_delete"):
                st.warning(f"Delete '{selected_name}'?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes", type="primary", key="view_confirm_del_yes", width="stretch"):
                        db.delete_recipe(recipe_id)
                        st.session_state["confirm_delete"] = False
                        st.session_state["recipe_success_msg"] = f"Deleted: {selected_name}"
                        st.rerun()
                with col_no:
                    if st.button("No", key="view_confirm_del_no", width="stretch"):
                        st.session_state["confirm_delete"] = False
                        st.rerun()

# =============================================================================
# CREATE TAB
# =============================================================================
with tab_create:
    # Recipe Name
    recipe_name = st.text_input("Recipe Name", key="create_recipe_name")

    # Current Ingredients
    with st.container(border=True):
        st.subheader("Ingredients")

        if st.session_state["new_recipe_ingredients"]:
            for i, item in enumerate(st.session_state["new_recipe_ingredients"]):
                ing_name = item[0]
                qty = item[1]
                cat_name = item[2] if len(item) > 2 else None
                store_name = item[3] if len(item) > 3 else None

                parts = [ing_name]
                if cat_name:
                    parts.append(cat_name)
                if store_name:
                    parts.append(f"@ {store_name}")
                display = parts[0] if len(parts) == 1 else f"{parts[0]} ({', '.join(parts[1:])})"

                st.write(f"- **{display}**: {qty}")
                if st.button("Remove", key=f"create_remove_{i}", width="stretch"):
                    st.session_state["new_recipe_ingredients"].pop(i)
                    st.rerun()
        else:
            st.info("No ingredients added yet")

    # Add Ingredient
    with st.expander("Add Ingredient", expanded=True):
        all_ingredients = db.get_all_ingredients()
        added_names = {item[0].lower() for item in st.session_state["new_recipe_ingredients"]}

        create_tab_existing, create_tab_new = st.tabs(["From Catalog", "Create New"])

        with create_tab_existing:
            if all_ingredients:
                available = [(id, name, cat_name, store_name)
                             for id, name, _, cat_name, _, store_name in all_ingredients
                             if name.lower() not in added_names]
                if available:
                    def format_display_create(name, cat_name, store_name):
                        parts = []
                        if cat_name:
                            parts.append(cat_name)
                        if store_name:
                            parts.append(f"@ {store_name}")
                        return f"{name} ({', '.join(parts)})" if parts else name

                    ing_display = [format_display_create(name, cat_name, store_name)
                                   for _, name, cat_name, store_name in available]
                    ing_map = {display: (name, cat_name, store_name)
                               for display, (_, name, cat_name, store_name) in zip(ing_display, available)}
                    selected_display = st.selectbox("Select Ingredient", options=ing_display, key="create_cat_select")
                    selected_ing, cat_name, store_name = ing_map[selected_display]
                    quantity = st.text_input("Quantity", key="create_cat_qty")
                    if st.button("Add", key="create_add_cat", width="stretch"):
                        if quantity.strip():
                            st.session_state["new_recipe_ingredients"].append(
                                (selected_ing, quantity.strip(), cat_name, store_name))
                            st.rerun()
                        else:
                            st.warning("Please enter a quantity")
                else:
                    st.info("All catalog ingredients added.")
            else:
                st.info("No ingredients in catalog yet.")

        with create_tab_new:
            new_ing = st.text_input("New Ingredient Name", key="create_new_ing")
            new_qty = st.text_input("Quantity", key="create_new_qty")

            categories = db.get_categories()
            cat_options = ["No category"] + [name for _, name in categories]
            selected_cat = st.selectbox("Category (optional)", options=cat_options, key="create_new_ing_cat")

            stores = db.get_stores()
            store_options = ["Any store"] + [name for _, name in stores]
            selected_store = st.selectbox("Sold at (optional)", options=store_options, key="create_new_ing_store")

            if st.button("Add", key="create_add_new", width="stretch"):
                if new_ing.strip() and new_qty.strip():
                    if new_ing.strip().lower() in added_names:
                        st.error("This ingredient is already added!")
                    else:
                        st.session_state["new_recipe_ingredients"].append(
                            (new_ing.strip(), new_qty.strip(),
                             selected_cat if selected_cat != "No category" else None,
                             selected_store if selected_store != "Any store" else None))
                        st.rerun()
                else:
                    st.warning("Please enter both ingredient name and quantity")

    # Save / Clear
    st.divider()

    if st.button("Save Recipe", type="primary", width="stretch", key="create_save"):
        if not recipe_name.strip():
            st.error("Please enter a recipe name")
        elif not st.session_state["new_recipe_ingredients"]:
            st.error("Please add at least one ingredient")
        else:
            try:
                categories = db.get_categories()
                cat_name_to_id = {name: id for id, name in categories}
                stores = db.get_stores()
                store_name_to_id = {name: id for id, name in stores}

                new_recipe_id = db.add_recipe(recipe_name.strip())
                for item in st.session_state["new_recipe_ingredients"]:
                    ing_name = item[0]
                    qty = item[1]
                    cat_name = item[2] if len(item) > 2 else None
                    store_name = item[3] if len(item) > 3 else None
                    cat_id = cat_name_to_id.get(cat_name) if cat_name else None
                    store_id = store_name_to_id.get(store_name) if store_name else None
                    ing_id = db.get_or_create_ingredient(ing_name, cat_id, store_id)
                    db.add_ingredient_to_recipe(new_recipe_id, ing_id, qty)
                st.session_state["recipe_success_msg"] = f"Created recipe: {recipe_name}"
                st.session_state["new_recipe_ingredients"] = []
                st.rerun()
            except Exception as e:
                if "UNIQUE" in str(e) or "Duplicate" in str(e):
                    st.error("A recipe with that name already exists!")
                else:
                    st.error(f"Error: {e}")

    if st.button("Clear All", width="stretch", key="create_clear"):
        st.session_state["new_recipe_ingredients"] = []
        st.rerun()
