"""
Synthetic Validation: Phantom Inventory Model
-----------------------------------------------
Since we have no real labelled phantom-inventory events, we validate the
model's sensitivity instead: does it correctly flag increasingly long,
artificially-injected periods of no sales as increasingly suspicious?

If the anomaly score doesn't rise as the injected gap grows, the model
isn't doing its job. This checks that it does.

This file also checks how the choice of alert threshold affects how many
products get flagged, since the 80-99% sensitivity range and the default
95% Critical threshold in app.py are demonstrative defaults, not values
calibrated against real outcomes. This section shows the tradeoff those
defaults represent, without claiming any one threshold is "correct".
"""

import pandas as pd
from model import compute_anomaly_score as _compute_anomaly_score

def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> float:
    return _compute_anomaly_score(velocity, hours_since_last_sale)["anomaly_score"]


def run_synthetic_gap_test(velocity: float, gap_hours_to_test: list[int]) -> pd.DataFrame:
    """
    Injects a range of artificial periods of no sales for one product's
    known velocity, and records how the anomaly score responds.
    A healthy model should show scores rising monotonically as the
    injected gap grows.
    """
    results = []
    for hours in gap_hours_to_test:
        score = compute_anomaly_confidence(velocity, hours)["anomaly_confidence"]
        results.append({"Injected_No_Sale_Hours": hours, "Anomaly_Score": round(score, 2)})
    return pd.DataFrame(results)


def run_threshold_sensitivity(catalog_path: str, hours_since_last_sale: int, thresholds: list[int]) -> pd.DataFrame:
    """
    For a fixed period of no sales, shows how many products in the real
    catalogue would be flagged as Critical at each candidate threshold.
    This doesn't prove any threshold is correct, it shows the tradeoff:
    a lower threshold flags more products (more false alarms, faster
    detection), a higher one flags fewer (fewer false alarms, slower
    detection). Real calibration would need labelled outcomes from a
    staff feedback loop, which this project doesn't have yet.
    """
    df = pd.read_csv(catalog_path)
    df["score"] = df["Calculated_Velocity"].apply(
        lambda v: compute_anomaly_confidence(v, hours_since_last_sale)["anomaly_confidence"]
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
    print(f"Validation for a product selling {test_velocity} units/hour on average:\n")
    print(results_df.to_string(index=False))

    scores = results_df["Anomaly_Score"].tolist()
    is_monotonic = all(scores[i] <= scores[i + 1] for i in range(len(scores) - 1))
    print(f"\nScores rise monotonically with longer periods of no sales: {is_monotonic}")

    # Part 2: how does the threshold choice affect how many products get flagged?
    print("\n" + "=" * 60)
    print("Threshold sensitivity across the real catalogue")
    print("=" * 60)

    thresholds_to_test = [80, 85, 90, 95, 99]
    hours_scenario = 3  # a fixed, realistic period of no sales to test against

    sensitivity_df = run_threshold_sensitivity(
        catalog_path="data/aggregated_catalog.csv",
        hours_since_last_sale=hours_scenario,
        thresholds=thresholds_to_test,
    )
    print(f"\nAt {hours_scenario} hours since last sale:\n")
    print(sensitivity_df.to_string(index=False))
    print(
        "\nThis shows the tradeoff behind the threshold choice, not a "
        "correct answer. A lower threshold flags more products sooner "
        "at the cost of more false alarms; a higher one flags fewer, "
        "more confidently, but may miss real issues longer."
    )
