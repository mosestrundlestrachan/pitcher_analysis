import logging
import sys
from data_load import load_pitch_data, load_statcast_grouped
from preprocessing import df_processing
from dashboard import pitching_dashboard
from data_load import get_player_id
from constants import stats
from fatigue import create_fatigue_features

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main(pitcher_id, season, stats):
    """
    Main function to load data, process it, and run the pitching dashboard.

    Args:
        pitcher_id (int): The ID of the pitcher.
        season (int): The season year.
        stats (list): List of stats to display.
    """
    try:
        logging.info(f"Loading Statcast data for pitcher ID {pitcher_id} and season {season}...")
        df_pyb = load_pitch_data(pitcher_id, season)
        if df_pyb.empty:
            logging.error("Pitcher data is empty. Please check the pitcher ID or data source.")
            return

        logging.info("Loading league-wide grouped Statcast data...")
        statcast_grouped_df = load_statcast_grouped(season)
        if statcast_grouped_df.empty:
            logging.error("League-wide data is empty. Please check the data source.")
            return

        logging.info("Processing pitcher's game-by-game data...")
        df_processed = df_processing(df_pyb)
        if df_processed.empty:
            logging.error("Processed data is empty. Please check the input data or processing logic.")
            return
        logging.info("Calculating fatigue features...")
        try:
            fatigue_df = create_fatigue_features(df_processed)
        except Exception as e:
            logging.warning(f"Could not calculate fatigue features: {e}")

        logging.info("Running the pitching dashboard...")
        pitching_dashboard(pitcher_id, df_processed, stats, statcast_grouped_df, season, fatigue_df)
        logging.info("Dashboard successfully launched.")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")


if __name__ == "__main__":
    # Prompt the user for the player's name
    pitcher_name = input("Enter the pitcher's name (First Last): ")
    pitcher_id = get_player_id(pitcher_name)  # Pass the pitcher_name to the function
    if pitcher_id:
        print(f"Player ID for {pitcher_name} is {pitcher_id}")
    else:
        print("Could not retrieve player ID. Exiting.")
        sys.exit(1)

    try:
        season = int(input("Enter the season year: "))
        #stats = input("Enter the stats to display (comma-separated, e.g., 'IP,TBF,WHIP'): ").split(',')
        #stats = [stat.strip() for stat in stats]  # Clean up whitespace
    except ValueError:
        logging.error("Invalid input. Please enter numeric values for season.")
        sys.exit(1)

    main(pitcher_id, season, stats)