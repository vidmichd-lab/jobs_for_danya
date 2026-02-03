#!/usr/bin/env python3
"""
Run daily job check and send new design vacancies to Telegram.
Use from cron, e.g.:
  0 9 * * * cd /path/to/resu && . .env 2>/dev/null; python run_daily.py
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram_bot import run_daily_send

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Set TELEGRAM_BOT_TOKEN (e.g. in .env)")
        return
    run_daily_send(token)

if __name__ == "__main__":
    main()
