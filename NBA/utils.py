import os
import glob
import pandas as pd
from datetime import date, datetime


def standardize(df: pd.DataFrame):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date"] = pd.to_datetime(df["date"])
    df['attendance'] = df['attendance'].str.replace(',', '').astype(float)
    df["visitor_pts"] = pd.to_numeric(df["visitor_pts"], errors="coerce")
    df["home_pts"] = pd.to_numeric(df["home_pts"], errors="coerce")

    home_df = df.copy()
    visitor_df = df.copy()

    # Home perspective
    home_df = home_df.rename(columns={
        'home_team': 'team',
        'home_pts': 'points_scored',
        'visitor_team': 'opponent',
        'visitor_pts': 'points_allowed'
    })
    home_df['is_home'] = True
    home_df['won'] = (home_df['points_scored'] > home_df['points_allowed']).astype(int)

    # Visitor perspective
    visitor_df = visitor_df.rename(columns={
        'visitor_team': 'team',
        'visitor_pts': 'points_scored',
        'home_team': 'opponent',
        'home_pts': 'points_allowed'
    })
    visitor_df['is_home'] = False
    visitor_df['won'] = (visitor_df['points_scored'] > visitor_df['points_allowed']).astype(int)
    cols_to_keep = ['date', 'start_(et)', 'team', 'opponent', 'is_home', 'points_scored', 'points_allowed', 'won', 'arena']
    long_df = pd.concat([home_df[cols_to_keep], visitor_df[cols_to_keep]], ignore_index=True)
    return long_df


def get_df_from_csvs(csv_dir: str) -> pd.DataFrame:
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    all_games = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        all_games.append(df)
    df = pd.concat(all_games, ignore_index=True)
    return standardize(df)

def get_last_n_games(df: pd.DataFrame, team: str, game_date: date, n: int = 5):
    past_games = df[
        ((df["home_team"] == team) | (df["visitor_team"] == team)) &
        (df["datetime"] < game_date)
    ].sort_values(by="datetime", ascending=False)
    return past_games.head(n)


print(get_df_from_csvs(f"{os.getcwd()}/NBA/data"))
