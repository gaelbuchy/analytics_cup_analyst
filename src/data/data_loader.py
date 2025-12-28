
import streamlit as st

from src.data.data_manager import DataManager
from src.data.passing_evaluation import PassingEvaluation

manager = DataManager()
pe = PassingEvaluation()


@st.cache_data()
def load_data():
    all_events, all_pass_possessions = manager.get_data_with_passing_options()
    all_pass_possessions = pe.compute_metrics(all_pass_possessions)

    players_data = manager.concatenate_all_matches_data()
    players = players_data.groupby(["id", "short_name"])[
        ["playing_time.total.minutes_played", "playing_time.total.minutes_tip"]].sum().reset_index()

    return {
        "all_events": all_events,
        "all_pass_possessions": all_pass_possessions,
        "players": players,
    }


@st.cache_data()
def load_tracking_data(match_id):
    return manager.load_enriched_tracking_data(
        match_id)


def load_data_with_filter(third="All"):

    data = load_data()

    data['filtered_possessions'] = pe.third_filter(
        data['all_pass_possessions'], third)
    data['grouped_by_players'] = pe.group_by_players(
        data['filtered_possessions'], data['players'])

    data['teams'] = sorted(data['filtered_possessions']
                           ['team_shortname'].unique().tolist())
    data['position_categories'] = sorted(
        data['filtered_possessions']['position_category'].unique().tolist())
    data['positions'] = sorted(
        data['filtered_possessions']['player_position'].unique().tolist())

    return data
