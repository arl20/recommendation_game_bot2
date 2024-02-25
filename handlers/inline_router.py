import asyncio
import json
import logging
from functools import partial

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (ChosenInlineResult, InlineQuery,
                           InlineQueryResultArticle, InputTextMessageContent)

import configparser

from utils.functions_for_recommendation import get_recommendations_by_game
from utils.utils import get_link, get_conn, load_data

from .commands import States

router = Router()


def get_inline_query_result(query, games_info_dict_by_name, game_list, pos):
    user_input = query.query.lower()[pos:].strip()
    similar_games = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games)
        ]
    return results


@router.inline_query(F.query.startswith("add "))
async def search_add_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict):
    results = get_inline_query_result(query, games_info_dict_by_name, list(games_info_dict_by_name.keys()), 4)
    await query.answer(results,
                       is_personal=True,
                       cache_time=0)
    await state.update_data(games=results.copy())
    await state.set_state(States.wait_for_adding_game)


@router.chosen_inline_result(States.wait_for_adding_game)
async def add_game(chosen_result: ChosenInlineResult, bot, state: FSMContext, 
                   games_info_dict_by_name: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select list_games from users where id = {user_id}")
    games = cursor.fetchone()
    if len(games) > 0:
        games = set(games[0])
    else:
        games = set()
    games.add(appid)
    cursor.execute(f"UPDATE users SET list_games = ARRAY{str(sorted(games))}::integer[] WHERE id = {user_id}")
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    await state.clear()
    logging.log(msg=f"{game} add to {user_id} list", level=logging.INFO)
    await bot.send_message(chat_id=user_id, text=f"Игра {game} добавлена в список ваших любимых игр")


@router.inline_query(F.query.startswith("delete "))
async def search_delete_handler(query: InlineQuery, state: FSMContext,
                                games_info_dict: dict,
                                games_info_dict_by_name: dict):
    user_id = query.from_user.id
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select list_games from users where id = {user_id}")
    games = cursor.fetchone()
    if len(games) > 0:
        games = set(games[0])
    else:
        games = set()
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    results = get_inline_query_result(query, games_info_dict_by_name,
                                      [games_info_dict[i]['Name'] for i in games], 7)
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games=results.copy())
    await state.set_state(States.wait_for_deleting_game)


@router.chosen_inline_result(States.wait_for_deleting_game)
async def delete_game(chosen_result: ChosenInlineResult, bot, state: FSMContext,
                      games_info_dict: dict,
                      games_info_dict_by_name: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id

    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select list_games from users where id = {user_id}")
    games = set(cursor.fetchone()[0])
    games.remove(appid)
    cursor.execute(f"UPDATE users SET list_games = ARRAY{str(sorted(games))}::integer[] WHERE id = {user_id}")
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    await state.clear()
    logging.log(msg=f"{game} delete from {user_id} list", level=logging.INFO)
    await bot.send_message(chat_id=user_id, text=f"Игра {game} удалена из списка ваших любимых игр")


@router.inline_query(F.query.startswith("info "))
async def search_info_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict):
    results = get_inline_query_result(query, games_info_dict_by_name, list(games_info_dict_by_name.keys()), 5)
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games=results.copy())
    await state.set_state(States.wait_for_info)


@router.chosen_inline_result(States.wait_for_info)
async def info_game(chosen_result: ChosenInlineResult, state: FSMContext, bot,
                    games_info_dict: dict, games_info_dict_by_name: dict, K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id         
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    info = f"""Информация об игре {games_info_dict[appid]['Name']}
<b>Возрастное ограничение:</b> {games_info_dict[appid]['Required age']}
<b>Жанры:</b> {games_info_dict[appid]['Genres']}
<b>Описание:</b> {games_info_dict[appid]['About the game']}
<a href="store.steampowered.com/app/{appid}">Ссылка на steam</a>
"""
    await state.clear()
    await bot.send_message(chat_id=user_id, text=info, parse_mode=ParseMode.HTML)
    logging.log(msg=f"info for user {user_id}", level=logging.INFO)


@router.inline_query(F.query.startswith("search similar "))
async def search_similar_handler(query: InlineQuery, state: FSMContext, games_info_dict_by_name: dict):
    results = get_inline_query_result(query, games_info_dict_by_name, list(games_info_dict_by_name.keys()), 15)
    await query.answer(results, is_personal=True, cache_time=0)
    await state.clear()
    await state.update_data(games=results.copy())
    await state.set_state(States.wait_for_similar)


@router.chosen_inline_result(States.wait_for_similar)
async def similar_games(chosen_result: ChosenInlineResult, state: FSMContext, bot,
                        similar_games_df,
                        games_info_dict: dict,
                        games_info_dict_by_name: dict,
                        K_GAMES: int):
    games = await state.get_data()
    user_id = chosen_result.from_user.id
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"select k_games from users where id = {user_id}")
    k_games = cursor.fetchone()
    if len(k_games) == 0:
        create_user(user_id, k_games[0])
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()
    game = games['games'][int(chosen_result.result_id)].title
    appid = games_info_dict_by_name[game]['AppID']
    logging.log(msg=f"similar games recommend for user {user_id}: start; k_games = {k_games[0]}", level=logging.INFO)
    recommendations_by_game = await asyncio.to_thread(get_recommendations_by_game,
                                                      similar_games_df,
                                                      [appid], k_games[0])
    get_game_link = partial(get_link, games_info_dict=games_info_dict)
    recommendations_by_game_answer = '\n'.join(map(get_game_link, recommendations_by_game))
    info = f"""<b> Игры, похожие на игру {game}:</b>
{recommendations_by_game_answer}
"""
    await state.clear()
    await bot.send_message(chat_id=user_id, text=info, parse_mode=ParseMode.HTML)
    logging.log(msg=f"similar games recommend for user {user_id}: finish", level=logging.INFO)
