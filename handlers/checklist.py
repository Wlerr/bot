# handlers/checklist.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def send_checklist(query, ck_id: str):
    """
    Собирает список кнопок, используя индексы вместо полных текстов.
    """
    from utils.storage import user_progress

    data = user_progress[ck_id]
    items = data["items"]
    status = data["status"]

    keyboard = []
    for i, text in enumerate(items):
        symbol = "✅" if status[i] else "🔲"
        # callback_data: toggle|<id>|<index>
        keyboard.append([
            InlineKeyboardButton(
                f"{symbol} {text}",
                callback_data=f"toggle|{ck_id}|{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "📤 Отправить отчет",
            callback_data=f"report|{ck_id}"
        )
    ])

    await query.edit_message_text(
        text="📝 *Чек-лист*", parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_handler(update, context):
    """
    Принимает индекс пункта, меняет его статус и перерисовывает.
    """
    from utils.storage import user_progress

    query = update.callback_query
    await query.answer()

    _, ck_id, idx_str = query.data.split("|", 2)
    i = int(idx_str)

    # Инвертируем статус
    user_progress[ck_id]["status"][i] = not user_progress[ck_id]["status"][i]

    # Перерисовываем
    from handlers.checklist import send_checklist
    await send_checklist(query, ck_id)
