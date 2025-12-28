# SkillCorner X PySport Analytics Cup

## Player Passing Decision Quality Analysis

### Introduction

This project is an interactive dashboard for analyzing player passing decisions. With new metrics and event data available for player possessions, we can now add context when evaluating passes and uncover new insights.

A common way to compare player decisions is looking at the xThreat created by each pass. But very different situations can produce the same xThreat values. One player might be choosing the best available option while another misses out on a more threatening pass.

Using SkillCorner's Dynamic Events Data and analyzing all available options in each pass situation, this dashboard provides tools to identify and compare how players make use of their passing opportunities.

### Usecase(s)

**Player Scouting:**
- Find players with good decision-making
- Compare players more fairly across different teams/leagues

**Coaching & Development:**
- Easily find and review situations where xThreat was missed or maximized

**Tactical Analysis:**
- Analyze opponents to find which players create threat
- Find patterns and weaknesses in decision-making


### Potential Audience

- **Football Clubs:** Performance analysts, recruitment teams, coaching staff
- **Media:** Data visualizations
- **Gaming:** Better player evaluation and ratings

---

## Video URL

https://drive.google.com/file/d/1a7xhIkp7NNEUNm0MrndWgcOaYA_k2ZvE/view

---

## Run Instructions

### Prerequisites

Python Installed

```
# if using virtual env
python -m venv venv
. venv/bin/activate

# install requirements
pip install -r requirements.txt
```

### Run the app

```
streamlit run main.py
```

---

## URL to Web App

https://analytics-cup-analyst-player-passing-decisions.streamlit.app/
