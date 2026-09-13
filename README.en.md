# 🏀 NBA 3PT Analysis — Do teams that shoot more 3-pointers win more games?

[🇬🇷 Ελληνικά](README.md) | 🇬🇧 English

![Python](https://img.shields.io/badge/Python-3.14-blue) ![pandas](https://img.shields.io/badge/pandas-live--data-150458) ![License](https://img.shields.io/badge/License-MIT-green)

> **TL;DR:** Shooting more three-pointers doesn't guarantee wins on its own — overall offensive and defensive rating (ORtg/DRtg) are the real deciding factors.

Statistical analysis of the relationship between 3-point shooting strategy and winning in the NBA, powered by a **live data pipeline** that pulls current stats directly from the official NBA API.

Started as a coursework project for a Statistics course (University of Crete) and evolved into an independent project with real, refreshable data.

## Research Questions

1. **Which factors most affect a team's performance?** (multiple regression, W/L% ~ ORtg, DRtg, Pace, TS%, 3PAr, 3P%)
2. **Do teams shoot 3-pointers differently at Home vs Away?** (t-test, game level)
3. **Does 3P% vary depending on opponent strength?** (ANOVA, game level)

## Findings

| Question | Result |
|---|---|
| 1. Key performance drivers | Backward elimination on the live data narrows it down to **ORtg**, **DRtg**, and **TS%** (p < 0.05, R² = 0.95) |
| 2. Home vs Away | Statistically significant difference (t-test, p = 0.023) — slightly better 3P% at home (36.3% vs 35.5%) |
| 3. Opponent strength | Statistically significant difference (ANOVA, p = 0.038) — better 3P% against weaker opponents |

![ORtg & DRtg vs W/L%](q1_ortg_drtg_vs_wl.png)
![3P% Home vs Away](q2_home_away_3pct.png)
![3P% by Opponent Strength](q3_opponent_strength_3pct.png)

## Project Structure

fetch_nba_data.py       # Pulls season-level team stats (ORtg, DRtg, Pace, 3PAr, 3P%, TS%)
analyze_regression.py   # Live regression + backward elimination for Question 1
analyze_game_level.py   # Pulls per-game data and runs Questions 2 & 3
NBAstats_live.csv        # Output of fetch_nba_data.py
NBA_gamelevel_live.csv   # Output of analyze_game_level.py

## How to run
pip install nba_api pandas scipy statsmodels

python fetch_nba_data.py        # Run this first
python analyze_regression.py    # Question 1
python analyze_game_level.py    # Questions 2 & 3

The current NBA season is calculated automatically based on today's date — no manual configuration needed.

## Methodological Notes & Limitations

- The original coursework examined Questions 2 and 3 at the **season** level (30 teams), using season-level 3P% and W/L% as a proxy. This version examines them correctly at the **game** level (2,400+ observations), answering the question as originally posed more precisely.
- The "opponent strength" categorization (Question 3) is based on the **final** season W/L% — meaning we know in hindsight which teams were strong, not their record at the time of the specific game. An acceptable simplification, but worth noting as a limitation.
- The **Age** (average roster age) and **SOS** (Strength of Schedule) variables from the original coursework were intentionally left out of the live pipeline: Age did not survive backward elimination in the original model (so removing it doesn't affect the conclusions), and SOS is not available through the official NBA API.
- The final model for Question 1 shows mild multicollinearity between ORtg and TS% (expected, since TS% contributes to the ORtg calculation) — the results are valid, but interpreting the individual coefficients should be done with care.

## Data

Official NBA stats API (via [`nba_api`](https://github.com/swar/nba_api)), live, on demand.

## Tech Stack

Python, pandas, scipy, nba_api

---
The original statistical analysis (coursework) was carried out jointly with Christos Ieronymakis. The live data pipeline, the extension to game-level analysis, and the correction of Questions 2-3 were developed independently by Skiada Katholiki.
---
*Skiada Katholiki*
