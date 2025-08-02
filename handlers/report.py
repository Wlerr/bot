# handlers/report.py

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config.config import REPORT_CHAT_IDS
from utils.storage import user_progress
from handlers.checklist import STATUS_ICONS


parse_mode=ParseMode.MARKDOWN

async def report_handler(update, context: ContextTypes.DEFAULT_TYPE):
    

    query = update.callback_query
    await query.answer()
    _, ck_id = query.data.split("|", 1)
    data = user_progress[ck_id]

    # Собираем статистику
    total = len(data["items"])
    counts = {
        "done": data["status"].count("done"),
        "skipped": data["status"].count("skipped"),
        "ignored": data["status"].count("ignored"),
        "none": data["status"].count(None)
    }

    # Собираем финальный текст чек-листа
    lines = []
    for status, text in zip(data["status"], data["items"]):
        lines.append(f"{STATUS_ICONS[status]} {text}")
    checklist_copy = "\n".join(lines)

    report = (
        f"📋 *Отчет по чек-листу*: {data['title']}\n"
        f"👤 *Сотрудник*: {data['user']}\n"
        f"🕒 *Начало*: {data['timestamp']}\n\n"
        f"✅ Выполнено: *{counts['done']}*\n"
        f"❌ Провалена/отменено: *{counts['skipped']}*\n"
        f"⚠️ Не понятно: *{counts['ignored']}*\n"
        f"⬜ Не отмечено: *{counts['none']}*\n\n"
        f"📝 *Копия чек-листа:*\n{checklist_copy}"
    )

    # Заменяем интерактивное сообщение на статичный отчёт
    await context.bot.edit_message_text(
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        text=report,
        parse_mode=ParseMode.MARKDOWN
    )

    # (опционально) чистим прогресс
    del user_progress[ck_id]
