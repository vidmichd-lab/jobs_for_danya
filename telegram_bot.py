"""
Telegram bot: add/remove job board URLs, daily digest of design jobs with cover letters.
"""
import asyncio
import json
import logging
from pathlib import Path

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import (
    DATA_DIR,
    URLS_JSON,
    SEEN_JOBS_JSON,
    PROFILE_PATH,
    RESUME_PDF_URL,
    ensure_data_dir,
)
from jobs_scraper import get_new_jobs, _load_seen, _save_seen
from yandex_gpt import generate_cover_letter

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

STATE_JSON = DATA_DIR / "bot_state.json"


def _load_urls() -> list[str]:
    ensure_data_dir()
    if not URLS_JSON.exists():
        return ["https://wise.jobs/jobs"]
    data = json.loads(URLS_JSON.read_text(encoding="utf-8"))
    return list(data.get("urls", []))


def _save_urls(urls: list[str]) -> None:
    ensure_data_dir()
    URLS_JSON.write_text(
        json.dumps({"urls": urls}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_chat_id() -> int | None:
    if not STATE_JSON.exists():
        return None
    try:
        data = json.loads(STATE_JSON.read_text(encoding="utf-8"))
        return data.get("chat_id")
    except Exception:
        return None


def _save_chat_id(chat_id: int) -> None:
    ensure_data_dir()
    data = {}
    if STATE_JSON.exists():
        try:
            data = json.loads(STATE_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["chat_id"] = chat_id
    STATE_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Привет. Я буду присылать подборку design-вакансий с готовым cover letter под каждую.\n\n"
        "Команды:\n"
        "/addurl <ссылка> — добавить страницу с вакансиями\n"
        "/removeurl <ссылка> — удалить ссылку\n"
        "/listurls — показать все ссылки\n"
        "/check — проверить сейчас и прислать новые вакансии\n"
        "/help — справка"
    )


async def cmd_addurl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажи ссылку: /addurl https://example.com/jobs")
        return
    url = context.args[0].strip()
    if not url.startswith("http"):
        url = "https://" + url
    urls = _load_urls()
    if url in urls:
        await update.message.reply_text("Эта ссылка уже в списке.")
        return
    urls.append(url)
    _save_urls(urls)
    await update.message.reply_text(f"Добавлено: {url}\nВсего ссылок: {len(urls)}")


async def cmd_removeurl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажи ссылку: /removeurl https://example.com/jobs")
        return
    url = context.args[0].strip()
    if not url.startswith("http"):
        url = "https://" + url
    urls = _load_urls()
    if url not in urls:
        await update.message.reply_text("Такой ссылки нет в списке.")
        return
    urls.remove(url)
    _save_urls(urls)
    await update.message.reply_text(f"Удалено: {url}\nОсталось ссылок: {len(urls)}")


async def cmd_listurls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    urls = _load_urls()
    if not urls:
        await update.message.reply_text("Список пуст. Добавь ссылку: /addurl <url>")
        return
    text = "Ссылки для мониторинга:\n\n" + "\n".join(f"• {u}" for u in urls)
    await update.message.reply_text(text)


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Проверяю вакансии…")
    urls = _load_urls()
    if not urls:
        await update.message.reply_text("Нет ссылок. Добавь: /addurl <url>")
        return
    try:
        jobs = get_new_jobs(urls)
    except Exception as e:
        logger.exception("Scraper error")
        await update.message.reply_text(f"Ошибка при сборе вакансий: {e}")
        return
    if not jobs:
        await update.message.reply_text("Новых design-вакансий не найдено.")
        return
    sent = 0
    for j in jobs:
        title = j.get("title", "Vacancy")
        url_job = j.get("url", "")
        company = j.get("company", "")
        desc = (j.get("description") or title)[:2000]
        try:
            letter = generate_cover_letter(title, desc, company)
        except Exception as e:
            logger.warning("Ya GPT error for %s: %s", url_job, e)
            letter = "(Не удалось сгенерировать письмо. Проверь YANDEX_API_KEY.)"
        msg = (
            f"<b>{title}</b>\n"
            f"Компания: {company}\n\n"
            f"Ссылка: {url_job}\n\n"
            f"<b>Cover letter:</b>\n{letter}\n\n"
            f"Резюме PDF: {RESUME_PDF_URL}"
        )
        try:
            await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
            sent += 1
        except Exception as e:
            logger.warning("Send error: %s", e)
    if sent < len(jobs):
        await update.message.reply_text(f"Отправлено {sent} из {len(jobs)} вакансий.")
    else:
        await update.message.reply_text(f"Готово. Отправлено вакансий: {sent}.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Бот раз в день (или по /check) проверяет твои ссылки на страницы с вакансиями, "
        "фильтрует design/product/graphic design и присылает тебе каждую вакансию с готовым cover letter и ссылкой на резюме.\n\n"
        "Добавляй и удаляй ссылки через /addurl и /removeurl. Резюме для писем берётся из profile.txt, письма генерирует Yandex GPT."
    )


def run_daily_send(bot_token: str) -> None:
    """Fetch new jobs and send to saved chat_id. Use from cron or scheduler."""
    chat_id = _load_chat_id()
    if not chat_id:
        logger.warning("No chat_id saved; user should /start the bot first.")
        return
    urls = _load_urls()
    if not urls:
        return
    try:
        jobs = get_new_jobs(urls)
    except Exception as e:
        logger.exception("Daily scraper error: %s", e)
        return
    if not jobs:
        return

    async def send_all():
        bot = Bot(token=bot_token)
        for j in jobs:
            title = j.get("title", "Vacancy")
            url_job = j.get("url", "")
            company = j.get("company", "")
            desc = (j.get("description") or title)[:2000]
            try:
                letter = generate_cover_letter(title, desc, company)
            except Exception as e:
                logger.warning("Ya GPT error: %s", e)
                letter = "(Ошибка генерации письма.)"
            msg = (
                f"<b>{title}</b>\n"
                f"Компания: {company}\n\n"
                f"Ссылка: {url_job}\n\n"
                f"<b>Cover letter:</b>\n{letter}\n\n"
                f"Резюме PDF: {RESUME_PDF_URL}"
            )
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            except Exception as e:
                logger.warning("Send error: %s", e)

    asyncio.run(send_all())


def main() -> None:
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in .env")
        return
    ensure_data_dir()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("addurl", cmd_addurl))
    app.add_handler(CommandHandler("removeurl", cmd_removeurl))
    app.add_handler(CommandHandler("listurls", cmd_listurls))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("help", cmd_help))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
