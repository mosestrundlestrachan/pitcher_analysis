import pandas as pd
import requests
import pybaseball as pyb
from io import StringIO
from pybaseball import playerid_lookup


def get_player_id(pitcher_name):
    parts = pitcher_name.split()
    if len(parts) < 2:
        print("Please enter both first and last name.")
        return None
    first, last = parts[0], parts[1]
    result = playerid_lookup(last, first)
    if result.empty:
        print(f"Could not find player ID for {pitcher_name}")
        return None
    return int(result.iloc[0]["key_mlbam"])


def load_pitch_data(pitcher_id, season: int):
    if season == 2023:
        start_date = "2023-03-30"
        end_date = "2023-10-01"
    elif season == 2024:
        start_date = "2024-03-20"
        end_date = "2024-10-01"
    else:
        start_date = f"{season}-03-28"
        end_date = f"{season}-10-01"
    return pyb.statcast_pitcher(start_date, end_date, pitcher_id)


def load_statcast_grouped(season:int):
    url = f"https://github.com/tnestico/pitching_summary/raw/main/statcast_2024_grouped.csv"
    response = requests.get(url)
    return pd.read_csv(StringIO(response.content.decode('utf-8')))


def fangraphs_pitching_leaderboards(season:int):
    url = f"https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=pit&lg=all&season={season}&season1={season}&ind=0&qual=0&type=8&month=0&pageitems=500000"
    data = requests.get(url).json()
    df = pd.DataFrame(data=data['data'])
    return df