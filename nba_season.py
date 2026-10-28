"""
nba_season.py

Κοινές βοηθητικές συναρτήσεις για τη σεζόν NBA, ώστε όλα τα scripts να
χρησιμοποιούν την ίδια λογική:
  - current_nba_season(): η τρέχουσα σεζόν, βάσει σημερινής ημερομηνίας
  - season_from_args(): η σεζόν από το --season, ή η τρέχουσα αν δεν δοθεί
  - warn_if_few_games(): προειδοποίηση όταν η σεζόν μόλις ξεκίνησε
"""

import argparse
import re
from datetime import date

# Κάτω από τόσους αγώνες ανά ομάδα, τα στατιστικά τεστ δεν είναι αξιόπιστα
MIN_GAMES_PER_TEAM = 20


def current_nba_season() -> str:
    """Υπολογίζει αυτόματα την τρέχουσα σεζόν NBA με βάση τη σημερινή
    ημερομηνία. Η σεζόν NBA ξεκινά τον Οκτώβριο: π.χ. αν είμαστε
    Νοέμβριος 2026, η σεζόν είναι "2026-27". Αν είμαστε πριν τον Οκτώβριο
    (π.χ. Ιούνιος 2026), θεωρούμε ότι τρέχει ακόμα η προηγούμενη σεζόν
    "2025-26"."""
    today = date.today()
    start_year = today.year if today.month >= 10 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _season_type(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise argparse.ArgumentTypeError(
            f"'{value}' δεν είναι έγκυρη σεζόν. Γράψε την π.χ. ως 2025-26."
        )
    return value


def season_from_args(description: str) -> str:
    """Διαβάζει το προαιρετικό --season από τη γραμμή εντολών.
    Χωρίς αυτό, χρησιμοποιείται η τρέχουσα σεζόν (live δεδομένα)."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--season",
        type=_season_type,
        default=None,
        help="Σεζόν NBA, π.χ. 2025-26 (προεπιλογή: η τρέχουσα σεζόν, live)",
    )
    args = parser.parse_args()
    return args.season or current_nba_season()


def warn_if_few_games(games_per_team: float, season: str) -> None:
    """Τυπώνει προειδοποίηση αν οι αγώνες ανά ομάδα είναι λίγοι."""
    if games_per_team >= MIN_GAMES_PER_TEAM:
        return
    print("\n" + "!" * 70)
    print(f"ΠΡΟΣΟΧΗ: Η σεζόν {season} έχει μόνο ~{games_per_team:.0f} αγώνες ανά ομάδα")
    print(f"(λιγότερους από {MIN_GAMES_PER_TEAM}). Η σεζόν μάλλον μόλις ξεκίνησε, οπότε")
    print("τα αποτελέσματα των τεστ ΔΕΝ είναι ακόμα αξιόπιστα.")
    print("Για αξιόπιστα αποτελέσματα τρέξε με ολοκληρωμένη σεζόν, π.χ.:")
    print("    python fetch_nba_data.py --season 2025-26")
    print("!" * 70 + "\n")
