import pandas as pd
import numpy as np

def create_fatigue_features(df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    """
    Generates game-level fatigue features for each pitch type using pitch-level Statcast data.

    Parameters:
        df (pd.DataFrame): Statcast data for a single pitcher, one season
        debug (bool): If True, prints intermediate values for inspection

    Returns:
        pd.DataFrame: Fatigue feature set with one row per game-pitch_type combo
    """
    df = df.sort_values(by='game_date')
    df['game_number'] = df['game_pk'].rank(method='dense').astype(int)

    fatigue_rows = []
    games = df['game_pk'].unique()
    pitch_types = df['pitch_type'].dropna().unique()

    for idx, game_id in enumerate(games):
        game_df = df[df['game_pk'] == game_id]
        past_df = df[df['game_pk'].isin(games[:idx])]

        if past_df.empty:
            continue

        for pt in pitch_types:
            game_pitch_df = game_df[game_df['pitch_type'] == pt]
            past_pitch_df = past_df[past_df['pitch_type'] == pt]

            if game_pitch_df.empty or past_pitch_df.empty:
                continue

            release_speed_mean = game_pitch_df['release_speed'].mean()
            release_spin_mean = game_pitch_df['release_spin_rate'].mean()
            balls = (game_pitch_df['balls'] > 0).sum()
            strikes = (game_pitch_df['strikes'] > 0).sum()
            ball_strike_ratio = balls / (balls + strikes) if (balls + strikes) > 0 else np.nan

            season_avg_velocity = past_pitch_df['release_speed'].mean()
            season_avg_spin = past_pitch_df['release_spin_rate'].mean()
            past_balls = (past_pitch_df['balls'] > 0).sum()
            past_strikes = (past_pitch_df['strikes'] > 0).sum()
            season_ball_strike_ratio = past_balls / (past_balls + past_strikes) if (past_balls + past_strikes) > 0 else np.nan

            velocity_drop = release_speed_mean - season_avg_velocity
            spin_drop = release_spin_mean - season_avg_spin
            command_drop = ball_strike_ratio - season_ball_strike_ratio

            fatigue_flag = int((velocity_drop < -1.0) and (command_drop > 0.05) and (spin_drop < -50))

            fatigue_rows.append({
                'game_pk': game_id,
                'game_date': game_pitch_df['game_date'].iloc[0],
                'game_number': idx + 1,
                'pitch_type': pt,
                'total_pitches': len(game_pitch_df),
                'release_speed_mean': release_speed_mean,
                'release_spin_mean': release_spin_mean,
                'season_avg_velocity': season_avg_velocity,
                'season_avg_spin': season_avg_spin,
                'velocity_drop': velocity_drop,
                'spin_drop': spin_drop,
                'ball_strike_ratio': ball_strike_ratio,
                'season_ball_strike_ratio': season_ball_strike_ratio,
                'command_drop': command_drop,
                'fatigue_flag': fatigue_flag
            })

            if debug:
                print(f"Game {idx + 1}, {pt}: velo_drop={velocity_drop:.2f}, spin_drop={spin_drop:.1f}, command_drop={command_drop:.2f}, fatigue={fatigue_flag}")

    return pd.DataFrame(fatigue_rows)
