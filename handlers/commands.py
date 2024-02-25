import asyncio
import datetime
import json
import logging
import time
from functools import partial

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from sshtunnel import SSHTunnelForwarder

import time

from utils.functions_for_recommendation import (games_chosen_to_matrix_line,
                                                get_new_recommendations,
                                                get_popular_recommendations,
                                                get_recommendations_by_game,
                                                get_recommendations_by_user)

from utils.utils import get_link, create_user, load_data, get_key, get_conn

router = Router()
    
class States(StatesGroup):
    wait_for_adding_game = State()
    wait_for_deleting_game = State()
    wait_for_info = State()
    wait_for_similar = State()
    wait_for_review = State()


@router.message(F.text, Command("start"))
async def cmd_start(message: Message, K_GAMES: int):
    user_id = message.from_user.id
    functions = f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекомендаций.\n
Вот список моих функций:
/add — добавить игру в список для рекомендаций
/delete — удалить игру из списка для рекомендаций
/list — получить текущий список ваших любимых игр
/clear — очистка списка ваших любимых игр

/info — найти информацию об игре

/set_k — установить значение количества рекомендуемых игр (по умолчанию {K_GAMES})
/recommend — получить список рекомендованных игр
/similar_games —  порекомендовать игры, похожие на конкретную игру

/review — оставить отзыв о работе бота
/help — повторить это сообщение

Можем начать прямо сейчас. Для этого добавь свои любимые игры в список для рекомендаций с помощью функций /add, /delete и /clear.

При использовании функций /add и /delete начни писать название игры и выбери нужную из всплывающего списка. Если подходящей игры там нет, сообщи нам об этом с помощью функции /review
"""
    kb = []
    kb.append([
        InlineKeyboardButton(
            text="Добавить игру в список любимых игр",
            switch_inline_query_current_chat="add "
        )
    ])
    kb.append([
        InlineKeyboardButton(
            text="Удалить игру из списка любимых игр",
            switch_inline_query_current_chat="delete "
        )
    ])
    kb.append([
        InlineKeyboardButton(
            text="Найти информацию об игре",
            switch_inline_query_current_chat="info "
        )
    ])
    await message.answer(functions, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    create_user(user_id=user_id, k_games=K_GAMES)

@router.message(F.text, Command("review"))
async def rating_bot_buttons(message: Message, bot):
    buttons = [
        [types.InlineKeyboardButton(text=f'{i}', callback_data=f'review_{i}') for i in range(1, 6)]
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=message.from_user.id,
                           text='Пожалуйста, оцените качество работы бота. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):',
                           reply_markup=keyboard)


@router.message(F.text, Command("help"))
async def help_info(message: Message, K_GAMES: int):
    functions = f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекомендаций.\n
Вот список моих функций:
/add — добавить игру в список для рекомендаций
/delete — удалить игру из списка для рекомендаций
/list — получить текущий список ваших любимых игр
/clear — очистка списка ваших любимых игр

/info — найти информацию об игре

/set_k — установить значение количества рекомендуемых игр (по умолчанию {K_GAMES})
/recommend — получить список рекомендованных игр
/similar_games —  порекомендовать игры, похожие на конкретную игру

/review — оставить отзыв о работе бота
/help — повторить это сообщение

Можем начать прямо сейчас. Для этого добавь свои любимые игры в список для рекомендаций с помощью функций /add, /delete и /clear.

При использовании функций /add и /delete начни писать название игры и выбери нужную из всплывающего списка. Если подходящей игры там нет, сообщи нам об этом с помощью функции /review
"""
    await message.answer(functions)


@router.message(F.text, Command("add"))
async def add_search_game(message: Message):
    kb = []
    kb.append([
        InlineKeyboardButton(
            text="Да",
            switch_inline_query_current_chat="add "
        )
    ])
    await message.answer(
        text="Вы хотите добавить игру в список ваших любимых игр?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@router.message(F.text, Command("info"))
async def info_search_game(message: Message):
    kb = []
    kb.append([
        InlineKeyboardButton(
            text="Да!",
            switch_inline_query_current_chat="info "
        )
    ])
    await message.answer(
        text="Вывести информацию об игре",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@router.message(F.text, Command("delete"))
async def delete_search_game(message: Message):
    kb = []
    kb.append([
        InlineKeyboardButton(
            text="Да",
            switch_inline_query_current_chat="delete "
        )
    ])
    await message.answer(
        text="Вы хотите удалить игру из списка ваших любимых игр?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@router.message(F.text, Command("list"))
async def get_list_of_game(message: Message, games_info_dict: dict, K_GAMES: int):
    user_id = message.from_user.id
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select list_games from users where id = {user_id}")
    games = cursor.fetchone()[0]
    if len(games) == 0:
        text = '<b>Список ваших любимых игр пуст</b>\n'
    else:
        text = '<b>Текущий список ваших любимых игр:</b>\n' + '\n'.join(sorted(map(lambda x: games_info_dict[x]['Name'], games)))
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    await message.answer(text=text, parse_mode=ParseMode.HTML)


@router.message(F.text, Command("clear"))
async def clear_list_of_game(message: Message, K_GAMES: int):
    user_id = message.from_user.id
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET list_games = ARRAY[]::integer[] WHERE id = {user_id}")
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    await message.answer(
        text='Список ваших любимых игр очищен'
    )
    logging.log(msg=f"{user_id} game list is cleared", level=logging.INFO)


@router.message(F.text, Command("set_k"))
async def set_k_games(message: Message, command: CommandObject, K_GAMES: int):
    user_id = message.from_user.id
    try:
        user_input = command.args.lower()
        k = int(user_input)
        if k > 0 and k <= 20:
            await message.answer(text=f'Установлено значение количества рекомендованных игр {user_input}')
            tunnel, conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(f"select k_games from users where id = {user_id}")
            k_games = cursor.fetchone()
            if len(k_games) == 0:
                create_user(user_id, k)
            else:
                cursor.execute(f"UPDATE users SET k_games = {k} WHERE id = {user_id}")
            cursor.close()
            conn.commit()
            conn.close()
            tunnel.stop()
            logging.log(msg=f"{user_id} set k = {k}", level=logging.INFO)
        else:
            await message.answer("Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20")
    except (AttributeError, ValueError):
        await message.answer("Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20")


@router.message(F.text, Command("similar_games"))
async def similar_search_game(message: Message):
    kb = []
    kb.append([
        InlineKeyboardButton(
            text="Вперед!",
            switch_inline_query_current_chat="search similar "
        )
    ])
    await message.answer(
        text="Введите название игры, и мы порекомендуем похожие на неё игры",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )


@router.message(F.text, Command("recommend"))
async def get_recommended_game(message: Message,
                               df,
                               games_info_dict: dict,
                               games_info_dict_by_name: dict,
                               similar_games_df,
                               K_GAMES: int,
                               K_NEIGHBOURS: int,
                               matrix,
                               app_id_to_index,
                               user_id_to_index, bot):
    user_id = message.from_user.id
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select k_games, list_games from users where id = {user_id}")
    data = cursor.fetchone()
    if len(data) == 0:
        create_user(user_id)
    k_games, list_games = data[0], data[1]
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    get_game_link = partial(get_link, games_info_dict=games_info_dict)
    await message.answer(text="Отлично, сейчас мы порекомендуем вам игры! Это может занять некоторое время")
    popular_list = await asyncio.to_thread(get_popular_recommendations, df, k_games)
    popular_list_answer = '\n'.join(map(get_game_link, popular_list))
    new_list = await asyncio.to_thread(get_new_recommendations, df, k_games)
    new_list_answer = '\n'.join(map(get_game_link, new_list))
    if len(list_games) == 0:
        await message.answer(text="""К сожалению, вы не дали мне информации
 о ваших любимых играх, поэтому я не могу сделать персональную рекомендацию. Но вы можете поиграть в самые популярные игры!""")
        await message.answer(f"""<b>Популярные игры с высоким рейтингом:</b>
{popular_list_answer}\n
<b>Набирающие популярность новинки:</b>
{new_list_answer}
        """, parse_mode=ParseMode.HTML)
        return
    logging.log(msg=f"recommend for user {user_id}: start, k_games = {k_games}", level=logging.INFO)
    recommendations_by_game = await asyncio.to_thread(get_recommendations_by_game,
                                                      similar_games_df,
                                                      list_games, k_games)
    logging.log(msg=f"recommend for user {user_id}: by game", level=logging.INFO)
    user_row = await asyncio.to_thread(games_chosen_to_matrix_line, list_games, df, app_id_to_index)
    recommendations_by_user = await asyncio.to_thread(get_recommendations_by_user, matrix,
                                                      user_row, K_NEIGHBOURS, k_games,
                                                      user_id_to_index, app_id_to_index, False)
    logging.log(msg=f"recommend for user {user_id}: by user", level=logging.INFO)
    recommendations_by_game_answer = '\n'.join(map(get_game_link, recommendations_by_game))
    recommendations_by_user_answer = '\n'.join(map(get_game_link, recommendations_by_user))
    await message.answer(f"""<b>Пользователи, похожие на Вас, играют в:</b>
{recommendations_by_user_answer}\n
<b>Игры, похожие на те, что Вы играли:</b>
{recommendations_by_game_answer}\n
<b>Популярные игры с высоким рейтингом:</b>
{popular_list_answer}\n
<b>Набирающие популярность новинки:</b>
{new_list_answer}
        """, parse_mode=ParseMode.HTML)
    await rating_buttons(message, bot)
    logging.log(msg=f"recommend for user {user_id}: finish", level=logging.INFO)


async def rating_buttons(message: Message, bot):
    buttons = [
        [types.InlineKeyboardButton(text=f'{i}', callback_data=f'rating_{i}') for i in range(1, 6)]
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=message.from_user.id, text='Пожалуйста, оцените качество наших рекомендаций. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):', reply_markup=keyboard)


@router.callback_query(F.data.startswith("rating_"))
async def process_game_callback(callback_query: types.CallbackQuery, bot):
    timestamp = str(datetime.datetime.fromtimestamp(time.time()))
    score = callback_query.data[-1]
    user_id = callback_query.from_user.id
    text = 'Спасибо за оценку!' if score == '5' else 'Спасибо за оценку! Мы будем совершенствовать наши рекомендации'
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"""INSERT INTO rating_rec_history (user_id, datetime, score)
                       VALUES ({user_id}, '{timestamp}', {score})""")
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
    await bot.send_message(user_id, text)
