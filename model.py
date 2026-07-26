"""
Core anomaly detection logic for the Inventory Intelligence Dashboard.
This is the single source of truth. app.py, the test suite, and the
validation script all import from here rather than redefining it.
"""

from scipy.stats import poisson


def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> dict:
    """
    How unusual is it that this product has had zero sales for this long?
    Pure function, no Streamlit calls, no side effects, so it can be tested independently.
    """
    expected_sales = velocity * hours_since_last_sale  # lambda for the Poisson model
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }