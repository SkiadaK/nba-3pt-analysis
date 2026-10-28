"""
fetch_nba_data.py

Τραβάει ζωντανά, τρέχοντα στατιστικά ομάδων NBA απευθείας από το επίσημο
stats.nba.com (μέσω του πακέτου nba_api) και τα αποθηκεύει σε καθαρό CSV,
με τις μεταβλητές που χρησιμοποιήθηκαν στο τελικό μοντέλο της ανάλυσης:
W/L%, ORtg, DRtg, Pace, TS%, 3PAr, 3P%.

Εγκατάσταση (μία φορά):
    pip install nba_api pandas

Εκτέλεση:
    python fetch_nba_data.py                    # τρέχουσα σεζόν (live)
    python fetch_nba_data.py --season 2025-26   # συγκεκριμένη σεζόν

Τα analyze_*.py διαβάζουν τη σεζόν από το CSV, οπότε τρέχουν πάντα
στην ίδια σεζόν με αυτό το script.
"""

import sys
import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats

from nba_season import season_from_args, warn_if_few_games

SEASON_TYPE = "Regular Season"


def fetch_team_measure(season: str, measure_type: str) -> pd.DataFrame:
    """Τραβάει πίνακα στατιστικών ομάδων (Base ή Advanced) από το nba_api."""
    response = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star=SEASON_TYPE,
        measure_type_detailed_defense=measure_type,
        per_mode_detailed="PerGame",
        timeout=60,
    )
    return response.get_data_frames()[0]


def main() -> None:
    season = season_from_args("Τραβάει season-level στατιστικά ομάδων NBA.")
    print(f"Τραβάω δεδομένα για τη σεζόν {season}...")

    try:
        base_raw = fetch_team_measure(season, "Base")
        advanced_raw = fetch_team_measure(season, "Advanced")
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

    df.insert(0, "Season", season)
    df = df[["Season", "Team", "W", "L", "W/L%", "PTS", "ORtg", "DRtg", "Pace", "3PAr", "3P%", "TS%"]]
    df = df.sort_values("W/L%", ascending=False).reset_index(drop=True)

    out_path = "NBAstats_live.csv"
    df.to_csv(out_path, index=False)
    print(f"\nΈτοιμο! Αποθηκεύτηκαν {len(df)} ομάδες στο {out_path}")
    print(df.head())

    warn_if_few_games((df["W"] + df["L"]).median(), season)


if __name__ == "__main__":
    main()
