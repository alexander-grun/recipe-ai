import streamlit as st
import pandas as pd
import db

db.init_db()

st.title("Shopping List Generator")

recipes = db.get_recipes()

if not recipes:
    st.info("No recipes yet. Create some recipes first!")
    st.stop()

# Multi-select recipes
recipe_options = {name: id for id, name in recipes}
selected_recipes = st.multiselect(
    "Select recipes to generate shopping list",
    options=list(recipe_options.keys())
)

if not selected_recipes:
    st.info("Select one or more recipes to generate a shopping list")
    st.stop()

# Generate shopping list
selected_ids = [recipe_options[name] for name in selected_recipes]
shopping_list = db.generate_shopping_list(selected_ids)

if not shopping_list:
    st.warning("No ingredients found for selected recipes")
    st.stop()

st.divider()
st.subheader("Shopping List")

# Display as table
df = pd.DataFrame(shopping_list, columns=["Ingredient", "Quantities"])
st.dataframe(df, width="stretch", hide_index=True)

# Export options
st.divider()
st.subheader("Export")

col_csv, col_text = st.columns(2)

with col_csv:
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="shopping_list.csv",
        mime="text/csv"
    )

with col_text:
    # Plain text format
    text_lines = [f"Shopping List for: {', '.join(selected_recipes)}", ""]
    for ingredient, quantities in shopping_list:
        text_lines.append(f"- {ingredient}: {quantities}")
    text_content = "\n".join(text_lines)

    st.download_button(
        label="Download Text",
        data=text_content,
        file_name="shopping_list.txt",
        mime="text/plain"
    )

# Preview text format
with st.expander("Preview Text Format"):
    st.code(text_content, language=None)
