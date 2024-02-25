import json
from collections import Counter

import logging
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, load_npz
from sklearn.metrics.pairwise import cosine_similarity
from .utils import get_key

def get_popular_recommendations(df, k):
    df = df.copy()
    df["Rating"] = (df["Positive"] / (df["Positive"] + df["Negative"])).round(2)
    top_games = df.sort_values(["Rating", "TotalReviews"], ascending=False).head(k)
    recommendation = list(top_games["AppID"])
    return recommendation


def get_new_recommendations(df, k):
    df = df.copy()
    df["Rating"] = (df["Positive"] / (df["Positive"] + df["Negative"])).round(2)
    df["Year"] = df['Release date'].astype(str).str[-4:]
    top_games = df.sort_values(["Year", "Rating", "TotalReviews"], ascending=False).head(k)
    recommendation = list(top_games["AppID"])
    return recommendation


def games_chosen_to_matrix_line(games_chosen_appid, df, app_index_dict):
    user_line = [1 if int(i) in games_chosen_appid else 0 for i in app_index_dict]
    return user_line


def get_recommendations_by_user(interaction_matrix, user_row, k, k_games, user_index_dict, app_id_to_index, test=False):
    user_similarity = cosine_similarity(csr_matrix(user_row), interaction_matrix)
    # Get the user's k nearest neighbors
    user_neighbors = np.argsort(user_similarity[0])[::-1][:k]
    # Calculating like ratios and number of reviews for each game among neighbors
    user_ratings = []
    for i in range(interaction_matrix[user_neighbors].shape[1]):
        game_ratings = interaction_matrix[user_neighbors][:, i]
        # If at least one neighbor rated the game, calculate liked ratio
        # else, assign it 0
        neighbor_average_rating = 0
        num_neighbors_reviewed = game_ratings.data.shape[0]
        if num_neighbors_reviewed != 0:
            c = Counter(game_ratings.data)
            pos = c[1] if 1 in c else 0
            neg = c[-1] if -1 in c else 0
            neighbor_average_rating = pos / (pos + neg)
        user_ratings.append((num_neighbors_reviewed, round(neighbor_average_rating, 2)))
    user_ratings = np.array(user_ratings)
    if test:
        all_games = np.where(csr_matrix(user_row).todense() != 10)[1]
        user_ratings = list(map(tuple, user_ratings[all_games]))
        # Sort by most reviews, then by like ratio
        recommendations = sorted(zip(all_games, user_ratings), key=lambda x: x[1], reverse=True)
    else:
        # Get games unrated by this user and their like ratios
        unrated_games = np.where(csr_matrix(user_row).todense() == 0)[1]
        user_ratings = list(map(tuple, user_ratings[unrated_games]))
        recommendations = sorted(zip(unrated_games, user_ratings), key=lambda x: x[1], reverse=True)
        recommendations_by_user = [get_key(app_id_to_index, j) for j in [r[0] for r in recommendations]][:k_games]
        #  recommendations_by_user = [r[0] for r in recommendations]
    logging.log(msg="recommend for user: finish func", level=logging.INFO)
    return recommendations_by_user


def get_recommendations_by_game(similar_games_df, user_played_appids, k_results):
    user_played_appids = set(user_played_appids)
    similar_games_for_user = similar_games_df[similar_games_df.appid.isin(user_played_appids)]
    similar_unplayed_games = similar_games_for_user[~similar_games_for_user.similar_appid.isin(
        user_played_appids)].sort_values("cos_distance", ascending=False).drop_duplicates(
        subset=["similar_appid"], keep="first")
    return similar_unplayed_games.similar_appid.head(k_results).values
