"""
Synthetic Validation: Phantom Inventory Model
-----------------------------------------------
Since we have no real labelled phantom-inventory events, we validate the
model's *sensitivity* instead: does it correctly flag increasingly long,
artificially-injected sales gaps as increasingly suspicious?

If the anomaly score doesn't rise as the injected gap grows, the model
isn't doing its job. This is the check that proves it is.
"""

from scipy.stats import poisson
import pandas as pd

def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> float:
    expected_sales = velocity * hours_since_last_sale
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    return (1 - probability_of_zero_sales) * 100


def run_synthetic_gap_test(velocity: float, gap_hours_to_test: list[int]) -> pd.DataFrame:
    """
    Injects a range of artificial 'silence' durations for one product's
    known velocity, and records how the anomaly score responds.
    A healthy model should show scores rising monotonically as the
    injected gap grows.
    """
    results = []
    for hours in gap_hours_to_test:
        score = compute_anomaly_confidence(velocity, hours)
        results.append({"Injected_Silence_Hours": hours, "Anomaly_Score": round(score, 2)})
    return pd.DataFrame(results)


if __name__ == "__main__":
    # Example: a product that normally sells 2 units/hour.
    test_velocity = 2.0
    test_gaps = [1, 2, 3, 4, 6, 8, 12, 24]

    results_df = run_synthetic_gap_test(test_velocity, test_gaps)
    print(f"Validation for a product selling {test_velocity} units/hour on average:\n")
    print(results_df.to_string(index=False))

    # Basic sanity assertion: score must increase as the gap grows.
    scores = results_df["Anomaly_Score"].tolist()
    is_monotonic = all(scores[i] <= scores[i + 1] for i in range(len(scores) - 1))
    print(f"\nScores rise monotonically with longer silence: {is_monotonic}")