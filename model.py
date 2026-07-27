"""
Core anomaly detection logic for the Inventory Intelligence Dashboard.
This is the single source of truth, app.py, the test suite, and the
validation script all import from here rather than redefining it.
"""

from scipy.stats import poisson


def compute_anomaly_score(velocity: float, hours_since_last_sale: float) -> dict:
    """
    How unusual is it that this product has had zero sales for this long?

    Under the Poisson model, this calculates the probability of zero sales
    given the product's assumed rate, then inverts it into a score where
    higher numbers mean more unusual. This is a decision-support measure,
    not a calibrated probability that stock is physically missing.
    """
    expected_sales = velocity * hours_since_last_sale
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    anomaly_score = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_score": anomaly_score,
    }


def classify(score: float, critical_threshold: float) -> str:
    """
    Applies the alert classification business rule. Warning begins 15
    percentage points below the Critical threshold, a demonstration rule
    (see BR01 in docs/requirements.md), not an empirically calibrated one.
    """
    if score >= critical_threshold:
        return "Critical"
    elif score >= (critical_threshold - 15):
        return "Warning"
    else:
        return "Normal"
