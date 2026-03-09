import streamlit as st
import db

db.init_db()


def home_page():
    st.title("Recipe Manager")

    # Dashboard stats
    stats = db.get_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Recipes", stats["recipe_count"])
    with col2:
        st.metric("Unique Ingredients", stats["ingredient_count"])

    st.divider()

    # Show recent recipes
    recipes = db.get_recipes()
    if recipes:
        st.subheader("Your Recipes")
        for recipe_id, name in recipes[:5]:
            ingredients = db.get_recipe_ingredients(recipe_id)
            ing_count = len(ingredients)
            st.write(f"- **{name}** ({ing_count} ingredient{'s' if ing_count != 1 else ''})")
        if len(recipes) > 5:
            st.caption(f"...and {len(recipes) - 5} more")
    else:
        st.info("No recipes yet. Go to 'Create Recipe' to add your first recipe!")


# Define pages
pg = st.navigation(
    [
        st.Page(home_page, title="Home", icon=":material/home:"),
        st.Page("pages/1_View_Recipes.py", title="View Recipes", icon=":material/menu_book:"),
        st.Page("pages/2_Create_Recipe.py", title="Create Recipe", icon=":material/add_circle:"),
        st.Page("pages/3_Shopping_List.py", title="Shopping List", icon=":material/shopping_cart:"),
    ],
    position="top",
)
pg.run()
