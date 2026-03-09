import requests
import db
from utils import get_secret


def send_to_all_users(message: str) -> tuple[int, int]:
    """Send a message to all registered Telegram users.

    Returns (success_count, fail_count).
    """
    token = get_secret("BOT_TOKEN")
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
