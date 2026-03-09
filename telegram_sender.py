import requests
import db


def _get_token() -> str:
    try:
        import streamlit as st
        return st.secrets["BOT_TOKEN"]
    except Exception:
        pass
    try:
        import tomllib
        from pathlib import Path
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets["BOT_TOKEN"]
    except Exception as e:
        raise ValueError(f"Could not load BOT_TOKEN: {e}")


def send_to_all_users(message: str) -> tuple[int, int]:
    """Send a message to all registered Telegram users.

    Returns (success_count, fail_count).
    """
    token = _get_token()
    users = db.get_telegram_users()

    success = 0
    fail = 0

    for chat_id, _, _ in users:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=10
            )
            if resp.status_code == 200:
                success += 1
            else:
                fail += 1
        except Exception:
            fail += 1

    return success, fail
