import numpy as np
import pandas as pd

from src.utils.log import log_message

metric_labels = {
    'safest_pass': 'Safest Pass',
    'highest_xthreat_pass': 'Highest xThreat Pass',

    'has_good_pass_opportunities': 'Has Good Opportunities',
    'good_pass_opportunity': 'Is Good Opportunity',
    'missed_good_pass_opportunity': 'Missed Good Opportunity',

    'xthreat_available': 'xThreat Available',
    'missed_xthreat': 'Missed xThreat',
    "decision_efficiency": "Decision Efficiency",

    'x_xthreat_best': 'Expected xThreat Best',
    'x_xthreat_avg': 'Expected xThreat Average',

    'options_count': 'Options Count',

    'better_x_xthreats_count': 'Better Expected xThreat Count ',

    'safest_pass_perc': "Safest Pass %",
    'safest_pass_sum': "Safest Pass Count",
    "highest_xthreat_pass_perc": "Highest xThreat Pass %",
    'highest_xthreat_pass_sum': "Highest xThreat Count",
    "has_good_pass_opportunities_perc": "Good Opportunities Available %",
    'has_good_pass_opportunities_sum': "Good Opportunities Available Count",
    "good_pass_opportunity_perc": "Good Opportunity %",
    'good_pass_opportunity_sum': "Good Opportunity Count",
    "missed_good_pass_opportunity_perc": "Missed Good Opportunity %",
    'missed_good_pass_opportunity_sum': "Missed Good Opportunity Count",
    "completed_perc": "Completion Rate",
    'completed_sum': "Completed",
    "completed_safest_pass_perc": "Safest Pass Completion Rate",
    'completed_safest_pass_sum': "Safest Pass Completed",
    "completed_highest_xthreat_pass_perc": "Highest xThreat Completion Rate",
    'completed_highest_xthreat_pass_sum': "Highest xThreat Completed",
    "completed_good_pass_opportunity_perc": "Good Opportunity Completion Rate",
    'completed_good_pass_opportunity_sum': "Good Opportunity Completed",
    'player_targeted_xthreat': "xThreat Created",
    'player_targeted_xthreat_sum': "xThreat Created",
    'player_targeted_xthreat_mean': "xThreat Created (Average)",
    'xthreat_available_sum': "xThreat Available",
    'xthreat_available_mean': "xThreat Available (Available)",
    'missed_xthreat_sum': "xThreat Missed",
    'missed_xthreat_mean': "xThreat Missed (Average)",
    'event_id_count': "Total Passes",
    'player_position': "Player Position",
    'position_category': "Position Category",
    'team_shortname': "Team",
    'short_name': "Player Name",
    'player_id': "Player ID",

    "xthreat_available_p90": "xThreat Available (P90)",
    "player_targeted_xthreat_p90": "xThreat Created (P90)",
    "missed_xthreat_p90": "Missed xThreat (P90)",
    "decision_efficiency_p90": "Decision Efficiency (P90)",

    "xthreat_available_p90_mean": "Average xThreat Available (P90)",
    "player_targeted_xthreat_p90_mean": "Average xThreat Created (P90)",
    "efficiency_p90": "Average Decision Efficiency (P90)",
    "highest_xthreat_pass_perc_mean": "Average Highest xThreat",

    "has_good_pass_opportunities_mean": "Good Opportunities Available On Average",
    "good_pass_opportunity_mean": "Average Good Opportunity",
    "missed_good_pass_opportunity_mean": "Missed Good Opportunity On Average",
    "safest_pass_perc_mean": "Average Safest Pass",
    "completed_perc_mean": "Average Completion Rate",
}


class PassingEvaluation:
    columns = [
        'event_id',
        'index',
        'match_id',
        'frame_start',
        'frame_end',
        'time_start',
        'time_end',
        'minute_start',
        'duration',
        'period',
        'event_type',
        'event_subtype',
        'player_id',
        'player_name',
        'player_position',
        'team_id',
        'team_shortname',
        'x_start',
        'y_start',
        'channel_start',
        'third_start',
        'penalty_area_start',
        'x_end',
        'y_end',
        'third_end',
        'game_state',
        'team_score',
        'opponent_team_score',
        'n_player_possessions_in_phase',
        'team_in_possession_phase_type',
        'team_out_of_possession_phase_type',
        'start_type',
        'end_type',
        'one_touch',
        'quick_pass',
        'carry',
        'forward_momentum',
        'is_header',
        'hand_pass',
        'pass_outcome',
        'targeted_passing_option_event_id',
        'player_targeted_id',
        'player_targeted_xpass_completion',
        'player_targeted_xthreat',
        'n_passing_options',
        'n_off_ball_runs',
        'pass_range',
        'passing_options',
        'position_category'
    ]

    def __init__(self, xpass_threshold=None, xthreat_threshold=None):
        self.good_xpass_threshold = xpass_threshold if xpass_threshold is not None else .8
        self.good_xthreat_threshold = xthreat_threshold
        self.realistic_xthreat_threshold = .4

    def init_xthreat_threshold(self, df):
        if self.good_xthreat_threshold is None:
            # get upper quartile from data
            self.good_xthreat_threshold = df['player_targeted_xthreat'].describe()[
                '75%']

    def compute_metrics(self, data):
        """Compute metrics for passing options"""
        # only keep situations with n_passing_options > 1 and with an player_targeted_xthreat
        df = data[(data['n_passing_options'] > 1) & (
            data['player_targeted_xthreat'].notna())][self.columns]

        self.init_xthreat_threshold(df)

        log_message(
            f"Using thresholds: xpass>= {self.good_xpass_threshold} and xthreat>= {self.good_xthreat_threshold}")

        # % pass will complete and will be a shot in the next 10s
        df['player_targeted_x_xthreat'] = df['player_targeted_xthreat'] * \
            df['player_targeted_xpass_completion']

        # process passing options
        options_results = df.apply(self.process_passing_options, axis=1)

        df['safest_pass'] = options_results.apply(lambda x: x['safest_pass'])
        df['highest_xthreat_pass'] = options_results.apply(
            lambda x: x['highest_xthreat_pass'])
        df['has_good_pass_opportunities'] = options_results.apply(
            lambda x: x['has_good_pass_opportunities'])
        df['good_pass_opportunity'] = options_results.apply(
            lambda x: x['good_pass_opportunity'])

        df['missed_good_pass_opportunity'] = options_results.apply(
            lambda x: x['missed_good_pass_opportunity'])

        df['xthreat_available'] = options_results.apply(
            lambda x: x['xthreat_available'])

        df['missed_xthreat'] = options_results.apply(
            lambda x: x['missed_xthreat'])

        df['decision_efficiency'] = (
            df['player_targeted_xthreat'] / df['xthreat_available']) * 100

        df['x_xthreat_best'] = options_results.apply(
            lambda x: x['x_xthreat_best'])
        df['x_xthreat_avg'] = options_results.apply(
            lambda x: x['x_xthreat_avg'])

        df['better_x_xthreats_count'] = options_results.apply(
            lambda x: x['better_x_xthreats_count'])

        df['options_count'] = options_results.apply(
            lambda x: x['options_count'])

        return df

    def is_good_pass_opportunity(self, xpass, xthreat):
        """Check if passing option is good opportunity"""
        return xpass >= self.good_xpass_threshold and xthreat >= self.good_xthreat_threshold

    def xthreat_available(self, options):
        """Calculate the maximum xThreat among realistic options.

            Args:
                options: List of dicts with 'xthreat' and 'completion_prob' keys

            Returns:
                float: Maximum xThreat where completion_prob >= 0.40
        """
        realistic_options = [
            opt['xthreat']
            for opt in options
            if opt['xpass_completion'] >= self.realistic_xthreat_threshold
        ]
        return max(realistic_options) if realistic_options else 0.0

    def process_passing_options(self, row):
        """Compare passing options"""

        options_data = row['passing_options']
        if not len(options_data):
            return

        player_targeted_x_xthreat = row['player_targeted_x_xthreat']
        player_targeted_xthreat = row['player_targeted_xthreat']
        player_targeted_xpass_completion = row['player_targeted_xpass_completion']

        # check if targeted is highest xthreat or completion
        higher_xpass_completion = False
        higher_xthreat = False
        has_good_pass_opportunities = False

        for o in options_data:
            if o['xpass_completion'] > player_targeted_xpass_completion:
                higher_xpass_completion = True

            if o['xthreat'] > player_targeted_xthreat:
                higher_xthreat = True

            if self.is_good_pass_opportunity(o['xpass_completion'], o['xthreat']):
                has_good_pass_opportunities = True

        targeted_is_good_pass_opportunity = self.is_good_pass_opportunity(
            row['player_targeted_xpass_completion'], row['player_targeted_xthreat'])

        # get best and average xthreat
        xthreat_available = self.xthreat_available(options_data)

        # calculate x_xthreat for each pass
        x_xthreats = [opt['xthreat'] * opt['xpass_completion']
                      for opt in options_data]
        x_xthreats_sorted = sorted(x_xthreats, reverse=True)
        x_xthreat_best = x_xthreats_sorted[0]
        x_xthreat_avg = np.mean(x_xthreats_sorted)

        better_x_xthreats_count = sum(
            1 if x > player_targeted_x_xthreat else 0 for x in x_xthreats)

        return {
            'safest_pass': 0 if higher_xpass_completion else 1,
            'highest_xthreat_pass': 0 if higher_xthreat else 1,

            'has_good_pass_opportunities': 1 if has_good_pass_opportunities else 0,
            'good_pass_opportunity': 1 if targeted_is_good_pass_opportunity else 0,
            'missed_good_pass_opportunity': 1 if not targeted_is_good_pass_opportunity and has_good_pass_opportunities else 0,

            'xthreat_available': xthreat_available if player_targeted_xthreat < xthreat_available else player_targeted_xthreat,
            'missed_xthreat': (xthreat_available - player_targeted_xthreat) if player_targeted_xthreat < xthreat_available else 0,

            'x_xthreat_best': x_xthreat_best,
            'x_xthreat_avg': x_xthreat_avg,

            'options_count': len(options_data),

            'better_x_xthreats_count': better_x_xthreats_count,
        }

    def group_by_players(self, df, minutes):
        df['completed'] = (df['pass_outcome'] == 'successful').astype(int)
        df['completed_safest_pass'] = (df['completed'] & df['safest_pass'])
        df['completed_highest_xthreat_pass'] = (
            df['completed'] & df['highest_xthreat_pass'])
        df['completed_good_pass_opportunity'] = (
            df['completed'] & df['good_pass_opportunity'])

        def subset_completion_rate(condition_col):
            def aggregator(x):
                subset = df.loc[x.index][df.loc[x.index]
                                         [condition_col] == 1][x.name]
                return (subset.sum() / subset.count() * 100) if subset.count() > 0 else 0
            return aggregator

        def subset_sum(condition_col):
            def aggregator(x):
                subset = df.loc[x.index][df.loc[x.index]
                                         [condition_col] == 1][x.name]
                return subset.sum()
            return aggregator

        players_agg = df.groupby('player_id').agg({
            'safest_pass': [lambda x: (x.sum() / len(x)) * 100, 'sum'],
            'highest_xthreat_pass': [lambda x: (x.sum() / len(x)) * 100, 'sum'],
            'has_good_pass_opportunities': [lambda x: (x.sum() / len(x)) * 100, 'sum'],
            'good_pass_opportunity': [subset_completion_rate('has_good_pass_opportunities'), subset_sum('has_good_pass_opportunities')],
            'missed_good_pass_opportunity': [subset_completion_rate('has_good_pass_opportunities'), subset_sum('has_good_pass_opportunities')],
            'completed': [lambda x: (x.sum() / len(x)) * 100, 'sum'],
            'completed_safest_pass': [subset_completion_rate('safest_pass'), subset_sum('safest_pass')],
            'completed_highest_xthreat_pass': [subset_completion_rate('highest_xthreat_pass'), subset_sum('highest_xthreat_pass')],
            'completed_good_pass_opportunity': [subset_completion_rate('good_pass_opportunity'), subset_sum('good_pass_opportunity')],
            'player_targeted_xthreat': ['sum', 'mean'],
            'xthreat_available': ['sum', 'mean'],
            'missed_xthreat': ['sum', 'mean'],
            'decision_efficiency': ['mean'],
            'event_id': 'count',
            'player_position': 'first',
            'position_category': 'first',
            'team_shortname': 'first'
        }).round(3).reset_index()

        players_agg.columns = ['_'.join(col).strip(
            '_') for col in players_agg.columns.values]

        players_agg.columns = [
            'player_id',
            'safest_pass_perc',
            'safest_pass_sum',
            'highest_xthreat_pass_perc',
            'highest_xthreat_pass_sum',
            'has_good_pass_opportunities_perc',
            'has_good_pass_opportunities_sum',
            'good_pass_opportunity_perc',
            'good_pass_opportunity_sum',
            'missed_good_pass_opportunity_perc',
            'missed_good_pass_opportunity_sum',
            'completed_perc',
            'completed_sum',
            'completed_safest_pass_perc',
            'completed_safest_pass_sum',
            'completed_highest_xthreat_pass_perc',
            'completed_highest_xthreat_pass_sum',
            'completed_good_pass_opportunity_perc',
            'completed_good_pass_opportunity_sum',
            'player_targeted_xthreat_sum',
            'player_targeted_xthreat_mean',
            'xthreat_available_sum',
            'xthreat_available_mean',
            'missed_xthreat_sum',
            'missed_xthreat_mean',
            'decision_efficiency_mean',
            'event_id_count',
            'player_position',
            'position_category',
            'team_shortname'
        ]

        df_merged = players_agg.merge(
            minutes[['id', "short_name", 'playing_time.total.minutes_played',
                     'playing_time.total.minutes_tip']],
            left_on='player_id',
            right_on='id'
        )

        df_merged['player_targeted_xthreat_p90'] = (
            df_merged['player_targeted_xthreat_sum'] * 90 / df_merged['playing_time.total.minutes_played'])

        df_merged['xthreat_available_p90'] = (
            df_merged['xthreat_available_sum'] * 90 / df_merged['playing_time.total.minutes_played'])

        df_merged['missed_xthreat_p90'] = (
            df_merged['missed_xthreat_sum'] * 90 / df_merged['playing_time.total.minutes_played'])

        df_merged['decision_efficiency_p90'] = (
            df_merged['player_targeted_xthreat_p90'] / df_merged['xthreat_available_p90']) * 100

        return df_merged

    def get_metrics(self, df):
        """Calculate league-wide metrics from aggregated player data.

        Args:
            df: DataFrame with aggregated player statistics (output of group_by_players)

        Returns:
            dict: Dictionary containing league-wide metrics
        """
        metrics = {
            'xthreat_available_p90_mean': df['xthreat_available_p90'].mean(),
            'player_targeted_xthreat_p90_mean': df['player_targeted_xthreat_p90'].mean(),
            'efficiency_p90': df['decision_efficiency_p90'].mean(),
            'has_good_pass_opportunities_mean': df['has_good_pass_opportunities_perc'].mean(),
            'good_pass_opportunity_mean': df['good_pass_opportunity_perc'].mean(),
            'missed_good_pass_opportunity_mean': df['missed_good_pass_opportunity_perc'].mean(),
            'missed_xthreat_sum': df['missed_xthreat_sum'].sum(),
            'safest_pass_perc_mean': df['safest_pass_perc'].mean(),
            'highest_xthreat_pass_perc_mean': df['highest_xthreat_pass_perc'].mean(),
            'completed_perc_mean': df['completed_perc'].mean(),
        }

        return metrics

    def time_bins(self, df):
        # Create time bins
        time_bins = [0, 15, 30, 45, 60, 75, 120]
        time_labels = ['0-15', '15-30', '30-45',
                       '45-60', '60-75', '75-90+']

        # Add time bin column to dataframe
        df_with_bins = df.copy()
        df_with_bins['time_bin'] = pd.cut(
            df_with_bins['minute_start'],
            bins=time_bins,
            labels=time_labels,
            include_lowest=True
        )

        return df_with_bins

    def third_filter(self, df, third):
        filtered = df.copy()

        if third != "All":
            third = f"{third.lower()}_third"
            filtered = filtered[(filtered['third_start'] == third)
                                | (filtered['third_end'] == third)]

        return filtered

    def page_filter(self, df, selected_teams, selected_categories, selected_positions, min_passes):
        """Filter aggregated player data based on teams, positions, and minimum passes.

        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()

        # Filter by teams
        if "All Teams" not in selected_teams and len(selected_teams) > 0:
            filtered = filtered[filtered['team_shortname'].isin(
                selected_teams)]

        # Filter by categories
        if "All" not in selected_categories and len(selected_categories) > 0:
            filtered = filtered[filtered['position_category'].isin(
                selected_categories)]

        # Filter by positions
        if "All" not in selected_positions and len(selected_positions) > 0:
            filtered = filtered[filtered['player_position'].isin(
                selected_positions)]

        # Filter by minimum passes
        filtered = filtered[filtered['event_id_count'] >= min_passes]

        return filtered
