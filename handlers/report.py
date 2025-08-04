# handlers/report.py

from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from utils.storage import user_progress
from handlers.checklist import STATUS_ICONS  # Значки для статусов: None, done, skipped, ignored

async def report_handler(update, context):
    """
    Обработчик нажатия кнопки «📤 Отправить отчёт».
    Он:
      1. Снимает интерактивность с сообщения (редактирует в статичный отчёт).
      2. Подсчитывает количество пунктов в каждом статусе.
      3. Формирует текст отчёта с копией чек-листа.
      4. Редактирует исходное группового сообщение.
      5. Очищает прогресс из памяти.
    """
    # 1. Получаем callback_query и подтверждаем его, чтобы убрать «часики»
    query = update.callback_query
    await query.answer()

    # 2. Разбираем callback_data вида "report|<ck_id>"
    _, ck_id = query.data.split("|", 1)
    data = user_progress.get(ck_id)
    if not data:
        # Если сессия не найдена — выходим
        await query.message.reply_text("❌ Сессия чек-листа не найдена.")
        return

    # 3. Считаем статистику по статусам
    counts = {
        "done":    data["status"].count("done"),
        "skipped": data["status"].count("skipped"),
        "ignored": data["status"].count("ignored"),
        "none":    data["status"].count(None)
    }

    # 4. Собираем копию чек-листа с иконками статусов
    lines = [
        f"{STATUS_ICONS[status]} {text}"
        for status, text in zip(data["status"], data["items"])
    ]
    checklist_copy = "\n".join(lines)

    # 5. Формируем итоговый текст отчёта
    report_text = (
        f"📋 *Отчет по чек-листу*: {data['title']}\n"
        f"👤 *Сотрудник*: {data['user']}\n"
        f"🕒 *Начало*: {data['timestamp']}\n\n"
        f"🍃 Выполнено: *{counts['done']}*\n"
        f"⚠️ Проблемы/неисправности: *{counts['skipped']}*\n"
        f"⁉️ Не понятно: *{counts['ignored']}*\n"
        f"⬜ Не отмечено: *{counts['none']}*\n\n"
        f"📝 *Копия чек-листа:*\n{checklist_copy}"
    )

    # 6. Пытаемся заменить интерактивное сообщение в групповом чате отчётом
    try:
        await context.bot.edit_message_text(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            text=report_text,
            parse_mode=ParseMode.MARKDOWN
        )
    except BadRequest as e:
        # Игнорируем ошибку, если контент не изменился
        if "Message is not modified" not in str(e):
            # Любую другую ошибку пробрасываем дальше
            raise

    # 7. Удаляем прогресс сессии из памяти, чтобы освободить место
    del user_progress[ck_id]
