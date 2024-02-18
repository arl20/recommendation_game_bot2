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

from utils.functions_for_recommendation import (games_chosen_to_matrix_line,
                                                get_link,
                                                get_new_recommendations,
                                                get_popular_recommendations,
                                                get_recommendations_by_game,
                                                get_recommendations_by_user,
                                                load_user_data)

router = Router()


class States(StatesGroup):
    wait_for_adding_game = State()
    wait_for_deleting_game = State()
    wait_for_info = State()
    wait_for_similar = State()
    wait_for_review = State()


@router.message(F.text, Command("start"))
async def cmd_start(message: Message, K_GAMES: int, user_data: dict):
    user_id = message.from_user.id
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set()
    user_data[user_id]['k'] = K_GAMES
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
async def get_list_of_game(message: Message, games_info_dict: dict, user_data: dict, K_GAMES: int):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data = await asyncio.to_thread(load_user_data, user_data, user_id, K_GAMES)
    if len(user_data[user_id]['list_of_games']) == 0:
        text = '<b>Список ваших любимых игр пуст</b>\n'
    else:
        text = '<b>Текущий список ваших любимых игр:</b>\n' + '\n'.join(sorted(map(lambda x: games_info_dict[x]['Name'], user_data[user_id]['list_of_games'])))
    await message.answer(text=text, parse_mode=ParseMode.HTML)


@router.message(F.text, Command("clear"))
async def clear_list_of_game(message: Message, user_data: dict, K_GAMES: int):
    user_id = message.from_user.id
    if user_id not in user_data:
        with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
            user_data[user_id] = json.load(file)
            user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
            user_data[user_id]['k'] = int(user_data[user_id]['k'])
    user_data[user_id]['list_of_games'] = set()
    await message.answer(
        text='Список ваших любимых игр очищен'
    )
    logging.log(msg=f"{user_id} game list is cleared", level=logging.INFO)


@router.message(F.text, Command("set_k"))
async def set_k_games(message: Message, command: CommandObject, user_data: dict, K_GAMES: int):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data = await asyncio.to_thread(load_user_data, user_data, user_id, K_GAMES)
    try:
        user_input = command.args.lower()
        user_data[user_id]['k'] = int(user_input)
        if user_data[user_id]['k'] > 0 and user_data[user_id]['k'] <= 20:
            await message.answer(text=f'Установлено значение количества рекомендованных игр {user_input}')
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'w') as file:
                user_data[user_id]['list_of_games'] = list(user_data[user_id]['list_of_games'])
                json.dump(user_data[user_id], file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
            logging.log(msg=f"{user_id} set k = {user_data[user_id]['k']}", level=logging.INFO)
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
                               user_data: dict,
                               similar_games_df,
                               K_GAMES: int,
                               K_NEIGHBOURS: int,
                               matrix,
                               app_id_to_index,
                               user_id_to_index, bot):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data = await asyncio.to_thread(load_user_data, user_data, user_id, K_GAMES)
    get_game_link = partial(get_link, games_info_dict=games_info_dict)
    await message.answer(text="Отлично, сейчас мы порекомендуем вам игры! Это может занять некоторое время")
    popular_list = await asyncio.to_thread(get_popular_recommendations, df, user_data[user_id]['k'])
    popular_list_answer = '\n'.join(map(get_game_link, popular_list))
    new_list = await asyncio.to_thread(get_new_recommendations, df, user_data[user_id]['k'])
    new_list_answer = '\n'.join(map(get_game_link, new_list))
    if len(user_data[user_id]['list_of_games']) == 0:
        await message.answer(text="""К сожалению, вы не дали мне информации
 о ваших любимых играх, поэтому я не могу сделать персональную рекомендацию. Но вы можете поиграть в самые популярные игры!""")
        await message.answer(f"""<b>Популярные игры с высоким рейтингом:</b>
{popular_list_answer}\n
<b>Набирающие популярность новинки:</b>
{new_list_answer}
        """, parse_mode=ParseMode.HTML)
        return
    user_row = await asyncio.to_thread(games_chosen_to_matrix_line, user_data[user_id]['list_of_games'], df, app_id_to_index)
    logging.log(msg=f"recommend for user {user_id}: start", level=logging.INFO)
    recommendations_by_game = await asyncio.to_thread(get_recommendations_by_game,
                                                      similar_games_df,
                                                      user_data[user_id]['list_of_games'], user_data[user_id]['k'])
    recommendations_by_user = await asyncio.to_thread(get_recommendations_by_user, matrix,
                                                      user_row, K_NEIGHBOURS, user_data[user_id]['k'],
                                                      user_id_to_index, app_id_to_index, False)
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
    score = callback_query.data[-1]
    user_id = callback_query.from_user.id
    text = 'Спасибо за оценку!' if score == '5' else 'Спасибо за оценку! Мы будем совершенствовать наши рекомендации'
    with open('rating_history.txt', mode='a') as rfile:
        print(f'{user_id};{str(datetime.datetime.fromtimestamp(time.time()))};{score}', file=rfile)
    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
    await bot.send_message(user_id, text)
