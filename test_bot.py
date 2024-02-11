import pytest
from handlers.commands import *
from handlers.reviews import *
from handlers.inline_router import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChosenInlineResult, InputTextMessageContent, InlineQueryResultArticle, InlineQuery, InlineQueryResultArticle
from aiogram_tests import MockedBot
from aiogram.fsm.context import FSMContext
from aiogram_tests.handler import MessageHandler, CallbackQueryHandler, InlineQueryHandler, ChosenInlineHandler
from aiogram_tests.types.dataset import MESSAGE, CALLBACK_QUERY, USER
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.methods import SendMessage
from functools import partial
from utils.functions_for_recommendation import get_key, get_link, load_data, get_popular_recommendations, get_new_recommendations
from utils.functions_for_recommendation import  games_chosen_to_matrix_line, get_recommendations_by_user, get_recommendations_by_game
import random

@pytest.mark.asyncio
async def test_cmd_start():
    start_message =  f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекомендаций.\n
Вот список моих функций:
/add — добавить игру в список для рекомендаций
/delete — удалить игру из списка для рекомендаций
/list — получить текущий список ваших любимых игр
/clear — очистка списка ваших любимых игр

/info — найти информацию об игре

/set_k — установить значение количества рекомендуемых игр (по умолчанию 5)
/recommend — получить список рекомендованных игр
/similar_games —  порекомендовать игры, похожие на конкретную игру

/review — оставить отзыв о работе бота
/help — повторить это сообщение

Можем начать прямо сейчас. Для этого добавь свои любимые игры в список для рекомендаций с помощью функций /add, /delete и /clear.

При использовании функций /add и /delete начни писать название игры и выбери нужную из всплывающего списка. Если подходящей игры там нет, сообщи нам об этом с помощью функции /review
"""
    cmd_start_wrapper = partial(cmd_start, K_GAMES = 5, user_data = {})
    requester = MockedBot(request_handler=MessageHandler(cmd_start_wrapper, auto_mock_success=True))
    message = MESSAGE.as_object(text="/start")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == start_message
    
    
@pytest.mark.asyncio
async def test_rating_bot_buttons():
    review_message = f"""
    Пожалуйста, оцените качество работы бота. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):
    """
    requester = MockedBot(request_handler=MessageHandler(rating_bot_buttons, auto_mock_success=True))
    message = MESSAGE.as_object(text="/review")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone()
    assert answer_message.text in review_message
    assert len(answer_message.reply_markup['inline_keyboard'][0]) == 5
    
    
@pytest.mark.asyncio
async def test_process_review_callback():
    review_text = 'Спасибо за оценку! Оставьте, пожалуйста, отзыв '
    requester = MockedBot(request_handler=CallbackQueryHandler(process_review_callback, auto_mock_success=True))
    callback_query = CALLBACK_QUERY.as_object(
        data='review_5', message=MESSAGE.as_object(text="5"))
    calls = await requester.query(callback_query)
    answer_message = calls.send_message[0].text
    assert answer_message == review_text
    

@pytest.mark.asyncio
async def test_wait_review():
    review_text = "Спасибо за обратную связь!"
    requester = MockedBot(
        request_handler=MessageHandler(
            wait_review, state=States.wait_for_review, state_data={"score": "5"}, auto_mock_success=True
        )
    )
    message = MESSAGE.as_object(text="test_text_review")
    calls = await requester.query(message)
    answer_message = calls.send_message[0].text
    assert answer_message == review_text

@pytest.mark.asyncio
async def test_help_info():
    start_message =  f"""Привет! Я бот. Ты можешь написать мне свои любимые игры и получить список рекомендаций.\n
Вот список моих функций:
/add — добавить игру в список для рекомендаций
/delete — удалить игру из списка для рекомендаций
/list — получить текущий список ваших любимых игр
/clear — очистка списка ваших любимых игр

/info — найти информацию об игре

/set_k — установить значение количества рекомендуемых игр (по умолчанию 5)
/recommend — получить список рекомендованных игр
/similar_games —  порекомендовать игры, похожие на конкретную игру

/review — оставить отзыв о работе бота
/help — повторить это сообщение

Можем начать прямо сейчас. Для этого добавь свои любимые игры в список для рекомендаций с помощью функций /add, /delete и /clear.

При использовании функций /add и /delete начни писать название игры и выбери нужную из всплывающего списка. Если подходящей игры там нет, сообщи нам об этом с помощью функции /review
"""
    help_info_wrapper = partial(help_info, K_GAMES = 5)
    requester = MockedBot(request_handler=MessageHandler(help_info_wrapper, auto_mock_success=True))
    message = MESSAGE.as_object(text="/help")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == start_message
    
@pytest.mark.asyncio
async def test_rating_buttons():
    review_message = f"""
    Пожалуйста, оцените качество наших рекомендаций. Поставьте оценку от 1 до 5 (1 - плохо, 5 - отлично):
    """
    requester = MockedBot(request_handler=CallbackQueryHandler(rating_buttons, auto_mock_success=True))
    callback_query = CALLBACK_QUERY.as_object(
        data='rating_5', message=MESSAGE.as_object(text="5"))
    calls = await requester.query(callback_query)
    answer_message = calls.send_message.fetchone()
    assert answer_message.text in review_message
    
@pytest.mark.asyncio
async def test_process_game_callback_5():
    review_message = 'Спасибо за оценку!'
    requester = MockedBot(request_handler=CallbackQueryHandler(process_game_callback, auto_mock_success=True))
    callback_query = CALLBACK_QUERY.as_object(
        data='rating_5', message=MESSAGE.as_object(text="5"))
    calls = await requester.query(callback_query)
    answer_message = calls.send_message.fetchone()
    assert answer_message.text == review_message
    
    
@pytest.mark.asyncio
async def test_process_game_callback_other():
    review_message = 'Спасибо за оценку! Мы будем совершенствовать наши рекомендации'
    requester = MockedBot(request_handler=CallbackQueryHandler(process_game_callback, auto_mock_success=True))
    callback_query = CALLBACK_QUERY.as_object(
        data='rating_3', message=MESSAGE.as_object(text="3"))
    calls = await requester.query(callback_query)
    answer_message = calls.send_message.fetchone()
    assert answer_message.text == review_message
    
    
@pytest.fixture
def data():
    config = configparser.ConfigParser()
    config.read('configs/config.ini')

    token = config.get('bot', 'token')
    K_NEIGHBOURS = config.getint('bot', 'K_NEIGHBOURS')
    K_GAMES = config.getint('bot', 'K_GAMES')
    URL = config.get('bot', 'URL')   
    logging.basicConfig(filename='log.txt', level=logging.INFO)
    user_data = dict()
    try:
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = load_data()
    except:
        gdown.download_folder(URL, remaining_ok = True)
        df, matrix, app_id_to_index, user_id_to_index, similar_games_df = load_data()
    df = df.sort_values(by = 'TotalReviews')
    return df, matrix, app_id_to_index, user_id_to_index, similar_games_df
 
@pytest.fixture
def games_info_dict_by_name(data):
    df = data[0]
    dct = df[~df.duplicated(subset = ['Name'], keep = 'last')].set_index('Name')[['AppID']].to_dict(orient='index')  
    return dct

@pytest.fixture
def games_info_dict(data):
    df = data[0]
    dct = df.set_index('AppID')[['Name', 'Price' , 'Required age', 'About the game',
                                         'Supported languages', 'Genres']].to_dict(orient='index')    
    return dct

@pytest.fixture
def df(data):
    return data[0]

@pytest.fixture
def  matrix(data):
    return data[1]

@pytest.fixture
def app_id_to_index(data):
    return data[2]

@pytest.fixture
def user_id_to_index(data):
    return data[3]

@pytest.fixture
def similar_games_df(data):
    return data[4]

@pytest.mark.asyncio
async def test_load_data(games_info_dict_by_name, games_info_dict):
    assert len(games_info_dict_by_name) > 0
    assert len(games_info_dict) > 0
      
@pytest.mark.asyncio
async def test_search_add_handler(games_info_dict_by_name):
    game = random.choice(list(games_info_dict_by_name.keys()))
    inline_query = InlineQuery(
        id="123",
        query=f"add {game}",
        from_user=USER.as_object(), offset = ''
    )
    search_add_handler_wrapper = partial(search_add_handler, 
                                         games_info_dict_by_name = games_info_dict_by_name,
                                         user_data = {})
    requester = MockedBot(request_handler=InlineQueryHandler(search_add_handler_wrapper,
                                                               auto_mock_success=True))
                                                              
    calls = await requester.query(inline_query)
    answer = calls.answer_inline_query.fetchone()
    assert len(answer.results) > 0
    for result in answer.results:
        assert game.lower() in result['title'].lower()

@pytest.mark.asyncio
async def test_add_game(games_info_dict_by_name, games_info_dict):
    add_game_wrapper = partial(add_game, games_info_dict_by_name = games_info_dict_by_name, user_data = {}, K_GAMES = 5)
    user_id = USER.as_object().id
    games = random.sample(list(games_info_dict.keys()), 3)
    game = random.choice(games)
    chosen_result = ChosenInlineResult(result_id = '0', from_user = USER.as_object(), query = f"add {game}")
    user_input = games_info_dict[games[0]]['Name'][:-1].lower()
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
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
    requester = MockedBot(request_handler=ChosenInlineHandler(add_game_wrapper, 
                                                               state = States.wait_for_adding_game,
                                                               state_data = {'games' : results.copy()},
                                                               auto_mock_success=True))
    calls = await requester.query(chosen_result)
    answer_message = calls.send_message.fetchone()
    add_text = f"Игра {games_info_dict[games[0]]['Name']} добавлена в список ваших любимых игр"
    assert answer_message.text == add_text
        
@pytest.mark.asyncio
async def test_search_delete_handler(games_info_dict_by_name, games_info_dict):
    games = random.sample(list(games_info_dict.keys()), 3)
    game = games_info_dict[games[0]]['Name']
    inline_query = InlineQuery(
        id="123",
        query=f"delete {game}",
        from_user=USER.as_object(), offset = ''
    )
    user_id = inline_query.from_user.id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
    search_delete_handler_wrapper = partial(search_delete_handler, 
                                         games_info_dict_by_name = games_info_dict_by_name,
                                         games_info_dict = games_info_dict,
                                         user_data = user_data)
    requester = MockedBot(request_handler=InlineQueryHandler(search_delete_handler_wrapper,  
                                                               auto_mock_success=True))
                                                              
    calls = await requester.query(inline_query)
    answer = calls.answer_inline_query.fetchone()
    assert len(answer.results) > 0 
    for result in answer.results:
        assert game.lower() in result['title'].lower() 
        
@pytest.mark.asyncio
async def test_delete_game(games_info_dict_by_name, games_info_dict):
    user_id = USER.as_object().id
    games = random.sample(list(games_info_dict.keys()), 3)
    game = random.choice(games)
    chosen_result = ChosenInlineResult(result_id = '0', from_user = USER.as_object(), query = f"delete {game}")
    user_input = games_info_dict[games[0]]['Name'][:-1].lower()
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
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
    delete_game_wrapper = partial(delete_game, games_info_dict_by_name = games_info_dict_by_name, 
                                  games_info_dict = games_info_dict,
                                  user_data = user_data, K_GAMES = 5)
    requester = MockedBot(request_handler=ChosenInlineHandler(delete_game_wrapper, 
                                                               state = States.wait_for_deleting_game,
                                                               state_data = {'games' : results.copy()},
                                                               auto_mock_success=True))
    calls = await requester.query(chosen_result)
    answer_message = calls.send_message.fetchone()
    delete_text = f"Игра {games_info_dict[games[0]]['Name']} удалена из списка ваших любимых игр"
    assert answer_message.text == delete_text
    
@pytest.mark.asyncio
async def test_search_info_handler(games_info_dict_by_name, games_info_dict):
    game = random.choice(list(games_info_dict_by_name.keys()))
    inline_query = InlineQuery(
        id="123",
        query=f"info {game}",
        from_user=USER.as_object(), offset = '')
   
    search_info_handler_wrapper = partial(search_info_handler, 
                                         games_info_dict_by_name = games_info_dict_by_name)
    requester = MockedBot(request_handler=InlineQueryHandler(search_info_handler_wrapper, 
                                                               auto_mock_success=True))
                                                              
    calls = await requester.query(inline_query)
    answer = calls.answer_inline_query.fetchone()
    assert len(answer.results) > 0
    
@pytest.mark.asyncio
async def test_info_game(games_info_dict_by_name, games_info_dict):
    user_id = USER.as_object().id
    games = random.sample(list(games_info_dict.keys()), 3)
    game = random.choice(games)
    game_name = games_info_dict[games[0]]['Name']
    chosen_result = ChosenInlineResult(result_id = '0', from_user = USER.as_object(), query = f"info {game_name}")
    user_input = game_name[:-1].lower()
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
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
    info_game_wrapper = partial(info_game, games_info_dict = games_info_dict,
                                           games_info_dict_by_name = games_info_dict_by_name, user_data = user_data, K_GAMES = 5)
    requester = MockedBot(request_handler=ChosenInlineHandler(info_game_wrapper, 
                                                               state = States.wait_for_info,
                                                               state_data = {'games' : results.copy()},
                                                               auto_mock_success=True))
    calls = await requester.query(chosen_result)
    answer_message = calls.send_message.fetchone()
    appid = games_info_dict_by_name[game_name]['AppID']
    info_text =  f"""Информация об игре {games_info_dict[appid]['Name']}
<b>Возрастное ограничение:</b> {games_info_dict[appid]['Required age']}
<b>Жанры:</b> {games_info_dict[appid]['Genres']}
<b>Описание:</b> {games_info_dict[appid]['About the game']}
<a href="store.steampowered.com/app/{appid}">Ссылка на steam</a>
"""
    assert answer_message.text == info_text
    
@pytest.mark.asyncio
async def test_search_similar_handler(games_info_dict_by_name, games_info_dict):
    games = random.sample(list(games_info_dict.keys()), 3)
    game = games_info_dict[games[0]]['Name']
    inline_query = InlineQuery(
        id="123",
        query=f"search similar {game}",
        from_user=USER.as_object(), offset = ''
    )
    user_id = inline_query.from_user.id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
    search_similar_handler_wrapper = partial(search_similar_handler, 
                                         games_info_dict_by_name = games_info_dict_by_name,
                                         user_data = user_data)
    requester = MockedBot(request_handler=InlineQueryHandler(search_similar_handler_wrapper,  
                                                               auto_mock_success=True))
                                                              
    calls = await requester.query(inline_query)
    answer = calls.answer_inline_query.fetchone()
    assert len(answer.results) > 0 
    for result in answer.results:
        assert game.lower() in result['title'].lower() 
        
    
@pytest.mark.asyncio
async def test_similar_games(games_info_dict_by_name, games_info_dict, similar_games_df):
    user_id = USER.as_object().id
    games = random.sample(list(games_info_dict.keys()), 3)
    game = random.choice(games)
    game_name = games_info_dict[games[0]]['Name']
    chosen_result = ChosenInlineResult(result_id = '0', from_user = USER.as_object(), query = f"search similar {game_name}")
    user_input = game_name[:-1].lower()
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
    user_data[user_id]['k']  = 5
    game_list = [games_info_dict[i]['Name'] for i in user_data[user_id]['list_of_games']]
    similar_games_list = [game for game in game_list if user_input in game.lower()][:50]
    results = [
            InlineQueryResultArticle(
                id=str(idx),
                title=game_name,
                input_message_content=InputTextMessageContent(message_text=game_name)
            )
            for idx, game_name in enumerate(similar_games_list) 
        ]
    similar_games_wrapper = partial(similar_games,
                                    similar_games_df = similar_games_df,
                                    games_info_dict = games_info_dict,
                                    games_info_dict_by_name = games_info_dict_by_name,
                                    user_data = user_data,
                                    K_GAMES = 5)
    requester = MockedBot(request_handler=ChosenInlineHandler(similar_games_wrapper, 
                                                               state = States.wait_for_similar,
                                                               state_data = {'games' : results.copy()},
                                                               auto_mock_success=True))
    calls = await requester.query(chosen_result)
    answer_message = calls.send_message.fetchone().text
    assert "Игры, похожие на игру" in answer_message
    
@pytest.mark.asyncio
async def test_add_search_game():
    add_message = "Вы хотите добавить игру в список ваших любимых игр?"
    requester = MockedBot(request_handler=MessageHandler(add_search_game, auto_mock_success=True))
    message = MESSAGE.as_object(text="/add")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == add_message
        
@pytest.mark.asyncio
async def test_delete_search_game():
    delete_message = "Вы хотите удалить игру из списка ваших любимых игр?"
    requester = MockedBot(request_handler=MessageHandler(delete_search_game, auto_mock_success=True))
    message = MESSAGE.as_object(text="/delete")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == delete_message
        
@pytest.mark.asyncio
async def test_info_search_game():
    info_message = "Вывести информацию об игре"
    requester = MockedBot(request_handler=MessageHandler(info_search_game, auto_mock_success=True))
    message = MESSAGE.as_object(text="/info")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == info_message
    
@pytest.mark.asyncio
async def test_similar_search_game():
    similar_message = "Введите название игры, и мы порекомендуем похожие на неё игры"
    requester = MockedBot(request_handler=MessageHandler(similar_search_game, auto_mock_success=True))
    message = MESSAGE.as_object(text="/similar_games")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == similar_message
    
@pytest.mark.asyncio
async def test_clear_list_of_game(games_info_dict_by_name, games_info_dict):
    games = random.sample(list(games_info_dict.keys()), 3)
    game = random.choice(games)
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
    clear_list_of_game_wrapper = partial(clear_list_of_game, user_data=user_data, K_GAMES = 5)
    requester = MockedBot(request_handler=MessageHandler(clear_list_of_game_wrapper, auto_mock_success=True))
    message = MESSAGE.as_object(text="/clear")
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    clear_text = 'Список ваших любимых игр очищен'
    assert answer_message == clear_text 
    assert len(user_data[user_id]['list_of_games']) == 0

@pytest.mark.asyncio
async def test_get_list_of_game_empty(games_info_dict_by_name, games_info_dict):
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set()
    get_list_of_game_wrapper_empty = partial(get_list_of_game, 
                                       games_info_dict = games_info_dict,
                                       user_data = user_data, K_GAMES = 5)
    requester = MockedBot(request_handler=MessageHandler(get_list_of_game_wrapper_empty, auto_mock_success=True))
    message = MESSAGE.as_object(text="/list")
    empty_list_message = '<b>Список ваших любимых игр пуст</b>\n'
    calls = await requester.query(message)
    answer_message = calls.send_message.fetchone().text
    assert answer_message == empty_list_message
    
@pytest.mark.asyncio
@pytest.mark.parametrize("k", ['1', '7', '20', '1000'])
async def test_set_k_games(games_info_dict_by_name, games_info_dict, k):
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set()
    user_data[user_id]['k']  =  5
    set_k_games_wrapper = partial(set_k_games, user_data = user_data, K_GAMES = 5, command = CommandObject("set_k", args = f'{k}'))
    requester = MockedBot(request_handler=MessageHandler(set_k_games_wrapper, auto_mock_success=True))
    message1 = MESSAGE.as_object(text=f"/set_k {k}")
    calls = await requester.query(message1)
    answer_message = calls.send_message.fetchone().text
    if int(k) > 0 and int(k) <= 21:
        result_message = f'Установлено значение количества рекомендованных игр {k}' 
        assert user_data[user_id]['k']  ==  int(k)
    else:
        result_message = 'Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20'
    assert result_message in answer_message
    
@pytest.mark.asyncio
async def test_set_k_games_empty(games_info_dict_by_name, games_info_dict):
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set()
    user_data[user_id]['k']  =  5
    set_k_games_wrapper_empty = partial(set_k_games, user_data = user_data, K_GAMES = 5, command = CommandObject("set_k"))
    requester2 = MockedBot(request_handler=MessageHandler(set_k_games_wrapper_empty, auto_mock_success=True))
    message2 = MESSAGE.as_object(text="/set_k")
    calls = await requester2.query(message2)
    answer_message = calls.send_message.fetchone().text
    assert 'Напишите команду в формате /set_k K, где K - целое положительное число от 1 до 20' == answer_message
    
@pytest.mark.asyncio    
async def test_get_recommended_game_empty(df, games_info_dict_by_name, games_info_dict, 
                                    similar_games_df, 
                                    matrix, app_id_to_index, user_id_to_index):
    games = random.sample(list(games_info_dict.keys()), 5)
    game = random.choice(games)
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set()
    user_data[user_id]['k']  =  5
    get_recommended_game_wrapper = partial(get_recommended_game, 
                                           df = df,
                                           games_info_dict = games_info_dict,
                                           games_info_dict_by_name = games_info_dict_by_name,
                                           user_data = user_data,
                                           similar_games_df = similar_games_df,
                                           K_GAMES = 5,
                                           K_NEIGHBOURS = 5,
                                           matrix = matrix,
                                           app_id_to_index = app_id_to_index,
                                           user_id_to_index = user_id_to_index)
    requester = MockedBot(request_handler=MessageHandler(get_recommended_game_wrapper, Command("recommend"), auto_mock_success=True))
    message = MESSAGE.as_object(text="/recommend")
    calls = await requester.query(message)
    answer_messages = calls.send_message.fetchall()
    assert "Отлично, сейчас мы порекомендуем вам игры! Это может занять некоторое время" == answer_messages[0].text 
    assert "К сожалению, вы " in answer_messages[1].text 
    assert "Популярные игры" in answer_messages[2].text 
    
    
@pytest.mark.asyncio    
async def test_get_recommended_game(df, games_info_dict_by_name, games_info_dict, 
                                    similar_games_df, 
                                    matrix, app_id_to_index, user_id_to_index):
    games = random.sample(list(games_info_dict.keys()), 5)
    game = random.choice(games)
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games']  = set(games.copy())
    user_data[user_id]['k']  =  5
    get_recommended_game_wrapper = partial(get_recommended_game, 
                                           df = df,
                                           games_info_dict = games_info_dict,
                                           games_info_dict_by_name = games_info_dict_by_name,
                                           user_data = user_data,
                                           similar_games_df = similar_games_df,
                                           K_GAMES = 5,
                                           K_NEIGHBOURS = 5,
                                           matrix = matrix,
                                           app_id_to_index = app_id_to_index,
                                           user_id_to_index = user_id_to_index)
    requester = MockedBot(request_handler=MessageHandler(get_recommended_game_wrapper, auto_mock_success=True))
    message = MESSAGE.as_object(text="/recommend")
    calls = await requester.query(message)
    answer_messages = calls.send_message.fetchall()
    assert "Отлично, сейчас мы порекомендуем вам игры! Это может занять некоторое время" == answer_messages[0].text 
    assert "Пользователи, похожие на Вас, играют в" in answer_messages[1].text 
    
@pytest.mark.asyncio    
async def test_get_link(games_info_dict):
    appid = random.choice(list(games_info_dict.keys()))
    name = games_info_dict[appid]['Name']
    assert f'<a href="store.steampowered.com/app/{appid}">{name}</a>' == get_link(appid, games_info_dict)
    
@pytest.mark.asyncio 
@pytest.mark.parametrize("k", [1, 5, 20])
async def test_get_popular_recommendations(df, k):
    recommendation = get_popular_recommendations(df, k)
    assert len(recommendation) > 0
    
@pytest.mark.asyncio
@pytest.mark.parametrize("k", [1, 5, 20])
async def test_get_new_recommendations(df, k):
    recommendation = get_new_recommendations(df, k)
    assert len(recommendation) > 0 
    
@pytest.mark.asyncio  
@pytest.mark.parametrize("k", [1, 3, 20])
async def test_games_chosen_to_matrix_line(df, app_id_to_index, games_info_dict, k):
    games_chosen_appid = random.sample(list(games_info_dict.keys()), k)
    user_line = games_chosen_to_matrix_line(games_chosen_appid, df, app_id_to_index)
    assert len(user_line) > 0

@pytest.mark.asyncio  
@pytest.mark.parametrize("k", [1, 3, 20])
async def test_get_recommendations_by_game(games_info_dict, similar_games_df, k):
    games = random.sample(list(games_info_dict.keys()), 3)
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set(games.copy())
    user_data[user_id]['k']  =  k
    recommendations_by_game = await asyncio.to_thread(get_recommendations_by_game, similar_games_df,
                                                          user_data[user_id]['list_of_games'],
                                                          user_data[user_id]['k'])
    assert len(recommendations_by_game) == k

@pytest.mark.asyncio  
@pytest.mark.parametrize("k", [1, 3, 20])
async def test_get_recommendations_by_user(games_info_dict, matrix, df, user_id_to_index, app_id_to_index, k):
    games = random.sample(list(games_info_dict.keys()), 3)
    user_id = USER.as_object().id
    user_data = {}
    user_data[user_id] = dict()
    user_data[user_id]['list_of_games'] = set(games.copy())
    user_data[user_id]['k']  =  k
    user_row = await asyncio.to_thread(games_chosen_to_matrix_line, user_data[user_id]['list_of_games'], df, app_id_to_index)
    recommendations_by_user = await asyncio.to_thread(get_recommendations_by_user, matrix, user_row, 5, user_data[user_id]['k'], 
                                                         user_id_to_index, app_id_to_index, False)
    assert len(recommendations_by_user) == k