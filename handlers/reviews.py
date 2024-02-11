import pandas as pd
import numpy as np
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChosenInlineResult, InputTextMessageContent, InlineQueryResultArticle, InlineQuery
from scipy.sparse import csr_matrix, load_npz
from aiogram.enums import ParseMode
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import gdown
import json
import configparser
from functools import partial
import datetime
import time
from aiogram.dispatcher import middlewares
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .commands import States

from utils.functions_for_recommendation import get_key, get_link, load_data, get_popular_recommendations, get_new_recommendations
from utils.functions_for_recommendation import  games_chosen_to_matrix_line, get_recommendations_by_user, get_recommendations_by_game

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
    with open('review_history.txt', mode = 'a') as rfile:
        print(f"{user_id};{str(datetime.datetime.fromtimestamp(time.time()))};{data['score']};{text}", file = rfile)
    await bot.send_message(chat_id = message.from_user.id, text = "Спасибо за обратную связь!")
    await state.clear()
    