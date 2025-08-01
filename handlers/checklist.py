# handlers/checklist.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


STATUS_ICONS = {
    None: "⬜",       # не отмечено
    "done": "✅",    # выполнено
    "skipped": "❌", # не выполнено
    "ignored": "⚪"  # проигнорировано
}

def next_status(current):
    order = [None, "done", "skipped", "ignored"]
    idx = order.index(current)
    return order[(idx + 1) % len(order)]


async def send_checklist(bot, ck_id: str):
    """
    Рисует или обновляет чек-лист в общем чате.
    """
    from utils.storage import user_progress
    data = user_progress[ck_id]
    chat_id = data["chat_id"]
    msg_id = data["message_id"]

    keyboard = []
    for idx, text in enumerate(data["items"]):
        icon = STATUS_ICONS[data["status"][idx]]
        cb = f"toggle|{ck_id}|{idx}"
        keyboard.append([InlineKeyboardButton(f"{icon} {text}", callback_data=cb)])

    keyboard.append([InlineKeyboardButton("📤 Отправить отчёт", callback_data=f"report|{ck_id}")])

    # обновляем именно то сообщение, что запомнили
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text="📝 *Чек-лист*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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