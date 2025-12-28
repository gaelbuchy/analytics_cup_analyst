import pandas as pd
import requests
import numpy as np
import os
from pathlib import Path

from src.utils.log import log_message


class DataManager:

    def __init__(self, current_dir=None, ids=[], cache=True):
        self._current_dir = Path(
            __file__).parent if current_dir is None else current_dir
        self.data_dir = f"{self._current_dir}/../../cache/"
        self.match_ids = ids if ids else [
            1886347, 1899585, 1925299, 1953632, 1996435, 2006229, 2011166, 2013725, 2015213, 2017461]
        self.cache = cache

    def time_to_seconds(self, time_str):
        if time_str is None:
            return 90 * 60  # 120 minutes = 7200 seconds
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def load_tracking_data(self, match_id):
        """Load and preprocess tracking data for a given match ID."""

        raw_data = pd.read_json(
            f"https://media.githubusercontent.com/media/SkillCorner/opendata/refs/heads/master/data/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl", lines=True
        )

        # Flatten the nested JSON structure
        raw_df = pd.json_normalize(
            raw_data.to_dict("records"),
            "player_data",
            ["frame", "timestamp", "period", "possession", "ball_data"],
        )

        # get possesion player and group
        raw_df["possession_player_id"] = raw_df["possession"].apply(
            lambda x: x.get("player_id")
        )
        raw_df["possession_group"] = raw_df["possession"].apply(
            lambda x: x.get("group"))

        # get the ball_data
        raw_df[["ball_x", "ball_y", "ball_z", "is_detected_ball"]] = pd.json_normalize(
            raw_df.ball_data
        )

        raw_df = raw_df.drop(columns=["possession", "ball_data"])

        raw_df["match_id"] = match_id
        tracking_df = raw_df.copy()

        return tracking_df

    def load_player_data(self, match_id):
        """Load match data and extract players"""
        meta_data_github_url = f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{match_id}/{match_id}_match.json"
        response = requests.get(meta_data_github_url)
        raw_match_data = response.json()

        raw_match_df = pd.json_normalize(raw_match_data, max_level=2)
        raw_match_df["home_team_side"] = raw_match_df["home_team_side"].astype(
            str)

        # get players
        players_df = pd.json_normalize(
            raw_match_df.to_dict("records"),
            record_path="players",
            meta=[
                "id",
                "home_team_score",
                "away_team_score",
                "date_time",
                "home_team_side",
                "home_team.name",
                "home_team.id",
                "away_team.name",
                "away_team.id",
            ],
            meta_prefix='match_'
        )

        # Take only players who played and create their total time
        players_df = players_df[
            ~((players_df.start_time.isna()) & (players_df.end_time.isna()))
        ]
        players_df["total_time"] = players_df["end_time"].apply(self.time_to_seconds) - players_df[
            "start_time"
        ].apply(self.time_to_seconds)

        # Create a flag for GK
        players_df["is_gk"] = players_df["player_role.acronym"] == "GK"

        # Add match name
        players_df["match_name"] = (
            players_df["match_home_team.name"] + " vs " +
            players_df["match_away_team.name"]
        )

        # Add a flag if the given player is home or away
        players_df["home_away_player"] = np.where(
            players_df.team_id == players_df["match_home_team.id"], "Home", "Away"
        )

        # Create flag from player
        players_df["team_name"] = np.where(
            players_df.team_id == players_df["match_home_team.id"],
            players_df["match_home_team.name"],
            players_df["match_away_team.name"],
        )

        # Figure out sides
        players_df[["home_team_side_1st_half", "home_team_side_2nd_half"]] = (
            players_df["match_home_team_side"]
            .astype(str)
            .str.strip("[]")
            .str.replace("'", "")
            .str.split(", ", expand=True)
        )
        # Clean up sides
        players_df["direction_player_1st_half"] = np.where(
            players_df.home_away_player == "Home",
            players_df.home_team_side_1st_half,
            players_df.home_team_side_2nd_half,
        )
        players_df["direction_player_2nd_half"] = np.where(
            players_df.home_away_player == "Home",
            players_df.home_team_side_2nd_half,
            players_df.home_team_side_1st_half,
        )

        # Clean up and keep the columns that we want to keep about
        columns_to_keep = [
            "start_time",
            "end_time",
            "match_id",
            "match_name",
            "match_date_time",
            "match_home_team.name",
            "match_away_team.name",
            "id",
            "short_name",
            "number",
            "team_id",
            "team_name",
            "player_role.position_group",
            "total_time",
            "playing_time.total.minutes_tip",
            "playing_time.total.minutes_played",
            "player_role.name",
            "player_role.acronym",
            "is_gk",
            "direction_player_1st_half",
            "direction_player_2nd_half",
        ]
        players_df = players_df[columns_to_keep]

        return players_df

    def load_enriched_tracking_data(self, match_id):
        """Load tracking data with player data"""

        path = f"{self.data_dir}match_{match_id}_enriched_tracking_data.parquet.gzip"

        if self.cache and os.path.exists(path):
            enriched_tracking_data = pd.read_parquet(path)

            log_message(f"Found {match_id} tracking from file cache")
        else:
            tracking_df = self.load_tracking_data(match_id)
            players_df = self.load_player_data(match_id)

            enriched_tracking_data = tracking_df.merge(
                players_df, left_on=["player_id"], right_on=["id"]
            )

            if self.cache:

                log_message(f"Storing {match_id} tracking to file cache")

                enriched_tracking_data.to_parquet(path, compression='gzip')

        return enriched_tracking_data

    def load_match_events(self, match_id):
        """Load dynamic events for match_id"""

        path = f"{self.data_dir}match_{match_id}_events.parquet.gzip"

        if self.cache and os.path.exists(path):
            events = pd.read_parquet(path)

            log_message(f"Found {match_id} events from file cache")
        else:
            events = pd.read_csv(
                f"https://raw.githubusercontent.com/SkillCorner/opendata/refs/heads/master/data/matches/{match_id}/{match_id}_dynamic_events.csv")
            if self.cache:

                log_message(f"Storing {match_id} events to file cache")

                events.to_parquet(path, compression='gzip')
        return events

    def concatenate_all_matches_events(self):
        """Get events for all matches"""

        df_list = []
        for i in self.match_ids:
            t = self.load_match_events(i)
            df_list.append(t)

        return pd.concat(df_list, ignore_index=True)

    def concatenate_all_matches_data(self):
        """Get all matches data"""

        df_list = []
        for i in self.match_ids:
            t = self.load_player_data(i)
            df_list.append(t)

        return pd.concat(df_list, ignore_index=True)

    def add_pass_options(self, all_events, possessions):
        """Add passing options to possessions"""

        possessions["passing_options"] = None

        for id in possessions.index:
            match_id = possessions.loc[id]['match_id']
            event_id = possessions.loc[id]['event_id']

            # find the associated passing options
            pass_options = all_events[(all_events['associated_player_possession_event_id'] == event_id) & (
                all_events['event_type'] == 'passing_option') & (all_events['match_id'] == match_id)]

            # get the fields
            options = pass_options[['xthreat', 'xpass_completion',
                                    'passing_option_score', 'associated_off_ball_run_subtype', 'pass_range']]

            possessions.at[id, 'passing_options'] = options.to_dict('records')

    def add_position_category(self, events):
        """Add position category"""

        position_to_category = {
            'GK': 'Keeper',
            'LB': 'Defender', 'RB': 'Defender', 'LCB': 'Defender', 'RCB': 'Defender',
            'CB': 'Defender', 'LWB': 'Defender', 'RWB': 'Defender',
            'LM': 'Midfielder', 'RM': 'Midfielder', 'LDM': 'Midfielder', 'RDM': 'Midfielder',
            'DM': 'Midfielder', 'AM': 'Midfielder',
            'LW': 'Attacker', 'RW': 'Attacker', 'LF': 'Attacker', 'RF': 'Attacker', 'CF': 'Attacker',
        }

        events['position_category'] = events['player_position'].map(
            position_to_category).fillna('Unknown')

    def get_data_with_passing_options(self):
        """Get all dynamic events with passing options"""

        path_events = f"{self.data_dir}all_events.parquet.gzip"
        path_possessions = f"{self.data_dir}all_possessions.parquet.gzip"

        if self.cache and os.path.exists(path_possessions) and os.path.exists(path_events):
            all_events = pd.read_parquet(path_events)
            all_pass_possessions = pd.read_parquet(path_possessions)

            log_message("Found all pass possessions from file cache")
        else:
            all_events = self.concatenate_all_matches_events()
            all_pass_possessions = all_events[(
                all_events['event_type'] == 'player_possession')]
            self.add_pass_options(all_events, all_pass_possessions)
            self.add_position_category(all_pass_possessions)

            if self.cache:
                all_pass_possessions.to_parquet(
                    path_possessions, compression='gzip')
                all_events.to_parquet(path_events, compression='gzip')

                log_message("Store all pass possessions to cache")

        return all_events, all_pass_possessions
