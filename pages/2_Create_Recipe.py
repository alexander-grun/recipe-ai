import streamlit as st
import db

db.init_db()

st.title("Create Recipe")

# Initialize session state for new recipe
if "new_recipe_ingredients" not in st.session_state:
    st.session_state["new_recipe_ingredients"] = []

# Recipe name
recipe_name = st.text_input("Recipe Name")

st.divider()

# Ingredients to add
st.subheader("Ingredients")

if st.session_state["new_recipe_ingredients"]:
    for i, item in enumerate(st.session_state["new_recipe_ingredients"]):
        # Handle (name, qty, category, store) format
        ing_name = item[0]
        qty = item[1]
        cat_name = item[2] if len(item) > 2 else None
        store_name = item[3] if len(item) > 3 else None

        col_ing, col_qty, col_del = st.columns([2, 2, 1])
        with col_ing:
            parts = [ing_name]
            if cat_name:
                parts.append(cat_name)
            if store_name:
                parts.append(f"@ {store_name}")
            display = parts[0] if len(parts) == 1 else f"{parts[0]} ({', '.join(parts[1:])})"
            st.write(display)
        with col_qty:
            st.write(qty)
        with col_del:
            if st.button("X", key=f"remove_{i}"):
                st.session_state["new_recipe_ingredients"].pop(i)
                st.rerun()
else:
    st.info("No ingredients added yet")

# Add ingredient section
st.divider()
st.subheader("Add Ingredient")

all_ingredients = db.get_all_ingredients()
added_names = {item[0].lower() for item in st.session_state["new_recipe_ingredients"]}

tab_existing, tab_new = st.tabs(["From Catalog", "Create New"])

with tab_existing:
    if all_ingredients:
        # all_ingredients is now (id, name, category_id, category_name, store_id, store_name)
        available = [(id, name, cat_name, store_name) for id, name, _, cat_name, _, store_name in all_ingredients if name.lower() not in added_names]
        if available:
            def format_display(name, cat_name, store_name):
                parts = []
                if cat_name:
                    parts.append(cat_name)
                if store_name:
                    parts.append(f"@ {store_name}")
                return f"{name} ({', '.join(parts)})" if parts else name

            ing_display = [format_display(name, cat_name, store_name) for _, name, cat_name, store_name in available]
            ing_map = {display: (name, cat_name, store_name) for display, (_, name, cat_name, store_name) in zip(ing_display, available)}
            selected_display = st.selectbox("Select Ingredient", options=ing_display)
            selected_ing, cat_name, store_name = ing_map[selected_display]
            quantity = st.text_input("Quantity", key="cat_qty")
            if st.button("Add", key="add_cat"):
                if quantity.strip():
                    st.session_state["new_recipe_ingredients"].append((selected_ing, quantity.strip(), cat_name, store_name))
                    st.rerun()
                else:
                    st.warning("Please enter a quantity")
        else:
            st.info("All catalog ingredients added. Create a new one below.")
    else:
        st.info("No ingredients in catalog yet. Create a new one below.")

with tab_new:
    new_ing = st.text_input("New Ingredient Name")
    new_qty = st.text_input("Quantity", key="new_qty")

    # Category selection (optional)
    categories = db.get_categories()
    cat_options = ["No category"] + [name for _, name in categories]
    selected_cat = st.selectbox("Category (optional)", options=cat_options, key="new_ing_cat")

    # Store selection (optional)
    stores = db.get_stores()
    store_options = ["Any store"] + [name for _, name in stores]
    selected_store = st.selectbox("Sold at (optional)", options=store_options, key="new_ing_store")

    if st.button("Add", key="add_new"):
        if new_ing.strip() and new_qty.strip():
            if new_ing.strip().lower() in added_names:
                st.error("This ingredient is already added!")
            else:
                # Store category and store names with ingredient for later creation
                st.session_state["new_recipe_ingredients"].append(
                    (new_ing.strip(), new_qty.strip(),
                     selected_cat if selected_cat != "No category" else None,
                     selected_store if selected_store != "Any store" else None)
                )
                st.rerun()
        else:
            st.warning("Please enter both ingredient name and quantity")

# Save recipe
st.divider()
col_save, col_clear = st.columns(2)

with col_save:
    if st.button("Save Recipe", type="primary"):
        if not recipe_name.strip():
            st.error("Please enter a recipe name")
        elif not st.session_state["new_recipe_ingredients"]:
            st.error("Please add at least one ingredient")
        else:
            try:
                # Build name -> id maps for categories and stores
                categories = db.get_categories()
                cat_name_to_id = {name: id for id, name in categories}
                stores = db.get_stores()
                store_name_to_id = {name: id for id, name in stores}

                recipe_id = db.add_recipe(recipe_name.strip())
                for item in st.session_state["new_recipe_ingredients"]:
                    ing_name = item[0]
                    qty = item[1]
                    cat_name = item[2] if len(item) > 2 else None
                    store_name = item[3] if len(item) > 3 else None
                    cat_id = cat_name_to_id.get(cat_name) if cat_name else None
                    store_id = store_name_to_id.get(store_name) if store_name else None
                    ing_id = db.get_or_create_ingredient(ing_name, cat_id, store_id)
                    db.add_ingredient_to_recipe(recipe_id, ing_id, qty)
                st.success(f"Created recipe: {recipe_name}")
                st.session_state["new_recipe_ingredients"] = []
                st.rerun()
            except Exception as e:
                if "UNIQUE" in str(e) or "Duplicate" in str(e):
                    st.error("A recipe with that name already exists!")
                else:
                    st.error(f"Error: {e}")

with col_clear:
    if st.button("Clear All"):
        st.session_state["new_recipe_ingredients"] = []
        st.rerun()
