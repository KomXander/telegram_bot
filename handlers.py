# handlers.py
import logging
from aiogram import types, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from quiz_data import quiz_data
from keyboards import generate_options_keyboard
from database import get_quiz_index, update_quiz_index, save_quiz_result, get_all_results

# Включаем INFO‑логгинг
logging.basicConfig(level=logging.INFO)

def register_handlers(dp: Dispatcher):

    user_scores = {}

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Начать игру"))
        await message.answer("Добро пожаловать в квиз!!!", reply_markup=builder.as_markup(resize_keyboard=True))

    @dp.message(F.text == "Начать игру")
    @dp.message(Command("quiz"))
    async def cmd_quiz(message: types.Message):
        user_scores[message.from_user.id] = 0
        logging.info(f"[QUIZ START] user={message.from_user.id} score reset to 0")
        await message.answer("Давайте начнем квиз!")
        await new_quiz(message)

    @dp.callback_query(lambda c: c.data and c.data.startswith("answer_"))
    async def process_answer(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        idx = int(callback.data.split("_")[1])
        current_question_index = await get_quiz_index(user_id)
        question = quiz_data[current_question_index]
        correct_index = question['correct_option']
        selected_text = question['options'][idx]

        # Логируем входные данные
        logging.info(f"[ANSWER RECEIVED] user={user_id} q_index={current_question_index} "
                     f"selected={idx} correct={correct_index} current_score={user_scores.get(user_id)}")

        # Убираем клавиатуру и показываем выбор
        await callback.bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        await callback.message.answer(f"Вы выбрали: {selected_text}")

        # Считаем баллы
        if idx == correct_index:
            user_scores[user_id] = user_scores.get(user_id, 0) + 1
            await callback.message.answer("Верно!")
        else:
            await callback.message.answer(f"Неправильно. Правильный ответ: {question['options'][correct_index]}")

        # Логируем обновлённый счёт
        logging.info(f"[SCORE UPDATED] user={user_id} new_score={user_scores[user_id]}")

        # Переходим к следующему индексу
        current_question_index += 1
        logging.info(f"[INDEX UPDATED] user={user_id} next_q_index={current_question_index}")

        # Если квиз закончен
        if current_question_index >= len(quiz_data):
            score = user_scores.get(user_id, 0)
            await save_quiz_result(user_id, score)
            await callback.message.answer(f"Квиз завершен! Ваш результат: {score} из {len(quiz_data)}")
            logging.info(f"[QUIZ END] user={user_id} final_score={score}")
            user_scores.pop(user_id, None)
            await update_quiz_index(user_id, 0)
        else:
            await update_quiz_index(user_id, current_question_index)
            await send_question(callback.message, user_id)

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        results = await get_all_results()
        if not results:
            await message.answer("Статистика пока пуста.")
            return
        text = "Статистика игроков (user_id: правильных ответов):\n"
        for uid, correct in results:
            text += f"{uid}: {correct} из {len(quiz_data)}\n"
        await message.answer(text)

    async def new_quiz(message):
        user_id = message.from_user.id
        user_scores[user_id] = 0
        await update_quiz_index(user_id, 0)
        await send_question(message, user_id)

    async def send_question(message, user_id):
        idx = await get_quiz_index(user_id)
        q = quiz_data[idx]
        kb = generate_options_keyboard(q['options'], q['options'][q['correct_option']])
        await message.answer(q['question'], reply_markup=kb)
