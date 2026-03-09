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
        # First connect to MotherDuck and create database if needed
        temp_con = duckdb.connect(f"md:?motherduck_token={token}")
        temp_con.execute("CREATE DATABASE IF NOT EXISTS recipe_app")
        temp_con.close()
        # Now connect to the database
        _connection = duckdb.connect(f"md:recipe_app?motherduck_token={token}")
    return _connection


def init_db():
    con = get_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            ingredient VARCHAR NOT NULL,
            quantity VARCHAR NOT NULL
        )
    """)
    con.execute("CREATE SEQUENCE IF NOT EXISTS recipes_seq START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS ingredients_seq START 1")


def add_recipe(name: str) -> int:
    con = get_connection()
    recipe_id = con.execute("SELECT nextval('recipes_seq')").fetchone()[0]
    con.execute("INSERT INTO recipes (id, name) VALUES (?, ?)", [recipe_id, name])
    return recipe_id


def add_ingredient(recipe_id: int, ingredient: str, quantity: str):
    con = get_connection()
    ing_id = con.execute("SELECT nextval('ingredients_seq')").fetchone()[0]
    con.execute(
        "INSERT INTO ingredients (id, recipe_id, ingredient, quantity) VALUES (?, ?, ?, ?)",
        [ing_id, recipe_id, ingredient, quantity]
    )


def get_recipes() -> list[tuple[int, str]]:
    con = get_connection()
    return con.execute("SELECT id, name FROM recipes ORDER BY name").fetchall()


def get_recipe_by_name(name: str) -> tuple[int, str] | None:
    con = get_connection()
    result = con.execute("SELECT id, name FROM recipes WHERE LOWER(name) = LOWER(?)", [name]).fetchone()
    return result


def get_ingredients(recipe_ids: list[int]) -> list[tuple[str, str, str]]:
    if not recipe_ids:
        return []
    con = get_connection()
    placeholders = ",".join(["?"] * len(recipe_ids))
    return con.execute(f"""
        SELECT r.name, i.ingredient, i.quantity
        FROM ingredients i
        JOIN recipes r ON i.recipe_id = r.id
        WHERE i.recipe_id IN ({placeholders})
        ORDER BY r.name, i.ingredient
    """, recipe_ids).fetchall()


def generate_shopping_list(recipe_ids: list[int]) -> list[tuple[str, str]]:
    if not recipe_ids:
        return []
    con = get_connection()
    placeholders = ",".join(["?"] * len(recipe_ids))
    return con.execute(f"""
        SELECT ingredient, STRING_AGG(quantity || ' (' || r.name || ')', ', ') as quantities
        FROM ingredients i
        JOIN recipes r ON i.recipe_id = r.id
        WHERE i.recipe_id IN ({placeholders})
        GROUP BY ingredient
        ORDER BY ingredient
    """, recipe_ids).fetchall()
