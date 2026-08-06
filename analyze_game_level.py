"""
analyze_game_level.py

Χτίζει ένα dataset σε επίπεδο ΑΓΩΝΑ (κάθε ομάδα σε κάθε ματς της σεζόν) και
απαντά σωστά στα Ερωτήματα 2 και 3 του report:
  - Ερώτημα 2: Διαφέρει το 3P% μιας ομάδας Εντός vs Εκτός έδρας;
  - Ερώτημα 3: Διαφέρει το 3P% ανάλογα με τη δύναμη του αντιπάλου εκείνου
    του αγώνα (Αδύναμος / Μεσαίος / Κορυφαίος αντίπαλος);

Χρησιμοποιεί το NBAstats_live.csv (season-level W/L% ανά ομάδα, από το
fetch_nba_data.py) για να κατηγοριοποιήσει τους αντιπάλους σε δύναμη.

ΣΗΜΕΙΩΣΗ ΜΕΘΟΔΟΛΟΓΙΑΣ: η κατηγοριοποίηση δύναμης βασίζεται στο ΤΕΛΙΚΟ W/L%
της σεζόν (δηλαδή "ξέρουμε εκ των υστέρων ποιος ήταν δυνατός"), όχι στο
ρεκόρ τη στιγμή εκείνου του συγκεκριμένου αγώνα. Είναι μια αποδεκτή
απλοποίηση, αλλά αξίζει να αναφέρεται ρητά ως περιορισμός στην αναφορά.

Εγκατάσταση (μία φορά):
    pip install nba_api pandas scipy

Εκτέλεση (ΑΦΟΥ έχεις ήδη τρέξει το fetch_nba_data.py, ώστε να υπάρχει το
NBAstats_live.csv στον ίδιο φάκελο):
    python analyze_game_level.py
"""

import sys
import pandas as pd
from scipy import stats
from nba_api.stats.endpoints import leaguegamefinder

from datetime import date


def current_nba_season() -> str:
    """Υπολογίζει αυτόματα την τρέχουσα σεζόν NBA με βάση τη σημερινή
    ημερομηνία. Η σεζόν NBA ξεκινά τον Οκτώβριο: π.χ. αν είμαστε
    Νοέμβριος 2026, η σεζόν είναι "2026-27". Αν είμαστε πριν τον Οκτώβριο
    (π.χ. Ιούνιος 2026), θεωρούμε ότι τρέχει ακόμα η προηγούμενη σεζόν
    "2025-26"."""
    today = date.today()
    if today.month >= 10:
        start_year = today.year
    else:
        start_year = today.year - 1
    end_year_short = str(start_year + 1)[-2:]
    return f"{start_year}-{end_year_short}"

SEASON = current_nba_season()  # υπολογίζεται αυτόματα
SEASON_TYPE = "Regular Season"
TEAM_STATS_FILE = "NBAstats_live.csv"


def fetch_game_logs() -> pd.DataFrame:
    response = leaguegamefinder.LeagueGameFinder(
        season_nullable=SEASON,
        season_type_nullable=SEASON_TYPE,
        league_id_nullable="00",
        player_or_team_abbreviation="T",
    )
    return response.get_data_frames()[0]


def main() -> None:
    # 1. Φόρτωσε το season-level W/L% ανά ομάδα
    try:
        team_stats = pd.read_csv(TEAM_STATS_FILE)
    except FileNotFoundError:
        print(f"Δεν βρέθηκε το {TEAM_STATS_FILE} σε αυτόν τον φάκελο.")
        print("Τρέξε πρώτα το fetch_nba_data.py, και μετά ξανατρέξε αυτό.")
        sys.exit(1)

    team_stats["strength"] = pd.qcut(
        team_stats["W/L%"], q=3, labels=["Αδύναμη", "Μεσαία", "Κορυφαία"]
    )
    strength_map = dict(zip(team_stats["Team"], team_stats["strength"]))

    # 2. Τράβα τα game logs (κάθε ομάδα - κάθε αγώνας)
    print("Τραβάω game logs (μπορεί να πάρει λίγα δευτερόλεπτα)...")
    try:
        games = fetch_game_logs()
    except Exception as exc:  # noqa: BLE001
        print("Αποτυχία κλήσης στο NBA API:", exc)
        sys.exit(1)

    print("Στήλες που επέστρεψε το API:", list(games.columns))
    print(f"Συνολικές γραμμές (ομάδα-αγώνας): {len(games)}\n")

    games = games[games["FG3A"] > 0].copy()  # αποφυγή διαίρεσης με το μηδέν

    # 3. Home/Away από το πεδίο MATCHUP ("TEAM vs. OPP" = εντός, "TEAM @ OPP" = εκτός)
    games["home_away"] = games["MATCHUP"].apply(
        lambda m: "Εντός Έδρας" if "vs." in m else "Εκτός Έδρας"
    )

    # 4. Βρες τον αντίπαλο κάθε αγώνα (self-merge πάνω στο GAME_ID)
    pairs = games[["GAME_ID", "TEAM_ID", "TEAM_NAME"]].rename(
        columns={"TEAM_ID": "OPP_TEAM_ID", "TEAM_NAME": "OPP_TEAM_NAME"}
    )
    games = games.merge(pairs, on="GAME_ID")
    games = games[games["TEAM_ID"] != games["OPP_TEAM_ID"]]

    # 5. Κατηγορία δύναμης αντιπάλου
    games["opponent_strength"] = games["OPP_TEAM_NAME"].map(strength_map)
    games = games.dropna(subset=["opponent_strength"])

    # Αποθήκευση του dataset σε επίπεδο αγώνα
    games_out = games[[
        "TEAM_NAME", "GAME_DATE", "MATCHUP", "home_away",
        "OPP_TEAM_NAME", "opponent_strength", "FG3A", "FG3M", "FG3_PCT",
    ]]
    games_out.to_csv("NBA_gamelevel_live.csv", index=False)
    print(f"Αποθηκεύτηκαν {len(games_out)} γραμμές στο NBA_gamelevel_live.csv\n")

    # 6. Ερώτημα 2: 3P% Εντός vs Εκτός έδρας
    home = games.loc[games["home_away"] == "Εντός Έδρας", "FG3_PCT"]
    away = games.loc[games["home_away"] == "Εκτός Έδρας", "FG3_PCT"]

    levene_2 = stats.levene(home, away)
    ttest_2 = stats.ttest_ind(home, away, equal_var=(levene_2.pvalue > 0.05))

    print("=== Ερώτημα 2: 3P% Εντός vs Εκτός Έδρας ===")
    print(f"Μέσο 3P% Εντός Έδρας: {home.mean():.4f}  (n={len(home)})")
    print(f"Μέσο 3P% Εκτός Έδρας: {away.mean():.4f}  (n={len(away)})")
    print(f"Levene test: W={levene_2.statistic:.4f}, p={levene_2.pvalue:.4f}")
    print(f"t-test: t={ttest_2.statistic:.4f}, p={ttest_2.pvalue:.4f}")
    print("→ Στατιστικά σημαντική διαφορά.\n" if ttest_2.pvalue < 0.05
          else "→ Καμία στατιστικά σημαντική διαφορά.\n")

    # 7. Ερώτημα 3: 3P% ανάλογα με τη δύναμη αντιπάλου (ANOVA)
    groups = [
        g["FG3_PCT"].values
        for _, g in games.groupby("opponent_strength", observed=True)
    ]
    levene_3 = stats.levene(*groups)
    anova_3 = stats.f_oneway(*groups)

    print("=== Ερώτημα 3: 3P% ανάλογα με τη Δύναμη Αντιπάλου ===")
    print(games.groupby("opponent_strength", observed=True)["FG3_PCT"].mean())
    print(f"Levene test: W={levene_3.statistic:.4f}, p={levene_3.pvalue:.4f}")
    print(f"ANOVA: F={anova_3.statistic:.4f}, p={anova_3.pvalue:.4f}")
    print("→ Στατιστικά σημαντική διαφορά μεταξύ κατηγοριών αντιπάλου."
          if anova_3.pvalue < 0.05
          else "→ Καμία στατιστικά σημαντική διαφορά μεταξύ κατηγοριών αντιπάλου.")


if __name__ == "__main__":
    main()
