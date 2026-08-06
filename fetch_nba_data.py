"""
fetch_nba_data.py

Τραβάει ζωντανά, τρέχοντα στατιστικά ομάδων NBA απευθείας από το επίσημο
stats.nba.com (μέσω του πακέτου nba_api) και τα αποθηκεύει σε καθαρό CSV,
με τις μεταβλητές που χρησιμοποιήθηκαν στο τελικό μοντέλο της ανάλυσης:
W/L%, ORtg, DRtg, Pace, TS%, 3PAr, 3P%.

Εγκατάσταση (μία φορά):
    pip install nba_api pandas

Εκτέλεση:
    python fetch_nba_data.py
"""

import sys
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats

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

# Άλλαξε τη σεζόν αν θες προηγούμενη (π.χ. "2023-24")
SEASON = current_nba_season()  # υπολογίζεται αυτόματα
SEASON_TYPE = "Regular Season"


def fetch_team_measure(measure_type: str) -> pd.DataFrame:
    """Τραβάει πίνακα στατιστικών ομάδων (Base ή Advanced) από το nba_api."""
    response = leaguedashteamstats.LeagueDashTeamStats(
        season=SEASON,
        season_type_all_star=SEASON_TYPE,
        measure_type_detailed_defense=measure_type,
        per_mode_detailed="PerGame",
    )
    return response.get_data_frames()[0]


def main() -> None:
    print(f"Τραβάω δεδομένα για τη σεζόν {SEASON}...")

    try:
        base_raw = fetch_team_measure("Base")
        advanced_raw = fetch_team_measure("Advanced")
    except Exception as exc:  # noqa: BLE001
        print("Αποτυχία κλήσης στο NBA API:", exc)
        print("Πιθανές αιτίες: δεν έχει ξεκινήσει ακόμα η σεζόν, πρόβλημα δικτύου,")
        print("ή το stats.nba.com μπλόκαρε το αίτημα (δοκίμασε ξανά σε λίγο).")
        sys.exit(1)

    base = base_raw[["TEAM_ID", "TEAM_NAME", "W", "L", "W_PCT", "PTS", "FGA", "FG3A", "FG3_PCT", "FTA"]]
    advanced = advanced_raw[["TEAM_ID", "OFF_RATING", "DEF_RATING", "PACE"]]

    df = base.merge(advanced, on="TEAM_ID")

    # Υπολογιζόμενα πεδία, ίδιος ορισμός με basketball-reference
    df["3PAr"] = df["FG3A"] / df["FGA"]
    df["TS%"] = df["PTS"] / (2 * (df["FGA"] + 0.44 * df["FTA"]))

    df = df.rename(columns={
        "TEAM_NAME": "Team",
        "W_PCT": "W/L%",
        "FG3_PCT": "3P%",
        "OFF_RATING": "ORtg",
        "DEF_RATING": "DRtg",
        "PACE": "Pace",
    })

    df = df[["Team", "W", "L", "W/L%", "PTS", "ORtg", "DRtg", "Pace", "3PAr", "3P%", "TS%"]]
    df = df.sort_values("W/L%", ascending=False).reset_index(drop=True)

    out_path = "NBAstats_live.csv"
    df.to_csv(out_path, index=False)
    print(f"\nΈτοιμο! Αποθηκεύτηκαν {len(df)} ομάδες στο {out_path}")
    print(df.head())


if __name__ == "__main__":
    main()
