# handlers/report.py

from telegram.ext import ContextTypes
from config.config import REPORT_CHAT_IDS

async def report_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Собирает статистику и копию чек-листа, и шлёт её в GROUP_CHAT_ID из конфига.
    """
    from utils.storage import user_progress

    query = update.callback_query
    await query.answer()

    _, ck_id = query.data.split("|", 1)
    data = user_progress[ck_id]

    place = data["place"]
    total = len(data["status"])
    done = sum(data["status"])
    user = data["user"]
    ts = data["timestamp"]
    title = data["title"]

    # Собираем копию чек-листа
    lines = []
    for item, ok in zip(data["items"], data["status"]):
        symbol = "✅" if ok else "🔲"
        lines.append(f"{symbol} {item}")
    checklist_copy = "\n".join(lines)

    # Текст отчёта
    report_text = (
        f"📋 *Отчет по чек-листу*: {title}\n"
        f"👤 *Сотрудник*: {user}\n"
        f"🕒 *Начало*: {ts}\n"
        f"✅ Выполнено: *{done}* из *{total}*\n\n"
        f"📝 *Копия чек-листа:*\n{checklist_copy}"
    )

    # Подтверждаем в личке
    await query.edit_message_text("Спасибо! Ваш отчёт отправлен ✅")

    # Отправляем в группу, назначенную для этой чайной
    report_chat_id = REPORT_CHAT_IDS.get(place)
    if report_chat_id is None:
        # fallback: в личку
        report_chat_id = query.message.chat.id

    await context.bot.send_message(
        chat_id=report_chat_id,
        text=report_text,
        parse_mode="Markdown"
    )

    # (опционально) очистить прогресс
    del user_progress[ck_id]
