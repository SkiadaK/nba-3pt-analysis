"""
analyze_regression.py

Τρέχει πολλαπλή γραμμική παλινδρόμηση με backward elimination πάνω στα
ζωντανά season-level δεδομένα (NBAstats_live.csv), για να απαντήσει στο
Ερώτημα 1: ποιοι παράγοντες επηρεάζουν περισσότερο το W/L%;

Ξεκινά με όλες τις ανεξάρτητες μεταβλητές (ORtg, DRtg, Pace, 3PAr, 3P%, TS%)
και αφαιρεί σε κάθε βήμα τη μεταβλητή με το μεγαλύτερο p-value, μέχρι να
μείνουν μόνο στατιστικά σημαντικές (p < 0.05).

Εγκατάσταση (μία φορά):
    pip install pandas statsmodels

Εκτέλεση (ΑΦΟΥ έχεις ήδη τρέξει το fetch_nba_data.py):
    python analyze_regression.py
"""

import sys
import pandas as pd
import statsmodels.api as sm

TEAM_STATS_FILE = "NBAstats_live.csv"
CANDIDATE_VARS = ["ORtg", "DRtg", "Pace", "3PAr", "3P%", "TS%"]
SIGNIFICANCE_LEVEL = 0.05


def main() -> None:
    try:
        df = pd.read_csv(TEAM_STATS_FILE)
    except FileNotFoundError:
        print(f"Δεν βρέθηκε το {TEAM_STATS_FILE} σε αυτόν τον φάκελο.")
        print("Τρέξε πρώτα το fetch_nba_data.py, και μετά ξανατρέξε αυτό.")
        sys.exit(1)

    y = df["W/L%"]
    predictors = CANDIDATE_VARS.copy()

    print(f"Ξεκινάμε με {len(predictors)} μεταβλητές: {predictors}\n")

    step = 1
    while True:
        X = sm.add_constant(df[predictors])
        model = sm.OLS(y, X).fit()

        pvalues = model.pvalues.drop("const")
        worst_var = pvalues.idxmax()
        worst_p = pvalues.max()

        print(f"--- Βήμα {step} ---")
        print(f"Μεταβλητές: {predictors}")
        print(f"R² = {model.rsquared:.4f}")
        print(pvalues.round(4).to_string())
        print()

        if worst_p <= SIGNIFICANCE_LEVEL:
            print("Όλες οι εναπομείνασες μεταβλητές είναι στατιστικά σημαντικές. Σταματάμε εδώ.\n")
            break

        print(f"Αφαιρείται η '{worst_var}' (p = {worst_p:.4f} > {SIGNIFICANCE_LEVEL})\n")
        predictors.remove(worst_var)
        step += 1

        if not predictors:
            print("Καμία μεταβλητή δεν έμεινε στατιστικά σημαντική.")
            break

    print("=== ΤΕΛΙΚΟ ΜΟΝΤΕΛΟ ===")
    print(f"Μεταβλητές: {predictors}")
    print(f"R² = {model.rsquared:.4f}")
    print(model.summary())


if __name__ == "__main__":
    main()
