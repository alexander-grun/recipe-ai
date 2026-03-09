import duckdb

_connection = None


def _get_token():
    try:
        import streamlit as st
        return st.secrets["MOTHERDUCK_TOKEN"]
    except Exception:
        pass
    try:
        import tomllib
        from pathlib import Path
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets["MOTHERDUCK_TOKEN"]
    except Exception as e:
        raise ValueError(f"Could not load MOTHERDUCK_TOKEN: {e}")


def get_connection():
    global _connection
    if _connection is None:
        token = _get_token()
        temp_con = duckdb.connect(f"md:?motherduck_token={token}")
        temp_con.execute("CREATE DATABASE IF NOT EXISTS recipe_app")
        temp_con.close()
        _connection = duckdb.connect(f"md:recipe_app?motherduck_token={token}")
    return _connection


def _is_streamlit_context():
    """Check if running in Streamlit context."""
    try:
        import streamlit as st
        # Try to access runtime - this will fail if not in Streamlit
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


def clear_cache():
    """Clear Streamlit cache if in Streamlit context."""
    if _is_streamlit_context():
        import streamlit as st
        st.cache_data.clear()


def init_db():
    """Initialize database schema and run migrations if needed."""
    con = get_connection()

    # Create recipes table (unchanged)
    con.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)

    # Check if we need to migrate from old schema
    tables = con.execute("SELECT table_name FROM duckdb_tables() WHERE database_name = 'recipe_app'").fetchall()
    table_names = [t[0] for t in tables]

    if 'ingredients' in table_names:
        # Check if it's the old schema (has recipe_id column directly)
        columns = con.execute("""
            SELECT column_name FROM duckdb_columns()
            WHERE database_name = 'recipe_app' AND table_name = 'ingredients'
        """).fetchall()
        column_names = [c[0] for c in columns]

        if 'recipe_id' in column_names:
            # Old schema detected, run migration
            _migrate_to_new_schema(con)
            return

    # New schema - create tables if they don't exist
    con.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity VARCHAR NOT NULL,
            UNIQUE(recipe_id, ingredient_id)
        )
    """)

    # Categories table
    con.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)

    # Stores table
    con.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)

    # Telegram users table (to send messages from web app)
    con.execute("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            chat_id BIGINT PRIMARY KEY,
            username VARCHAR,
            first_name VARCHAR
        )
    """)

    con.execute("CREATE SEQUENCE IF NOT EXISTS recipes_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS ingredients_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS recipe_ingredients_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS categories_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS stores_seq START 1")

    # Migration: add category_id and store_id columns to ingredients if not exists
    try:
        con.execute("ALTER TABLE ingredients ADD COLUMN category_id INTEGER")
    except Exception:
        pass  # Column already exists

    try:
        con.execute("ALTER TABLE ingredients ADD COLUMN store_id INTEGER")
    except Exception:
        pass  # Column already exists


def _migrate_to_new_schema(con):
    """Migrate from old schema to new schema."""
    # Extract unique ingredients from old table
    old_ingredients = con.execute("""
        SELECT DISTINCT ingredient FROM ingredients
    """).fetchall()

    # Get old data for migration
    old_data = con.execute("""
        SELECT recipe_id, ingredient, quantity FROM ingredients
    """).fetchall()

    # Drop old ingredients table
    con.execute("DROP TABLE ingredients")

    # Create new ingredients catalog table
    con.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)

    # Create junction table
    con.execute("""
        CREATE TABLE recipe_ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity VARCHAR NOT NULL,
            UNIQUE(recipe_id, ingredient_id)
        )
    """)

    # Create sequences
    con.execute("CREATE SEQUENCE IF NOT EXISTS recipes_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS ingredients_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS recipe_ingredients_seq START 1")

    # Insert unique ingredients and build mapping
    ingredient_map = {}
    for (ingredient_name,) in old_ingredients:
        ing_id = con.execute("SELECT nextval('ingredients_seq')").fetchone()[0]
        con.execute("INSERT INTO ingredients (id, name) VALUES (?, ?)", [ing_id, ingredient_name])
        ingredient_map[ingredient_name] = ing_id

    # Migrate recipe-ingredient relationships
    for recipe_id, ingredient_name, quantity in old_data:
        ingredient_id = ingredient_map[ingredient_name]
        ri_id = con.execute("SELECT nextval('recipe_ingredients_seq')").fetchone()[0]
        try:
            con.execute("""
                INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?, ?)
            """, [ri_id, recipe_id, ingredient_id, quantity])
        except Exception:
            # Skip duplicates (same recipe + ingredient)
            pass


# ============ Recipe CRUD ============

def add_recipe(name: str) -> int:
    """Add a new recipe and return its ID."""
    con = get_connection()
    recipe_id = con.execute("SELECT nextval('recipes_seq')").fetchone()[0]
    con.execute("INSERT INTO recipes (id, name) VALUES (?, ?)", [recipe_id, name])
    clear_cache()
    return recipe_id


def get_recipes() -> list[tuple[int, str]]:
    """Get all recipes, optionally cached in Streamlit."""
    if _is_streamlit_context():
        return _get_recipes_cached()
    return _get_recipes_uncached()


def _get_recipes_uncached() -> list[tuple[int, str]]:
    con = get_connection()
    return con.execute("SELECT id, name FROM recipes ORDER BY name").fetchall()


def _get_recipes_cached():
    import streamlit as st

    @st.cache_data(ttl=60)
    def fetch():
        con = get_connection()
        return con.execute("SELECT id, name FROM recipes ORDER BY name").fetchall()

    return fetch()


def get_recipe_by_name(name: str) -> tuple[int, str] | None:
    """Get a recipe by name (case-insensitive)."""
    con = get_connection()
    result = con.execute("SELECT id, name FROM recipes WHERE LOWER(name) = LOWER(?)", [name]).fetchone()
    return result


def get_recipe_by_id(recipe_id: int) -> tuple[int, str] | None:
    """Get a recipe by ID."""
    con = get_connection()
    result = con.execute("SELECT id, name FROM recipes WHERE id = ?", [recipe_id]).fetchone()
    return result


def update_recipe_name(recipe_id: int, new_name: str):
    """Update recipe name."""
    con = get_connection()
    con.execute("UPDATE recipes SET name = ? WHERE id = ?", [new_name, recipe_id])
    clear_cache()


def delete_recipe(recipe_id: int):
    """Delete a recipe and its ingredient associations."""
    con = get_connection()
    con.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", [recipe_id])
    con.execute("DELETE FROM recipes WHERE id = ?", [recipe_id])
    clear_cache()


# ============ Category CRUD ============

def add_category(name: str) -> int:
    """Add a new category and return its ID."""
    con = get_connection()
    cat_id = con.execute("SELECT nextval('categories_seq')").fetchone()[0]
    con.execute("INSERT INTO categories (id, name) VALUES (?, ?)", [cat_id, name])
    clear_cache()
    return cat_id


def get_categories() -> list[tuple[int, str]]:
    """Get all categories, optionally cached."""
    if _is_streamlit_context():
        return _get_categories_cached()
    return _get_categories_uncached()


def _get_categories_uncached() -> list[tuple[int, str]]:
    con = get_connection()
    return con.execute("SELECT id, name FROM categories ORDER BY name").fetchall()


def _get_categories_cached():
    import streamlit as st

    @st.cache_data(ttl=60)
    def fetch():
        con = get_connection()
        return con.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

    return fetch()


def update_category_name(category_id: int, new_name: str):
    """Update category name."""
    con = get_connection()
    con.execute("UPDATE categories SET name = ? WHERE id = ?", [new_name, category_id])
    clear_cache()


def delete_category(category_id: int):
    """Delete a category, setting ingredients to uncategorized first."""
    con = get_connection()
    con.execute("UPDATE ingredients SET category_id = NULL WHERE category_id = ?", [category_id])
    con.execute("DELETE FROM categories WHERE id = ?", [category_id])
    clear_cache()


def set_ingredient_category(ingredient_id: int, category_id: int | None):
    """Set or clear the category for an ingredient."""
    con = get_connection()
    con.execute("UPDATE ingredients SET category_id = ? WHERE id = ?", [category_id, ingredient_id])
    clear_cache()


def get_ingredients_by_category(category_id: int | None) -> list[tuple[int, str]]:
    """Get ingredients by category. Pass None for uncategorized."""
    con = get_connection()
    if category_id is None:
        return con.execute(
            "SELECT id, name FROM ingredients WHERE category_id IS NULL ORDER BY name"
        ).fetchall()
    return con.execute(
        "SELECT id, name FROM ingredients WHERE category_id = ? ORDER BY name",
        [category_id]
    ).fetchall()


# ============ Store CRUD ============

def add_store(name: str) -> int:
    """Add a new store and return its ID."""
    con = get_connection()
    store_id = con.execute("SELECT nextval('stores_seq')").fetchone()[0]
    con.execute("INSERT INTO stores (id, name) VALUES (?, ?)", [store_id, name])
    clear_cache()
    return store_id


def get_stores() -> list[tuple[int, str]]:
    """Get all stores, optionally cached."""
    if _is_streamlit_context():
        return _get_stores_cached()
    return _get_stores_uncached()


def _get_stores_uncached() -> list[tuple[int, str]]:
    con = get_connection()
    return con.execute("SELECT id, name FROM stores ORDER BY name").fetchall()


def _get_stores_cached():
    import streamlit as st

    @st.cache_data(ttl=60)
    def fetch():
        con = get_connection()
        return con.execute("SELECT id, name FROM stores ORDER BY name").fetchall()

    return fetch()


def update_store_name(store_id: int, new_name: str):
    """Update store name."""
    con = get_connection()
    con.execute("UPDATE stores SET name = ? WHERE id = ?", [new_name, store_id])
    clear_cache()


def delete_store(store_id: int):
    """Delete a store, setting ingredients to no store first."""
    con = get_connection()
    con.execute("UPDATE ingredients SET store_id = NULL WHERE store_id = ?", [store_id])
    con.execute("DELETE FROM stores WHERE id = ?", [store_id])
    clear_cache()


def set_ingredient_store(ingredient_id: int, store_id: int | None):
    """Set or clear the store for an ingredient."""
    con = get_connection()
    con.execute("UPDATE ingredients SET store_id = ? WHERE id = ?", [store_id, ingredient_id])
    clear_cache()


def get_ingredients_by_store(store_id: int | None) -> list[tuple[int, str]]:
    """Get ingredients by store. Pass None for ingredients without a specific store."""
    con = get_connection()
    if store_id is None:
        return con.execute(
            "SELECT id, name FROM ingredients WHERE store_id IS NULL ORDER BY name"
        ).fetchall()
    return con.execute(
        "SELECT id, name FROM ingredients WHERE store_id = ? ORDER BY name",
        [store_id]
    ).fetchall()


# ============ Ingredient Catalog CRUD ============

def get_all_ingredients() -> list[tuple[int, str, int | None, str | None, int | None, str | None]]:
    """Get all ingredients with category and store info: (id, name, category_id, category_name, store_id, store_name)."""
    if _is_streamlit_context():
        return _get_all_ingredients_cached()
    return _get_all_ingredients_uncached()


def _get_all_ingredients_uncached() -> list[tuple[int, str, int | None, str | None, int | None, str | None]]:
    con = get_connection()
    return con.execute("""
        SELECT i.id, i.name, i.category_id, c.name, i.store_id, s.name
        FROM ingredients i
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN stores s ON i.store_id = s.id
        ORDER BY i.name
    """).fetchall()


def _get_all_ingredients_cached():
    import streamlit as st

    @st.cache_data(ttl=60)
    def fetch():
        con = get_connection()
        return con.execute("""
            SELECT i.id, i.name, i.category_id, c.name, i.store_id, s.name
            FROM ingredients i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN stores s ON i.store_id = s.id
            ORDER BY i.name
        """).fetchall()

    return fetch()


def get_or_create_ingredient(name: str, category_id: int | None = None, store_id: int | None = None) -> int:
    """Get ingredient ID by name, or create if not exists."""
    con = get_connection()
    result = con.execute("SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?)", [name]).fetchone()
    if result:
        return result[0]

    ing_id = con.execute("SELECT nextval('ingredients_seq')").fetchone()[0]
    con.execute("INSERT INTO ingredients (id, name, category_id, store_id) VALUES (?, ?, ?, ?)", [ing_id, name, category_id, store_id])
    clear_cache()
    return ing_id


# ============ Recipe-Ingredient CRUD ============

def add_ingredient_to_recipe(recipe_id: int, ingredient_id: int, quantity: str):
    """Add an ingredient to a recipe with quantity."""
    con = get_connection()
    ri_id = con.execute("SELECT nextval('recipe_ingredients_seq')").fetchone()[0]
    con.execute("""
        INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity)
        VALUES (?, ?, ?, ?)
    """, [ri_id, recipe_id, ingredient_id, quantity])
    clear_cache()


def update_recipe_ingredient(recipe_id: int, ingredient_id: int, quantity: str):
    """Update quantity of an ingredient in a recipe."""
    con = get_connection()
    con.execute("""
        UPDATE recipe_ingredients SET quantity = ?
        WHERE recipe_id = ? AND ingredient_id = ?
    """, [quantity, recipe_id, ingredient_id])
    clear_cache()


def remove_ingredient_from_recipe(recipe_id: int, ingredient_id: int):
    """Remove an ingredient from a recipe."""
    con = get_connection()
    con.execute("""
        DELETE FROM recipe_ingredients WHERE recipe_id = ? AND ingredient_id = ?
    """, [recipe_id, ingredient_id])
    clear_cache()


def get_recipe_ingredients(recipe_id: int) -> list[tuple[int, str, str]]:
    """Get ingredients for a single recipe: (ingredient_id, name, quantity)."""
    if _is_streamlit_context():
        return _get_recipe_ingredients_cached(recipe_id)
    return _get_recipe_ingredients_uncached(recipe_id)


def _get_recipe_ingredients_uncached(recipe_id: int) -> list[tuple[int, str, str]]:
    con = get_connection()
    return con.execute("""
        SELECT i.id, i.name, ri.quantity
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
        ORDER BY i.name
    """, [recipe_id]).fetchall()


def _get_recipe_ingredients_cached(recipe_id: int):
    import streamlit as st

    @st.cache_data(ttl=60)
    def fetch(rid):
        con = get_connection()
        return con.execute("""
            SELECT i.id, i.name, ri.quantity
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
            ORDER BY i.name
        """, [rid]).fetchall()

    return fetch(recipe_id)


# ============ Legacy compatibility / Shopping List ============

def add_ingredient(recipe_id: int, ingredient: str, quantity: str):
    """Legacy function: add ingredient to recipe by name."""
    ingredient_id = get_or_create_ingredient(ingredient)
    add_ingredient_to_recipe(recipe_id, ingredient_id, quantity)


def get_ingredients(recipe_ids: list[int]) -> list[tuple[str, str, str]]:
    """Get ingredients for multiple recipes: (recipe_name, ingredient_name, quantity)."""
    if not recipe_ids:
        return []
    con = get_connection()
    placeholders = ",".join(["?"] * len(recipe_ids))
    return con.execute(f"""
        SELECT r.name, i.name, ri.quantity
        FROM recipe_ingredients ri
        JOIN recipes r ON ri.recipe_id = r.id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id IN ({placeholders})
        ORDER BY r.name, i.name
    """, recipe_ids).fetchall()


def generate_shopping_list(recipe_ids: list[int]) -> list[tuple[str, str]]:
    """Generate aggregated shopping list from multiple recipes."""
    if not recipe_ids:
        return []
    con = get_connection()
    placeholders = ",".join(["?"] * len(recipe_ids))
    return con.execute(f"""
        SELECT i.name, STRING_AGG(ri.quantity || ' (' || r.name || ')', ', ') as quantities
        FROM recipe_ingredients ri
        JOIN recipes r ON ri.recipe_id = r.id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id IN ({placeholders})
        GROUP BY i.name
        ORDER BY i.name
    """, recipe_ids).fetchall()


def get_stats() -> dict:
    """Get dashboard statistics."""
    con = get_connection()
    recipe_count = con.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
    ingredient_count = con.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0]
    category_count = con.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    store_count = con.execute("SELECT COUNT(*) FROM stores").fetchone()[0]
    return {
        "recipe_count": recipe_count,
        "ingredient_count": ingredient_count,
        "category_count": category_count,
        "store_count": store_count,
    }


# ============ Telegram Users ============

def save_telegram_user(chat_id: int, username: str | None, first_name: str | None):
    """Save or update a Telegram user."""
    con = get_connection()
    con.execute("""
        INSERT OR REPLACE INTO telegram_users (chat_id, username, first_name)
        VALUES (?, ?, ?)
    """, [chat_id, username, first_name])


def get_telegram_users() -> list[tuple[int, str | None, str | None]]:
    """Get all saved Telegram users."""
    con = get_connection()
    return con.execute("SELECT chat_id, username, first_name FROM telegram_users").fetchall()


def get_telegram_user_count() -> int:
    """Get count of saved Telegram users."""
    con = get_connection()
    return con.execute("SELECT COUNT(*) FROM telegram_users").fetchone()[0]
