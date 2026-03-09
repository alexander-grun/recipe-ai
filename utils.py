"""Shared utility functions."""


def get_secret(key: str) -> str:
    """Get a secret from Streamlit secrets or .streamlit/secrets.toml."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        pass
    try:
        import tomllib
        from pathlib import Path
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets[key]
    except Exception as e:
        raise ValueError(f"Could not load {key}: {e}")


def format_ingredient_display(name: str, cat_name: str | None, store_name: str | None) -> str:
    """Format ingredient with category and store info for display."""
    parts = []
    if cat_name:
        parts.append(cat_name)
    if store_name:
        parts.append(f"@ {store_name}")
    return f"{name} ({', '.join(parts)})" if parts else name
