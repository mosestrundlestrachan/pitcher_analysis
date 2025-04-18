import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import requests
import math
import matplotlib.gridspec as gridspec
from PIL import Image
from io import BytesIO
import matplotlib.ticker as mtick
from matplotlib.ticker import MaxNLocator, FuncFormatter
import matplotlib.colors as mcolors
from preprocessing import df_grouping, plot_pitch_format, get_cell_colors, cmap_sum, cmap_sum_r
from constants import dict_color, image_dict, font_properties, font_properties_titles
from constants import font_properties_axes, pitch_stats_dict, table_columns, color_stats
#from matplotlib.offsetbox import OffsetImage, AnnotationBbox


def player_headshot(pitcher_id: str, ax: plt.Axes):
    url = f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_640,q_auto:best/v1/people/{pitcher_id}/headshot/silo/current.png'
    img = Image.open(BytesIO(requests.get(url).content))
    ax.set_xlim(0, 1.3)
    ax.set_ylim(0, 1)
    ax.imshow(img, extent=[0, 1, 0, 1], origin='upper')
    ax.axis('off')


def player_bio(pitcher_id: str, ax: plt.Axes):
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={pitcher_id}&hydrate=currentTeam"
    data = requests.get(url).json()
    p = data['people'][0]
    ax.text(0.5, 1, f"{p['fullName']}", va='top', ha='center', fontsize=56)
    ax.text(0.5, 0.65, f"{p['pitchHand']['code']}HP, Age:{p['currentAge']}, {p['height']}/{p['weight']}", va='top', ha='center', fontsize=30)
    ax.text(0.5, 0.40, f'Season Pitching Summary', va='top', ha='center', fontsize=40)
    ax.text(0.5, 0.15, f'2024 MLB Season', va='top', ha='center', fontsize=30, fontstyle='italic')
    ax.axis('off')


def plot_logo(pitcher_id: str, ax: plt.Axes):
    data = requests.get(f"https://statsapi.mlb.com/api/v1/people?personIds={pitcher_id}&hydrate=currentTeam").json()
    team_url = 'https://statsapi.mlb.com/' + data['people'][0]['currentTeam']['link']
    team_data = requests.get(team_url).json()
    team_abb = team_data['teams'][0]['abbreviation']
    logo_url = image_dict.get(team_abb)
    img = Image.open(BytesIO(requests.get(logo_url).content))
    ax.set_xlim(0, 1.3)
    ax.set_ylim(0, 1)
    ax.imshow(img, extent=[0.3, 1.3, 0, 1], origin='upper')
    ax.axis('off')


def velocity_kdes(df: pd.DataFrame,
                  ax: plt.Axes,
                  gs: gridspec,
                  gs_x: list,
                  gs_y: list,
                  fig: plt.Figure,
                  df_statcast_group: pd.DataFrame):
    sorted_value_counts = df['pitch_type'].value_counts().sort_values(ascending=False)
    items_in_order = sorted_value_counts.index.tolist()
    ax.axis('off')
    ax.set_title('Pitch Velocity Distribution', fontdict={'size': 20})

    inner_grid_1 = gridspec.GridSpecFromSubplotSpec(len(items_in_order), 1, subplot_spec=gs[gs_x[0]:gs_x[-1], gs_y[0]:gs_y[-1]])
    ax_top = []

    for inner in inner_grid_1:
        ax_top.append(fig.add_subplot(inner))

    for ax_number, i in enumerate(items_in_order):

        ax_top[ax_number].set_ylabel('')
        ax_top[ax_number].yaxis.set_visible(False)
        ax_top[ax_number].set_yticklabels([])

        pitch_df = df[df['pitch_type'] == i]
        if np.unique(pitch_df['release_speed']).size == 1:
            ax_top[ax_number].plot([pitch_df['release_speed'].iloc[0]]*2, [0, 1], linewidth=4,
                                   color=dict_color[i], zorder=20)
        else:
            sns.kdeplot(pitch_df['release_speed'], ax=ax_top[ax_number], fill=True,
                        clip=(pitch_df['release_speed'].min(), pitch_df['release_speed'].max()),
                        color=dict_color[i])

        mean_speed = pitch_df['release_speed'].mean()
        ax_top[ax_number].axvline(mean_speed, linestyle='--', color=dict_color[i])

        group_speed = df_statcast_group[df_statcast_group['pitch_type'] == i]['release_speed'].mean()
        ax_top[ax_number].axvline(group_speed, linestyle=':', color=dict_color[i])

        ax_top[ax_number].set_xlim(math.floor(df['release_speed'].min() / 5) * 5, math.ceil(df['release_speed'].max() / 5) * 5)
        ax_top[ax_number].set_xticks(range(math.floor(df['release_speed'].min() / 5) * 5, math.ceil(df['release_speed'].max() / 5) * 5, 5))
        ax_top[ax_number].set_yticks([])
        ax_top[ax_number].grid(axis='x', linestyle='--')
        ax_top[ax_number].text(-0.01, 0.5, i, transform=ax_top[ax_number].transAxes, fontsize=14, va='center', ha='right')
        if ax_number < len(items_in_order) - 1:
            ax_top[ax_number].spines[['top', 'right', 'left']].set_visible(False)
            ax_top[ax_number].tick_params(axis='x', colors='none')
        else:
            ax_top[ax_number].spines[['top', 'right', 'left']].set_visible(False)
            ax_top[ax_number].set_xlabel('Velocity (mph)')


def rolling_pitch_usage(df: pd.DataFrame, ax: plt.Axes, window: int):
    df_game_group = pd.DataFrame((df.groupby(['game_pk', 'game_date', 'pitch_type'])['release_speed'].count() /
                                df.groupby(['game_pk', 'game_date'])['release_speed'].count()).reset_index())

    all_games = pd.Series(df_game_group['game_pk'].unique())
    all_pitch_types = pd.Series(df_game_group['pitch_type'].unique())
    all_combinations = pd.MultiIndex.from_product([all_games, all_pitch_types], names=['game_pk', 'pitch_type']).to_frame(index=False)
    df_complete = pd.merge(all_combinations, df_game_group, on=['game_pk', 'pitch_type'], how='left')
    df_complete['release_speed'] = df_complete['release_speed'].fillna(0)

    game_list = df.sort_values(by='game_date')['game_pk'].unique()
    range_list = list(range(1, len(game_list) + 1))
    game_to_range = dict(zip(game_list, range_list))
    game_to_date = df.set_index('game_pk')['game_date'].to_dict()

    df_complete['game_date'] = df_complete['game_pk'].map(game_to_date)
    df_complete = df_complete.sort_values(by='game_date')
    df_complete['game_number'] = df_complete['game_pk'].map(game_to_range)

    sorted_value_counts = df['pitch_type'].value_counts().sort_values(ascending=False)
    items_in_order = sorted_value_counts.index.tolist()
    max_roll = []

    for i in items_in_order:
        pitch_data = df_complete[df_complete['pitch_type'] == i]
        rolling_usage = pitch_data['release_speed'].rolling(window).sum() / window
        sns.lineplot(x=pitch_data['game_number'], y=rolling_usage,
                     color=dict_color[i], ax=ax, linewidth=3)
        max_roll.append(rolling_usage.max())

    ax.set_xlim(window, len(game_list))
    ax.set_ylim(0, math.ceil(max(max_roll) * 10) / 10)
    ax.set_xlabel('Game', fontdict=font_properties_axes)
    ax.set_ylabel('Pitch Usage', fontdict=font_properties_axes)
    ax.set_title(f"{window} Game Rolling Pitch Usage", fontdict=font_properties_titles)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))


def break_plot(df: pd.DataFrame, ax: plt.Axes):
    print("Pitch types in df:", df['pitch_type'].unique())
    hand = df['p_throws'].values[0]
    x = df['pfx_x'] * (-1 if hand == 'R' else 1)
    sns.scatterplot(ax=ax, x=x, y=df['pfx_z'],
                    hue=df['pitch_type'], palette=dict_color,
                    ec='black', alpha=1, zorder=2)

    ax.axhline(y=0, color='#808080', alpha=0.5, linestyle='--', zorder=1)
    ax.axvline(x=0, color='#808080', alpha=0.5, linestyle='--', zorder=1)

    ax.set_xlabel('Horizontal Break (in)', fontdict=font_properties_axes)
    ax.set_ylabel('Induced Vertical Break (in)', fontdict=font_properties_axes)
    ax.set_title("Pitch Breaks", fontdict=font_properties_titles)
    #ax.get_legend().remove()
    ax.set_xticks(range(-20, 21, 10))
    ax.set_xticklabels(range(-20, 21, 10), fontdict=font_properties)
    ax.set_yticks(range(-20, 21, 10))
    ax.set_yticklabels(range(-20, 21, 10), fontdict=font_properties)
    ax.set_xlim((-25, 25))
    ax.set_ylim((-25, 25))
    ax.set_aspect('equal', adjustable='box')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: int(x)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: int(x)))

    if hand == 'R':
        ax.text(-24.2, -24.2, s='← Glove Side', fontstyle='italic', ha='left', va='bottom',
                bbox=dict(facecolor='white', edgecolor='black'), fontsize=10, zorder=3)
        ax.text(24.2, -24.2, s='Arm Side →', fontstyle='italic', ha='right', va='bottom',
                bbox=dict(facecolor='white', edgecolor='black'), fontsize=10, zorder=3)
    else:
        ax.invert_xaxis()
        ax.text(24.2, -24.2, s='← Arm Side', fontstyle='italic', ha='left', va='bottom',
                bbox=dict(facecolor='white', edgecolor='black'), fontsize=10, zorder=3)
        ax.text(-24.2, -24.2, s='Glove Side →', fontstyle='italic', ha='right', va='bottom',
                bbox=dict(facecolor='white', edgecolor='black'), fontsize=10, zorder=3)


def fangraphs_pitcher_stats(pitcher_id: int, ax: plt.Axes, stats : list, season: int, fontsize: int = 20):
    from data_load import fangraphs_pitching_leaderboards
    df = fangraphs_pitching_leaderboards(season)
    df_pitcher = df[df['xMLBAMID'] == pitcher_id][stats].reset_index(drop=True)

    format_map = {
        'IP': '.1f', 'TBF': '.0f', 'WHIP': '.2f', 'ERA': '.2f', 'FIP': '.2f',
        'K%': '.1%', 'BB%': '.1%', 'K-BB%': '.1%'
    }

    df_pitcher = df_pitcher.astype('object')  # allow mixing types
    df_pitcher.loc[0] = [str(format(df_pitcher[x][0], format_map[x])) if df_pitcher[x][0] != '---' else '---' for x in df_pitcher]

    table_fg = ax.table(cellText=df_pitcher.values, colLabels=stats, cellLoc='center',
                        bbox=[0.00, 0.0, 1, 1])
    table_fg.set_fontsize(fontsize)
    ax.axis('off')


def plot_pitch_format(df: pd.DataFrame):
    df_group = df[table_columns].fillna('—')
    for column, props in pitch_stats_dict.items():
        if column in df_group.columns:
            df_group[column] = df_group[column].apply(
                lambda x: format(x, props['format']) if isinstance(x, (int, float)) else x)
    return df_group


def get_color(value, normalize, cmap):
    color = cmap(normalize(value))
    return mcolors.to_hex(color)


def get_cell_colors(df_group: pd.DataFrame,
                     df_statcast_group: pd.DataFrame,
                     color_stats: list,
                     cmap_sum: mcolors.Colormap,
                     cmap_sum_r: mcolors.Colormap):
    color_list_df = []
    for pt in df_group.pitch_type.unique():
        row = []
        df_pitch = df_group[df_group['pitch_type'] == pt]
        statcast_pitch = df_statcast_group[df_statcast_group['pitch_type'] == pt]

        for col in table_columns:
            val = df_pitch[col].values[0] if col in df_pitch.columns else None

            if col not in statcast_pitch.columns:
                row.append('#ffffff')
                continue

            ref = pd.to_numeric(statcast_pitch[col], errors='coerce')

            if col in color_stats and isinstance(val, (int, float)):
                if np.isnan(val):
                    row.append('#ffffff')
                elif col == 'release_speed':
                    normalize = mcolors.Normalize(vmin=ref.mean() * 0.95, vmax=ref.mean() * 1.05)
                    row.append(get_color(val, normalize, cmap_sum))
                elif col == 'delta_run_exp_per_100':
                    normalize = mcolors.Normalize(vmin=-1.5, vmax=1.5)
                    row.append(get_color(val, normalize, cmap_sum))
                elif col == 'xwoba':
                    normalize = mcolors.Normalize(vmin=ref.mean() * 0.7, vmax=ref.mean() * 1.3)
                    row.append(get_color(val, normalize, cmap_sum_r))
                else:
                    normalize = mcolors.Normalize(vmin=ref.mean() * 0.7, vmax=ref.mean() * 1.3)
                    row.append(get_color(val, normalize, cmap_sum))
            else:
                row.append('#ffffff')
        color_list_df.append(row)
    return color_list_df

def plot_fatigue_trend(fatigue_df: pd.DataFrame, ax: plt.Axes):
    if fatigue_df.empty:
        ax.text(0.5, 0.5, 'No Fatigue Data Available', ha='center', va='center')
        ax.axis('off')
        return

    # Create pivot table
    pivot_df = fatigue_df.pivot_table(index='game_number', 
                                    columns='pitch_type', 
                                    values='fatigue_flag',
                                    aggfunc='max').fillna(0)

    # Plotting
    colors = [dict_color[pt] for pt in pivot_df.columns]
    pivot_df.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.8)

    # Formatting
    ax.set_title("Fatigue Flags by Game and Pitch Type", fontdict=font_properties_titles)
    ax.set_xlabel("Game Number", fontdict=font_properties_axes)
    ax.set_ylabel("Fatigue Flag", fontdict=font_properties_axes)
    ax.legend(title='Pitch Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(0, 1.5)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add data labels
    for idx, (game, row) in enumerate(pivot_df.iterrows()):
        if row.sum() > 0:
            ax.text(idx, 1.1, 'Fatigue\nDetected', 
                   ha='center', va='bottom', 
                   fontsize=10, color='red')


def pitch_table(df: pd.DataFrame, ax: plt.Axes, df_statcast_group: pd.DataFrame, fontsize: int = 20):
    df_group, color_list = df_grouping(df)
    color_list_df = get_cell_colors(df_group, df_statcast_group, color_stats, cmap_sum, cmap_sum_r)
    df_plot = plot_pitch_format(df_group)

    print("df_plot shape:", df_plot.shape)
    print("color_list_df shape:", (len(color_list_df), len(color_list_df[0]) if color_list_df else 0))

    table_plot = ax.table(cellText=df_plot.values, colLabels=df_plot.columns.tolist(), cellLoc='center',
                          bbox=[0, -0.1, 1, 1], cellColours=color_list_df)

    table_plot.auto_set_font_size(False)
    table_plot.set_fontsize(fontsize)
    table_plot.scale(1, 0.5)

    for i in range(len(df_plot)):
        table_plot.get_celld()[(i + 1, 0)].get_text().set_fontweight('bold')

    ax.axis('off')