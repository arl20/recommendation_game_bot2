import asyncio
import configparser
import logging

import gdown
from aiogram import Bot, Dispatcher

from handlers import commands, inline_router, reviews
from utils.functions_for_recommendation import load_data


async def main():
    dp = Dispatcher()
    dp.include_routers(commands.router, inline_router.router, reviews.router)
    config = configparser.ConfigParser()
    config.read('configs/config.ini')

    token = config.get('bot', 'token')
    K_NEIGHBOURS = config.getint('bot', 'K_NEIGHBOURS')
    K_GAMES = config.getint('bot', 'K_GAMES')
    URL = config.get('bot', 'URL')
    logging.basicConfig(filename='log.txt', level=logging.INFO)
    user_data = dict()
    try:
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = await asyncio.to_thread(load_data)
    except FileNotFoundError:
        gdown.download_folder(URL, remaining_ok=True)
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = await asyncio.to_thread(load_data)
    df = df.sort_values(by='TotalReviews')
    games_info_dict_by_name = df[~df.duplicated(subset=['Name'],
                                                keep='last')].set_index('Name')[['AppID']].to_dict(orient='index')
    games_info_dict = df.set_index('AppID')[['Name', 'Price',
                                             'Required age', 'About the game',
                                             'Supported languages', 'Genres']].to_dict(orient='index')
    bot = Bot(token=token)
    dp['K_NEIGHBOURS'] = K_NEIGHBOURS
    dp['K_GAMES'] = K_GAMES
    await dp.start_polling(bot, df=df, user_data=user_data,
                           games_info_dict=games_info_dict,
                           games_info_dict_by_name=games_info_dict_by_name,
                           similar_games_df=similar_games_df,
                           matrix=matrix,
                           app_id_to_index=app_id_to_index,
                           user_id_to_index=user_id_to_index,
                           K_NEIGHBOURS=K_NEIGHBOURS)
if __name__ == "__main__":
    asyncio.run(main())
