import streamlit as st
import db

db.init_db()

st.title("Manage Ingredients")

# Create Ingredient section
st.subheader("Create Ingredient")

new_ing_name = st.text_input("Ingredient Name")

col1, col2 = st.columns(2)
with col1:
    categories = db.get_categories()
    cat_options = ["No category"] + [name for _, name in categories]
    cat_map = {name: id for id, name in categories}
    selected_cat = st.selectbox("Category (optional)", options=cat_options, key="new_cat")

with col2:
    stores = db.get_stores()
    store_options = ["Any store"] + [name for _, name in stores]
    store_map = {name: id for id, name in stores}
    selected_store = st.selectbox("Sold at (optional)", options=store_options, key="new_store")

if st.button("Create Ingredient"):
    if new_ing_name.strip():
        try:
            cat_id = cat_map.get(selected_cat) if selected_cat != "No category" else None
            store_id = store_map.get(selected_store) if selected_store != "Any store" else None
            db.get_or_create_ingredient(new_ing_name.strip(), cat_id, store_id)
            st.success(f"Created ingredient: {new_ing_name}")
            st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("An ingredient with that name already exists!")
            else:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter an ingredient name")

st.divider()

# Ingredient list and editing
all_ingredients = db.get_all_ingredients()

if not all_ingredients:
    st.info("No ingredients yet. Create one above!")
    st.stop()

st.subheader("Edit Ingredients")

# Build display options
def format_ingredient(name, cat_name, store_name):
    parts = []
    if cat_name:
        parts.append(cat_name)
    if store_name:
        parts.append(f"@ {store_name}")
    return f"{name} ({', '.join(parts)})" if parts else name

ing_display = [format_ingredient(name, cat_name, store_name)
               for _, name, _, cat_name, _, store_name in all_ingredients]
ing_map = {display: (id, name, cat_id, store_id)
           for display, (id, name, cat_id, _, store_id, _) in zip(ing_display, all_ingredients)}

selected_display = st.selectbox("Select Ingredient", options=ing_display)
selected_id, selected_name, current_cat_id, current_store_id = ing_map[selected_display]

st.divider()

# Edit section
col_cat, col_store = st.columns(2)

with col_cat:
    st.subheader("Category")
    # Find current category index
    cat_index = 0
    if current_cat_id:
        for i, (cid, cname) in enumerate(categories):
            if cid == current_cat_id:
                cat_index = i + 1  # +1 because "No category" is first
                break

    new_cat = st.selectbox("Category", options=cat_options, index=cat_index, key="edit_cat")
    new_cat_id = cat_map.get(new_cat) if new_cat != "No category" else None

    if new_cat_id != current_cat_id:
        if st.button("Update Category"):
            db.set_ingredient_category(selected_id, new_cat_id)
            st.success("Category updated!")
            st.rerun()

with col_store:
    st.subheader("Store")
    # Find current store index
    store_index = 0
    if current_store_id:
        for i, (sid, sname) in enumerate(stores):
            if sid == current_store_id:
                store_index = i + 1  # +1 because "Any store" is first
                break

    new_store = st.selectbox("Sold at", options=store_options, index=store_index, key="edit_store")
    new_store_id = store_map.get(new_store) if new_store != "Any store" else None

    if new_store_id != current_store_id:
        if st.button("Update Store"):
            db.set_ingredient_store(selected_id, new_store_id)
            st.success("Store updated!")
            st.rerun()

st.divider()

# Show which recipes use this ingredient
st.subheader("Used In Recipes")
recipes = db.get_recipes()
used_in = []
for recipe_id, recipe_name in recipes:
    ingredients = db.get_recipe_ingredients(recipe_id)
    if any(ing_id == selected_id for ing_id, _, _ in ingredients):
        used_in.append(recipe_name)

if used_in:
    for recipe_name in used_in:
        st.write(f"- {recipe_name}")
else:
    st.info("Not used in any recipes yet.")
