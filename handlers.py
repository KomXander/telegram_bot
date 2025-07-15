from aiogram import types, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from quiz_data import quiz_data
from keyboards import generate_options_keyboard
from database import get_quiz_index, update_quiz_index, save_quiz_result, get_all_results

def register_handlers(dp: Dispatcher):
    
    # Словарь для хранения количества правильных ответов по пользователям
    user_scores = {}

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Начать игру"))
        await message.answer("Добро пожаловать в квиз!!!", reply_markup=builder.as_markup(resize_keyboard=True))

    @dp.message(F.text == "Начать игру")
    @dp.message(Command("quiz"))
    async def cmd_quiz(message: types.Message):
        user_scores[message.from_user.id] = 0  # Сброс счёта
        await message.answer("Давайте начнем квиз!")
        await new_quiz(message)

    @dp.callback_query(lambda c: c.data and c.data.startswith("answer_"))
    async def process_answer(callback: types.CallbackQuery):
        idx = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        current_question_index = await get_quiz_index(user_id)
        question = quiz_data[current_question_index]
        correct_index = question['correct_option']
        selected_text = question['options'][idx]

        # Убираем клавиатуру
        await callback.bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=callback.message.message_id,
            reply_markup=None
        )

        # Выводим выбранный ответ
        await callback.message.answer(f"Вы выбрали: {selected_text}")

        if idx == correct_index:
            await callback.message.answer("Верно!")
            user_scores[user_id] = user_scores.get(user_id, 0) + 1
        else:
            await callback.message.answer(f"Неправильно. Правильный ответ: {question['options'][correct_index]}")

        # Проверяем, последний ли это вопрос
        if current_question_index + 1 == len(quiz_data):
            score = user_scores.get(user_id, 0)
            await save_quiz_result(user_id, score)
            await callback.message.answer(f"Квиз завершен! Ваш результат: {score} из {len(quiz_data)}")
            user_scores.pop(user_id, None)
            await update_quiz_index(user_id, 0)  # Сбрасываем индекс
        else:
            # Переходим к следующему вопросу
            current_question_index += 1
            await update_quiz_index(user_id, current_question_index)
            await send_question(callback.message, user_id)

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        results = await get_all_results()
        if not results:
            await message.answer("Статистика пока пуста.")
            return

        text = "Статистика игроков (user_id: правильных ответов):\n"
        for user_id, correct_answers in results:
            text += f"{user_id}: {correct_answers} из {len(quiz_data)}\n"
        await message.answer(text)

    async def new_quiz(message):
        user_id = message.from_user.id
        user_scores[user_id] = 0
        await update_quiz_index(user_id, 0)
        await send_question(message, user_id)

    async def send_question(message, user_id):
        current_question_index = await get_quiz_index(user_id)
        question_data = quiz_data[current_question_index]
        correct_option = question_data['correct_option']
        options = question_data['options']
        kb = generate_options_keyboard(options, options[correct_option])
        await message.answer(question_data['question'], reply_markup=kb)
