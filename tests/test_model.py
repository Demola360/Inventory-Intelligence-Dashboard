"""
Unit tests for the core anomaly detection logic and classification rule.
Run with: pytest tests/
"""

import sys
import os
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model import compute_anomaly_score, classify


def get_anomaly_score(velocity: float, hours_since_last_sale: float) -> float:
    return compute_anomaly_score(velocity, hours_since_last_sale)["anomaly_score"]


def test_zero_hours_means_zero_anomaly():
    """No time has passed, so there should be no anomaly at all."""
    score = get_anomaly_score(velocity=2.0, hours_since_last_sale=0)
    assert score == 0.0


def test_longer_gap_increases_score():
    """A longer period of no sales should never produce a lower score than a shorter one."""
    short_gap_score = get_anomaly_score(velocity=2.0, hours_since_last_sale=2)
    long_gap_score = get_anomaly_score(velocity=2.0, hours_since_last_sale=10)
    assert long_gap_score > short_gap_score


def test_faster_velocity_flags_sooner():
    """A faster-selling product should look more suspicious after the same
    gap than a slower-selling one."""
    slow_score = get_anomaly_score(velocity=0.2, hours_since_last_sale=5)
    fast_score = get_anomaly_score(velocity=5.0, hours_since_last_sale=5)
    assert fast_score > slow_score


def test_score_stays_within_valid_percentage_range():
    """The score is a percentage, it must never leave 0-100."""
    score = get_anomaly_score(velocity=3.0, hours_since_last_sale=24)
    assert 0.0 <= score <= 100.0


def test_known_exact_value():
    """
    When velocity x hours = ln(20), the probability of zero sales is
    exactly 5%, so the anomaly score should be exactly 95%. This proves
    the calculation itself, not just its direction.
    """
    expected_sales = math.log(20)
    score = get_anomaly_score(velocity=expected_sales, hours_since_last_sale=1)
    assert round(score, 2) == 95.00


def test_classify_critical_at_or_above_threshold():
    """A score at or above the configured threshold must be Critical."""
    assert classify(score=95.0, critical_threshold=95) == "Critical"
    assert classify(score=99.9, critical_threshold=95) == "Critical"


def test_classify_warning_band():
    """A score within 15 points below the threshold must be Warning."""
    assert classify(score=85.0, critical_threshold=95) == "Warning"
    assert classify(score=80.0, critical_threshold=95) == "Warning"


def test_classify_normal_below_warning_band():
    """A score more than 15 points below the threshold must be Normal."""
    assert classify(score=79.9, critical_threshold=95) == "Normal"
    assert classify(score=10.0, critical_threshold=95) == "Normal"


def test_classify_boundary_exact_threshold():
    """Exactly at the threshold should count as Critical, not Warning."""
    assert classify(score=90.0, critical_threshold=90) == "Critical"