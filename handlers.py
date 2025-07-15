from aiogram import types, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from quiz_data import quiz_data
from keyboards import generate_options_keyboard
from database import get_quiz_index, update_quiz_index

# Функция регистрации всех хендлеров
def register_handlers(dp: Dispatcher):
    
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Начать игру"))
        await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

    @dp.message(F.text == "Начать игру")
    @dp.message(Command("quiz"))
    async def cmd_quiz(message: types.Message):
        await message.answer("Давайте начнем квиз!")
        await new_quiz(message)

    @dp.callback_query(F.data == "right_answer")
    async def right_answer(callback: types.CallbackQuery):
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        await callback.message.answer("Верно!")

        current_question_index = await get_quiz_index(callback.from_user.id)
        current_question_index += 1
        await update_quiz_index(callback.from_user.id, current_question_index)

        if current_question_index < len(quiz_data):
            await send_question(callback.message, callback.from_user.id)
        else:
            await callback.message.answer("Это был последний вопрос. Квиз завершен!")

    @dp.callback_query(F.data == "wrong_answer")
    async def wrong_answer(callback: types.CallbackQuery):
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )

        current_question_index = await get_quiz_index(callback.from_user.id)
        correct_option = quiz_data[current_question_index]['correct_option']
        await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

        current_question_index += 1
        await update_quiz_index(callback.from_user.id, current_question_index)

        if current_question_index < len(quiz_data):
            await send_question(callback.message, callback.from_user.id)
        else:
            await callback.message.answer("Это был последний вопрос. Квиз завершен!")

    async def new_quiz(message):
        user_id = message.from_user.id
        current_question_index = 0
        await update_quiz_index(user_id, current_question_index)
        await send_question(message, user_id)

    async def send_question(message, user_id):
        current_question_index = await get_quiz_index(user_id)
        question_data = quiz_data[current_question_index]
        correct_option = question_data['correct_option']
        options = question_data['options']
        kb = generate_options_keyboard(options, options[correct_option])
        await message.answer(question_data['question'], reply_markup=kb)
