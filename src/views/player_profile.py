import streamlit as st
import pandas as pd

from src.data.data_loader import load_data_with_filter
from src.data.passing_evaluation import PassingEvaluation, metric_labels

from src.visualizations.charts import create_beeswarm, create_time_chart
from src.visualizations.events import plot_event


# add the third filter to the sidebar
with st.sidebar:
    st.header("🔍 Global Filters")
    options = ["Attacking", "Middle", "Defensive", "All"]

    third = st.radio(
        "Third:",
        options,
        index=3,
        help="Third of the pitch where the event started or ended",
    )

    third_label = "Full Pitch" if third == "All" else f"{third} Third"


# get the data
all_data = load_data_with_filter(third)
pe = PassingEvaluation()

st.title("⚽ Player Passing Decision Quality - Player Profile")

# Select form for player
player_options = all_data['players'].apply(
    lambda row: f"{row['id']} - {row['short_name']}", axis=1).tolist()

selected_index = None
if "player" in st.query_params:
    player_id = int(st.query_params["player"])
    player = all_data['players'][all_data['players']['id'] == player_id]
    if len(player):
        selected = f"{player['id'].iloc[0]} - {player['short_name'].iloc[0]}"
        selected_index = player_options.index(selected)

selected_player_with_id = st.selectbox(
    "Select Player",
    options=player_options,
    index=selected_index
)

if selected_player_with_id is not None:

    selected_player_id = int(selected_player_with_id.split(" - ")[0])
    all_players_stats = all_data['grouped_by_players']
    all_players_possessions = all_data['filtered_possessions']

    selected_player_stats = all_players_stats[all_players_stats["player_id"]
                                              == selected_player_id]

    selected_player_possessions = all_players_possessions[all_players_possessions['player_id']
                                                          == selected_player_id]

    if not len(selected_player_stats):
        st.warning(f"No stats for Player {selected_player_with_id}")
    else:

        selected_player_stats = selected_player_stats.iloc[0]

        with st.container(border=True):
            stat_col1, stat_col2 = st.columns([7, 3])

            with stat_col1:
                st.subheader(
                    f"Stats for {selected_player_stats['short_name']} ({third_label})")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Team", selected_player_stats['team_shortname'])

                    st.metric(metric_labels['xthreat_available_sum'],
                              f"{selected_player_stats['xthreat_available_sum']:.2f}",
                              help="Total xThreat available")

                    st.metric(
                        metric_labels['highest_xthreat_pass_sum'],
                        f"{int(selected_player_stats['highest_xthreat_pass_sum'])} ({selected_player_stats['highest_xthreat_pass_perc']:.1f}%)",
                        help="Times the Highest xThreat pass was chosen"
                    )

                    st.metric(
                        metric_labels['has_good_pass_opportunities_sum'],
                        f"{int(selected_player_stats['has_good_pass_opportunities_sum'])} ({selected_player_stats['has_good_pass_opportunities_perc']:.1f}%)",
                        help="Times a good pass opportunity was available"
                    )

                with col2:
                    st.metric(
                        "Position", selected_player_stats['player_position'])

                    st.metric(metric_labels['player_targeted_xthreat_sum'],
                              f"{selected_player_stats['player_targeted_xthreat_sum']:.2f}",
                              help="Total xThreat created"
                              )

                    st.metric(
                        metric_labels['safest_pass_sum'],
                        f"{int(selected_player_stats['safest_pass_sum'])} ({selected_player_stats['safest_pass_perc']:.1f}%)",
                        help="Times the Safest pass was chosen"
                    )

                    st.metric(
                        metric_labels['missed_good_pass_opportunity_sum'],
                        f"{int(selected_player_stats['missed_good_pass_opportunity_sum'])} ({selected_player_stats['missed_good_pass_opportunity_perc']:.1f}%)",
                        help="Times a good pass opportunity was missed"
                    )

                with col3:
                    st.metric(metric_labels['event_id_count'],
                              f"{int(selected_player_stats['event_id_count'])}",
                              help="Total passes")

                    de = selected_player_stats['player_targeted_xthreat_sum'] / \
                        selected_player_stats['xthreat_available_sum'] * 100

                    st.metric(metric_labels['decision_efficiency'],
                              f"{de:.1f}%")

            with stat_col2:
                # Calculate metrics for completion rates
                good_opp_total = int(
                    selected_player_stats['good_pass_opportunity_sum'])
                good_opp_completed = int(
                    selected_player_stats['completed_good_pass_opportunity_sum'])
                good_opp_perc = selected_player_stats['completed_good_pass_opportunity_perc']

                highest_xt_total = int(
                    selected_player_stats['highest_xthreat_pass_sum'])
                highest_xt_completed = int(
                    selected_player_stats['completed_highest_xthreat_pass_sum'])
                highest_xt_perc = selected_player_stats['completed_highest_xthreat_pass_perc']

                safest_total = int(selected_player_stats['safest_pass_sum'])
                safest_completed = int(
                    selected_player_stats['completed_safest_pass_sum'])
                safest_perc = selected_player_stats['completed_safest_pass_perc']

                total_passes = int(selected_player_stats['event_id_count'])
                total_completed = int(selected_player_stats['completed_sum'])
                total_perc = int(selected_player_stats['completed_perc'])

                # Display completion rates
                st.markdown("**Good Opportunities Passes**")
                st.progress(good_opp_perc / 100 if good_opp_perc else 0,
                            text=f"{good_opp_perc:.1f}% ({good_opp_completed}/{good_opp_total} completed)")
                st.write("")

                st.markdown("**Most Threatening Passes**")
                st.progress(highest_xt_perc / 100 if highest_xt_perc else 0,
                            text=f"{highest_xt_perc:.1f}% ({highest_xt_completed}/{highest_xt_total} completed)")
                st.write("")

                st.markdown("**Safest Passes**")
                st.progress(safest_perc / 100 if safest_perc else 0,
                            text=f"{safest_perc:.1f}% ({safest_completed}/{safest_total} completed)")
                st.write("")

                st.markdown("**All Passes**")
                st.progress(total_perc / 100 if total_perc else 0,
                            text=f"{total_perc:.1f}% ({total_completed}/{total_passes} completed)")
                st.write("")

        with st.container(border=True):

            tab1, tab2, tab3 = st.tabs(
                ["🆚 Metrics Comparison", "📈 Decision Efficiency Over Time", "👁️ Visualize Specific Situations"])

            with tab1:
                col1, col2 = st.columns([7, 3])

                with col2:
                    st.write("🔍 Comparison Filters")

                    comparison_filter = st.radio(
                        "Compare with:",
                        options=["All Players", "Same Position",
                                 "Same Position Category", "Same Team"],
                        index=0,
                        horizontal=False
                    )

                    # Set filter flags based on selection
                    same_position = comparison_filter == "Same Position"
                    same_position_category = comparison_filter == "Same Position Category"
                    same_team = comparison_filter == "Same Team"

                    comparison_stats = all_players_stats.copy()
                    # Apply comparison filters
                    if same_position:
                        comparison_stats = comparison_stats[
                            comparison_stats['player_position'] == selected_player_stats['player_position']
                        ]

                    if same_position_category:
                        comparison_stats = comparison_stats[
                            comparison_stats['position_category'] == selected_player_stats['position_category']
                        ]

                    if same_team:
                        comparison_stats = comparison_stats[
                            comparison_stats['team_shortname'] == selected_player_stats['team_shortname']
                        ]

                with col1:
                    filter_description = []

                    if same_position:
                        filter_description.append("same position")
                    if same_position_category:
                        filter_description.append("same position category")
                    if same_team:
                        filter_description.append("same team")

                    if filter_description:
                        st.subheader(
                            f"🆚 Comparison with Players ({', '.join(filter_description)})")
                    else:
                        st.subheader("🆚 Comparison with All Players")

                    st.caption(f"Comparing {len(comparison_stats)} players")

                    swarm_metrics = [
                        "safest_pass_perc",
                        "highest_xthreat_pass_perc",
                        "has_good_pass_opportunities_perc",
                        "good_pass_opportunity_perc",
                        "missed_good_pass_opportunity_perc",
                        "completed_perc",
                        "completed_safest_pass_perc",
                        "completed_highest_xthreat_pass_perc",
                        "completed_good_pass_opportunity_perc",
                        "decision_efficiency_p90",
                        "xthreat_available_p90",
                        "player_targeted_xthreat_p90",
                        "missed_xthreat_p90",
                    ]

                    plot_data = []
                    for metric in swarm_metrics:
                        for _, row in comparison_stats.iterrows():

                            # add first all the other players
                            if row["player_id"] != selected_player_id:
                                plot_data.append({
                                    "player_id": row["player_id"],
                                    "metric": metric_labels[metric],
                                    "value": row[metric],
                                    "selected": row["player_id"] == selected_player_id,
                                })

                        # add the current player at the end
                        plot_data.append({
                            "player_id": selected_player_stats["player_id"],
                            "metric": metric_labels[metric],
                            "value": selected_player_stats[metric],
                            "selected": True,
                        })

                    fig = create_beeswarm(pd.DataFrame(plot_data))

                    st.plotly_chart(fig)

            with tab2:
                st.subheader("📈 Decision Efficiency Over Time")

                filtered_possessions_bins = pe.time_bins(
                    all_players_possessions)

                fig_time = create_time_chart(
                    filtered_possessions_bins, selected_player_id)

                st.plotly_chart(fig_time)

            with tab3:
                st.subheader("👁️ Vizualize Specific Situations")

                # Add filters
                st.write("🔍 Filters")
                de_range = st.slider(
                    "Decision Efficiency Range",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=10,
                )

                options = ["Most Threatening", "Safest",
                           "Good Opportunity", "Missed Opportunity", "All"]

                decision_type = st.radio(
                    "Decision Type:",
                    options,
                    index=4,
                    horizontal=True,
                    help="Third of the pitch where the event started or ended",
                )

                filtered_player_df = selected_player_possessions[
                    (selected_player_possessions['decision_efficiency'] >= de_range[0]) &
                    (selected_player_possessions['decision_efficiency']
                     <= de_range[1])
                ]

                # filter by decision type
                if decision_type != "All":
                    attrs = {
                        "Most Threatening": 'highest_xthreat_pass',
                        "Safest": 'safest_pass',
                        "Good Opportunity": 'good_pass_opportunity',
                        "Missed Opportunity": 'missed_good_pass_opportunity'
                    }
                    filtered_player_df = selected_player_possessions[
                        selected_player_possessions[attrs[decision_type]] == 1]

                st.caption(
                    f"Showing {len(filtered_player_df)} of {len(selected_player_possessions)} rows")

                columns = [
                    "event_id",
                    "match_id",
                    "minute_start",
                    "team_score",
                    "opponent_team_score",
                    "decision_efficiency",
                    "player_targeted_xthreat",
                    "missed_xthreat",
                    "highest_xthreat_pass",
                    "safest_pass",
                    "good_pass_opportunity",
                ]
                selection = st.dataframe(
                    filtered_player_df[columns],
                    selection_mode="single-row",
                    on_select="rerun",
                    hide_index=True,
                )

                selected_rows = selection.selection.rows

                if len(selected_rows) > 0:
                    event = filtered_player_df.iloc[selected_rows[0]]

                    selected_match_id = event['match_id']
                    selected_event_id = event['event_id']

                    possession_event = selected_player_possessions[
                        (selected_player_possessions["match_id"] == selected_match_id) &
                        (selected_player_possessions["event_id"]
                         == selected_event_id)
                    ]

                    st.space()

                    st.subheader(f"Event {selected_event_id}")

                    event_col1, event_col2 = st.columns([7, 3])

                    with event_col1:
                        with st.spinner("Loading..."):
                            plot_event(possession_event,
                                       all_data['all_events'])

                    with event_col2:
                        st.subheader("Event Metrics")

                        # Extract event data
                        event = possession_event.iloc[0]

                        # Decision Quality Metrics
                        st.metric(metric_labels['decision_efficiency'],
                                  f"{event.get('decision_efficiency', 0):.1f}%")
                        st.metric(metric_labels['xthreat_available'],
                                  f"{event.get('xthreat_available', 0):.3f}")
                        st.metric(metric_labels['player_targeted_xthreat'],
                                  f"{event.get('player_targeted_xthreat', 0):.3f}")

                        if event['safest_pass'] or event['highest_xthreat_pass'] or event['good_pass_opportunity']:
                            # Decision Flags
                            st.markdown("Decision Type")

                            metrics = [
                                'safest_pass', 'highest_xthreat_pass', 'good_pass_opportunity']
                            for m in metrics:
                                if event.get(m, False):
                                    st.success(f"✓ {metric_labels[m]}")

                        # Completion Status
                        st.markdown("Pass Outcome")
                        if event.get('pass_outcome') == "successful":
                            st.success("✓ Completed")
                        else:
                            st.error("✗ Incomplete")
                else:
                    st.info("Select a pass to vizualize it")
