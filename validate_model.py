"""
Synthetic Behaviour Testing: Sales-Gap Anomaly Model
-----------------------------------------------------
This checks two things about the implemented model, not whether it
correctly identifies real phantom inventory, that would require labelled
outcomes this project doesn't have.

Part 1 checks that anomaly scores increase monotonically as the
simulated no-sale interval increases, a sanity check that the formula
was implemented correctly, not evidence of predictive performance.

Part 2 shows how the choice of alert threshold changes the size of the
resulting worklist across the real catalogue. This is a workload
sensitivity analysis, not a measure of accuracy: without confirmed
shelf-check outcomes, there's no way to know which flagged items are
genuine issues and which aren't, so no threshold here can be described
as producing more or fewer false alarms, only a larger or smaller
worklist.
"""

import pandas as pd
from model import compute_anomaly_score


def get_anomaly_score(velocity: float, hours_since_last_sale: float) -> float:
    """Thin wrapper so the functions below can call this with just two
    arguments and get a plain number back, instead of unpacking a dict
    every time."""
    return compute_anomaly_score(velocity, hours_since_last_sale)["anomaly_score"]


def run_synthetic_gap_test(velocity: float, gap_hours_to_test: list[int]) -> pd.DataFrame:
    """
    Checks that anomaly scores increase monotonically as the simulated
    no-sale interval increases, for one product's known velocity.
    """
    results = []
    for hours in gap_hours_to_test:
        score = get_anomaly_score(velocity, hours)
        results.append({"Injected_No_Sale_Hours": hours, "Anomaly_Score": round(score, 2)})
    return pd.DataFrame(results)


def run_threshold_sensitivity(catalog_path: str, hours_since_last_sale: int, thresholds: list[int]) -> pd.DataFrame:
    """
    For a fixed period of no sales, shows how many products in the real
    catalogue would be classified as Critical at each candidate
    threshold. This is a workload sensitivity analysis: a lower
    threshold generates a larger investigation worklist, a higher
    threshold generates a smaller, more selective one. The impact on
    false-positive and missed-issue rates cannot be measured without
    confirmed shelf-check outcomes, which this project doesn't have.
    """
    df = pd.read_csv(catalog_path)
    df["score"] = df["Monitoring_Velocity"].apply(
        lambda v: get_anomaly_score(v, hours_since_last_sale)
    )

    results = []
    total_products = len(df)
    for threshold in thresholds:
        flagged = (df["score"] >= threshold).sum()
        results.append({
            "Threshold_%": threshold,
            "Products_Flagged": flagged,
            "Percent_of_Catalogue": round((flagged / total_products) * 100, 1),
        })
    return pd.DataFrame(results)


if __name__ == "__main__":
    # Part 1: does the score respond correctly to a longer period of no sales?
    test_velocity = 0.3
    test_gaps = [1, 2, 3, 4, 6, 8, 12, 24]

    results_df = run_synthetic_gap_test(test_velocity, test_gaps)
    print(f"Checking a product selling {test_velocity} units/hour on average:\n")
    print(results_df.to_string(index=False))

    scores = results_df["Anomaly_Score"].tolist()
    is_monotonic = all(scores[i] <= scores[i + 1] for i in range(len(scores) - 1))
    print(f"\nScores increase monotonically with longer periods of no sales: {is_monotonic}")

    # Part 2: how does the threshold choice affect worklist size?
    print("\n" + "=" * 60)
    print("Workload sensitivity across the real catalogue")
    print("=" * 60)

    thresholds_to_test = [80, 85, 90, 95, 99]
    hours_scenario = 3  # matches the dashboard's default "Current Hours with Zero Sales"

    sensitivity_df = run_threshold_sensitivity(
        catalog_path="data/aggregated_catalog.csv",
        hours_since_last_sale=hours_scenario,
        thresholds=thresholds_to_test,
    )
    print(f"\nAt {hours_scenario} hours since last sale:\n")
    print(sensitivity_df.to_string(index=False))
    print(
        "\nA lower threshold generates a larger investigation workload "
        "and increases sensitivity to unusual gaps. A higher threshold "
        "produces a smaller, more selective worklist. Which alerts turn "
        "out to be genuine issues cannot be determined without confirmed "
        "shelf-check outcomes."
    )