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
    for i, (ing_name, qty) in enumerate(st.session_state["new_recipe_ingredients"]):
        col_ing, col_qty, col_del = st.columns([2, 2, 1])
        with col_ing:
            st.write(ing_name)
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
added_names = {name.lower() for name, _ in st.session_state["new_recipe_ingredients"]}

tab_existing, tab_new = st.tabs(["From Catalog", "Create New"])

with tab_existing:
    if all_ingredients:
        available = [(id, name) for id, name in all_ingredients if name.lower() not in added_names]
        if available:
            ing_names = [name for _, name in available]
            selected_ing = st.selectbox("Select Ingredient", options=ing_names)
            quantity = st.text_input("Quantity", key="cat_qty")
            if st.button("Add", key="add_cat"):
                if quantity.strip():
                    st.session_state["new_recipe_ingredients"].append((selected_ing, quantity.strip()))
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
    if st.button("Add", key="add_new"):
        if new_ing.strip() and new_qty.strip():
            if new_ing.strip().lower() in added_names:
                st.error("This ingredient is already added!")
            else:
                st.session_state["new_recipe_ingredients"].append((new_ing.strip(), new_qty.strip()))
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
                recipe_id = db.add_recipe(recipe_name.strip())
                for ing_name, qty in st.session_state["new_recipe_ingredients"]:
                    ing_id = db.get_or_create_ingredient(ing_name)
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
