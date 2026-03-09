import streamlit as st
import db

db.init_db()

st.title("View Recipes")

recipes = db.get_recipes()

if not recipes:
    st.info("No recipes yet. Go to 'Create Recipe' to add one!")
    st.stop()

# Recipe selector
recipe_options = {name: id for id, name in recipes}
selected_name = st.selectbox("Select Recipe", options=list(recipe_options.keys()))
recipe_id = recipe_options[selected_name]

st.divider()

# Recipe detail view
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(selected_name)
with col2:
    if st.button("Delete Recipe", type="secondary"):
        st.session_state["confirm_delete"] = True

# Confirm delete
if st.session_state.get("confirm_delete"):
    st.warning(f"Are you sure you want to delete '{selected_name}'?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, delete", type="primary"):
            db.delete_recipe(recipe_id)
            st.session_state["confirm_delete"] = False
            st.rerun()
    with col_no:
        if st.button("Cancel"):
            st.session_state["confirm_delete"] = False
            st.rerun()
    st.stop()

# Rename recipe
with st.expander("Rename Recipe"):
    new_name = st.text_input("New name", value=selected_name, key="rename_input")
    if st.button("Save Name"):
        if new_name.strip() and new_name.strip() != selected_name:
            try:
                db.update_recipe_name(recipe_id, new_name.strip())
                st.success("Recipe renamed!")
                st.rerun()
            except Exception as e:
                if "UNIQUE" in str(e) or "Duplicate" in str(e):
                    st.error("A recipe with that name already exists!")
                else:
                    st.error(f"Error: {e}")

# Ingredients list
st.subheader("Ingredients")
ingredients = db.get_recipe_ingredients(recipe_id)

if not ingredients:
    st.info("No ingredients yet. Add some below!")
else:
    for ing_id, ing_name, quantity in ingredients:
        col_ing, col_qty, col_del = st.columns([2, 2, 1])
        with col_ing:
            st.write(ing_name)
        with col_qty:
            new_qty = st.text_input(
                "Quantity",
                value=quantity,
                key=f"qty_{ing_id}",
                label_visibility="collapsed"
            )
            if new_qty != quantity:
                db.update_recipe_ingredient(recipe_id, ing_id, new_qty)
                st.rerun()
        with col_del:
            if st.button("X", key=f"del_{ing_id}"):
                db.remove_ingredient_from_recipe(recipe_id, ing_id)
                st.rerun()

# Add ingredient to recipe
st.divider()
st.subheader("Add Ingredient")

all_ingredients = db.get_all_ingredients()
existing_ing_ids = {ing_id for ing_id, _, _ in ingredients}
# all_ingredients is now (id, name, category_id, category_name, store_id, store_name)
available_ingredients = [(id, name, cat_name, store_name) for id, name, _, cat_name, _, store_name in all_ingredients if id not in existing_ing_ids]

tab_existing, tab_new = st.tabs(["From Catalog", "Create New"])

with tab_existing:
    if available_ingredients:
        def format_display(name, cat_name, store_name):
            parts = []
            if cat_name:
                parts.append(cat_name)
            if store_name:
                parts.append(f"@ {store_name}")
            return f"{name} ({', '.join(parts)})" if parts else name

        ing_display = [format_display(name, cat_name, store_name) for _, name, cat_name, store_name in available_ingredients]
        ing_map = {display: (id, name) for display, (id, name, _, _) in zip(ing_display, available_ingredients)}
        selected_display = st.selectbox("Select Ingredient", options=ing_display)
        selected_id, selected_name_val = ing_map[selected_display]
        quantity = st.text_input("Quantity", key="existing_qty")
        if st.button("Add to Recipe", key="add_existing"):
            if quantity.strip():
                db.add_ingredient_to_recipe(recipe_id, selected_id, quantity.strip())
                st.success(f"Added {selected_name_val}")
                st.rerun()
            else:
                st.warning("Please enter a quantity")
    else:
        st.info("All catalog ingredients are already in this recipe. Create a new one below.")

with tab_new:
    new_ing_name = st.text_input("New Ingredient Name")
    new_ing_qty = st.text_input("Quantity", key="new_qty")

    # Category selection (optional)
    categories = db.get_categories()
    cat_options = ["No category"] + [name for _, name in categories]
    cat_map = {name: id for id, name in categories}
    selected_cat = st.selectbox("Category (optional)", options=cat_options, key="new_ing_cat")

    # Store selection (optional)
    stores = db.get_stores()
    store_options = ["Any store"] + [name for _, name in stores]
    store_map = {name: id for id, name in stores}
    selected_store = st.selectbox("Sold at (optional)", options=store_options, key="new_ing_store")

    if st.button("Create & Add", key="add_new"):
        if new_ing_name.strip() and new_ing_qty.strip():
            cat_id = cat_map.get(selected_cat) if selected_cat != "No category" else None
            store_id = store_map.get(selected_store) if selected_store != "Any store" else None
            ing_id = db.get_or_create_ingredient(new_ing_name.strip(), cat_id, store_id)
            if ing_id in existing_ing_ids:
                st.error("This ingredient is already in the recipe!")
            else:
                db.add_ingredient_to_recipe(recipe_id, ing_id, new_ing_qty.strip())
                st.success(f"Added {new_ing_name}")
                st.rerun()
        else:
            st.warning("Please enter both ingredient name and quantity")
