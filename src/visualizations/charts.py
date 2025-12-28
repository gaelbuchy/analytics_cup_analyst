import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from mplsoccer import Radar, FontManager, grid

from src.data.passing_evaluation import metric_labels

line_color = "white" if st.context.theme.type == "dark" else "black"
main_color = "#197BBD"
secondary_color = "#ED254E"


def add_completion_colors(colors, df, metric):
    for comp_rate in df[metric]:
        if comp_rate > 75:
            colors.append('#66BB6A')
        elif comp_rate >= 50:
            colors.append('#BDBDBD')
        else:
            colors.append('#C62828')


def get_completion_legend(label):
    color_legend = {
        'label': label,
        'colors': [
            ('>75%', '#66BB6A'),
            ('50-75%', '#BDBDBD'),
            ('<50%', '#C62828')
        ]
    }
    return color_legend


def get_colors(player_metrics_df, color_by):
    color_legend = None

    if 'Completion Rate' in color_by:
        fields = {
            'Completion Rate': 'completed_perc',
            'Completion Rate Highest xThreat': 'completed_highest_xthreat_pass_perc',
            'Completion Rate Good': 'completed_good_pass_opportunity_perc'
        }
        colors = []
        add_completion_colors(colors, player_metrics_df, fields[color_by])
        color_legend = get_completion_legend(color_by)
    elif color_by == 'Position Category':
        position_colors = {
            'Keeper': '#757575',
            'Defender': '#1976D2',
            'Midfielder': '#388E3C',
            'Attacker': '#C62828'
        }
        colors = player_metrics_df['position_category'].map(
            lambda x: position_colors.get(x, '#757575')
        )
        unique_positions = sorted(
            player_metrics_df['position_category'].unique())
        color_legend = {
            'label': 'Position',
            'colors': [(pos, position_colors.get(pos, '#757575')) for pos in unique_positions]
        }
    else:
        # Use a distinct color palette for teams (10 colors)
        team_color_palette = [
            "#841A1B",
            '#3498DB',
            '#2ECC71',
            "#EEB75F",
            '#9B59B6',
            '#1ABC9C',
            "#F05186",
            "#FF7700",
            '#00BCD4',
            '#795548',
        ]
        unique_teams = sorted(player_metrics_df['team_shortname'].unique())
        team_color_map = {team: team_color_palette[i % len(team_color_palette)]
                          for i, team in enumerate(unique_teams)}
        colors = player_metrics_df['team_shortname'].map(team_color_map)
        color_legend = {
            'label': 'Team',
            'colors': [(team, team_color_map[team]) for team in unique_teams]
        }

    return colors, color_legend


def create_tops_bar_chart(player_metrics_df,
                          metric='highest_xthreat_pass_perc',
                          completion_metric='completed_highest_xthreat_pass_perc',
                          title="",
                          xaxis="",
                          n=10):
    top_players = player_metrics_df.nlargest(n, metric)

    fig = go.Figure()

    colors = []
    if completion_metric is not None:
        add_completion_colors(colors, top_players, completion_metric)

        hover_template = (
            '<b>%{y}</b><br>' +
            'Most Threatening Chosen: %{x:.1f}%<br>' +
            'Completion Rate: %{customdata[1]:.1f}%<br>' +
            'Total Passes: %{customdata[2]}<br>' +
            '<extra></extra>'
        )
    else:
        hover_template = (
            '<b>%{y}</b><br>' +
            'Most Threatening Chosen: %{x:.1f}%<br>' +
            'Total Passes: %{customdata[1]}<br>' +
            '<extra></extra>'
        )

    fig.add_trace(go.Bar(
        y=top_players['short_name'],
        x=top_players[metric],
        orientation='h',
        marker=dict(
            color=colors if len(colors) else None
        ),
        text=[
            (f"{row[metric]:.1f}%")
            for _, row in top_players.iterrows()
        ],
        textposition='outside',
        hovertemplate=hover_template,
        customdata=top_players[['player_id', completion_metric, 'event_id_count']
                               ].values if completion_metric is not None else top_players[['player_id', 'event_id_count']].values
    ))

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title=xaxis,
            range=[0, max(top_players[metric]) * 1.15],
            showline=True,
            linewidth=2,
            linecolor=line_color,
            tickcolor=line_color,
            ticks='outside',
        ),
        yaxis=dict(
            title="",
            autorange='reversed',
        ),
        height=500,
        showlegend=False,
        margin=dict(l=150, r=150, t=80, b=50)
    )

    # Add vertical reference lines
    avg_pct = player_metrics_df[metric].mean()
    fig.add_vline(
        x=avg_pct,
        line_dash="dash",
        line_color=line_color,
        annotation=dict(
            text=f"Avg: {avg_pct:.1f}%",
            font=dict(size=12, color=line_color),
            bordercolor=line_color,
            borderwidth=1,
            borderpad=4
        ),
        annotation_position="top"
    )

    return fig


def create_scatter(player_metrics_df,
                   x_metric,
                   y_metric,
                   title="",
                   xaxis_title="",
                   yaxis_title="",
                   annotations=[],
                   color_by=None):
    """
    Create scatter plot showing relationship between
    choosing threatening passes and executing them.
    """

    colors, color_legend, = get_colors(
        player_metrics_df, color_by)

    # Create hover text
    hover_text = []
    for idx, row in player_metrics_df.iterrows():
        text = f"""<b>{row['short_name']}</b> | {row['team_shortname']} | {row['position_category']}<br><br>
Passes: {row['event_id_count']:.0f}<br>
xThreat Available: {row['xthreat_available_p90']:.2f} Per 90<br>
xThreat Created: {row['player_targeted_xthreat_p90']:.2f} Per 90<br>
Decision Efficiency: {row['decision_efficiency_p90']:.1f}%<br>
xThreat Missed: {row['missed_xthreat_p90']:.2f} Per 90<br><br>
Completion Rate: {row['completed_perc']:.1f}%<br><br>
<i>Click to see player details →</i>"""
        hover_text.append(text)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player_metrics_df[x_metric],
        y=player_metrics_df[y_metric],
        mode='markers',
        marker=dict(
            size=16,
            color=colors,
            showscale=False,
            line=dict(width=1, color='white'),
            opacity=0.8
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        customdata=player_metrics_df[['player_id']].values,
        name=''
    ))

    avg_x = player_metrics_df[x_metric].mean()
    avg_y = player_metrics_df[y_metric].mean()

    fig.add_hline(
        y=avg_y,
        line_dash="dash",
        line_color=line_color,
        line_width=1,
        annotation=dict(
            text=f"Avg: {avg_y:.1f}%",
            font=dict(size=12, color=line_color),
            bordercolor=line_color,
            borderwidth=1,
            borderpad=4
        ),
        annotation_position="right"
    )

    text = f"Avg: {avg_x:.2f}" if x_metric == "xthreat_available_p90" else f"Avg: {avg_x:.1f}%"
    fig.add_vline(
        x=avg_x,
        line_dash="dash",
        line_color=line_color,
        line_width=1,
        annotation=dict(
            text=text,
            font=dict(size=12, color=line_color),
            bordercolor=line_color,
            borderwidth=1,
            borderpad=4
        ),
        annotation_position="top"
    )

    if len(annotations) > 3:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=.95, y=.95,
            text=annotations[0],
            showarrow=False, font=dict(size=12, color=line_color)
        )
        fig.add_annotation(
            xref="paper", yref="paper",
            x=.05, y=.95,
            text=annotations[1],
            showarrow=False, font=dict(size=12, color=line_color)
        )
        fig.add_annotation(
            xref="paper", yref="paper",
            x=.95, y=.05,
            text=annotations[2],
            showarrow=False, font=dict(size=12, color=line_color)
        )
        fig.add_annotation(
            xref="paper", yref="paper",
            x=.05, y=.05,
            text=annotations[3],
            showarrow=False, font=dict(size=12, color=line_color)
        )

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis=dict(
            title=xaxis_title,
            showgrid=True,
            gridcolor='gray',
            griddash='2px',
            layer='below traces',
            showline=True,
            linewidth=2,
            linecolor=line_color,
            tickcolor=line_color,
            ticks='outside',
        ),
        yaxis=dict(
            title=yaxis_title,
            showgrid=True,
            gridcolor='gray',
            griddash='2px',
            layer='below traces',
        ),
        height=600,
        hovermode='closest',
        margin=dict(r=100)
    )

    return fig, color_legend


def create_beeswarm(metrics):

    plot_df = metrics.copy()

    # Add normalized values for plotting and keep original for hover
    plot_df['original_value'] = plot_df['value']

    # Normalize by metric
    plot_df['value'] = plot_df.groupby('metric')['value'].transform(
        lambda x: (x - x.min()) / (x.max() - x.min()
                                   ) if x.max() != x.min() else 0.5
    )

    # Create custom hover text
    plot_df['hover_text'] = plot_df.apply(
        lambda row: f"{row['metric']}<br>Value: {row['original_value']:.2f}",
        axis=1
    )

    fig = px.strip(plot_df, x='value', y='metric',
                   color="selected", stripmode="overlay",
                   hover_name='hover_text',
                   color_discrete_map={
                       False: main_color,
                       True: secondary_color
                   })

    fig.update_traces(
        marker=dict(
            size=10,
            line=dict(width=0),
            opacity=.5
        ),
        selector=dict(name='False')
    )

    fig.update_traces(
        marker=dict(
            size=15,
            # symbol='diamond',  # Or 'hexagon', 'square', etc.
            line=dict(width=1, color='white')
        ),
        selector=dict(name='True')
    )

    fig.update_layout(
        title=dict(
            text='Player Performance Comparison',
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(
            title='',
            showgrid=False,
            showticklabels=False
        ),
        yaxis=dict(
            title='',
            showgrid=True,
            zeroline=False,
        ),
        showlegend=False,
        hovermode='closest',
        height=600,
    )

    # Add Labels
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.05,
        y=-0.05,
        text="← Worse",
        showarrow=False,
        font=dict(size=14, color='rgba(255, 255, 255, 0.6)'),
        xanchor='left'
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.95,
        y=-0.05,
        text="Better →",
        showarrow=False,
        font=dict(size=14, color='rgba(255, 255, 255, 0.6)'),
        xanchor='right'
    )

    return fig


def create_time_chart(filtered_possessions_bins, selected_player_id):

    player_metrics = filtered_possessions_bins[filtered_possessions_bins['player_id']
                                               == selected_player_id]

    colors = {
        'global_avg': 'rgba(150, 150, 150, 0.8)',
        'decision_efficiency': '#2E86AB',
        'highest_xthreat': '#A23B72',
        'safest_pass': '#F18F01',
        'good_opportunity': '#06A77D',
    }

    # Define metrics to plot
    metrics_config = [
        {
            'column': 'decision_efficiency',
            'name': metric_labels['decision_efficiency'],
            'color': colors['decision_efficiency'],
            'width': 3,
            'size': 8,
            'is_percentage': False,
        },
        {
            'column': 'highest_xthreat_pass',
            'name': metric_labels['highest_xthreat_pass'],
            'color': colors['highest_xthreat'],
            'width': 2,
            'size': 7,
            'is_percentage': True,
        },
        {
            'column': 'safest_pass',
            'name': metric_labels['safest_pass'],
            'color': colors['safest_pass'],
            'width': 2,
            'size': 7,
            'is_percentage': True,
        },
        {
            'column': 'good_pass_opportunity',
            'name': metric_labels['good_pass_opportunity'],
            'color': colors['good_opportunity'],
            'width': 2,
            'size': 7,
            'is_percentage': True,
        },
    ]

    # Calculate stats for all metrics
    time_stats = {}
    for metric in metrics_config:
        col = metric['column']
        stats = player_metrics.groupby('time_bin', observed=True)[
            col].mean().reset_index()

        if metric['is_percentage']:
            stats['value'] = stats[col] * 100
        else:
            stats['value'] = stats[col]

        time_stats[col] = stats

    # Calculate global average for decision efficiency
    global_time_stats = filtered_possessions_bins.groupby('time_bin', observed=True)[
        'decision_efficiency'].mean().reset_index()

    fig = go.Figure()

    # Add global average line
    fig.add_trace(
        go.Scatter(
            x=global_time_stats['time_bin'],
            y=global_time_stats['decision_efficiency'],
            mode='lines+markers',
            name='Global Average Decision Efficiency',
            line=dict(color=colors['global_avg'],
                      width=2, dash='dash'),
            marker=dict(size=6, color=colors['global_avg']),
        )
    )

    # Add player metrics
    for metric in metrics_config:
        col = metric['column']
        stats = time_stats[col]

        fig.add_trace(
            go.Scatter(
                x=stats['time_bin'],
                y=stats['value'],
                mode='lines+markers',
                name=metric['name'],
                line=dict(color=metric['color'],
                          width=metric['width']),
                marker=dict(size=metric['size'],
                            color=metric['color']),
            )
        )

    fig.update_traces(
        hovertemplate='<b>%{fullData.name}</b>: %{y:.1f}%<extra></extra>'
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            yanchor="top",
        ),
        margin=dict(b=100),
        hovermode='x unified',
        xaxis=dict(
            title="Minutes",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            griddash='dot',
            layer='below traces',
            showline=True,
            linewidth=2,
            linecolor=line_color,
            tickcolor=line_color,
            ticks='outside',
        ),
        yaxis=dict(
            title="Metrics (%)",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            griddash='2px',
            layer='below traces',
        ),
    )

    return fig


def create_radar(filtered_stats, radar_metrics, player1, player2):
    radar_metric_labels = [metric_labels[key] for key in radar_metrics]

    player1_values = [player1[metric]
                      for metric in radar_metrics]
    player2_values = [player2[metric]
                      for metric in radar_metrics]
    radar = Radar(radar_metric_labels, filtered_stats[radar_metrics].min(
    ).tolist(), filtered_stats[radar_metrics].max().tolist())

    fig, axs = grid(figheight=14,
                    grid_height=0.915, title_height=0.06, endnote_height=0.025,
                    title_space=0, endnote_space=0, grid_key='radar', axis=False)

    robotto_regular = FontManager()

    radar.setup_axis(ax=axs['radar'])
    rings_inner = radar.draw_circles(
        ax=axs['radar'], facecolor='#fff', edgecolor='lightgrey')
    radar_output = radar.draw_radar_compare(player1_values, player2_values, ax=axs['radar'],
                                            kwargs_radar={
                                                'facecolor': main_color, 'alpha': 0.6},
                                            kwargs_compare={'facecolor': secondary_color, 'alpha': 0.6})
    radar_poly, radar_poly2, vertices1, vertices2 = radar_output
    range_labels = radar.draw_range_labels(ax=axs['radar'], fontsize=15,
                                           fontproperties=robotto_regular.prop)
    param_labels = radar.draw_param_labels(ax=axs['radar'], fontsize=20,
                                           fontproperties=robotto_regular.prop)
    axs['radar'].scatter(vertices1[:, 0], vertices1[:, 1],
                         c=main_color, edgecolors=main_color, marker='o', s=100, zorder=2)
    axs['radar'].scatter(vertices2[:, 0], vertices2[:, 1],
                         c=secondary_color, edgecolors=secondary_color, marker='o', s=100, zorder=2)

    title1_text = axs['title'].text(0.01, 0.65, player1['short_name'], fontsize=25, color=main_color,
                                    fontproperties=robotto_regular.prop, ha='left', va='center')
    title2_text = axs['title'].text(0.01, 0.25, player1['team_shortname'], fontsize=20,
                                    fontproperties=robotto_regular.prop,
                                    ha='left', va='center', color=main_color)
    title3_text = axs['title'].text(0.99, 0.65, player2['short_name'], fontsize=25,
                                    fontproperties=robotto_regular.prop,
                                    ha='right', va='center', color=secondary_color)
    title4_text = axs['title'].text(0.99, 0.25, player2['team_shortname'], fontsize=20,
                                    fontproperties=robotto_regular.prop,
                                    ha='right', va='center', color=secondary_color)

    return fig
