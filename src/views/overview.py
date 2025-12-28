import streamlit as st

from src.data.data_loader import load_data_with_filter
from src.data.passing_evaluation import PassingEvaluation, metric_labels
from src.visualizations.charts import create_scatter

from src.utils.helpers import create_tops_section, show_legend, player_details_section


# add the third filter to the sidebar
with st.sidebar:
    st.header("🔍 Global Filters")
    options = ["Attacking", "Middle", "Defensive", "All"]

    third = st.radio(
        "Third:",
        options,
        index=0,
        help="Third of the pitch where the event started or ended",
    )

    third_label = "Full Pitch" if third == "All" else f"{third} Third"

# get the data
all_data = load_data_with_filter(third)
pe = PassingEvaluation()


st.title("⚽ Player Passing Decision Quality - Overview")

st.space()

found = False

with st.container(border=True):
    st.subheader(f"📊 Overall Metrics ({third_label})")
    global_metrics = pe.get_metrics(all_data['grouped_by_players'])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            metric_labels['xthreat_available_p90_mean'],
            f"{global_metrics['xthreat_available_p90_mean']:.2f}",
            help="xThreat available on average per players per 90 mins"
        )

        st.metric(
            metric_labels['highest_xthreat_pass_perc_mean'],
            f"{global_metrics['highest_xthreat_pass_perc_mean']:.1f}%",
            help="% of time players choose the high xThreat passing option"
        )

        st.metric(
            metric_labels['has_good_pass_opportunities_mean'],
            f"{global_metrics['has_good_pass_opportunities_mean']:.1f}%",
            help="% of time a good passing option is available"
        )

    with col2:
        st.metric(
            metric_labels['player_targeted_xthreat_p90_mean'],
            f"{global_metrics['player_targeted_xthreat_p90_mean']:.2f}",
            help="xThreat actually created on average per players per 90 mins"
        )

        st.metric(
            metric_labels['safest_pass_perc_mean'],
            f"{global_metrics['safest_pass_perc_mean']:.1f}%",
            help="% of time players choose the safest passing option"
        )

        st.metric(
            metric_labels['missed_good_pass_opportunity_mean'],
            f"{global_metrics['missed_good_pass_opportunity_mean']:.1f}%",
            help="% of time players choose a good passing option"
        )

    with col3:
        st.metric(
            metric_labels['efficiency_p90'],
            f"{global_metrics['efficiency_p90']:.1f}%",
            help="Decision Efficiency"
        )

        st.metric(
            metric_labels['completed_perc_mean'],
            f"{global_metrics['completed_perc_mean']:.1f}%",
            help="Average pass completion rate"
        )

with st.container(border=True):
    st.subheader(f"🔍 Filters for the next sections ({third_label})")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        selected_teams = st.multiselect(
            "Team",
            options=all_data['teams'],
        )

    with col_f2:
        selected_categories = st.multiselect(
            "Position Category",
            options=all_data["position_categories"]
        )

    with col_f3:
        selected_positions = st.multiselect(
            "Position",
            options=all_data["positions"]
        )

    with col_f4:
        min_passes = st.slider(
            "Minimum Final Third Passes",
            min_value=10,
            max_value=100,
            value=10,
            help="Filter out players with too few passes for reliable analysis"
        )

    page_filtered = pe.page_filter(
        all_data['grouped_by_players'], selected_teams, selected_categories, selected_positions, min_passes)

    found = page_filtered['player_id'].count()

    if found:
        st.caption(f"Found {page_filtered['player_id'].count()} players")

if found:
    with st.container(border=True):
        st.subheader(
            "📈 Decision Efficiency - Who uses the most xThreat available?")

        col_main_scatter, col_main_view_player = st.columns([8, 2])

        with col_main_scatter:

            main_color_by = st.radio(
                "Color points by:",
                [metric_labels['completed_perc'], metric_labels['position_category'],
                    metric_labels['team_shortname']],
                horizontal=True
            )

            fig_main_scatter, color_legend = create_scatter(
                page_filtered,
                'xthreat_available_p90',
                'decision_efficiency_p90',
                title="Decision Efficiency vs xThreat Available",
                xaxis_title=metric_labels['xthreat_available_p90'],
                yaxis_title=metric_labels['decision_efficiency_p90'],
                color_by=main_color_by,
            )

            selected_players = st.plotly_chart(
                fig_main_scatter,
                on_select="rerun",
                selection_mode="points"
            )

            show_legend(st, color_legend)

        player_details_section(col_main_view_player,
                               selected_players, page_filtered, 'main')

    with st.container(border=True):
        st.subheader("📊 Tops Charts")

        tab1, tab2, tab3 = st.tabs(
            ["🎯 Most threatening", "✅ Most reliable", "⚠️ Biggest wasters"])

        create_tops_section(
            tab=tab1,
            df=page_filtered,
            subheader="Who tries to get the most xThreat more often?",
            metric="highest_xthreat_pass_perc",
            completion_metric="completed_highest_xthreat_pass_perc",
            top_title="Top 10 Most Threatening",
            top_xaxis="% of time they chose the most threatening option",
            scatter_title="Completion Rate vs Highest xThreat Frequency",
            scatter_yaxis=metric_labels['completed_highest_xthreat_pass_perc'],
            scatter_xaxis=metric_labels['highest_xthreat_pass_perc']
        )

        create_tops_section(
            tab=tab2,
            df=page_filtered,
            subheader="Who consistently find good opportunities",
            metric="good_pass_opportunity_perc",
            completion_metric="completed_good_pass_opportunity_perc",
            top_title="Top 10 Most Reliable",
            top_xaxis="% of time they chose a good pass option",
            scatter_title="Completion Rate vs Good Opportunity Frequency",
            scatter_yaxis=metric_labels['completed_good_pass_opportunity_perc'],
            scatter_xaxis=metric_labels['good_pass_opportunity_perc']
        )

        create_tops_section(
            tab=tab3,
            df=page_filtered,
            subheader="Who misses out more often?",
            caption="Players who most frequently miss good passing options",
            metric="missed_good_pass_opportunity_perc",
            top_title="Top 10 Wasters",
            top_xaxis="% of time they missed a good option",
        )

    with st.container(border=True):
        st.subheader("🔢 Full Rankings")

        # add rank for decision efficiency
        page_filtered = page_filtered.sort_values(
            'decision_efficiency_p90', ascending=False)
        page_filtered.insert(0, 'Rank', range(1, len(page_filtered) + 1))

        columns = [
            'Rank',
            'short_name',
            'team_shortname',
            'player_position',
            'event_id_count',
            'decision_efficiency_p90',
            'xthreat_available_p90',
            'player_targeted_xthreat_p90',
            'missed_xthreat_p90',
            'highest_xthreat_pass_perc',
            'completed_highest_xthreat_pass_perc',
            'good_pass_opportunity_perc',
            'completed_good_pass_opportunity_perc',
            'safest_pass_perc',
            'completed_safest_pass_perc',
            'completed_perc',
        ]

        st.dataframe(
            page_filtered[columns],
            column_config={
                "rank": st.column_config.NumberColumn(
                    "Rank",
                    help="Player rank by decision efficiency",
                    width="small"
                ),
                "short_name": st.column_config.TextColumn(
                    "Player",
                    help="Player name",
                    width="small",
                ),
                "team_shortname": st.column_config.TextColumn(
                    "Team",
                    help="Team name",
                    width="small",
                ),
                "player_position": st.column_config.TextColumn(
                    metric_labels['player_position'],
                    help="Player position",
                    width="small",
                ),
                "event_id_count": st.column_config.NumberColumn(
                    metric_labels['event_id_count'],
                    help="Total number of passing events",
                    width="small",
                    format="%d",
                ),
                "decision_efficiency_p90": st.column_config.ProgressColumn(
                    metric_labels['decision_efficiency_p90'],
                    help="Decision efficiency per 90 minutes",
                    format="%.2f",
                    color="auto",
                    min_value=0,
                    width="medium",
                    max_value=page_filtered['decision_efficiency_p90'].max(),
                ),
                "xthreat_available_p90": st.column_config.ProgressColumn(
                    metric_labels['xthreat_available_p90'],
                    help="Expected threat available per 90 minutes",
                    format="%.2f",
                    color="auto",
                    min_value=0,
                    width="medium",
                    max_value=page_filtered['xthreat_available_p90'].max(),
                ),
                "player_targeted_xthreat_p90": st.column_config.ProgressColumn(
                    metric_labels['player_targeted_xthreat_p90'],
                    help="Player targeted expected threat per 90 minutes",
                    format="%.2f",
                    color="auto",
                    min_value=0,
                    width="medium",
                    max_value=page_filtered['player_targeted_xthreat_p90'].max(
                    ),
                ),
                "missed_xthreat_p90": st.column_config.ProgressColumn(
                    metric_labels['missed_xthreat_p90'],
                    help="Missed expected threat per 90 minutes",
                    format="%.2f",
                    color="auto-inverse",
                    min_value=0,
                    width="medium",
                    max_value=page_filtered['missed_xthreat_p90'].max(),
                ),
                "highest_xthreat_pass_perc": st.column_config.ProgressColumn(
                    metric_labels['highest_xthreat_pass_perc'],
                    help="Percentage of times the highest xThreat pass was chosen",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="medium",
                ),
                "completed_highest_xthreat_pass_perc": st.column_config.ProgressColumn(
                    metric_labels['completed_highest_xthreat_pass_perc'],
                    help="Completion percentage of highest xThreat passes",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="small",
                ),
                "good_pass_opportunity_perc": st.column_config.ProgressColumn(
                    metric_labels['good_pass_opportunity_perc'],
                    help="Percentage of times a good pass opportunity was taken",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="medium",
                ),
                "completed_good_pass_opportunity_perc": st.column_config.ProgressColumn(
                    metric_labels['completed_good_pass_opportunity_perc'],
                    help="Completion percentage of good pass opportunities",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="small",
                ),
                "safest_pass_perc": st.column_config.ProgressColumn(
                    metric_labels['safest_pass_perc'],
                    help="Percentage of times the safest pass was chosen",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="medium",
                ),
                "completed_safest_pass_perc": st.column_config.ProgressColumn(
                    metric_labels['completed_safest_pass_perc'],
                    help="Completion percentage of safest passes",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    color="auto",
                    width="small",
                ),
                "completed_perc": st.column_config.ProgressColumn(
                    metric_labels['completed_perc'],
                    help="Pass completion percentage",
                    format="%.1f%%",
                    color="auto",
                    min_value=0,
                    max_value=100,
                    width="medium",
                ),
            },
            hide_index=True,
            height=600
        )
else:
    st.warning(f"No players found")
