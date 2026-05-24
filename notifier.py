import requests, time
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BOT_NAME
from logger import logger

ICONS = {
    "INFO":"ℹ️","BUY":"🟢","SELL":"🔴","HOLD":"⏸","STOP":"⛔",
    "ERROR":"🚨","WARNING":"⚠️","PROFIT":"💰","LOSS":"📉",
    "MARKET":"🌍","REPORT":"📊","ALIVE":"💓","RECOVER":"📈",
}
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_telegram(message: str, alert_type: str = "INFO") -> bool:
    icon = ICONS.get(alert_type, "📌")
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"{icon} *{BOT_NAME}* [{alert_type}]\n"
        f"🕐 `{ts}`\n"
        f"{'─'*28}\n"
        f"{message}"
    )
    for attempt in range(3):
        try:
            r = requests.post(
                f"{BASE_URL}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID,
                      "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
            if r.ok:
                logger.info(f"Telegram [{alert_type}] sent")
                return True
            logger.warning(f"Telegram failed: {r.status_code}")
            return False
        except Exception as e:
            logger.error(f"Telegram error attempt {attempt+1}: {e}")
            time.sleep(2)
    return False

def get_updates(offset: int = 0) -> list:
    try:
        r = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 10},
            timeout=15
        )
        if r.ok:
            return r.json().get("result", [])
    except Exception as e:
        logger.error(f"getUpdates error: {e}")
    return []
