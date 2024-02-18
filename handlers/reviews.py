import datetime
import time

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .commands import States

router = Router()


@router.callback_query(F.data.startswith("review_"))
async def process_review_callback(callback_query: types.CallbackQuery, bot, state: FSMContext):
    score = callback_query.data[-1]
    user_id = callback_query.from_user.id
    text = 'Спасибо за оценку! Оставьте, пожалуйста, отзыв '
    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
    await bot.send_message(user_id, text)
    await state.set_state(States.wait_for_review)
    await state.update_data(score=score)


@router.message(States.wait_for_review)
async def wait_review(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    with open('review_history.txt', mode='a') as rfile:
        print(f"{user_id};{str(datetime.datetime.fromtimestamp(time.time()))};{data['score']};{text}", file=rfile)
    await bot.send_message(chat_id=message.from_user.id, text="Спасибо за обратную связь!")
    await state.clear()
