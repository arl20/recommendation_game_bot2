import configparser
import json
import numpy as np
import pandas as pd
import psycopg2
from scipy.sparse import csr_matrix, load_npz
from sshtunnel import SSHTunnelForwarder
import logging

def get_conn():
    config = configparser.ConfigParser()
    config.read('configs/config.ini')
    ssh_host = config.get('server', 'ssh_host')
    ssh_user = config.get('server', 'ssh_user')
    ssh_password = config.get('server', 'ssh_password')
    ssh_port = config.getint('server', 'ssh_port')
    db_host = config.get('server', 'db_host')
    db_user = config.get('server', 'db_user')
    db_password = config.get('server', 'db_password')
    db_port = config.getint('server', 'db_port')
    db_name = config.get('server', 'db_name')
    tunnel = SSHTunnelForwarder(
    (ssh_host, ssh_port),
    ssh_username=ssh_user,
    ssh_password=ssh_password,
    remote_bind_address=(db_host, db_port)
    )
    tunnel.start()
    conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=tunnel.local_bind_host,
            port=tunnel.local_bind_port,
            database=db_name
        )
    return tunnel, conn

def create_user(user_id = -1, k_games = 10):
    tunnel, conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
    cursor.execute(f"""INSERT INTO users (id, K_GAMES, list_games)
                       VALUES ({user_id}, {k_games}, ARRAY[]::integer[])""")
    cursor.close()
    conn.commit()
    conn.close()
    tunnel.stop()


def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return int(k)


def load_data():
    logging.log(msg="Load games_df", level=logging.INFO)
    df = pd.read_csv('recommendation_bot_data/games_df.csv')
    logging.log(msg="Load matrix", level=logging.INFO)
    matrix = load_npz('recommendation_bot_data/sparse_interaction_matrix.npz')
    logging.log(msg="Load games", level=logging.INFO)
    steam_game_similarities = pd.read_csv('recommendation_bot_data/steam_game_similarities.csv')
    logging.log(msg="Load app_id_to_index", level=logging.INFO)
    with open('recommendation_bot_data/app_id_to_index.json', 'r') as file:
        app_id_to_index = json.load(file)
    logging.log(msg="Load user_id_to_index", level=logging.INFO)         
    with open('recommendation_bot_data/user_id_to_index.json', 'r') as file:
        user_id_to_index = json.load(file)
    logging.log(msg="Loading finished", level=logging.INFO)  
    return df, matrix, app_id_to_index, user_id_to_index, steam_game_similarities
    
    
def get_link(appid, games_info_dict):
    name = games_info_dict[appid]['Name']
    return f'<a href="store.steampowered.com/app/{appid}">{name}</a>'
