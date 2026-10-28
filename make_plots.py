"""
make_plots.py

Φτιάχνει τα τρία γραφήματα του README από τα CSV που παράγουν τα άλλα scripts:
  - q1_ortg_drtg_vs_wl.png          (Ερώτημα 1, από το NBAstats_live.csv)
  - q2_home_away_3pct.png           (Ερώτημα 2, από το NBA_gamelevel_live.csv)
  - q3_opponent_strength_3pct.png   (Ερώτημα 3, από το NBA_gamelevel_live.csv)

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

HOME, AWAY = "Εντός Έδρας", "Εκτός Έδρας"
STRENGTH_ORDER = ["Αδύναμη", "Μεσαία", "Κορυφαία"]


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


def plot_q1(team_stats: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    panels = [
        ("ORtg", "Επιθετική Απόδοση (ORtg)", BLUE),
        ("DRtg", "Αμυντική Απόδοση (DRtg)", RED),
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

    fig.suptitle("Ερώτημα 1: ORtg & DRtg vs Ποσοστό Νικών (W/L%)",
                 fontweight="bold", fontsize=14)
    fig.tight_layout()
    fig.savefig("q1_ortg_drtg_vs_wl.png", dpi=150)
    plt.close(fig)


def plot_q2(games: pd.DataFrame) -> None:
    home = games.loc[games["home_away"] == HOME, "FG3_PCT"]
    away = games.loc[games["home_away"] == AWAY, "FG3_PCT"]

    levene = stats.levene(home, away)
    ttest = stats.ttest_ind(home, away, equal_var=(levene.pvalue > 0.05))

    fig, ax = plt.subplots(figsize=(6, 5))
    draw_boxplot(ax, [home, away], [HOME, AWAY], [BLUE, RED])
    ax.set_title(f"Ερώτημα 2: 3P% Εντός vs Εκτός Έδρας\n"
                 f"(t-test, p = {ttest.pvalue:.3f})", fontweight="bold")
    fig.tight_layout()
    fig.savefig("q2_home_away_3pct.png", dpi=150)
    plt.close(fig)


def plot_q3(games: pd.DataFrame) -> None:
    present = [s for s in STRENGTH_ORDER if s in set(games["opponent_strength"])]
    groups = [games.loc[games["opponent_strength"] == s, "FG3_PCT"] for s in present]
    anova = stats.f_oneway(*groups)

    colors = dict(zip(STRENGTH_ORDER, [GREEN, ORANGE, RED]))
    fig, ax = plt.subplots(figsize=(7, 5))
    draw_boxplot(ax, groups, present, [colors[s] for s in present])
    ax.set_xlabel("Δύναμη Αντιπάλου (βάσει τελικού W/L%)")
    ax.set_title(f"Ερώτημα 3: 3P% ανά Δύναμη Αντιπάλου\n"
                 f"(ANOVA, p = {anova.pvalue:.3f})", fontweight="bold")
    fig.tight_layout()
    fig.savefig("q3_opponent_strength_3pct.png", dpi=150)
    plt.close(fig)


def main() -> None:
    team_stats = load_csv(TEAM_STATS_FILE, "fetch_nba_data.py")
    games = load_csv(GAME_LEVEL_FILE, "analyze_game_level.py")

    plot_q1(team_stats)
    plot_q2(games)
    plot_q3(games)
    print("Έτοιμο! Αποθηκεύτηκαν τα q1_ortg_drtg_vs_wl.png, "
          "q2_home_away_3pct.png και q3_opponent_strength_3pct.png")


if __name__ == "__main__":
    main()
