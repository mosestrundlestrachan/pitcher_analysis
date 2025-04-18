import pandas as pd
import matplotlib.colors as mcolors
import numpy as np
from constants import dict_color, dict_pitch, table_columns, pitch_stats_dict


def df_processing(df_pyb: pd.DataFrame):
    df = df_pyb.copy()

    swing_code = [
        'foul_bunt', 'foul', 'hit_into_play', 'swinging_strike',
        'foul_tip', 'swinging_strike_blocked', 'missed_bunt', 'bunt_foul_tip'
    ]
    whiff_code = ['swinging_strike', 'foul_tip', 'swinging_strike_blocked']

    df['swing'] = df['description'].isin(swing_code)
    df['whiff'] = df['description'].isin(whiff_code)
    df['in_zone'] = df['zone'] < 10
    df['out_zone'] = df['zone'] > 10
    df['chase'] = (~df['in_zone']) & df['swing']

    df['pfx_z'] = df['pfx_z'] * 12
    df['pfx_x'] = df['pfx_x'] * 12
    
    return df


def df_grouping(df: pd.DataFrame):
    df_group = df.groupby(['pitch_type']).agg(
        pitch=('pitch_type', 'count'),
        release_speed=('release_speed', 'mean'),
        pfx_z=('pfx_z', 'mean'),
        pfx_x=('pfx_x', 'mean'),
        release_spin_rate=('release_spin_rate', 'mean'),
        release_pos_x=('release_pos_x', 'mean'),
        release_pos_z=('release_pos_z', 'mean'),
        release_extension=('release_extension', 'mean'),
        delta_run_exp=('delta_run_exp', 'sum'),
        swing=('swing', 'sum'),
        whiff=('whiff', 'sum'),
        in_zone=('in_zone', 'sum'),
        out_zone=('out_zone', 'sum'),
        chase=('chase', 'sum'),
        xwoba=('estimated_woba_using_speedangle', 'mean'),
    ).reset_index()

    df_group['pitch_description'] = df_group['pitch_type'].map(dict_pitch)
    df_group['pitch_usage'] = df_group['pitch'] / df_group['pitch'].sum()
    df_group['whiff_rate'] = df_group['whiff'] / df_group['swing']
    df_group['in_zone_rate'] = df_group['in_zone'] / df_group['pitch']
    df_group['chase_rate'] = df_group['chase'] / df_group['out_zone']
    df_group['delta_run_exp_per_100'] = -df_group['delta_run_exp'] / df_group['pitch'] * 100
    df_group['color'] = df_group['pitch_type'].map(dict_color)
    df_group = df_group.sort_values(by='pitch_usage', ascending=False)

    color_list = df_group['color'].tolist()

    plot_table_all = pd.DataFrame(data={
        'pitch_type': 'All',
        'pitch_description': 'All',
        'pitch': df['pitch_type'].count(),
        'pitch_usage': 1,
        'release_speed': np.nan,
        'pfx_z': np.nan,
        'pfx_x': np.nan,
        'release_spin_rate': np.nan,
        'release_pos_x': np.nan,
        'release_pos_z': np.nan,
        'release_extension': df['release_extension'].mean(),
        'delta_run_exp_per_100': df['delta_run_exp'].sum() / df['pitch_type'].count() * -100,
        'whiff_rate': df['whiff'].sum() / df['swing'].sum(),
        'in_zone_rate': df['in_zone'].sum() / df['pitch_type'].count(),
        'chase_rate': df['chase'].sum() / df['out_zone'].sum(),
        'xwoba': df['estimated_woba_using_speedangle'].mean()
    }, index=[0])

    df_plot = pd.concat([df_group, plot_table_all], ignore_index=True)
    return df_plot, color_list


cmap_sum = mcolors.LinearSegmentedColormap.from_list("", ['#648FFF', '#FFFFFF', '#FFB000'])
cmap_sum_r = mcolors.LinearSegmentedColormap.from_list("", ['#FFB000', '#FFFFFF', '#648FFF'])


def get_color(value, normalize, cmap):
    return mcolors.to_hex(cmap(normalize(value)))


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


def plot_pitch_format(df: pd.DataFrame):
    """
    Format the grouped DataFrame for visualization by applying column-specific formats.
    """
    # Ensure all required columns are present and fill missing values with placeholders
    df_group = df[table_columns].fillna('—')

    # Apply the formats defined in `pitch_stats_dict` to the DataFrame columns
    for column, props in pitch_stats_dict.items():
        if column in df_group.columns:
            df_group[column] = df_group[column].apply(
                lambda x: format(x, props['format']) if isinstance(x, (int, float)) else x
            )
    return df_group


