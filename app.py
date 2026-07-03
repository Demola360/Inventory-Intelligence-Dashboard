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
    """Load the pre-calculated product catalogue from a CSV file."""
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
    """Calculate the probability that zero sales is an actual anomaly."""
    expected_sales = velocity * hours_since_last_sale
    probability_of_zero_sales = poisson.pmf(0, expected_sales)
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }


def classify_priority(confidence: float, threshold: float) -> str:
    """Turn raw statistical confidence into a clear, operational label."""
    if confidence >= threshold:
        return "🚨 CRITICAL (Check Shelf)"
    elif confidence >= (threshold - 15):
        return "⚠️ WARNING (Monitor)"
    return "✅ NORMAL"


# =====================================================================
# SECTION 3: SIMULATED OPERATIONS (MOCK DATA)
# =====================================================================
def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent, fake aisle reference for the worklist."""
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


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
tier = classify_priority(phantom_stock_confidence, confidence_threshold)

# --- UI Header ---
st.title("Inventory Intelligence Dashboard")
st.markdown(f"**Analyzing Core Inventory Stream** | Selected Item: `{selected_sku}` - *{product_desc}*")

with st.expander("Methodology & Simulation Purpose (MVP Framework)"):
    st.markdown("""
    * **Simulating Live Data:** Retail environments change constantly. The sliders on the left act as a live simulation control panel, letting stakeholders instantly tweak sales velocities and hours of silence to see exactly how the dashboard adapts to fluid store patterns.
    * **Why Poisson?** It only needs a single baseline metric (the average historical sales rate) to successfully flag a dead sales window, making it highly reliable even for low-volume inventory tracks.
    * **Operational Boundaries:** Aisle locations are mock values generated consistently via SKU hashing to showcase a scannable floor-staff output without relying on a live production warehouse map.
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
st.markdown("### Status Assessment")
if "CRITICAL" in tier:
    st.error(f"""
    ### {tier} ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** This product has recorded zero sales for {hours_zero_sales} hours. 
    Given its normal movement patterns, there is only a {prob_of_slow_gap * 100:.2f}% chance this gap is natural. 
    A team member needs to check the shelf immediately.
    """)
elif "WARNING" in tier:
    st.warning(f"""
    ### {tier} ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** Sales are slower than normal but still sit within marginal statistical variance. 
    Monitor the item over the next shift before dispatching a physical check.
    """)
else:
    st.success(f"""
    ### {tier} ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** This sales gap falls entirely within normal, expected trading fluctuations for an item selling at {normal_velocity:.1f} units/hr. No operational action is required.
    """)

# --- Scannable Floor Staff Action Table ---
st.markdown("---")
st.markdown("### Floor Staff Action List")

# Create a clean, single-row dataframe representing ONLY the active product being evaluated
action_data = pd.DataFrame([{
    "SKU Code": selected_sku,
    "Product Description": product_desc,
    "Where to Check (simulated)": get_mock_shelf_location(selected_sku),
    "Current Status": tier
}])

st.dataframe(
    action_data, 
    use_container_width=True, 
    hide_index=True
)

st.markdown("---")
