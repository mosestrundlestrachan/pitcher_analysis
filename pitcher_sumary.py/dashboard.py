import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
from preprocessing import df_processing
from visuals import (
    player_headshot, player_bio, plot_logo,
    velocity_kdes, rolling_pitch_usage, break_plot,
    fangraphs_pitcher_stats, pitch_table, plot_fatigue_trend
)
from fatigue import create_fatigue_features

def pitching_dashboard(pitcher_id: str, df: pd.DataFrame, stats: list, df_statcast_group: pd.DataFrame, season: int, fatigue_df: pd.DataFrame):
    # Process the data
    df = df_processing(df)

    fatigue_df = create_fatigue_features(df)

    # Update grid layout
    fig = plt.figure(figsize=(20, 28))  # Increased height
    gs = gridspec.GridSpec(7, 8,  # Added row for fatigue chart
                         height_ratios=[2, 14, 5, 36, 36, 36, 8],
                         width_ratios=[1, 18, 18, 18, 18, 18, 18, 1])

    # Add fatigue axis
    ax_fatigue = fig.add_subplot(gs[5, 1:7])
    
    # Existing axes setup...
    ax_table = fig.add_subplot(gs[4, 1:7])  # Moved table up
    ax_fatigue = fig.add_subplot(gs[5, 1:7])  # New fatigue chart

    # Add fatigue plot call

    # Create figure and layout grid
    fig = plt.figure(figsize=(20, 24))
    gs = gridspec.GridSpec(6, 8,
                           height_ratios=[2, 10, 5, 30, 30, 8],
                           width_ratios=[1, 18, 18, 18, 18, 18, 18, 1])

    # Axes layout
    ax_headshot = fig.add_subplot(gs[1, 1:2])
    ax_bio = fig.add_subplot(gs[1, 2:4])
    ax_logo = fig.add_subplot(gs[1, 5:6])
    ax_season_table = fig.add_subplot(gs[2, 1:7])
    ax_plot_1 = fig.add_subplot(gs[3, 1:3])
    ax_plot_2 = fig.add_subplot(gs[3, 3:5])
    ax_plot_3 = fig.add_subplot(gs[3, 5:7])
    ax_table = fig.add_subplot(gs[4, 1:7])
    ax_footer = fig.add_subplot(gs[-1, 1:7])
    ax_header = fig.add_subplot(gs[0, 1:7])
    ax_left = fig.add_subplot(gs[:, 0])
    ax_right = fig.add_subplot(gs[:, -1])

    # Hide unused frames
    for ax in [ax_footer, ax_header, ax_left, ax_right]:
        ax.axis('off')

    # Visual content
    player_headshot(pitcher_id, ax_headshot)
    player_bio(pitcher_id, ax_bio)
    plot_logo(pitcher_id, ax_logo)

    # Top stats
    fangraphs_pitcher_stats(pitcher_id, ax_season_table, stats, season=season, fontsize=20)
    plot_fatigue_trend(fatigue_df, ax_fatigue)

    # Pitch visuals
    pitch_table(df, ax_table, df_statcast_group, fontsize=16)
    velocity_kdes(df=df, ax=ax_plot_1, gs=gs, gs_x=[3, 4], gs_y=[1, 3], fig=fig, df_statcast_group=df_statcast_group)
    rolling_pitch_usage(df, ax=ax_plot_2, window=5)
    break_plot(df=df, ax=ax_plot_3)

    # Footer text
    ax_footer.text(0, 1, 'By: Moses TS', ha='left', va='top', fontsize=22)
    ax_footer.text(0.5, 1, 'Color Coding Compares to League Average By Pitch', ha='center', va='top', fontsize=16)
    ax_footer.text(1, 1, 'Data: MLB, Fangraphs\nImages: MLB, ESPN', ha='right', va='top', fontsize=20)

    # Optional: add pitch-type legend from break plot
    handles, labels = ax_plot_3.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc='lower center', ncol=6, fontsize=13)

    plt.tight_layout()
    fig.savefig("pitching_dashboard.pdf", format="pdf", bbox_inches="tight", dpi=300)
    plt.show()
