import streamlit as st
import db
from utils import format_ingredient_display

db.init_db()

st.title("Manage Data")

# Display any pending success messages
if msg := st.session_state.pop("manage_data_success_msg", None):
    st.success(msg)

# === Tabs for Categories, Stores, Ingredients ===
tab_categories, tab_stores, tab_ingredients = st.tabs(["Categories", "Stores", "Ingredients"])

# =============================================================================
# CATEGORIES TAB
# =============================================================================
with tab_categories:
    categories = db.get_categories()

    # List existing categories
    with st.container(border=True):
        st.subheader(f"Categories ({len(categories)})")
        if categories:
            for _, name in categories:
                st.write(f"- {name}")
        else:
            st.info("No categories yet")

    # Add new category (collapsed expander)
    with st.expander("Add New Category"):
        new_cat_name = st.text_input("Category Name", key="new_cat_name")
        if st.button("Create Category", key="create_cat"):
            if new_cat_name.strip():
                try:
                    db.add_category(new_cat_name.strip())
                    st.session_state["manage_data_success_msg"] = f"Created category: {new_cat_name}"
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e) or "Duplicate" in str(e):
                        st.error("A category with that name already exists!")
                    else:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter a category name")

    # Edit category (collapsed expander)
    if categories:
        with st.expander("Edit Category"):
            cat_options = {name: id for id, name in categories}
            selected_cat_name = st.selectbox("Select Category", options=list(cat_options.keys()), key="edit_cat_select")
            selected_cat_id = cat_options[selected_cat_name]

            # Rename
            new_name = st.text_input("New Name", value=selected_cat_name, key="rename_cat")
            if st.button("Save Name", key="save_cat_name"):
                if new_name.strip() and new_name.strip() != selected_cat_name:
                    try:
                        db.update_category_name(selected_cat_id, new_name.strip())
                        st.session_state["manage_data_success_msg"] = "Category renamed!"
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e) or "Duplicate" in str(e):
                            st.error("A category with that name already exists!")
                        else:
                            st.error(f"Error: {e}")

            # Ingredients in this category
            st.caption("Ingredients in this category")
            ingredients_in_cat = db.get_ingredients_by_category(selected_cat_id)
            if ingredients_in_cat:
                for _, ing_name in ingredients_in_cat:
                    st.write(f"- {ing_name}")
            else:
                st.write("No ingredients in this category.")

            # Delete
            st.divider()
            st.caption("Deleting will set ingredients to uncategorized.")
            if st.button("Delete Category", key="del_cat", type="secondary"):
                st.session_state["confirm_delete_cat"] = True

            if st.session_state.get("confirm_delete_cat"):
                st.warning(f"Delete '{selected_cat_name}'?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes", key="confirm_del_cat_yes", type="primary"):
                        db.delete_category(selected_cat_id)
                        st.session_state["confirm_delete_cat"] = False
                        st.session_state["manage_data_success_msg"] = f"Deleted: {selected_cat_name}"
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key="confirm_del_cat_no"):
                        st.session_state["confirm_delete_cat"] = False
                        st.rerun()

# =============================================================================
# STORES TAB
# =============================================================================
with tab_stores:
    stores = db.get_stores()

    # List existing stores
    with st.container(border=True):
        st.subheader(f"Stores ({len(stores)})")
        if stores:
            for _, name in stores:
                st.write(f"- {name}")
        else:
            st.info("No stores yet")

    # Add new store (collapsed expander)
    with st.expander("Add New Store"):
        new_store_name = st.text_input("Store Name", key="new_store_name")
        if st.button("Create Store", key="create_store"):
            if new_store_name.strip():
                try:
                    db.add_store(new_store_name.strip())
                    st.session_state["manage_data_success_msg"] = f"Created store: {new_store_name}"
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e) or "Duplicate" in str(e):
                        st.error("A store with that name already exists!")
                    else:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter a store name")

    # Edit store (collapsed expander)
    if stores:
        with st.expander("Edit Store"):
            store_options = {name: id for id, name in stores}
            selected_store_name = st.selectbox("Select Store", options=list(store_options.keys()), key="edit_store_select")
            selected_store_id = store_options[selected_store_name]

            # Rename
            new_name = st.text_input("New Name", value=selected_store_name, key="rename_store")
            if st.button("Save Name", key="save_store_name"):
                if new_name.strip() and new_name.strip() != selected_store_name:
                    try:
                        db.update_store_name(selected_store_id, new_name.strip())
                        st.session_state["manage_data_success_msg"] = "Store renamed!"
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e) or "Duplicate" in str(e):
                            st.error("A store with that name already exists!")
                        else:
                            st.error(f"Error: {e}")

            # Ingredients at this store
            st.caption("Ingredients at this store")
            ingredients_at_store = db.get_ingredients_by_store(selected_store_id)
            if ingredients_at_store:
                for _, ing_name in ingredients_at_store:
                    st.write(f"- {ing_name}")
            else:
                st.write("No ingredients at this store.")

            # Delete
            st.divider()
            st.caption("Deleting will remove store from ingredients.")
            if st.button("Delete Store", key="del_store", type="secondary"):
                st.session_state["confirm_delete_store"] = True

            if st.session_state.get("confirm_delete_store"):
                st.warning(f"Delete '{selected_store_name}'?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes", key="confirm_del_store_yes", type="primary"):
                        db.delete_store(selected_store_id)
                        st.session_state["confirm_delete_store"] = False
                        st.session_state["manage_data_success_msg"] = f"Deleted: {selected_store_name}"
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key="confirm_del_store_no"):
                        st.session_state["confirm_delete_store"] = False
                        st.rerun()

# =============================================================================
# INGREDIENTS TAB
# =============================================================================
with tab_ingredients:
    categories = db.get_categories()
    cat_options = ["No category"] + [name for _, name in categories]
    cat_map = {name: id for id, name in categories}

    stores = db.get_stores()
    store_options = ["Any store"] + [name for _, name in stores]
    store_map = {name: id for id, name in stores}

    all_ingredients = db.get_all_ingredients()

    # List existing ingredients grouped by category
    with st.container(border=True):
        st.subheader(f"Ingredients ({len(all_ingredients)})")
        if all_ingredients:
            by_category = {}
            for _, name, _, cat_name, _, store_name in all_ingredients:
                cat_label = cat_name or "Uncategorized"
                if cat_label not in by_category:
                    by_category[cat_label] = []
                by_category[cat_label].append((name, store_name))

            for cat_label in sorted(by_category.keys()):
                st.caption(cat_label)
                for ing_name, store_name in by_category[cat_label]:
                    display = f"- {ing_name}"
                    if store_name:
                        display += f" @ {store_name}"
                    st.write(display)
        else:
            st.info("No ingredients yet")

    # Add new ingredient (collapsed expander)
    with st.expander("Add New Ingredient"):
        new_ing_name = st.text_input("Ingredient Name", key="new_ing_name")
        selected_cat = st.selectbox("Category (optional)", options=cat_options, key="new_ing_cat")
        selected_store = st.selectbox("Sold at (optional)", options=store_options, key="new_ing_store")

        if st.button("Create Ingredient", key="create_ing"):
            if new_ing_name.strip():
                try:
                    cat_id = cat_map.get(selected_cat) if selected_cat != "No category" else None
                    store_id = store_map.get(selected_store) if selected_store != "Any store" else None
                    db.get_or_create_ingredient(new_ing_name.strip(), cat_id, store_id)
                    st.session_state["manage_data_success_msg"] = f"Created ingredient: {new_ing_name}"
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e) or "Duplicate" in str(e):
                        st.error("An ingredient with that name already exists!")
                    else:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter an ingredient name")

    # Edit ingredient (collapsed expander)
    if all_ingredients:
        with st.expander("Edit Ingredient"):
            ing_display = [format_ingredient_display(name, cat_name, store_name)
                           for _, name, _, cat_name, _, store_name in all_ingredients]
            ing_map = {display: (id, name, cat_id, store_id)
                       for display, (id, name, cat_id, _, store_id, _) in zip(ing_display, all_ingredients)}

            selected_display = st.selectbox("Select Ingredient", options=ing_display, key="edit_ing_select")
            selected_id, selected_name, current_cat_id, current_store_id = ing_map[selected_display]

            # Update category
            cat_index = 0
            if current_cat_id:
                for i, (cid, _) in enumerate(categories):
                    if cid == current_cat_id:
                        cat_index = i + 1
                        break
            new_cat = st.selectbox("Category", options=cat_options, index=cat_index, key="edit_ing_cat")
            new_cat_id = cat_map.get(new_cat) if new_cat != "No category" else None

            if new_cat_id != current_cat_id:
                if st.button("Update Category", key="update_ing_cat"):
                    db.set_ingredient_category(selected_id, new_cat_id)
                    st.session_state["manage_data_success_msg"] = "Category updated!"
                    st.rerun()

            # Update store
            store_index = 0
            if current_store_id:
                for i, (sid, _) in enumerate(stores):
                    if sid == current_store_id:
                        store_index = i + 1
                        break
            new_store = st.selectbox("Sold at", options=store_options, index=store_index, key="edit_ing_store")
            new_store_id = store_map.get(new_store) if new_store != "Any store" else None

            if new_store_id != current_store_id:
                if st.button("Update Store", key="update_ing_store"):
                    db.set_ingredient_store(selected_id, new_store_id)
                    st.session_state["manage_data_success_msg"] = "Store updated!"
                    st.rerun()

            # Show which recipes use this ingredient
            st.caption("Used in recipes")
            used_in = db.get_recipes_for_ingredient(selected_id)
            if used_in:
                st.write(", ".join(name for _, name in used_in))
            else:
                st.write("Not used in any recipes.")
