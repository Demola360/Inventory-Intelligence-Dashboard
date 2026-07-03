"""
Inventory Intelligence Dashboard
---------------------------------
WHAT THIS APP DOES (plain English):
A shop's till system knows exactly what SHOULD be selling. If a normally
fast-moving product suddenly stops selling for several hours, that's often
a sign it's not actually on the shelf anymore (misplaced, damaged, stolen,
or a listing error) - even though the computer still says it's in stock.
This is called "phantom inventory".

Rather than making a staff member manually check every slow product, this
tool uses a statistical model (Poisson distribution) to work out how
UNUSUAL a sales gap really is for that specific product, and only flags
the ones worth a human going to check.

NOTE ON DATA: the underlying dataset is a UK-filtered subset of a public
online retail dataset, deliberately repurposed here to simulate a single
physical branch. See README for full details on this design choice.
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import hashlib

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# =====================================================================
# SECTION 1: LOADING THE DATA
# =====================================================================
DATA_FILE = "aggregated_catalog.csv"


@st.cache_data
def load_catalog(filepath: str) -> dict:
    """
    Load the pre-calculated product catalogue (SKU -> description + normal
    sales velocity) from a CSV file.
    """
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(
            f"Data file '{filepath}' was not found. The app needs this "
            "file to run - please check it has been uploaded alongside "
            "the app script."
        )
        return {}
    except pd.errors.EmptyDataError:
        st.error(f"Data file '{filepath}' is empty. Nothing to display.")
        return {}

    if df.empty or "StockCode" not in df.columns:
        st.error(
            "Data file was loaded but is missing expected columns "
            "(StockCode). Please check the file was generated correctly."
        )
        return {}

    df["StockCode"] = df["StockCode"].astype(str)
    catalog_df = df.set_index("StockCode")
    return catalog_df.to_dict("index")


# Fixed reference examples to illustrate low, medium, and high velocities
CURATED_SKUS = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53},
}


# =====================================================================
# SECTION 2: THE STATISTICAL MODEL
# =====================================================================
def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> dict:
    """
    Work out how UNUSUAL it is that a product has had zero sales for a
    given number of hours, given how fast it normally sells.
    """
    expected_sales = velocity * hours_since_last_sale
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }


def classify_priority(confidence: float, threshold: float) -> str:
    """Turn a raw confidence percentage into an actionable priority label."""
    if confidence >= threshold:
        return "CRITICAL"
    elif confidence >= (threshold - 15):
        return "WARNING"
    return "MONITOR"


# =====================================================================
# SECTION 3: SIMULATED OPERATIONAL DETAILS (MOCK DATA)
# =====================================================================
def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent, fake aisle/shelf reference for a given SKU."""
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible-looking but entirely FAKE unit price."""
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


def build_worklist(sku_catalog: dict, selected_sku: str, normal_velocity: float,
                   hours_zero_sales: float, confidence_threshold: float) -> pd.DataFrame:
    """Build a mock worklist table for the selected item and neighboring SKUs."""
    sku_list = list(sku_catalog.keys())
    selected_idx = sku_list.index(selected_sku)
    sample_skus = [
        selected_sku,
        sku_list[(selected_idx + 1) % len(sku_list)],
        sku_list[(selected_idx + 2) % len(sku_list)],
    ]

    rows = []
    for i, sku in enumerate(sample_skus):
        velocity = normal_velocity if i == 0 else sku_catalog[sku]["Calculated_Velocity"]

        result = compute_anomaly_confidence(velocity, hours_zero_sales)
        tier = classify_priority(result["anomaly_confidence"], confidence_threshold)

        mock_price = get_mock_unit_price(sku)
        simulated_revenue_at_risk = result["expected_sales"] * mock_price

        rows.append({
            "Task ID": f"TSK-{9400 + selected_idx + i}",
            "SKU": sku,
            "Description": sku_catalog[sku]["Description"],
            "Aisle Location (simulated)": get_mock_shelf_location(sku),
            "Unit Price (simulated)": f"£{mock_price:.2f}",
            "Est. Revenue at Risk (simulated)": f"£{simulated_revenue_at_risk:.2f}",
            "Anomaly Confidence": f"{result['anomaly_confidence']:.1f}%",
            "Priority Tier": tier,
        })

    return pd.DataFrame(rows)


# =====================================================================
# SECTION 4: APP LAYOUT & CONTROL FLOW
# =====================================================================
full_catalog = load_catalog(DATA_FILE)

if not full_catalog:
    st.stop()

st.sidebar.header("Simulation Controls")
show_all = st.sidebar.checkbox("Explore Full Catalogue")

sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),
    format_func=lambda x: f"{x} — {sku_catalog[x]['Description']}",
)

default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

normal_velocity = st.sidebar.slider(
    "Normal Sales Velocity (Units/Hour)",
    min_value=0.1,
    max_value=max(20.0, float(default_velocity) * 1.5),
    value=float(default_velocity),
    step=0.1,
    key=f"vel_{selected_sku}",
)

hours_zero_sales = st.sidebar.slider(
    "Current Hours with Zero Sales",
    min_value=1,
    max_value=24,
    value=3,
    step=1,
    key=f"hrs_{selected_sku}",
)

confidence_threshold = st.sidebar.slider(
    "Alert Sensitivity (%)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="sensitivity_slider",
)

# --- Model Calculations ---
result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
prob_of_slow_gap = result["probability_of_zero_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

# --- UI Header ---
st.title("Inventory Intelligence Dashboard")
st.markdown(f"**Analyzing Core Inventory Stream** | Selected Item: `{selected_sku}` - *{product_desc}*")

with st.expander("Methodology & Operational Boundaries (MVP Framework)"):
    st.markdown("""
    * **Why Poisson?** It only needs a single number (the average sales rate) to work, making it usable even for low-volume products where more data-hungry models would be unreliable.
    * **Operational baseline:** trading hours (06:00–20:00) were derived directly from the data itself, not assumed - see README for detail.
    * **Everything under "Automated Floor Staff Worklist" below (locations, prices, revenue figures) is simulated for demonstration only and is not live operational data.**
    """)

st.markdown("---")

# --- Top Level Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Historical Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Observed Silence Window", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales (in window)", f"{expected_sales_in_window:.1f} units")

st.markdown("---")

# --- Anomaly Assessment ---
st.markdown("### Anomaly Assessment")
if phantom_stock_confidence >= confidence_threshold:
    st.error(f"""
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** This product has recorded zero sales for {hours_zero_sales} hours.
    Given its normal sales rate, there is only a {prob_of_slow_gap * 100:.2f}% chance this is a
    natural quiet spell. Recommended action: a human should verify the shelf/pick location.
    """)
elif phantom_stock_confidence >= (confidence_threshold - 15):
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** Sales are unusually slow but still within marginal statistical variance.
    Worth monitoring before dispatching anyone to check.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** This sales gap falls within expected normal variance for a product
    selling at {normal_velocity:.1f} units/hr. No action required.
    """)

# --- Simulated Operational Worklist ---
st.markdown("---")
st.markdown("### Automated Floor Staff Worklist *(simulated demo output)*")
st.caption(
    "⚠️ Everything in this table and summary metrics below (locations, prices, and revenue figures) is "
    "simulated for demonstration purposes and is not connected to a real warehouse, till, or pricing system."
)

worklist_df = build_worklist(
    sku_catalog, selected_sku, normal_velocity, hours_zero_sales, confidence_threshold
)

critical_count = (worklist_df["Priority Tier"] == "CRITICAL").sum()
warning_count = (worklist_df["Priority Tier"] == "WARNING").sum()

# Recompute total simulated revenue at risk from the dataframe for the summary metric
at_risk_mask = worklist_df["Priority Tier"].isin(["CRITICAL", "WARNING"])
total_revenue_at_risk = (
    worklist_df.loc[at_risk_mask, "Est. Revenue at Risk (simulated)"]
    .str.replace("£", "", regex=False)
    .astype(float)
    .sum()
)

st.subheader("Operational Exceptions & Simulated Financial Exposure")

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric(
        label="Critical Breaches (simulated)",
        value=f"{critical_count} SKUs",
        delta=f"+{critical_count} Action Required" if critical_count > 0 else "Clear",
        delta_color="inverse",
    )
with metric_col2:
    st.metric(
        label="Warning Flags (simulated)",
        value=f"{warning_count} SKUs",
        delta=f"{warning_count} Monitored" if warning_count > 0 else "Stable",
    )
with metric_col3:
    st.metric(
        label="Simulated Revenue at Risk",
        value=f"£{total_revenue_at_risk:.2f}",
        delta="Illustrative only" if total_revenue_at_risk > 0 else "No Exposure",
        delta_color="off",
    )

st.dataframe(
    worklist_df, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Priority Tier": st.column_config.TextColumn(
            "Priority Tier",
            help="Automated alert classification level."
        )
    }
)

st.markdown("---")
