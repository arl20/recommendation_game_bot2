import pandas as pd
import numpy as np
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, ChosenInlineResult, InputTextMessageContent, InlineQueryResultArticle
from scipy.sparse import csr_matrix, load_npz
from aiogram.enums import ParseMode
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import gdown
import json
import configparser
from functools import partial
import functions_for_recommendation as rec
import datetime
import time

dp = Dispatcher()
router = Router()
dp.include_routers(router)

class States(StatesGroup):
    wait_for_adding_game = State()
    wait_for_deleting_game = State()
    wait_for_info = State()
    wait_for_similar = State()
    wait_for_review = State()
    
async def rating_buttons(bot, message: Message):  
    buttons = [
        [types.InlineKeyboardButton(text=f'{i}', callback_data=f'rating_{i}') for i in range(1, 6)]
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id = message.from_user.id, text = 'Пожалуйста, оцените качество наших рекомендаций. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):', reply_markup=keyboard)
    
    
@dp.callback_query(F.data.startswith("rating_"))
async def process_game_callback(callback_query: types.CallbackQuery, bot):
    score = callback_query.data[-1]
    user_id = callback_query.from_user.id
    text = 'Спасибо за оценку!' if score == '5' else 'Спасибо за оценку! Мы будем совершенствовать наши рекомендации'
    with open('rating_history.txt', mode = 'a') as rfile:
        print(f'{user_id};{str(datetime.datetime.fromtimestamp(time.time()))};{score}', file = rfile)
    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
    await bot.send_message(user_id, text)
    
async def rating_bot_buttons(bot, message: Message):  
    buttons = [
        [types.InlineKeyboardButton(text=f'{i}', callback_data=f'review_{i}') for i in range(1, 6)]
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id = message.from_user.id, text = 'Пожалуйста, оцените качество работы бота. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):', reply_markup=keyboard)

@dp.callback_query(F.data.startswith("review_"))
async def process_game_callback(callback_query: types.CallbackQuery, bot, state: FSMContext):
    score = callback_query.data[-1]
    user_id = callback_query.from_user.id
    text = 'Спасибо за оценку! Оставьте, пожалуйста, отзыв '
    await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
    await bot.send_message(user_id, text)
    await state.set_state(States.wait_for_review)
    await state.update_data(score=score)

@dp.message(States.wait_for_review)
async def wait_review(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    with open('review_history.txt', mode = 'a') as rfile:
        print(f"{user_id};{str(datetime.datetime.fromtimestamp(time.time()))};{data['score']};{text}", file = rfile)
    await bot.send_message(chat_id = message.from_user.id, text = "Спасибо за обратную связь!")
    await state.clear()
    
@dp.message(F.text, Command("start"))
async def cmd_start(message: Message, K_GAMES: int, user_data: dict):
    user_id = message.from_user.id
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set()
    user_data[user_id]['k'] = K_GAMES
    functions = f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекоммендаций.\n
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
"""
    await message.answer(functions)
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
    await message.answer(
        text="Можем начать прямо сейчас",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.message(F.text, Command("help"))
async def help_info(message: Message, K_GAMES: int):
    functions = f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекоммендаций.\n
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
/help — повторить это сообщение"""
    await message.answer(functions)  
    
@dp.message(F.text, Command("review"))
async def help_info(message: Message, bot):
    await rating_bot_buttons(bot, message)
    
@router.inline_query(F.query.startswith("add "))
async def search_add_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict, user_data: dict):
    user_input = query.query.lower()[4:].strip()
    game_list = list(games_info_dict_by_name.keys())
    similar_games = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games) 
        ]
    await query.answer(results, is_personal=True, cache_time=0)
    await state.update_data(games = results.copy())
    await state.set_state(States.wait_for_adding_game)
    
@router.chosen_inline_result(States.wait_for_adding_game)
async def add_game(chosen_result: ChosenInlineResult, bot, state: FSMContext, games_info_dict_by_name: dict, 
                   user_data: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    user_data[user_id]['list_of_games'].add(appid)
    with open(f'recommendation_bot_data/userdata/{user_id}.json', 'w') as file:
        user_data[user_id]['list_of_games'] = list(user_data[user_id]['list_of_games'])
        json.dump(user_data[user_id], file)
        user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
    await state.clear()
    logging.log(msg = f"{game} add to {user_id} list", level=logging.INFO)
    await bot.send_message(chat_id = user_id, text = f"Игра {game} добавлена в список ваших любимых игр")
    
    
@router.inline_query(F.query.startswith("delete "))
async def search_delete_handler(query: InlineQuery, state: FSMContext, 
                                games_info_dict: dict,
                                games_info_dict_by_name: dict, user_data: dict):
    user_id = query.from_user.id
    user_input = query.query.lower()[7:].strip()
    game_list = [games_info_dict[i]['Name'] for i in user_data[user_id]['list_of_games']]
    similar_games = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games) 
        ]
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games = results.copy())
    await state.set_state(States.wait_for_deleting_game)
    
@router.chosen_inline_result(States.wait_for_deleting_game)
async def delete_game(chosen_result: ChosenInlineResult, bot, state: FSMContext,
                      games_info_dict: dict,
                      games_info_dict_by_name: dict, user_data: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    user_data[user_id]['list_of_games'].remove(appid)
    with open(f'recommendation_bot_data/userdata/{user_id}.json', 'w') as file:
        user_data[user_id]['list_of_games'] = list(user_data[user_id]['list_of_games'])
        json.dump(user_data[user_id], file)
        user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
    await state.clear()
    logging.log(msg = f"{game} delete from {user_id} list", level=logging.INFO)
    await bot.send_message(chat_id = user_id, text = f"Игра {game} удалена из списка ваших любимых игр")
    
@router.inline_query(F.query.startswith("info "))
async def search_info_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict, user_data: dict):
    user_id = query.from_user.id
    user_input = query.query.lower()[5:].strip()
    game_list = list(games_info_dict_by_name.keys())
    similar_games = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games) 
        ]
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games = results.copy())
    await state.set_state(States.wait_for_info)
    
@router.chosen_inline_result(States.wait_for_info)
async def info_game(chosen_result: ChosenInlineResult, state: FSMContext, bot,
                    games_info_dict: dict, games_info_dict_by_name: dict, user_data: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    info = f"""Информация об игре {games_info_dict[appid]['Name']}
<b>Возрастное ограничение:</b> {games_info_dict[appid]['Required age']}
<b>Жанры:</b> {games_info_dict[appid]['Genres']}
<b>Описание:</b> {games_info_dict[appid]['About the game']}
<a href="store.steampowered.com/app/{appid}">Ссылка на steam</a>
"""
    await state.clear()
    await bot.send_message(chat_id = user_id, text = info, parse_mode = ParseMode.HTML)
    logging.log(msg = f"info for user {user_id}", level=logging.INFO)
    
    
@dp.message(F.text, Command("add"))
async def add_search_game(message: Message,
                      command: CommandObject):
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
    
@dp.message(F.text, Command("info"))
async def info_search_game(message: Message,
                      command: CommandObject):
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
    
@dp.message(F.text, Command("delete"))
async def delete_search_game(message: Message,
                      command: CommandObject):
    
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
    
@dp.message(F.text, Command("list"))
async def get_list_of_game(message: Message,
                      command: CommandObject, games_info_dict: dict, user_data: dict, K_GAMES: int):
    user_id = message.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    if len(user_data[user_id]['list_of_games']) == 0:
        text = '<b>Список ваших любимых игр пуст</b>\n'
    else:
        text='<b>Текущий список ваших любимых игр:</b>\n' + '\n'.join(sorted(map(lambda x: games_info_dict[x]['Name'], user_data[user_id]['list_of_games'])))
    await message.answer(text = text, parse_mode = ParseMode.HTML)
    
@dp.message(F.text, Command("clear"))
async def clear_list_of_game(message: Message,
                      command: CommandObject, user_data: dict, K_GAMES: int):
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
    logging.log(msg = f"{user_id} game list is cleared", level=logging.INFO)
    
@dp.message(F.text, Command("set_k"))
async def set_k_games(message: Message,
                      command: CommandObject, user_data: dict, K_GAMES: int):
    user_id = message.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    try:
        user_input = command.args.lower()
        user_data[user_id]['k'] = int(user_input)
        if user_data[user_id]['k']  > 0 and user_data[user_id]['k']  <= 20:
            await message.answer(text=f'Установлено значение количества рекомендованных игр {user_input}')
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'w') as file:
                user_data[user_id]['list_of_games'] = list(user_data[user_id]['list_of_games'])
                json.dump(user_data[user_id], file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
            logging.log(msg = f"{user_id} set k = {user_data[user_id]['k']}", level=logging.INFO)
        else:
            await message.answer(
            "Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20"
        )
    except:
        await message.answer(
            "Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20"
        )
        
@dp.message(F.text, Command("delete"))
async def delete_search_game(message: Message,
                      command: CommandObject):
    
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
    
    
@dp.message(F.text, Command("similar_games"))
async def similar_search_game(message: Message,
                      command: CommandObject):
    
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
    
@router.inline_query(F.query.startswith("search similar "))
async def search_similar_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict, user_data: dict):
    user_id = query.from_user.id
    user_input = query.query.lower()[15:].strip()
    game_list = list(games_info_dict_by_name.keys())
    similar_games = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games) 
        ]
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games = results.copy())
    await state.set_state(States.wait_for_similar)
    
    
@router.chosen_inline_result(States.wait_for_similar)
async def similar_games(chosen_result: ChosenInlineResult, state: FSMContext, bot, similar_games_df,
                    games_info_dict: dict, games_info_dict_by_name: dict, user_data: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    logging.log(msg = f"similar games recommend for user {user_id}: start", level=logging.INFO)
    recommendations_by_game = await asyncio.to_thread(rec.get_recommendations_by_game, 
                                                      similar_games_df,
                                                      [appid], user_data[user_id]['k'])
    get_game_link = partial(rec.get_link, games_info_dict =  games_info_dict)
    recommendations_by_game_answer = '\n'.join(map(get_game_link, recommendations_by_game))
    info = f"""<b> Игры, похожие на игру {game}:</b>
{recommendations_by_game_answer}
"""
    await state.clear()
    await bot.send_message(chat_id = user_id, text = info, parse_mode = ParseMode.HTML)
    logging.log(msg = f"similar games recommend for user {user_id}: finish", level=logging.INFO)
    
@dp.message(F.text, Command("recommend"))
async def get_recommended_game(message: Message,
                               command: CommandObject,
                               bot,
                               df,
                               games_info_dict: dict, 
                               games_info_dict_by_name: dict, 
                               user_data: dict, 
                               similar_games_df,
                               K_GAMES: int,
                               K_NEIGHBOURS : int,
                               matrix,
                               app_id_to_index,
                               user_id_to_index):
    user_id = message.from_user.id
    if user_id not in user_data:
        try:
            with open(f'recommendation_bot_data/userdata/{user_id}.json', 'r') as file:
                user_data[user_id] = json.load(file)
                user_data[user_id]['list_of_games'] = set(user_data[user_id]['list_of_games'])
                user_data[user_id]['k'] = int(user_data[user_id]['k'])
        except:
                user_data[user_id] = dict()
                user_data[user_id]['list_of_games'] = set()
                user_data[user_id]['k'] = K_GAMES
    get_game_link = partial(rec.get_link, games_info_dict =  games_info_dict)
    await message.answer(text = f"Отлично, сейчас мы порекомендуем вам игры! Это может занять некоторое время")
    popular_list = await asyncio.to_thread(rec.get_popular_recommendations, df, user_data[user_id]['k'])
    popular_list_answer = '\n'.join(map(get_game_link, popular_list))
    new_list = await asyncio.to_thread(rec.get_new_recommendations, df, user_data[user_id]['k'])
    new_list_answer = '\n'.join(map(get_game_link, new_list))
    if len(user_data[user_id]['list_of_games']) == 0:
        await message.answer(text = f"""К сожалению, вы не дали мне информации 
о ваших любимых играх, поэтому я не могу сделать персональную рекомендацию. Но вы можете поиграть в самые популярные игры!""")
        await message.answer(
        f"""<b>Популярные игры с высоким рейтингом:</b>
{popular_list_answer}\n
<b>Набирающие популярность новинки:</b>
{new_list_answer}
        """,
        parse_mode=ParseMode.HTML
    )
        return
    user_row = await asyncio.to_thread(rec.games_chosen_to_matrix_line, user_data[user_id]['list_of_games'], df, app_id_to_index)
    logging.log(msg = f"recommend for user {user_id}: start", level=logging.INFO)
    recommendations_by_game = await asyncio.to_thread(rec.get_recommendations_by_game, 
                                                      similar_games_df,
                                                      user_data[user_id]['list_of_games'], user_data[user_id]['k'])
    recommendations_by_user = await asyncio.to_thread(rec.get_recommendations_by_user, matrix, 
                                                user_row, K_NEIGHBOURS, user_data[user_id]['k'], 
                                                      user_id_to_index, app_id_to_index, False)
    
    recommendations_by_game_answer = '\n'.join(map(get_game_link, recommendations_by_game))
    recommendations_by_user_answer = '\n'.join(map(get_game_link, recommendations_by_user))
    await message.answer(
        f"""
<b>Пользователи, похожие на Вас, играют в:</b>
{recommendations_by_user_answer}\n
<b>Игры, похожие на те, что Вы играли:</b>
{recommendations_by_game_answer}\n
<b>Популярные игры с высоким рейтингом:</b>
{popular_list_answer}\n
<b>Набирающие популярность новинки:</b>
{new_list_answer}
        """,
        parse_mode=ParseMode.HTML
    )
    await rating_buttons(bot, message)
    logging.log(msg = f"recommend for user {user_id}: finish", level=logging.INFO)

async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    token = config.get('bot', 'token')
    K_NEIGHBOURS = config.getint('bot', 'K_NEIGHBOURS')
    K_GAMES = config.getint('bot', 'K_GAMES')
    URL = config.get('bot', 'URL')   
    logging.basicConfig(filename='log.txt', level=logging.INFO)
    user_data = dict()
    try:
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = await asyncio.to_thread(rec.load_data)
    except:
        gdown.download_folder(URL, remaining_ok = True)
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = await asyncio.to_thread(rec.load_data)
    df = df.sort_values(by = 'TotalReviews')
    games_info_dict_by_name = df[~df.duplicated(subset = ['Name'], keep = 'last')].set_index('Name')[['AppID']].to_dict(orient='index')
    
    games_info_dict = df.set_index('AppID')[['Name', 'Price' , 'Required age', 'About the game',
                                         'Supported languages', 'Genres']].to_dict(orient='index')    
    bot = Bot(token=token)
    dp['K_NEIGHBOURS'] = K_NEIGHBOURS
    dp['K_GAMES'] = K_GAMES
    await dp.start_polling(bot, df = df, user_data = user_data, 
                           games_info_dict = games_info_dict,
                           games_info_dict_by_name = games_info_dict_by_name,
                           similar_games_df = similar_games_df, 
                           matrix = matrix, 
                           app_id_to_index = app_id_to_index, 
                           user_id_to_index = user_id_to_index,
                           K_NEIGHBOURS = K_NEIGHBOURS)

if __name__ == "__main__":
    asyncio.run(main())
