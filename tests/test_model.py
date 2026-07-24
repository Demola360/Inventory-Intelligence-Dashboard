"""
Unit tests for the core anomaly detection logic.
Run with: pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scipy.stats import poisson


def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> float:
    expected_sales = velocity * hours_since_last_sale
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    return (1 - probability_of_zero_sales) * 100


def test_zero_hours_means_zero_anomaly():
    """No time has passed, so there should be no anomaly at all."""
    score = compute_anomaly_confidence(velocity=2.0, hours_since_last_sale=0)
    assert score == 0.0


def test_longer_gap_increases_score():
    """A longer period of no sales should never produce a lower score than a shorter one."""
    short_gap_score = compute_anomaly_confidence(velocity=2.0, hours_since_last_sale=2)
    long_gap_score = compute_anomaly_confidence(velocity=2.0, hours_since_last_sale=10)
    assert long_gap_score > short_gap_score


def test_faster_velocity_flags_sooner():
    """A faster-selling product should look more suspicious after the same
    gap than a slower-selling one."""
    slow_score = compute_anomaly_confidence(velocity=0.2, hours_since_last_sale=5)
    fast_score = compute_anomaly_confidence(velocity=5.0, hours_since_last_sale=5)
    assert fast_score > slow_score


def test_score_stays_within_valid_percentage_range():
    """The score is a percentage, it must never leave 0-100."""
    score = compute_anomaly_confidence(velocity=3.0, hours_since_last_sale=24)
    assert 0.0 <= score <= 100.0