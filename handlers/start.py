# handlers/start.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes
from utils.storage import CHECKLISTS

async def start_command(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE:
        # если в группе — даём инструкцию
        await context.bot.send_message(
            chat_id=chat.id,
            text="👋 Чтобы начать отчёт по чек-листу, напишите мне в личку: @ВашBotUsername"
        )
        return

    # дальше — сбор интерфейса для ЛС
    keyboard = [
        [InlineKeyboardButton(place, callback_data=f"place|{place}")]
        for place in CHECKLISTS.keys()
    ]
    await context.bot.send_message(
        chat_id=chat.id,
        text="👋 Привет! Выберите чайную для отчёта:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )