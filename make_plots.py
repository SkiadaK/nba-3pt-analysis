"""
make_plots.py

Φτιάχνει τα τρία γραφήματα του README από τα CSV που παράγουν τα άλλα scripts,
σε δύο γλώσσες: ελληνικά (για το README.md) και αγγλικά (για το README.en.md).
  - q1_ortg_drtg_vs_wl.png          / q1_ortg_drtg_vs_wl_en.png          (Ερώτημα 1)
  - q2_home_away_3pct.png           / q2_home_away_3pct_en.png           (Ερώτημα 2)
  - q3_opponent_strength_3pct.png   / q3_opponent_strength_3pct_en.png   (Ερώτημα 3)

Τα p-values στους τίτλους υπολογίζονται εδώ, με τον ίδιο τρόπο όπως στο
analyze_game_level.py, ώστε γραφήματα και αποτελέσματα να συμφωνούν πάντα.

Εγκατάσταση (μία φορά):
    pip install pandas scipy matplotlib

Εκτέλεση (ΑΦΟΥ έχεις τρέξει τα fetch_nba_data.py και analyze_game_level.py):
    python make_plots.py
"""

import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

TEAM_STATS_FILE = "NBAstats_live.csv"
GAME_LEVEL_FILE = "NBA_gamelevel_live.csv"

BLUE = "#3b5998"
RED = "#c8102e"
GREEN = "#5a9e3a"
ORANGE = "#eba73c"

# Τιμές όπως είναι γραμμένες στο NBA_gamelevel_live.csv
HOME, AWAY = "Εντός Έδρας", "Εκτός Έδρας"
STRENGTH_ORDER = ["Αδύναμη", "Μεσαία", "Κορυφαία"]

# Κείμενα των γραφημάτων ανά γλώσσα (suffix = κατάληξη στο όνομα αρχείου)
TEXT = {
    "el": {
        "suffix": "",
        "q1_title": "Ερώτημα 1: ORtg & DRtg vs Ποσοστό Νικών (W/L%)",
        "ortg": "Επιθετική Απόδοση (ORtg)",
        "drtg": "Αμυντική Απόδοση (DRtg)",
        "q2_title": "Ερώτημα 2: 3P% Εντός vs Εκτός Έδρας",
        "home": "Εντός Έδρας",
        "away": "Εκτός Έδρας",
        "q3_title": "Ερώτημα 3: 3P% ανά Δύναμη Αντιπάλου",
        "q3_xlabel": "Δύναμη Αντιπάλου (βάσει τελικού W/L%)",
        "strength": {"Αδύναμη": "Αδύναμη", "Μεσαία": "Μεσαία", "Κορυφαία": "Κορυφαία"},
    },
    "en": {
        "suffix": "_en",
        "q1_title": "Question 1: ORtg & DRtg vs Win Percentage (W/L%)",
        "ortg": "Offensive Rating (ORtg)",
        "drtg": "Defensive Rating (DRtg)",
        "q2_title": "Question 2: 3P% Home vs Away",
        "home": "Home",
        "away": "Away",
        "q3_title": "Question 3: 3P% by Opponent Strength",
        "q3_xlabel": "Opponent Strength (based on final W/L%)",
        "strength": {"Αδύναμη": "Weak", "Μεσαία": "Average", "Κορυφαία": "Strong"},
    },
}


def load_csv(path: str, made_by: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        print(f"Δεν βρέθηκε το {path} σε αυτόν τον φάκελο.")
        print(f"Τρέξε πρώτα το {made_by}, και μετά ξανατρέξε αυτό.")
        sys.exit(1)


def style_axes(ax) -> None:
    ax.grid(alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def draw_boxplot(ax, groups, labels, colors) -> None:
    """Boxplot με μουστάκια από min έως max και ρόμβο για τον μέσο όρο."""
    bp = ax.boxplot(
        groups,
        tick_labels=labels,
        whis=(0, 100),
        widths=0.5,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white",
                   "markeredgecolor": "black", "markersize": 8},
        medianprops={"color": "black", "linewidth": 2},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    for i, g in enumerate(groups, start=1):
        ax.annotate(f"{np.mean(g):.3f}", xy=(i, np.mean(g)),
                    xytext=(0, 14), textcoords="offset points",
                    ha="center", fontsize=10)
    ax.set_ylabel("3P%")
    style_axes(ax)


def plot_q1(team_stats: pd.DataFrame, t: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    panels = [
        ("ORtg", t["ortg"], BLUE),
        ("DRtg", t["drtg"], RED),
    ]
    for ax, (col, xlabel, color) in zip(axes, panels):
        x, y = team_stats[col], team_stats["W/L%"]
        r = x.corr(y)
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 100)

        ax.scatter(x, y, color=color, s=60, edgecolor="white", alpha=0.95)
        ax.plot(xs, slope * xs + intercept, "--", color=color, alpha=0.8)
        ax.set_title(f"r = {r:.2f}")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("W/L%")
        style_axes(ax)

    fig.suptitle(t["q1_title"], fontweight="bold", fontsize=14)
    fig.tight_layout()
    fig.savefig(f"q1_ortg_drtg_vs_wl{t['suffix']}.png", dpi=150)
    plt.close(fig)


def plot_q2(games: pd.DataFrame, t: dict) -> None:
    home = games.loc[games["home_away"] == HOME, "FG3_PCT"]
    away = games.loc[games["home_away"] == AWAY, "FG3_PCT"]

    levene = stats.levene(home, away)
    ttest = stats.ttest_ind(home, away, equal_var=(levene.pvalue > 0.05))

    fig, ax = plt.subplots(figsize=(6, 5))
    draw_boxplot(ax, [home, away], [t["home"], t["away"]], [BLUE, RED])
    ax.set_title(f"{t['q2_title']}\n"
                 f"(t-test, p = {ttest.pvalue:.3f})", fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"q2_home_away_3pct{t['suffix']}.png", dpi=150)
    plt.close(fig)


def plot_q3(games: pd.DataFrame, t: dict) -> None:
    present = [s for s in STRENGTH_ORDER if s in set(games["opponent_strength"])]
    groups = [games.loc[games["opponent_strength"] == s, "FG3_PCT"] for s in present]
    anova = stats.f_oneway(*groups)

    colors = dict(zip(STRENGTH_ORDER, [GREEN, ORANGE, RED]))
    fig, ax = plt.subplots(figsize=(7, 5))
    labels = [t["strength"][s] for s in present]
    draw_boxplot(ax, groups, labels, [colors[s] for s in present])
    ax.set_xlabel(t["q3_xlabel"])
    ax.set_title(f"{t['q3_title']}\n"
                 f"(ANOVA, p = {anova.pvalue:.3f})", fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"q3_opponent_strength_3pct{t['suffix']}.png", dpi=150)
    plt.close(fig)


def main() -> None:
    team_stats = load_csv(TEAM_STATS_FILE, "fetch_nba_data.py")
    games = load_csv(GAME_LEVEL_FILE, "analyze_game_level.py")

    for t in TEXT.values():
        plot_q1(team_stats, t)
        plot_q2(games, t)
        plot_q3(games, t)
    print("Έτοιμο! Αποθηκεύτηκαν τα γραφήματα στα ελληνικά (q1/q2/q3_*.png)")
    print("και στα αγγλικά (q1/q2/q3_*_en.png).")


if __name__ == "__main__":
    main()
