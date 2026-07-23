"""
Inventory Intelligence Dashboard
---------------------------------
A retail store's inventory system may say an item is in stock when it
physically isn't — stolen, misplaced, or damaged. This is phantom inventory.

This tool uses a Poisson model to work out how unusual a sales gap is for
a given product, and only flags the ones worth a staff member checking.

The dataset is a UK-filtered subset of a public online retail dataset,
deliberately repurposed to simulate a single physical branch.
"""

import streamlit as st
import pandas as pd
from scipy.stats import poisson
import hashlib

st.set_page_config(
    page_title="Inventory Intelligence Dashboard",
    layout="wide"
)

DATA_FILE = "data/aggregated_catalog.csv"


@st.cache_data  # stops the CSV being re-read on every widget interaction
def load_catalog(filepath: str) -> dict:
    """Load product catalogue (SKU → description + sales velocity) from CSV."""
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

    # StockCode as string to avoid silently dropping leading zeros (e.g. "07001" → 7001)
    df["StockCode"] = df["StockCode"].astype(str)
    catalog_df = df.set_index("StockCode")

    # Dict over DataFrame — the app only ever needs one SKU at a time, O(1) lookup
    return catalog_df.to_dict("index")


# 6 SKUs selected by velocity range so a first-time visitor sees varied product
# behaviour without scrolling through all 3,645 products
CURATED_SKUS = {
    "22439": {"Description": "6 ROCKET BALLON", "Calculated_Velocity": 0.59},
    "22046": {"Description": "TEA WRAPPING PAPER", "Calculated_Velocity": 0.59},
    "22713": {"Description": "CARD I LOVE LONDON", "Calculated_Velocity": 1.13},
    "17003": {"Description": "BROCADE RING PURSE", "Calculated_Velocity": 8.04},
    "90062": {"Description": "CARNIVAL BRACELET", "Calculated_Velocity": 0.20},
    "22670": {"Description": "FRENCH WC SIGN BLUE METAL", "Calculated_Velocity": 0.53},
}


def compute_anomaly_confidence(velocity: float, hours_since_last_sale: float) -> dict:
    """
    How unusual is it that this product has had zero sales for this long?
    Pure function — no Streamlit calls, no side effects, so it can be tested independently.
    """
    expected_sales = velocity * hours_since_last_sale  # lambda for the Poisson model

    # scipy's implementation, not hand-rolled — well tested and peer reviewed
    probability_of_zero_sales = poisson.pmf(0, expected_sales)

    # Flip probability into anomaly confidence — easier for non-technical staff to act on
    anomaly_confidence = (1 - probability_of_zero_sales) * 100

    return {
        "expected_sales": expected_sales,
        "probability_of_zero_sales": probability_of_zero_sales,
        "anomaly_confidence": anomaly_confidence,
    }


# Mock data only — not connected to any real warehouse, till, or pricing system

def get_mock_shelf_location(sku: str) -> str:
    """Generate a consistent fake shelf reference for a given SKU."""
    # md5 hash not random — same SKU must always map to the same location across reruns
    hash_val = int(hashlib.md5(str(sku).encode()).hexdigest(), 16)
    return f"Aisle {(hash_val % 24) + 1}, Shelf {chr(65 + (hash_val % 6))}-{(hash_val % 10) + 1}"


def get_mock_unit_price(sku: str) -> float:
    """Generate a plausible but entirely fake unit price."""
    sku_digits = "".join(filter(str.isdigit, str(sku)))
    if not sku_digits:
        return 4.50
    return float((int(sku_digits) % 135 + 15) / 10)


full_catalog = load_catalog(DATA_FILE)
if not full_catalog:
    st.stop()  # error already shown in load_catalog()

st.sidebar.header("Simulation Controls")

show_all = st.sidebar.checkbox("View all Products")
sku_catalog = full_catalog if show_all else CURATED_SKUS

selected_sku = st.sidebar.selectbox(
    "Select Target Product",
    options=list(sku_catalog.keys()),
    index=min(4, len(sku_catalog) - 1),  # guards against short list going out of bounds
    format_func=lambda x: f"{sku_catalog[x]['Description']} ({x})",
)

default_velocity = sku_catalog[selected_sku]["Calculated_Velocity"]
product_desc = sku_catalog[selected_sku]["Description"]

st.sidebar.markdown("---")

# key tied to selected_sku so switching products doesn't carry over stale slider values
normal_velocity = st.sidebar.slider(
    "Normal Sales Velocity (Units/Hour)",
    min_value=0.1,
    max_value=max(20.0, float(default_velocity) * 1.5),
    value=float(default_velocity),
    step=0.1,
    key=f"vel_{selected_sku}",
    help="How fast this product normally sells. Higher = a faster-moving product.",
)

hours_zero_sales = st.sidebar.slider(
    "Current Hours with Zero Sales",
    min_value=1,
    max_value=24,
    value=3,
    step=1,
    key=f"hrs_{selected_sku}",
    help="How many hours it's been since this product last sold. Drag this up to simulate a longer period.",
)

confidence_threshold = st.sidebar.slider(
    "Alert Sensitivity (%)",
    min_value=80,
    max_value=99,
    value=95,
    step=1,
    key="sensitivity_slider",
    help="How sure the model needs to be before it raises a CRITICAL alert. Lower = more alerts, higher = fewer but more certain ones.",
)

result = compute_anomaly_confidence(normal_velocity, hours_zero_sales)
expected_sales_in_window = result["expected_sales"]
phantom_stock_confidence = result["anomaly_confidence"]

# Warning fires 15 points below Critical — a watch tier before action is required
is_flagged = phantom_stock_confidence >= (confidence_threshold - 15)
is_critical = phantom_stock_confidence >= confidence_threshold

mock_price = get_mock_unit_price(selected_sku)
# Revenue only shown when item is flagged — a normal item gets no revenue figure at all
simulated_lost_revenue = expected_sales_in_window * mock_price if is_flagged else 0.0

st.title("Inventory Intelligence Dashboard")
st.markdown(
    "This is an intelligent inventory monitoring tool that identifies products with unusual"
    " low sales volume and prioritises them for investigation."
)

if is_critical:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in **{hours_zero_sales} hours**. "
        f"Based on its usual sales pattern, this is longer than expected and may indicate a stock issue. "
        f"A quick shelf check is recommended."
    )
elif is_flagged:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has not sold in the last **{hours_zero_sales} hours**, "
        f"despite usually selling around {normal_velocity:.0f} unit{'s' if normal_velocity >= 1.5 or normal_velocity < 0.5 else ''} per hour. "
        f"At this sales rate, we would normally expect some activity by now. Consider checking the shelf availability or inventory records."
    )
else:
    narrative_text = (
        f"**{product_desc} ({selected_sku})** has had no sales in the last **{hours_zero_sales} hours**. "
        f"This is not unusual because the product typically sells slowly, so a short period without sales is expected. "
        f"No action is recommended at this time."
    )

st.info(narrative_text)

with st.expander("How does the model decide what's suspicious?"):
    st.markdown("""
The model asks a simple question: based on how fast this product normally sells, how likely is it to genuinely have zero sales this long?

Very unlikely → flags as suspicious.

Quite likely → no action required.

That probability is converted into a single anomaly confidence percentage for proper understanding.

**Try it:** use the sliders in the sidebar to change the sales rate, hours without sales, or
confidence score, and watch the assessment below update in real time.
    """)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Normal Sales Rate", f"{normal_velocity:.2f} units/hr")
with col2:
    st.metric("Hours Since Last Sale", f"{hours_zero_sales} hours")
with col3:
    st.metric("Expected Sales in This Window", f"{expected_sales_in_window:.1f} units")

st.markdown("---")
st.markdown("### Anomaly Assessment")

if is_critical:
   st.error(f"""
### CRITICAL: HIGH SHELF-CHECK PRIORITY ({phantom_stock_confidence:.1f}% Anomaly Score)
**What this means:** it is statistically unusual for this product to have zero sales this long, given its normal rate. This flags it as worth a physical check, it does not confirm stock is missing.
**Action Required:** Verify the item at its location immediately.
""")
elif is_flagged:
    st.warning(f"""
    ### WARNING: ELEVATED RISK ({phantom_stock_confidence:.1f}% Anomaly Score)
    **Observation:** Sales are unusually slow but still within marginal statistical variance. Worth monitoring before dispatching staff.
    """)
else:
    st.success(f"""
    ### STATUS NORMAL ({phantom_stock_confidence:.1f}% Anomaly Score)
    **Observation:** This sales gap falls within expected normal variance. No action required.
    """)

if is_flagged:
    st.markdown("---")
    st.markdown("### Recommended Action")
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
