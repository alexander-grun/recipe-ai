import streamlit as st
import db

db.init_db()

st.title("Manage Stores")

# Create Store section
st.subheader("Create Store")
new_store_name = st.text_input("Store Name")
if st.button("Create Store"):
    if new_store_name.strip():
        try:
            db.add_store(new_store_name.strip())
            st.success(f"Created store: {new_store_name}")
            st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("A store with that name already exists!")
            else:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a store name")

st.divider()

# Store list and management
stores = db.get_stores()

if not stores:
    st.info("No stores yet. Create one above!")
    st.stop()

st.subheader("Manage Existing Stores")

# Store selector
store_options = {name: id for id, name in stores}
selected_store_name = st.selectbox("Select Store", options=list(store_options.keys()))
selected_store_id = store_options[selected_store_name]

st.divider()

# Rename section
st.subheader("Rename Store")
new_name = st.text_input("New Name", value=selected_store_name, key="rename_input")
if st.button("Save Name"):
    if new_name.strip() and new_name.strip() != selected_store_name:
        try:
            db.update_store_name(selected_store_id, new_name.strip())
            st.success("Store renamed!")
            st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e) or "Duplicate" in str(e):
                st.error("A store with that name already exists!")
            else:
                st.error(f"Error: {e}")

st.divider()

# View ingredients sold at this store
st.subheader("Ingredients at this Store")
ingredients_at_store = db.get_ingredients_by_store(selected_store_id)

if ingredients_at_store:
    for ing_id, ing_name in ingredients_at_store:
        st.write(f"- {ing_name}")
else:
    st.info("No ingredients marked as sold at this store yet.")

st.divider()

# Delete section
st.subheader("Delete Store")
st.caption("Deleting a store will remove the store association from its ingredients.")

if st.button("Delete Store", type="secondary"):
    st.session_state["confirm_delete_store"] = True

if st.session_state.get("confirm_delete_store"):
    st.warning(f"Are you sure you want to delete '{selected_store_name}'?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, delete", type="primary"):
            db.delete_store(selected_store_id)
            st.session_state["confirm_delete_store"] = False
            st.rerun()
    with col_no:
        if st.button("Cancel"):
            st.session_state["confirm_delete_store"] = False
            st.rerun()
