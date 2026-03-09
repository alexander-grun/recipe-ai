import streamlit as st
import db

db.init_db()

st.title("Manage Categories")

# Create Category section
st.subheader("Create Category")
new_cat_name = st.text_input("Category Name")
if st.button("Create Category"):
    if new_cat_name.strip():
        try:
            db.add_category(new_cat_name.strip())
            st.success(f"Created category: {new_cat_name}")
            st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("A category with that name already exists!")
            else:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a category name")

st.divider()

# Category list and management
categories = db.get_categories()

if not categories:
    st.info("No categories yet. Create one above!")
    st.stop()

st.subheader("Manage Existing Categories")

# Category selector
cat_options = {name: id for id, name in categories}
selected_cat_name = st.selectbox("Select Category", options=list(cat_options.keys()))
selected_cat_id = cat_options[selected_cat_name]

st.divider()

# Rename section
st.subheader("Rename Category")
new_name = st.text_input("New Name", value=selected_cat_name, key="rename_input")
if st.button("Save Name"):
    if new_name.strip() and new_name.strip() != selected_cat_name:
        try:
            db.update_category_name(selected_cat_id, new_name.strip())
            st.success("Category renamed!")
            st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("A category with that name already exists!")
            else:
                st.error(f"Error: {e}")

st.divider()

# View ingredients in category
st.subheader("Ingredients in this Category")
ingredients_in_cat = db.get_ingredients_by_category(selected_cat_id)

if ingredients_in_cat:
    for ing_id, ing_name in ingredients_in_cat:
        st.write(f"- {ing_name}")
else:
    st.info("No ingredients in this category yet.")

st.divider()

# Delete section
st.subheader("Delete Category")
st.caption("Deleting a category will set its ingredients to uncategorized.")

if st.button("Delete Category", type="secondary"):
    st.session_state["confirm_delete_cat"] = True

if st.session_state.get("confirm_delete_cat"):
    st.warning(f"Are you sure you want to delete '{selected_cat_name}'?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, delete", type="primary"):
            db.delete_category(selected_cat_id)
            st.session_state["confirm_delete_cat"] = False
            st.rerun()
    with col_no:
        if st.button("Cancel"):
            st.session_state["confirm_delete_cat"] = False
            st.rerun()
