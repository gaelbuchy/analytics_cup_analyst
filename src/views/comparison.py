import streamlit as st

from src.data.data_loader import load_data_with_filter
from src.data.passing_evaluation import PassingEvaluation, metric_labels
from src.visualizations.charts import create_radar
from src.utils.helpers import check_player, get_metrics_df


# get the data
all_data = load_data_with_filter("All")
# init evaluation class
pe = PassingEvaluation()

st.title("⚽ Player Passing Decision Quality - Player Comparison")

player_stats = all_data['grouped_by_players']

with st.container(border=True):
    st.subheader("Players")
    st.write("Select exactly 2 players from the table to compare:")

    table_columns = [
        'player_id',
        'short_name',
        'team_shortname',
        'player_position',
        'position_category',
        'event_id_count',
    ]

    selection = st.dataframe(
        player_stats[table_columns],
        selection_mode="multi-row",
        on_select="rerun",
        key="player_selection",
        column_config={
            col: st.column_config.NumberColumn(metric_labels.get(
                col, col)) if col == "event_id_count" else st.column_config.TextColumn(metric_labels.get(col, col))
            for col in table_columns
        }
    )

    selected_rows = selection.selection.rows

# Check if exactly 2 players are selected
if len(selected_rows) != 2:
    st.warning("Please select exactly 2 players from the table above to compare.")
else:

    # Get player ids from selected rows
    player1_id = player_stats.iloc[selected_rows[0]]['player_id']
    player2_id = player_stats.iloc[selected_rows[1]]['player_id']

    with st.container(border=True):
        st.subheader("📊 Comparison")

        # Add filters
        st.write("🔍 Filters")
        options = ["Attacking", "Middle", "Defensive", "All"]

        third = st.radio(
            "Third:",
            options,
            index=3,
            horizontal=True,
            help="Third of the pitch where the event started or ended",
        )

        # filter data and get players
        filtered_data = load_data_with_filter(third)
        filtered_stats = filtered_data['grouped_by_players']

        player1 = check_player(
            filtered_stats[filtered_stats["player_id"] == player1_id], player1_id)
        player2 = check_player(
            filtered_stats[filtered_stats["player_id"] == player2_id], player2_id)

        tab1, tab2 = st.tabs(["🕸️ Radar Chart", "📊 Detailed Metrics"])

        with tab1:

            # Define metrics for radar chart
            radar_metrics = [
                "decision_efficiency_p90",
                "safest_pass_perc",
                "completed_safest_pass_perc",

                "highest_xthreat_pass_perc",
                "completed_highest_xthreat_pass_perc",

                "good_pass_opportunity_perc",
                "completed_good_pass_opportunity_perc",
            ]

            with st.spinner("Loading..."):
                fig = create_radar(
                    filtered_stats, radar_metrics, player1, player2)
                st.pyplot(fig, width=800)

        with tab2:
            basic_info = [
                'team_shortname',
                'player_position',
                'event_id_count',
            ]

            basic_df = get_metrics_df(basic_info, player1, player2)

            st.dataframe(basic_df, hide_index=True)

            percentage_metrics = [
                'decision_efficiency_p90',
                'completed_perc',
                'highest_xthreat_pass_perc',
                'completed_highest_xthreat_pass_perc',
                'has_good_pass_opportunities_perc',
                'good_pass_opportunity_perc',
                'completed_good_pass_opportunity_perc',
                'safest_pass_perc',
                'completed_safest_pass_perc',
            ]

            perc_df = get_metrics_df(percentage_metrics, player1, player2)

            st.dataframe(
                perc_df,
                column_config={
                    "Metric": st.column_config.TextColumn("Metric", width="medium"),
                    player1['short_name']: st.column_config.ProgressColumn(
                        player1['short_name'],
                        width="medium",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100,
                        color="auto",
                    ),
                    player2['short_name']: st.column_config.ProgressColumn(
                        player2['short_name'],
                        width="medium",
                        format="%.2f%%",
                        min_value=0,
                        max_value=100,
                        color="auto",
                    ),
                },
                hide_index=True,
            )

            p90_metrics = [
                'xthreat_available_p90',
                'player_targeted_xthreat_p90',
                'missed_xthreat_p90',
            ]

            p90_df = get_metrics_df(p90_metrics, player1, player2)

            max_val = filtered_stats['xthreat_available_p90'].max()

            st.dataframe(
                p90_df,
                column_config={
                    "Metric": st.column_config.TextColumn("Metric", width="medium"),
                    player1['short_name']: st.column_config.ProgressColumn(
                        player1['short_name'],
                        width="medium",
                        format="%.2f",
                        min_value=0,
                        max_value=max_val,
                        color="auto",
                    ),
                    player2['short_name']: st.column_config.ProgressColumn(
                        player2['short_name'],
                        width="medium",
                        format="%.2f",
                        min_value=0,
                        max_value=max_val,
                        color="auto",
                    ),
                },
                hide_index=True,
            )
