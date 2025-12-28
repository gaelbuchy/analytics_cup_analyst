import streamlit as st
from matplotlib.lines import Line2D
from src.data.data_loader import load_tracking_data

from mplsoccer import Pitch
from mplsoccer import FontManager


# define color constants
BACKGROUND_COLOR = "#ffffff"
LINE_COLOR = "#181c1f"
HOME_COLOR = "#197BBD"
AWAY_COLOR = "#ED254E"
PASSING_COLOR = "#F9DC5C"
CHOSEN_COLOR = "#0C7C59"


def plot_event(event, events=None):
    enriched_tracking_data = load_tracking_data(event.match_id.iloc[0])

    synced = event.merge(
        enriched_tracking_data,
        left_on=["frame_end"],
        right_on="frame",
        suffixes=("_event", "_tracking"),
    )

    pitch = Pitch(
        pitch_type="skillcorner",
        line_alpha=0.3,
        pitch_length=105,
        pitch_width=68,
        pitch_color=BACKGROUND_COLOR,
        line_color=LINE_COLOR,
        linewidth=1.5,
    )

    fig, ax = pitch.grid(figheight=8, endnote_height=0,
                         title_height=0.1, title_space=0.02,
                         axis=False,
                         )

    # then setup the pitch plot markers we want to animate
    marker_kwargs = {'marker': 'o',
                     'linestyle': 'None', 'markeredgecolor': 'None'}

    # plot out of possession team
    out_of_possession_team = synced[synced.team_id_event !=
                                    synced.team_id_tracking]
    ax['pitch'].plot(
        out_of_possession_team["x"],
        out_of_possession_team["y"],
        ms=10,
        markerfacecolor=AWAY_COLOR,
        **marker_kwargs
    )

    # plot possession team
    possession_team = synced[synced.team_id_event == synced.team_id_tracking]
    ax['pitch'].plot(
        possession_team["x"],
        possession_team["y"],
        ms=10,
        markerfacecolor=HOME_COLOR,
        **marker_kwargs
    )

    # plot ball
    ax['pitch'].plot(synced.iloc[0].ball_x,
                     synced.iloc[0].ball_y,
                     ms=6,
                     markerfacecolor=BACKGROUND_COLOR,
                     zorder=3,
                     marker='o',
                     linestyle='None',
                     markeredgecolor=LINE_COLOR
                     )

    robotto_regular = FontManager()

    if events is not None:
        associated_events = events[(events['associated_player_possession_event_id'] == event['event_id'].iloc[0]) & (
            events['match_id'] == event['match_id'].iloc[0])]

        current_passing_x = []
        current_passing_y = []
        for id in associated_events.index:
            # match_id = associated_events.loc[id]['match_id']
            # event_id = associated_events.loc[id]['event_id']
            event_type = associated_events.loc[id]['event_type']
            player_id = associated_events.loc[id]['player_id']
            # frame_start = associated_events.loc[id]['frame_start']
            # frame_end = associated_events.loc[id]['frame_end']
            xt_value = associated_events.loc[id]['xthreat']
            xpass_completion = round(
                associated_events.loc[id]['xpass_completion'] * 100, 1)

            player_tracking = synced[synced['player_id_tracking']
                                     == player_id].iloc[0]

            # add passing option
            if event_type == 'passing_option':
                current_passing_x.append(player_tracking['x'])
                current_passing_y.append(player_tracking['y'])

                label = f"{xpass_completion:.0f}% - {xt_value:.3f} xT"

                # annote passing option values
                ax['pitch'].annotate(
                    label,
                    xy=(player_tracking['x'], player_tracking['y']),
                    xytext=(5, -10),  # Offset 5 points right and up
                    textcoords='offset points',
                    fontsize=9,
                    color=HOME_COLOR,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor=HOME_COLOR, alpha=0.7),
                    fontproperties=robotto_regular.prop
                )

        # plot passing options
        ax['pitch'].plot(
            current_passing_x,
            current_passing_y,
            ms=15,
            marker='o',
            linestyle='None',
            markerfacecolor="None",
            markeredgecolor=HOME_COLOR,
        )

    # plot target
    targeted_player_tracking = synced[synced['player_id_tracking']
                                      == event.player_targeted_id.iloc[0]]

    ax['pitch'].plot(targeted_player_tracking.iloc[0].x,
                     targeted_player_tracking.iloc[0].y,
                     ms=10,
                     markerfacecolor=CHOSEN_COLOR,
                     **marker_kwargs
                     )

    # Extract context data for title
    first_row = synced.iloc[0]
    home_team = first_row['match_home_team.name']
    away_team = first_row['match_away_team.name']
    minute = int(event.iloc[0]['minute_start'])
    team_score = event.iloc[0]['team_score']
    opponent_score = event.iloc[0]['opponent_team_score']

    title = f"{home_team} {int(team_score)}-{int(opponent_score)} {away_team} ({minute}min)"
    ax['title'].text(0.5, 0.5, title,
                     va='center', ha='center', color='black',
                     fontproperties=robotto_regular.prop, fontsize=16)

    # Create custom legend handles
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Possession Team',
               markerfacecolor=HOME_COLOR, markersize=10, linestyle='None'),
        Line2D([0], [0], marker='o', color='w', label='Opposition Team',
               markerfacecolor=AWAY_COLOR, markersize=10, linestyle='None'),
        Line2D([0], [0], marker='o', color='w', label='Passing Options',
               markerfacecolor='None', markeredgecolor=HOME_COLOR,
               markersize=10, linestyle='None', markeredgewidth=2),
        Line2D([0], [0], marker='o', color='w', label='Targeted Player',
               markerfacecolor=CHOSEN_COLOR, markersize=10, linestyle='None'),
    ]

    # Add legend to the pitch axes
    ax['pitch'].legend(handles=legend_elements,
                       frameon=True,
                       facecolor='white',
                       edgecolor=None,
                       fontsize=10,
                       framealpha=0.9
                       )

    st.pyplot(fig)
