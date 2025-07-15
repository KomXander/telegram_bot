from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for idx, option in enumerate(answer_options):
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{idx}"
        ))
    builder.adjust(1)
    return builder.as_markup()
