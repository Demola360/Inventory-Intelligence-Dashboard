"""
Inventory Intelligence Dashboard
---------------------------------
WHAT THIS APP DOES:
A store's till system knows exactly what SHOULD be selling. If a normally
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
from scipy.stats import poisson
import hashlib

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

# LOADING THE DATA

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


# Curated list for the default view
CURATED_SKUS = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53},
}


# THE STATISTICAL MODEL

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


# SIMULATED OPERATIONAL DETAILS (MOCK DATA)

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



# APP LAYOUT & CONTROL FLOW

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

# Model calculations (done once, reused everywhere below)
result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

is_flagged = phantom_stock_confidence >= (confidence_threshold - 15)
is_critical = phantom_stock_confidence >= confidence_threshold

mock_price = get_mock_unit_price(selected_sku)
simulated_lost_revenue = expected_sales_in_window * mock_price if is_flagged else 0.0

# UI Header
st.title("Inventory Intelligence Dashboard")
st.markdown(f"**Analyzing Core Inventory Stream** | Selected Item: `{selected_sku}` - *{product_desc}*")

with st.expander("Methodology, Sliders, & Operational Boundaries (MVP Framework)"):
    with st.expander("ℹ️ About this Dashboard"):
    st.markdown("""
**Purpose:** This dashboard helps retailers identify products that are likely missing from the shop floor, even when the inventory system still shows them as being in stock.
**How it works:** It compares each product's normal sales pattern with its current sales activity. If a product stops selling for longer than expected, the system estimates the likelihood that it has become phantom stock and prioritises it for investigation.
**Try it:** Use the controls in the sidebar to change the expected sales rate, hours without sales, and alert sensitivity to see how the risk level changes in real time.
""")

st.markdown("---")

# Top-level metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Historical Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Time Without Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales (in window)", f"{expected_sales_in_window:.1f} units")

st.markdown("---")

# Anomaly Assessment 
st.markdown("### Anomaly Assessment")

if is_critical:
    st.error(f"""
    ### CRITICAL: PHANTOM INVENTORY SUSPECTED ({phantom_stock_confidence:.1f}% Confidence)
    **Action Required:** Verify the item at its location immediately.
    """)
elif is_flagged:
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Confidence)
    **Observation:** Sales are unusually slow but still within marginal statistical variance. Worth monitoring before dispatching staff.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Confidence)
    **Observation:** This sales gap falls within expected normal variance. No action required.
    """)

# Action card only appears when the item is flagged
if is_flagged:
    st.markdown("---")
    st.markdown("### Recommended Action *(simulated demo output)*")
    st.caption(
        "Shelf location and revenue figures below are simulated for "
        "demonstration purposes and are not connected to a real warehouse, "
        "till, or pricing system."
    )

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.metric("Where to Check", get_mock_shelf_location(selected_sku))
    with action_col2:
        st.metric("Potential Lost Revenue", f"£{simulated_lost_revenue:.2f}")

st.markdown("---")
