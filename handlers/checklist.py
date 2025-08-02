# handlers/checklist.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from utils.storage import user_progress


STATUS_ICONS = {
    None: "⬜",       # не отмечено
    "done": "✅",    # выполнено
    "skipped": "❌", # не выполнено
    "ignored": "⚠️"  # проигнорировано
}

def next_status(current):
    order = [None, "done", "skipped", "ignored"]
    idx = order.index(current)
    return order[(idx + 1) % len(order)]



async def send_checklist(bot, ck_id: str):
    """
    Обновляет сообщение с чек-листом в общем чате.
    """
    

    data = user_progress[ck_id]
    chat_id = data["chat_id"]
    message_id = data["message_id"]

    # Строим кнопки
    keyboard = []
    for idx, text in enumerate(data["items"]):
        icon = STATUS_ICONS[data["status"][idx]]
        cb = f"toggle|{ck_id}|{idx}"
        keyboard.append([InlineKeyboardButton(f"{icon} {text}", callback_data=cb)])

    # Добавляем кнопку отправки отчета
    keyboard.append([
        InlineKeyboardButton("📤 Отправить отчёт", callback_data=f"report|{ck_id}")
    ])

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="📝 *Чек-лист*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise

async def toggle_handler(update, context):
    from utils.storage import user_progress

    query = update.callback_query
    await query.answer()
    _, ck_id, idx_str = query.data.split("|")
    idx = int(idx_str)

    # переключаем статус
    data = user_progress[ck_id]
    data["status"][idx] = next_status(data["status"][idx])

    # перерисовываем в групповом сообщении
    await send_checklist(context.bot, ck_id)