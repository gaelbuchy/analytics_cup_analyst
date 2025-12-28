
import streamlit as st
import pandas as pd

from src.visualizations.charts import create_tops_bar_chart, create_scatter, get_completion_legend
from src.data.passing_evaluation import metric_labels


def create_tops_section(tab,
                        df=None,
                        subheader="",
                        caption=None,
                        metric="",
                        completion_metric=None,
                        top_title="",
                        top_xaxis="",
                        scatter_title="",
                        scatter_xaxis="",
                        scatter_yaxis="",
                        annotations=[]
                        ):
    tab.subheader(subheader)
    if caption is not None:
        tab.caption(caption)

    col1, col2 = tab.columns([8, 2])

    if completion_metric is not None:
        view_mode = col1.pills("View", ["Top 10", "All"],
                               key=f"top_{metric}",
                               label_visibility="collapsed", default="Top 10")

    completion_label = "Completion Rate Highest xThreat" if completion_metric == "completed_highest_xthreat_pass_perc" else "Completion Rate Good"

    if completion_metric is None or view_mode == "Top 10":
        fig = create_tops_bar_chart(
            df,
            metric,
            completion_metric,
            title=top_title,
            xaxis=top_xaxis,
            n=10)

        sp = col1.plotly_chart(
            fig,
            on_select="rerun",
            selection_mode="points",
            key=f"top10_{metric}"
        )

        if completion_metric is not None:
            show_legend(col1, get_completion_legend(completion_label))
    else:
        color_by = col1.radio(
            "Color points by:",
            [completion_label, "Position Category", "Team"],
            horizontal=True,
            key=f"color_by_{metric}",
        )

        fig, color_legend = create_scatter(
            df,
            metric,
            completion_metric,
            title=scatter_title,
            xaxis_title=scatter_xaxis,
            yaxis_title=scatter_yaxis,
            annotations=annotations,
            color_by=color_by,
        )

        sp = col1.plotly_chart(fig,
                               on_select="rerun",
                               selection_mode="points",
                               key=f"tops_scatter_{metric}"
                               )

        show_legend(col1, color_legend)

    player_details_section(col2, sp, df, metric)


def show_legend(container, color_legend):
    if color_legend:
        container.markdown("**Color Legend**")
        container.caption(f"{color_legend['label']}:")
        legend_html = ""
        for name, color in color_legend['colors']:
            legend_html += f'<span style="display:inline-block; width:12px; height:12px; background-color:{color}; margin-right:5px; border-radius:5px;"></span> {name} &nbsp;&nbsp; '
        container.markdown(legend_html, unsafe_allow_html=True)


def player_details_section(container, sp, df, key):
    container.markdown("Player Details")
    if sp and len(sp['selection']['points']) > 0:
        player_id = sp['selection']['points'][0]['customdata']['0']
        selected_player = df[df['player_id'] == player_id].iloc[0]

        container.markdown(f"**{selected_player['short_name']}**")
        container.caption(
            f"{selected_player['team_shortname']}")

        if container.button("Explore Full Profile →", key=f"link_btn_{key}"):
            st.switch_page(
                "src/views/player_profile.py", query_params={"player": selected_player['player_id']})
    else:
        container.info(
            "👆 Click a player from the chart")


def get_metrics_df(metrics, player1, player2):
    return pd.DataFrame({
        'Metric': [metric_labels[col] for col in metrics],
        player1['short_name']: [player1[col] for col in metrics],
        player2['short_name']: [player2[col] for col in metrics],
    })


def check_player(player, id):
    if not len(player):
        st.warning(f"No stats for Player {id}")
        st.stop()
    else:
        return player.iloc[0]
