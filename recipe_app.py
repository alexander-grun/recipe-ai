import streamlit as st
import pandas as pd
import db

db.init_db()

st.title("Recipe Manager")

# --- Add Recipe ---
st.header("Add Recipe")
new_recipe = st.text_input("Recipe name")
if st.button("Add Recipe"):
    if new_recipe.strip():
        try:
            recipe_id = db.add_recipe(new_recipe.strip())
            st.success(f"Added recipe: {new_recipe}")
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("Recipe already exists!")
            else:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a recipe name")

# --- Add Ingredient ---
st.header("Add Ingredient")
recipes = db.get_recipes()
if recipes:
    recipe_options = {name: id for id, name in recipes}
    selected_recipe = st.selectbox("Select recipe", options=list(recipe_options.keys()))

    col1, col2 = st.columns(2)
    with col1:
        ingredient = st.text_input("Ingredient")
    with col2:
        quantity = st.text_input("Quantity")

    if st.button("Add Ingredient"):
        if ingredient.strip() and quantity.strip():
            db.add_ingredient(recipe_options[selected_recipe], ingredient.strip(), quantity.strip())
            st.success(f"Added {quantity} {ingredient} to {selected_recipe}")
        else:
            st.warning("Please enter both ingredient and quantity")
else:
    st.info("Add a recipe first to add ingredients")

# --- Shopping List Generator ---
st.header("Shopping List Generator")
if recipes:
    recipe_names = [name for _, name in recipes]
    selected_recipes = st.multiselect("Select recipes for shopping list", options=recipe_names)

    if selected_recipes:
        selected_ids = [recipe_options[name] for name in selected_recipes]
        shopping_list = db.generate_shopping_list(selected_ids)

        if shopping_list:
            st.subheader("Shopping List")
            df = pd.DataFrame(shopping_list, columns=["Ingredient", "Quantities"])
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="shopping_list.csv",
                mime="text/csv"
            )
        else:
            st.info("No ingredients found for selected recipes")
else:
    st.info("Add recipes to generate a shopping list")

# --- View All Ingredients ---
st.header("View Recipe Ingredients")
if recipes:
    view_recipe = st.selectbox("View ingredients for", options=list(recipe_options.keys()), key="view_recipe")
    if view_recipe:
        ingredients = db.get_ingredients([recipe_options[view_recipe]])
        if ingredients:
            ing_df = pd.DataFrame(ingredients, columns=["Recipe", "Ingredient", "Quantity"])
            st.dataframe(ing_df[["Ingredient", "Quantity"]], use_container_width=True)
        else:
            st.info("No ingredients added yet")
